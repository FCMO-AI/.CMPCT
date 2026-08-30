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

The canonical user-tree digest is derived directly from the authenticated filesystem manifest. Keeping that
identity at the profile semantic owner prevents release wrappers and evidence harnesses from inventing different
spellings of the same filesystem contract.
"""

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

import msgpack

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


def semantic_tree_sha256(decoded: dict) -> str:
    """Hash an authenticated filesystem manifest using the canonical r25 user-tree grammar."""
    rows = []
    for row in sorted(decoded["manifest"]["entries"], key=lambda item: item[0]):
        rel, kind, _mode, _mtime, _uid, _gid, _xattrs, extra = row
        if kind == "f":
            size, digest = extra
            semantic = [rel, "f", int(size), bytes(digest)]
        elif kind == "d":
            semantic = [rel, "d"]
        elif kind == "l":
            semantic = [rel, "l", extra]
        elif kind == "h":
            semantic = [rel, "h", extra]
        else:
            raise RuntimeError(f"unknown logs filesystem entry kind {kind!r} for {rel!r}")
        rows.append(semantic)
    encoded = msgpack.packb(["cmpct-user-tree-v1", rows], use_bin_type=True)
    return hashlib.sha256(encoded).hexdigest()


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
    user_tree = semantic_tree_sha256(decoded)
    verified.update({
        "canonical_filesystem_manifest": True,
        "filesystem_manifest_bytes": len(manifest_raw),
        "filesystem_manifest_entries": len(decoded["manifest"]["entries"]),
        "filesystem_regular_members": len(decoded["regular"]),
        "tree_sha256": user_tree,
        "user_tree_sha256": user_tree,
        "canonical_user_tree_sha256": user_tree,
    })
    return verified


def read_member_with_stats(path: Path, rel: str) -> tuple[bytes, dict]:
    """Read one user-visible member with exact cold-operation locality accounting.

    Resolving a user-visible path requires the authenticated filesystem manifest, so its decoded context belongs
    to the selective-read operation rather than being hidden outside the locality budget. Regular files and
    hardlink aliases then read the authenticated graph owner through the v2 cold reader. Symlink bytes come from
    the authenticated manifest itself. Directories are not byte-valued members.
    """
    path = Path(path)
    if not isinstance(rel, str):
        raise TypeError("logs member path must be text")
    with Archive(path) as archive:
        paths = archive._paths()
        try:
            manifest_index = paths.index(FS.FILESYSTEM_MANIFEST)
        except ValueError as exc:
            raise RuntimeError("logs canonical profile is missing filesystem manifest") from exc
        manifest_raw, manifest_context = archive.read_member(manifest_index)
        decoded = FS.decode_manifest(
            manifest_raw,
            max_path_bytes=MAX_PATH_BYTES,
            max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
        )
        rows = FS.entry_map(decoded)
        if rel not in rows:
            raise KeyError(rel)
        row = rows[rel]
        kind = row[1]
        extra = row[7]

        if kind == "d":
            raise IsADirectoryError(rel)
        if kind == "l":
            value = extra.encode("utf-8")
            content_context = 0
        else:
            owner = rel if kind == "f" else extra
            try:
                owner_index = paths.index(owner)
            except ValueError as exc:
                raise RuntimeError("logs canonical filesystem owner is missing from content graph") from exc
            value, content_context = archive.read_member(owner_index)
            expected_size, expected_sha = decoded["regular"][owner]
            if len(value) != int(expected_size) or hashlib.sha256(value).digest() != bytes(expected_sha):
                raise RuntimeError("logs canonical selective-read filesystem/content identity mismatch")

    decoded_context = int(manifest_context) + int(content_context)
    logical_bytes = len(value)
    amplification = decoded_context / max(1, logical_bytes)
    if decoded_context > MAX_DECODE_UNIT or amplification > MAX_MEMBER_AMPLIFICATION:
        raise RuntimeError("logs canonical selective-read locality violation")
    return value, {
        "logical_bytes": logical_bytes,
        "decoded_context_bytes": decoded_context,
        "decoded_context_amplification": amplification,
        "filesystem_manifest_decoded_context_bytes": int(manifest_context),
        "content_decoded_context_bytes": int(content_context),
        "locality_accounting": "authenticated-manifest-plus-cold-content-v1",
        "max_member_read_amplification": MAX_MEMBER_AMPLIFICATION,
        "max_decode_unit_bytes": MAX_DECODE_UNIT,
    }


def read_member(path: Path, rel: str) -> bytes:
    return read_member_with_stats(path, rel)[0]


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
