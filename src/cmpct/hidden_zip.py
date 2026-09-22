from __future__ import annotations

"""Bounded, fail-closed discovery for optional hidden-ZIP virtualization.

This module is deliberately not a second ZIP parser. It cheaply rejects ordinary
files before any EOCD-tail read, proves only a bounded conventional ZIP envelope,
and uses exact compressed-payload identity to estimate reusable structure. Any
rejection means "store normally", never "fail the build".
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import stat
import struct
import zipfile

from .codec import _compressed_payload

LOCAL_SIG = b"PK\x03\x04"
EOCD_SIG = b"PK\x05\x06"
EOCD_MIN = 22
MAX_COMMENT = 65535
MAX_TAIL = EOCD_MIN + MAX_COMMENT
MAX_ENTRIES = 8192
MAX_CENTRAL_DIRECTORY = 16 * 1024 * 1024
ZIP64_U16 = 0xFFFF
ZIP64_U32 = 0xFFFFFFFF
SUPPORTED_METHODS = frozenset((zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED))
EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))
MIN_VERIFIED_REUSE = 2176
_REPEATED = object()


@dataclass(frozen=True)
class HiddenZipPreflight:
    eligible: bool
    reason: str
    file_size: int
    head_bytes_read: int
    tail_bytes_read: int
    entries: int = 0
    central_directory_size: int = 0
    central_directory_offset: int = 0
    eocd_offset: int = 0


@dataclass(frozen=True)
class HiddenZipAdmission:
    rel: str
    stamp: tuple[int, int, int, int]
    verified_reuse_bytes: int


@dataclass(frozen=True)
class HiddenZipObservation:
    admitted: tuple[HiddenZipAdmission, ...]
    files_observed: int
    candidates_parsed: int
    head_bytes_read: int
    tail_bytes_read: int
    verification_bytes_read: int
    rejects: tuple[tuple[str, int], ...]


def hidden_zip_preflight(path: Path) -> HiddenZipPreflight:
    """Return a conservative envelope verdict and exact discovery I/O accounting."""
    path = Path(path)
    head_read = 0
    try:
        size = path.stat().st_size
        if size < EOCD_MIN:
            return HiddenZipPreflight(False, "too_small", size, 0, 0)
        with path.open("rb") as f:
            head = f.read(4)
            head_read = len(head)
            # Optional discovery deliberately ignores prefixed/self-extracting ZIPs. Exactness is
            # unaffected because rejected files continue through ordinary opaque storage.
            if head != LOCAL_SIG:
                return HiddenZipPreflight(False, "local_signature_miss", size, head_read, 0)
            tail_n = min(size, MAX_TAIL)
            f.seek(size - tail_n)
            tail = f.read(tail_n)

        pos = len(tail)
        while True:
            idx = tail.rfind(EOCD_SIG, 0, pos)
            if idx < 0:
                return HiddenZipPreflight(False, "eocd_not_found", size, head_read, len(tail))
            if idx + EOCD_MIN <= len(tail):
                disk, cd_disk, n_disk, n_total, cd_size, cd_off, comment_len = struct.unpack_from(
                    "<HHHHIIH", tail, idx + 4
                )
                if idx + EOCD_MIN + comment_len == len(tail):
                    break
            pos = idx

        absolute = size - tail_n + idx
        if disk != 0 or cd_disk != 0 or n_disk != n_total:
            return HiddenZipPreflight(False, "multi_disk", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if n_total == ZIP64_U16 or cd_size == ZIP64_U32 or cd_off == ZIP64_U32:
            return HiddenZipPreflight(False, "zip64_optional_path_rejected", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if n_total == 0:
            return HiddenZipPreflight(False, "empty_archive", size, head_read, len(tail), 0, cd_size, cd_off, absolute)
        if n_total > MAX_ENTRIES:
            return HiddenZipPreflight(False, "entry_budget", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if cd_size > MAX_CENTRAL_DIRECTORY:
            return HiddenZipPreflight(False, "central_directory_budget", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if cd_off > absolute or cd_size > absolute - cd_off:
            return HiddenZipPreflight(False, "central_directory_bounds", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        return HiddenZipPreflight(True, "eligible", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
    except (OSError, struct.error, ValueError):
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        return HiddenZipPreflight(False, "io_or_structure_error", size, head_read, 0)


def _physical_hidden_files(root: Path):
    """Yield lexical first-inode owners, mirroring Builder's hardlink ownership boundary."""
    root = Path(root)
    seen: set[tuple[int, int]] = set()

    def walk(absdir: Path, prefix: str = ""):
        with os.scandir(absdir) as it:
            entries = sorted(it, key=lambda e: e.name)
        for e in entries:
            rel = f"{prefix}/{e.name}" if prefix else e.name
            st = e.stat(follow_symlinks=False)
            if stat.S_ISDIR(st.st_mode):
                yield from walk(Path(e.path), rel)
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            ik = (int(st.st_dev), int(st.st_ino))
            if st.st_nlink > 1:
                if ik in seen:
                    continue
                seen.add(ik)
            if Path(e.name).suffix.lower() in EXPLICIT_SUFFIXES:
                continue
            yield Path(e.path), rel, (ik[0], ik[1], int(st.st_size), int(st.st_mtime_ns))

    yield from walk(root)


