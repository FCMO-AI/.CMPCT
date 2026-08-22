from __future__ import annotations

"""Canonical-filesystem wrapper for the recoverable physical-locality logs inverse profile.

v2 proved the compression/locality/recovery envelope on exact file bytes but still owned only regular-file content.
This wrapper pays the same authenticated filesystem-manifest tax as the other canonical r25 profiles. The manifest
is stored as an ordinary bounded logical member inside the inverse profile, so its bytes are included in complete
artifact pricing and its identity is covered by the existing pack/metadata authentication and two-way recovery.

This remains pre-selector until the resulting complete product boundary, native reader and Android parity all pass.
"""

import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from experiments import entropygraph_v030_logs_inverse_profile_v2 as V2
from experiments import entropygraph_v030_product_fs as FS

PROFILE = V2.PROFILE
LEVEL = V2.LEVEL
MAX_DECODE_UNIT = V2.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = V2.MAX_MEMBER_AMPLIFICATION
MAX_FILES = V2.P.MAX_FILES
MAX_PATH_BYTES = V2.P.MAX_PATH_BYTES
MAX_LOGICAL_BYTES = 512 * 1024 * 1024

Archive = V2.Archive
recovery_probe = V2.recovery_probe


def build(source: Path, archive: Path) -> dict:
    source = Path(source)
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-fs-stage-", dir=archive.parent) as td:
        staging = Path(td) / "profile"
        fs_stats = FS.prepare_profile_tree(
            source,
            staging,
            max_path_bytes=MAX_PATH_BYTES,
            max_profile_files=MAX_FILES - 1,
            max_profile_logical_bytes=MAX_LOGICAL_BYTES,
            max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
        )
        stats = dict(V2.build(staging, archive))
    stats.update({
        "profile_writer_revision": 3,
        "canonical_filesystem_manifest": True,
        "filesystem_manifest_bytes": int(fs_stats["manifest_bytes"]),
        "filesystem_manifest_sha256": str(fs_stats["manifest_sha256"]),
        "filesystem_manifest_entries": int(fs_stats["entries"]),
        "filesystem_regular_members": int(fs_stats["regular_graph_members"]),
    })
    return stats


def _manifest_from_archive(path: Path) -> bytes:
    with Archive(path) as archive:
        paths = archive._paths()
        try:
            index = paths.index(FS.FILESYSTEM_MANIFEST)
        except ValueError as exc:
            raise RuntimeError("logs canonical profile is missing filesystem manifest") from exc
        raw, _context = archive.read_member(index)
    return raw


def strong_verify(path: Path) -> dict:
    verified = dict(V2.strong_verify(path))
    manifest_raw = _manifest_from_archive(path)
    decoded = FS.decode_manifest(
        manifest_raw,
        max_path_bytes=MAX_PATH_BYTES,
        max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
    )

    identities = {
        rel: (int(size), bytes.fromhex(digest))
        for rel, size, digest in verified["identities"]
        if rel != FS.FILESYSTEM_MANIFEST
    }
    if identities != decoded["regular"]:
        raise RuntimeError("logs canonical profile filesystem/content identity mismatch")
    verified.update({
        "canonical_filesystem_manifest": True,
        "filesystem_manifest_bytes": len(manifest_raw),
        "filesystem_manifest_entries": len(decoded["manifest"]["entries"]),
        "filesystem_regular_members": len(decoded["regular"]),
    })
    return verified


def extract(path: Path, dst: Path) -> None:
    path = Path(path)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="cmpct-v030-logs-extract-", dir=dst.parent))
    stage = temp_root / "tree"
    try:
        V2.extract(path, stage)
        manifest_path = stage.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise RuntimeError("logs canonical extraction did not materialize filesystem manifest")
        decoded = FS.decode_manifest(
            manifest_path.read_bytes(),
            max_path_bytes=MAX_PATH_BYTES,
            max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
        )
        FS.restore_manifest_tree(stage, decoded)
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        os.replace(stage, dst)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
