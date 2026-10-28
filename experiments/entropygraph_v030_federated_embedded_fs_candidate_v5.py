from __future__ import annotations

"""C25EG05: federated candidate with filesystem control embedded in authenticated metadata.

C25EG04 reduced the office all-best floor to 5,954,155 B, only 129 B above the immutable accepted-v0.29 row.
At that point an entire physical pack + graph member for the filesystem control plane is disproportionate overhead.
C25EG05 keeps the exact C25EG04 filesystem-control grammar but stores its bounded bytes inside EntropyGraph's
already-authenticated, already-primary/tail-replicated metadata instead of as a hidden profile file.

This preserves two-way recovery while removing one physical pack header and its reconstruction/path framing.
Research/candidate only: shipping selector, native/Android dispatch and every release threshold remain unchanged.
"""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

import msgpack

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS

MAGIC = b"C25EG05\0"
TAIL_MAGIC = b"C25EG5T\0"
LEVEL_CAP = 1
EMBEDDED_FS_KEY = "f5"
MAX_PATH_BYTES = EG01.MAX_PATH_BYTES
MAX_PROFILE_FILES = EG01.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = EG01.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = EG01.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = EG01.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG01.MAX_MEMBER_AMPLIFICATION
_LOCK = EG01._LOCK

# Research benchmark adapters build through V25 directly.  Keep the bounded control bytes associated with the
# exact temporary profile so those adapters can finalize the archive after V25 has emitted its physical packs.
_PENDING_CONTROL: dict[str, bytes] = {}


def _treehash(root: Path) -> str:
    return EG01._treehash(root)


@contextmanager
def _engine(archive: Path, profile: Path | None = None):
    with _LOCK:
        old = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)
        original_zc = V25.zc
        V25.OUT = archive
        if profile is not None:
            V25.ROOT = profile
        V25.MAG = MAGIC
        V25.TAIL = TAIL_MAGIC

        def capped(raw: bytes, level: int = 19) -> bytes:
            return original_zc(raw, min(int(level), LEVEL_CAP))

        V25.zc = capped
        try:
            yield
        finally:
            V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc = old


@contextmanager
def _eg01_identity_bridge():
    with _LOCK:
        old_magic, old_tail = EG01.MAGIC, EG01.TAIL_MAGIC
        EG01.MAGIC, EG01.TAIL_MAGIC = MAGIC, TAIL_MAGIC
        try:
            yield
        finally:
            EG01.MAGIC, EG01.TAIL_MAGIC = old_magic, old_tail


def _profile_key(profile: Path) -> str:
    return str(profile.resolve())


