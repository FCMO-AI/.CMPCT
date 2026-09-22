from __future__ import annotations

"""Bounded, fail-closed discovery for optional hidden-ZIP virtualization.

This is deliberately not a second ZIP parser. It cheaply rejects ordinary files,
proves only a bounded conventional ZIP envelope, and uses exact compressed-payload
identity to estimate reusable structure. Rejection means "store normally".
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
# Match the existing reader hardening ceiling: optional discovery must never route a
# candidate requiring more logical materialization than one directly decoded object.
MAX_CANDIDATE_LOGICAL_BYTES = 256 * 1024 * 1024
# Tree-wide ceilings bound optional observation state independently of per-ZIP limits.
MAX_OBSERVATION_FILES = 262144
MAX_OBSERVATION_DESCRIPTORS = 131072
ZIP64_U16 = 0xFFFF
ZIP64_U32 = 0xFFFFFFFF
SUPPORTED_METHODS = frozenset((zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED))
EXPLICIT_SUFFIXES = frozenset((".zip", ".whl"))
MIN_VERIFIED_REUSE = 2176


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


def _physical_observation_files(root: Path):
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
            explicit = Path(e.name).suffix.lower() in EXPLICIT_SUFFIXES
            yield Path(e.path), rel, (ik[0], ik[1], int(st.st_size), int(st.st_mtime_ns)), explicit

    yield from walk(root)


def _metadata_descriptors(path: Path):
    """Return necessary-condition descriptors and declared logical work without payload reads."""
    try:
        with zipfile.ZipFile(path) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            if not infos:
                return None, 0, 0, "empty_members"
            logical_bytes = sum(max(0, int(i.file_size)) for i in infos)
            if any(i.flag_bits & 1 for i in infos):
                return None, len(infos), logical_bytes, "encrypted"
            if any(i.compress_type not in SUPPORTED_METHODS for i in infos):
                return None, len(infos), logical_bytes, "unsupported_method"
            descriptors = {
                (int(i.compress_type), int(i.compress_size), int(i.file_size), int(i.CRC))
                for i in infos
                if i.file_size > 0
            }
            if not descriptors:
                return None, len(infos), logical_bytes, "no_payload_members"
            return descriptors, len(infos), logical_bytes, None
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, struct.error):
        return None, 0, 0, "exact_parse_rejected"


def _verify_stream(path: Path, descriptor: tuple[int, int, int, int]):
    """Hash only payloads matching a repeated metadata hint."""
    method, compressed_size, _file_size, _crc = descriptor
    identities: set[tuple[int, int, bytes]] = set()
    read = 0
    try:
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir() or (
                    int(info.compress_type), int(info.compress_size), int(info.file_size), int(info.CRC)
                ) != descriptor:
                    continue
                payload = _compressed_payload(path, info)
                read += len(payload)
                if len(payload) != compressed_size:
                    return None, read
                identities.add((method, compressed_size, hashlib.sha256(payload).digest()))
        return identities or None, read
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, struct.error):
        return None, read


def observe_hidden_zip_admission(
    root: Path,
    *,
    min_verified_reuse: int = MIN_VERIFIED_REUSE,
    max_observation_files: int = MAX_OBSERVATION_FILES,
    max_observation_descriptors: int = MAX_OBSERVATION_DESCRIPTORS,
    max_candidate_logical_bytes: int = MAX_CANDIDATE_LOGICAL_BYTES,
) -> HiddenZipObservation:
    """Discover hidden candidates with bounded metadata pruning then exact stream proof."""
    root = Path(root)
    rejects: Counter[str] = Counter()
    stamps: dict[str, tuple[int, int, int, int]] = {}
    hidden: set[str] = set()
    parsed = head_bytes = tail_bytes = verification_bytes = descriptor_count = files_observed = 0
    candidates: list[tuple[Path, str, bool, set[tuple[int, int, int, int]]]] = []
    metadata_owners: Counter[tuple[int, int, int, int]] = Counter()

    for path, rel, stamp, explicit in _physical_observation_files(root):
        files_observed += 1
        if files_observed > int(max_observation_files):
            rejects["observation_file_budget"] += 1
            return HiddenZipObservation((), files_observed, parsed, head_bytes, tail_bytes, 0, tuple(sorted(rejects.items())))

        # Evidence providers obey the same optional envelope as hidden candidates; explicit storage
        # semantics are untouched because rejection only removes this file from reuse evidence.
        pf = hidden_zip_preflight(path)
        head_bytes += pf.head_bytes_read
        tail_bytes += pf.tail_bytes_read
        if not pf.eligible:
            rejects[("explicit_" if explicit else "") + pf.reason] += 1
            continue

        descriptors, entries, logical_bytes, reason = _metadata_descriptors(path)
        if descriptors is None:
            rejects[("explicit_" if explicit else "") + (reason or "exact_parse_rejected")] += 1
            continue
        # Canonical VZIP recipe construction fully decompresses members. Reject from metadata before
        # that future path can turn a tiny compressed candidate into unbounded logical materialization.
        if logical_bytes > int(max_candidate_logical_bytes):
            rejects[("explicit_" if explicit else "") + "logical_work_budget"] += 1
            continue
        descriptor_count += entries
        if descriptor_count > int(max_observation_descriptors):
            rejects["observation_descriptor_budget"] += 1
            return HiddenZipObservation((), files_observed, parsed, head_bytes, tail_bytes, 0, tuple(sorted(rejects.items())))
        stamps[rel] = stamp
        if not explicit:
            hidden.add(rel)
        parsed += 1
        candidates.append((path, rel, explicit, descriptors))
        metadata_owners.update(descriptors)

    repeated_hints = {d for d, count in metadata_owners.items() if count >= 2}
    exact_owners: dict[tuple[int, int, bytes], set[str]] = {}
    for path, rel, _explicit, descriptors in candidates:
        for descriptor in descriptors & repeated_hints:
            identities, read = _verify_stream(path, descriptor)
            verification_bytes += read
            if identities is None:
                rejects["verification_rejected"] += 1
                continue
            for identity in identities:
                exact_owners.setdefault(identity, set()).add(rel)

    reuse: Counter[str] = Counter()
    for identity, rels in exact_owners.items():
        if len(rels) < 2:
            continue
        for rel in rels:
            reuse[rel] += identity[1]

    admitted = tuple(
        HiddenZipAdmission(rel, stamps[rel], int(reuse[rel]))
        for rel in sorted(hidden)
        if reuse[rel] >= int(min_verified_reuse)
    )
    return HiddenZipObservation(
        admitted, files_observed, parsed, head_bytes, tail_bytes, verification_bytes, tuple(sorted(rejects.items()))
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
