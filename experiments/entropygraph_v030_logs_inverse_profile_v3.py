from __future__ import annotations

"""Canonical-filesystem wrapper for the recoverable physical-locality logs inverse profile.

v2 proved the compression/locality/recovery envelope on exact file bytes but still owned only regular-file content.
This wrapper pays the same authenticated filesystem-manifest tax as the other canonical r25 profiles. The manifest
is stored as an ordinary bounded logical member inside the inverse profile, so its bytes are included in complete
artifact pricing and its identity is covered by the existing pack/metadata authentication and two-way recovery.
The internal manifest is placed in a bounded compressed direct pack: this changes no user-file representation and
avoids spending the narrow v0.29 byte margin on highly compressible control metadata.

Canonical v3 also freezes the inverse-codec set to codecs already implemented by the bounded native preparity
reader. Discovery may observe XZ or future sidecars, but unsupported relations are encoded as ordinary direct or
segmented files instead of emitting a derive edge that a required release reader cannot decode. This changes no
frozen logs winner bytes because its selected inverse edges are gzip and Zstd.

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
NATIVE_SUPPORTED_INVERSE_CODECS = frozenset({"gzip", "zstd"})

Archive = V2.Archive


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
        stats = dict(
            V2.build(
                staging,
                archive,
                compressed_direct_paths={FS.FILESYSTEM_MANIFEST},
                allowed_inverse_codecs=NATIVE_SUPPORTED_INVERSE_CODECS,
            )
        )
    used_codecs = frozenset(stats["edge_detection"].get("inverse_edge_codecs", ()))
    if not used_codecs <= NATIVE_SUPPORTED_INVERSE_CODECS:
        raise RuntimeError("logs canonical writer emitted a non-portable inverse codec")
    stats.update({
        "profile_writer_revision": 3,
        "canonical_filesystem_manifest": True,
        "filesystem_manifest_pack_compressed": True,
        "filesystem_manifest_bytes": int(fs_stats["manifest_bytes"]),
        "filesystem_manifest_sha256": str(fs_stats["manifest_sha256"]),
        "filesystem_manifest_entries": int(fs_stats["entries"]),
        "filesystem_regular_members": int(fs_stats["regular_graph_members"]),
        "native_supported_inverse_codecs": sorted(NATIVE_SUPPORTED_INVERSE_CODECS),
        "inverse_edge_codecs": sorted(used_codecs),
        "native_inverse_codec_safe": True,
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


def recovery_probe(path: Path) -> dict:
    """Exercise two-way metadata recovery through the full canonical verifier, not only content identity."""
    original = Path(path).read_bytes()
    results = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-fs-recovery-") as td:
        root = Path(td)

        primary = root / "primary-damaged.cmpct"
        raw = bytearray(original)
        if len(raw) <= V2.P.HEADER.size + 8:
            raise RuntimeError("logs canonical profile archive too short for recovery probe")
        raw[V2.P.HEADER.size + 3] ^= 0x5A
        primary.write_bytes(raw)
        results["primary_damage"] = strong_verify(primary)

        footer = V2.P.FOOTER.unpack(original[-V2.P.FOOTER.size:])
        tail_csize = int(footer[1])
        tail_meta_offset = len(original) - V2.P.FOOTER.size - tail_csize

        tail = root / "tail-damaged.cmpct"
        raw = bytearray(original)
        raw[tail_meta_offset + 3] ^= 0xA5
        tail.write_bytes(raw)
        results["tail_damage"] = strong_verify(tail)

        both = root / "both-damaged.cmpct"
        raw = bytearray(original)
        raw[V2.P.HEADER.size + 3] ^= 0x5A
        raw[tail_meta_offset + 3] ^= 0xA5
        both.write_bytes(raw)
        try:
            strong_verify(both)
            both_failed_closed = False
        except Exception:
            both_failed_closed = True
        results["both_failed_closed"] = both_failed_closed
    return results


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