def _prepare_profile(source: Path, profile: Path) -> dict:
    v1_raw, regular_sources, stats = FS.capture_filesystem_manifest(
        source,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=MAX_PROFILE_FILES,
        max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    implicit_raw = IFS4.encode_v1(v1_raw, max_path_bytes=MAX_PATH_BYTES, max_entries=MAX_MANIFEST_ENTRIES)
    if not IFS4.semantics_equal(
        v1_raw,
        implicit_raw,
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    ):
        raise RuntimeError("embedded-fs candidate changed canonical filesystem semantics")
    profile.mkdir(parents=True, exist_ok=True)
    for src, rel in regular_sources:
        target = profile.joinpath(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, target, follow_symlinks=False)
        except OSError:
            shutil.copyfile(src, target)
    _PENDING_CONTROL[_profile_key(profile)] = implicit_raw
    return {
        **stats,
        "v1_manifest_bytes": len(v1_raw),
        "manifest_bytes": len(implicit_raw),
        "manifest_saving_bytes": len(v1_raw) - len(implicit_raw),
        "implicit_raw": implicit_raw,
        "filesystem_control_storage": "authenticated-primary-tail-metadata",
    }


def _parse_physical_region(raw: bytes) -> tuple[dict, bytes]:
    if len(raw) < V25.HDR.size + V25.FTR.size:
        raise RuntimeError("embedded-fs candidate archive is truncated")
    magic, mcs, mus, pack_count, meta_hash = V25.HDR.unpack_from(raw, 0)
    if magic != MAGIC:
        raise RuntimeError("embedded-fs candidate primary magic")
    meta_start = V25.HDR.size
    meta_end = meta_start + int(mcs)
    if meta_end > len(raw):
        raise RuntimeError("embedded-fs candidate primary metadata bounds")
    meta_raw = V25.zd(raw[meta_start:meta_end], int(mus))
    if hashlib.sha256(meta_raw).digest() != meta_hash:
        raise RuntimeError("embedded-fs candidate primary metadata authentication")
    meta = msgpack.unpackb(meta_raw, raw=False)
    pos = meta_end
    for _ in range(int(pack_count)):
        if pos + V25.PH.size > len(raw):
            raise RuntimeError("embedded-fs candidate pack-header bounds")
        _codec, _usize, csize, _crc, _sha = V25.PH.unpack_from(raw, pos)
        pos += V25.PH.size + int(csize)
        if pos > len(raw):
            raise RuntimeError("embedded-fs candidate pack-payload bounds")
    physical = raw[meta_end:pos]
    expected_end = pos + int(mcs) + V25.FTR.size
    if expected_end != len(raw):
        raise RuntimeError("embedded-fs candidate trailing layout")
    tail, tmcs, tmus, tmh = V25.FTR.unpack_from(raw, len(raw) - V25.FTR.size)
    if tail != TAIL_MAGIC or int(tmcs) != int(mcs) or int(tmus) != int(mus) or tmh != meta_hash:
        raise RuntimeError("embedded-fs candidate tail metadata disagreement")
    if raw[pos : pos + int(mcs)] != raw[meta_start:meta_end]:
        raise RuntimeError("embedded-fs candidate metadata copies differ")
    return meta, physical


def _embed_control(archive: Path, control: bytes) -> dict:
    if not isinstance(control, bytes) or not control or len(control) > FS.MAX_MANIFEST_BYTES:
        raise RuntimeError("embedded-fs control declaration")
    raw = archive.read_bytes()
    meta, physical = _parse_physical_region(raw)
    if EMBEDDED_FS_KEY in meta:
        raise RuntimeError("embedded-fs metadata key already present")
    meta[EMBEDDED_FS_KEY] = control
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = V25.zc(meta_raw, 12)
    meta_hash = hashlib.sha256(meta_raw).digest()
    pack_count = int(meta["pack_count"])
    rebuilt = b"".join(
        (
            V25.HDR.pack(MAGIC, len(meta_comp), len(meta_raw), pack_count, meta_hash),
            meta_comp,
            physical,
            meta_comp,
            V25.FTR.pack(TAIL_MAGIC, len(meta_comp), len(meta_raw), meta_hash),
        )
    )
    archive.write_bytes(rebuilt)
    return {
        "embedded_control_bytes": len(control),
        "metadata_raw_bytes": len(meta_raw),
        "metadata_compressed_bytes": len(meta_comp),
        "physical_region_bytes": len(physical),
    }


def finalize_research_archive(archive: Path, profile: Path, fs: dict | None = None) -> dict:
    control = fs.get("implicit_raw") if fs is not None else _PENDING_CONTROL.get(_profile_key(profile))
    if not isinstance(control, bytes):
        raise RuntimeError("embedded-fs research finalizer has no filesystem control for profile")
    result = _embed_control(archive, control)
    _PENDING_CONTROL.pop(_profile_key(profile), None)
    return result


def _metadata_control(archive: Path) -> bytes:
    with _engine(archive.resolve()):
        stream, meta, _packs = V25.open_ar()
        try:
            control = meta.get(EMBEDDED_FS_KEY)
        finally:
            stream.close()
    if not isinstance(control, bytes) or not control or len(control) > FS.MAX_MANIFEST_BYTES:
        raise RuntimeError("embedded-fs authenticated control missing or invalid")
    return control


def _restore_profile(profile: Path, control: bytes) -> dict:
    identities = IFS4.identities_from_profile(
        profile,
        control,
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
        internal_path=".__cmpct_no_physical_fs_member__",
    )
    decoded = IFS4.decode_to_v1(
        control,
        regular_identities=identities,
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    FS.restore_manifest_tree(profile, decoded)
    return decoded


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path)


def extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    control = _metadata_control(archive)
    with tempfile.TemporaryDirectory(prefix=".cmpct-eg05-extract-", dir=destination.parent) as td:
        work = Path(td)
        profile = work / "profile"
        previous = work / "previous"
        with _engine(archive.resolve()):
            V25.extract(profile)
        _restore_profile(profile, control)
        had_previous = destination.exists() or destination.is_symlink()
        if had_previous:
            os.replace(destination, previous)
        try:
            os.replace(profile, destination)
        except Exception:
            if had_previous and (previous.exists() or previous.is_symlink()):
                os.replace(previous, destination)
            raise
        if had_previous:
            _remove_path(previous)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    control = _metadata_control(archive)
    with _engine(archive.resolve()):
        inner = dict(V25.strong_verify())
    with tempfile.TemporaryDirectory(prefix="cmpct-eg05-verify-") as td:
        restored = Path(td) / "restored"
        with _engine(archive.resolve()):
            V25.extract(restored)
        decoded = _restore_profile(restored, control)
        tree = _treehash(restored)
    if expected_tree is not None and tree != expected_tree:
        raise RuntimeError(f"canonical user-tree mismatch: {tree} != {expected_tree}")
    return {
        "ok": True,
        "profile": "federated-eg05-embedded-fs",
        "canonical_user_tree_sha256": tree,
        "filesystem_entries": len(decoded["manifest"]["entries"]),
        "inner": inner,
    }


def locality_report(archive: Path) -> dict:
    with _eg01_identity_bridge():
        return EG01.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg05-build-") as td:
        profile = Path(td) / "profile"
        fs = _prepare_profile(source, profile)
        with _engine(archive, profile):
            stats = dict(V25.build())
            framing = finalize_research_archive(archive, profile, fs)
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("embedded-fs federated candidate exceeds frozen locality/decode limits")
    return {
        "profile": "federated-eg05-embedded-fs",
        "format_revision": 25,
        "archive_bytes": archive.stat().st_size,
        "filesystem_manifest_bytes": int(fs["manifest_bytes"]),
        "filesystem_manifest_v1_bytes": int(fs["v1_manifest_bytes"]),
        "filesystem_manifest_saving_bytes": int(fs["manifest_saving_bytes"]),
        "filesystem_control_storage": "authenticated-primary-tail-metadata",
        "framing": framing,
        "build_stats": stats,
        "verified": verified,
        "locality": locality,
    }