def _exact_stream_descriptors(path: Path):
    """Return exact compressed-stream identities or a fail-closed rejection reason."""
    try:
        with zipfile.ZipFile(path) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if not infos:
                return None, "empty_members", 0
            if any(i.flag_bits & 1 for i in infos):
                return None, "encrypted", 0
            if any(i.compress_type not in SUPPORTED_METHODS for i in infos):
                return None, "unsupported_method", 0
            descriptors = set()
            read = 0
            for i in infos:
                if i.file_size <= 0:
                    continue
                payload = _compressed_payload(path, i)
                if len(payload) != i.compress_size:
                    return None, "compressed_payload_bounds", read + len(payload)
                read += len(payload)
                descriptors.add((int(i.compress_type), len(payload), hashlib.sha256(payload).digest()))
            if not descriptors:
                return None, "no_payload_members", read
            return descriptors, None, read
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, struct.error):
        return None, "exact_parse_rejected", 0


def observe_hidden_zip_admission(root: Path, *, min_verified_reuse: int = MIN_VERIFIED_REUSE) -> HiddenZipObservation:
    """Discover hidden candidates with bounded memory and exact repeated-stream identity.

    Two passes intentionally trade candidate-only re-reading for bounded whole-tree memory: pass one
    retains one compact owner state per exact stream, never per-path descriptor graphs; pass two recomputes
    each candidate locally to derive its verified reusable bytes and admission record.
    """
    root = Path(root)
    owners: dict[tuple[int, int, bytes], object] = {}
    rejects: Counter[str] = Counter()
    parsed = head_bytes = tail_bytes = verification_bytes = 0

    candidates = list(_physical_hidden_files(root))
    for path, rel, stamp in candidates:
        pf = hidden_zip_preflight(path)
        head_bytes += pf.head_bytes_read
        tail_bytes += pf.tail_bytes_read
        if not pf.eligible:
            rejects[pf.reason] += 1
            continue
        descriptors, reason, read = _exact_stream_descriptors(path)
        verification_bytes += read
        if descriptors is None:
            rejects[reason or "exact_parse_rejected"] += 1
            continue
        parsed += 1
        for d in descriptors:
            prior = owners.get(d)
            if prior is None:
                owners[d] = rel
            elif prior != rel:
                owners[d] = _REPEATED

    admitted: list[HiddenZipAdmission] = []
    for path, rel, stamp in candidates:
        pf = hidden_zip_preflight(path)
        head_bytes += pf.head_bytes_read
        tail_bytes += pf.tail_bytes_read
        if not pf.eligible:
            continue
        descriptors, reason, read = _exact_stream_descriptors(path)
        verification_bytes += read
        if descriptors is None:
            continue
        reuse = sum(d[1] for d in descriptors if owners.get(d) is _REPEATED)
        if reuse >= int(min_verified_reuse):
            admitted.append(HiddenZipAdmission(rel, stamp, reuse))

    return HiddenZipObservation(
        tuple(admitted), len(candidates), parsed, head_bytes, tail_bytes, verification_bytes, tuple(sorted(rejects.items()))
    )


def admission_is_current(root: Path, admission: HiddenZipAdmission) -> bool:
    """Revalidate the physical first-owner stamp immediately before canonical storage selection."""
    try:
        st = os.stat(Path(root) / admission.rel, follow_symlinks=False)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode):
        return False
    current = (int(st.st_dev), int(st.st_ino), int(st.st_size), int(st.st_mtime_ns))
    return current == admission.stamp
