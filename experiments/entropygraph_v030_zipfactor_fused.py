"""Single-pass source builder for the compact r25 ZIP-factor profile.

Canonical staging normally hashes every regular file for the filesystem manifest and the content encoder then reads
it again. This builder preserves the exact filesystem-manifest grammar while parsing/hashing each graph-owned ZIP
from the same in-memory read. It emits the same compact-v2 archive grammar and fails closed on unsupported source
semantics. The optimization is creation-time machinery only; reader semantics remain owned by zipfactor_compact.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from pathlib import PurePosixPath
import stat

import msgpack
import zstandard as zstd

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact as ZFC
from experiments import entropygraph_v030_zipfactor_profile as BASE

MAX_LOGICAL_BYTES = 512 * 1024 * 1024


class ProfileNotEligible(RuntimeError):
    pass


def _scan(root: Path) -> tuple[bytes, list[tuple[str, dict]], dict]:
    root = Path(root)
    if not root.is_dir():
        raise ProfileNotEligible("ZIP-factor fused source must be a directory tree")
    entries: list[list] = []
    items: list[tuple[str, dict]] = []
    inode_first: dict[tuple[int, int], str] = {}
    logical_bytes = 0
    signature = None

    def reserve() -> None:
        if len(entries) >= FS.DEFAULT_MAX_MANIFEST_ENTRIES:
            raise ProfileNotEligible("ZIP-factor filesystem entry count exceeds policy")

    def walk(abs_dir: Path, prefix: str = "") -> None:
        nonlocal logical_bytes, signature
        with os.scandir(abs_dir) as iterator:
            children = sorted(iterator, key=lambda item: item.name)
        for child in children:
            reserve()
            rel = f"{prefix}/{child.name}" if prefix else child.name
            try:
                FS.safe_relpath(rel, max_path_bytes=ZFC.MAX_PATH)
            except Exception as exc:
                raise ProfileNotEligible("ZIP-factor source path is not canonical") from exc
            path = Path(child.path)
            st = child.stat(follow_symlinks=False)
            fields = FS._metadata_fields(path, st)
            if stat.S_ISDIR(st.st_mode):
                entries.append([rel, "d", *fields, None]); walk(path, rel); continue
            if stat.S_ISLNK(st.st_mode):
                target = os.readlink(path)
                if "\x00" in target:
                    raise ProfileNotEligible("ZIP-factor symlink target contains NUL")
                entries.append([rel, "l", *fields, target]); continue
            if not stat.S_ISREG(st.st_mode):
                raise ProfileNotEligible(f"ZIP-factor special file: {rel}")
            if FS._is_sparse(st):
                raise ProfileNotEligible(f"ZIP-factor sparse file: {rel}")
            inode = (int(getattr(st, "st_dev", 0)), int(getattr(st, "st_ino", 0)))
            if st.st_nlink > 1 and inode[1] and inode in inode_first:
                entries.append([rel, "h", *fields, inode_first[inode]]); continue
            if path.suffix.lower() != ".zip":
                raise ProfileNotEligible("ZIP-factor graph-owned regular files must all be ZIPs")
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).digest()
            parsed = BASE._parse_zip(raw)
            if parsed is None:
                raise ProfileNotEligible(f"unsupported ZIP structure: {rel}")
            sig = BASE._signature(parsed)
            if signature is None:
                signature = sig
            elif sig != signature:
                raise ProfileNotEligible(f"ZIP framing layout drift: {rel}")
            if st.st_nlink > 1 and inode[1]:
                inode_first[inode] = rel
            entries.append([rel, "f", *fields, [len(raw), digest]])
            items.append((rel, parsed))
            logical_bytes += len(raw)
            if logical_bytes > MAX_LOGICAL_BYTES or len(items) > ZFC.MAX_FILES:
                raise ProfileNotEligible("ZIP-factor source exceeds content bounds")

    walk(root)
    if len(items) < 2:
        raise ProfileNotEligible("ZIP-factor requires at least two graph-owned ZIPs")
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    try:
        manifest_raw = msgpack.packb(manifest, use_bin_type=True)
    except Exception as exc:
        raise ProfileNotEligible("ZIP-factor manifest is not portable MessagePack") from exc
    if len(manifest_raw) > FS.MAX_MANIFEST_BYTES:
        raise ProfileNotEligible("ZIP-factor filesystem manifest exceeds policy")
    return manifest_raw, items, {
        "entries": len(entries),
        "regular_graph_members": len(items),
        "logical_regular_bytes": logical_bytes,
        "manifest_bytes": len(manifest_raw),
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
    }


def build(root: Path, out: Path, *, level: int = 6, group_size: int = 7) -> dict:
    manifest_raw, items, fs_stats = _scan(Path(root))
    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[index:index + group_size] for index in range(0, len(items), group_size)]
    group_raws = [ZFC._pack_group(group) for group in groups]
    decoded_manifest = FS.decode_manifest(manifest_raw, max_path_bytes=ZFC.MAX_PATH,
                                          max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES)
    regular = decoded_manifest["regular"]
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular[rel][0] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > ZFC.MAX_DECODE or max_amp > ZFC.MAX_AMP:
        raise ProfileNotEligible("ZIP-factor locality ceiling")
    compressor = zstd.ZstdCompressor(level=level, threads=0)
    manifest_blob = compressor.compress(manifest_raw)
    template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]
    meta = {
        "v": ZFC.VERSION,
        "profile": ZFC.PROFILE,
        "level": level,
        "manifest_raw": len(manifest_raw),
        "manifest_sha": hashlib.sha256(manifest_raw).digest(),
        "template_raw": len(template_raw),
        "template_sha": hashlib.sha256(template_raw).digest(),
        "groups": [[len(raw), hashlib.sha256(raw).digest(), [rel for rel, _item in group]]
                   for group, raw in zip(groups, group_raws, strict=True)],
        "max_decode_unit": max_decode,
        "max_member_read_amplification": float(max_amp),
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > ZFC.MAX_META:
        raise ProfileNotEligible("ZIP-factor metadata exceeds policy")
    meta_blob = compressor.compress(meta_raw)
    payload = bytearray(ZFC.MAGIC)
    import struct as _struct
    payload += _struct.pack("<I", len(meta_raw))
    payload += BASE._blob(meta_blob); payload += BASE._blob(manifest_blob); payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(payload)
    return {
        "archive_bytes": out.stat().st_size,
        "format_revision": ZFC.REVISION,
        "format_profile": ZFC.PROFILE,
        "user_files": len(items),
        "groups": len(groups),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": level,
        "group_size": group_size,
        "raw_meta_bytes": len(meta_raw),
        "compressed_meta_bytes": len(meta_blob),
        "fused_source_scan": True,
        **fs_stats,
    }
