from __future__ import annotations

"""C25EG02: structural-factoring candidate for the office/analytics federated profile.

C25EG01 proved that the inherited EntropyGraph representation can beat ZIP and Zstd under canonical filesystem,
recovery and locality requirements, but exact evidence shows compression effort alone cannot satisfy the frozen
v0.29 floor without exceeding the ZIP-time budget. C25EG02 changes only filesystem-control ownership: regular
content identity stays authenticated by the federated graph, while a compact manifest carries filesystem-only
semantics and is required to name exactly the graph's public regular paths.

This is research/candidate code. Shipping selector/native/Android dispatch remain closed.
"""

from contextlib import contextmanager
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_candidate as EG01
from experiments import entropygraph_v030_fs_compact as CFS
from experiments import entropygraph_v030_product_fs as FS

MAGIC = b"C25EG02\0"
TAIL_MAGIC = b"C25EG2T\0"
LEVEL_CAP = 1
MAX_PATH_BYTES = EG01.MAX_PATH_BYTES
MAX_PROFILE_FILES = EG01.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = EG01.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = EG01.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = EG01.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG01.MAX_MEMBER_AMPLIFICATION
_LOCK = EG01._LOCK


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
    """Reuse the audited EG01 recipe/locality walker against the EG02 identity only."""
    with _LOCK:
        old_magic, old_tail = EG01.MAGIC, EG01.TAIL_MAGIC
        EG01.MAGIC, EG01.TAIL_MAGIC = MAGIC, TAIL_MAGIC
        try:
            yield
        finally:
            EG01.MAGIC, EG01.TAIL_MAGIC = old_magic, old_tail


def _prepare_profile(source: Path, profile: Path) -> dict:
    v1_raw, regular_sources, stats = FS.capture_filesystem_manifest(
        source,
        max_path_bytes=MAX_PATH_BYTES,
        max_profile_files=MAX_PROFILE_FILES,
        max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    compact_raw = CFS.encode_v1(v1_raw, max_path_bytes=MAX_PATH_BYTES, max_entries=MAX_MANIFEST_ENTRIES)
    if not CFS.semantics_equal(v1_raw, compact_raw, max_path_bytes=MAX_PATH_BYTES, max_entries=MAX_MANIFEST_ENTRIES):
        raise RuntimeError("compact filesystem manifest changed canonical semantics")
    profile.mkdir(parents=True, exist_ok=True)
    for src, rel in regular_sources:
        target = profile.joinpath(*PurePosixPath(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, target, follow_symlinks=False)
        except OSError:
            shutil.copyfile(src, target)
    manifest_path = profile.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(compact_raw)
    return {
        **stats,
        "v1_manifest_bytes": len(v1_raw),
        "manifest_bytes": len(compact_raw),
        "manifest_saving_bytes": len(v1_raw) - len(compact_raw),
        "compact_raw": compact_raw,
    }


def _restore_profile(profile: Path) -> dict:
    manifest_path = profile.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("compact candidate omitted authenticated filesystem manifest")
    raw = manifest_path.read_bytes()
    identities = CFS.identities_from_profile(
        profile,
        raw,
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    decoded = CFS.decode_to_v1(
        raw,
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
    with tempfile.TemporaryDirectory(prefix=".cmpct-eg02-extract-", dir=destination.parent) as td:
        work = Path(td)
        profile = work / "profile"
        previous = work / "previous"
        with _engine(archive.resolve()):
            V25.extract(profile)
        _restore_profile(profile)
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
    with _engine(archive.resolve()):
        inner = dict(V25.strong_verify())
    with tempfile.TemporaryDirectory(prefix="cmpct-eg02-verify-") as td:
        restored = Path(td) / "restored"
        extract(archive, restored)
        tree = _treehash(restored)
    if expected_tree is not None and tree != expected_tree:
        raise RuntimeError(f"canonical user-tree mismatch: {tree} != {expected_tree}")
    return {"ok": True, "profile": "federated-eg02-compact-fs", "canonical_user_tree_sha256": tree, "inner": inner}


def locality_report(archive: Path) -> dict:
    with _eg01_identity_bridge():
        return EG01.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg02-build-") as td:
        profile = Path(td) / "profile"
        fs = _prepare_profile(source, profile)
        with _engine(archive, profile):
            stats = dict(V25.build())
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("compact federated candidate exceeds frozen locality/decode limits")
    return {
        "profile": "federated-eg02-compact-fs",
        "format_revision": 25,
        "archive_bytes": archive.stat().st_size,
        "filesystem_manifest_bytes": int(fs["manifest_bytes"]),
        "filesystem_manifest_v1_bytes": int(fs["v1_manifest_bytes"]),
        "filesystem_manifest_saving_bytes": int(fs["manifest_saving_bytes"]),
        "filesystem_manifest_entries": int(fs["entries"]),
        "build_stats": stats,
        "verified": verified,
        "locality": locality,
    }
