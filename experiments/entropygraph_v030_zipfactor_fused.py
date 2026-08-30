"""Single-pass source builder for the compact r25 ZIP-factor profile.

Canonical staging normally hashes every regular file for the filesystem manifest and the content encoder then reads
it again. This builder preserves the exact filesystem-manifest grammar while parsing/hashing each graph-owned ZIP
from the same in-memory read. It emits the same compact-v2 archive grammar and fails closed on unsupported source
semantics. Eligibility is structural: bounded ZIP parsing plus one shared framing signature. File names and suffixes
are metadata only and never decide whether the mechanism runs.

ZIP source parsing uses the product-side EOCD-indexed parser. Exact-head A/B evidence showed that traversal to be
materially faster than the mature linear parser while returning the identical parsed object and preserving the exact
14,033-byte pre-recovery candidate/SHA. Hostile-equivalence and valid-comment-signature oracles remain the semantic
promotion boundary; the mature profile parser is retained as the differential reference rather than duplicated here.

The default compression level is 3. A repeated same-runner level sweep found no level that by itself beat ZIP on
complete creation time. Level 2 was marginally faster but left only a 36-byte size margin versus solid Zstd-19;
level 3 retained a 219-byte margin at essentially the same latency and was materially faster than the old level-6
default. The level remains recorded in archive metadata and callers may override it for controlled evidence work;
canonical productization still has to earn the full four-way gate after mandatory verification.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from typing import Callable

import msgpack
import zstandard as zstd

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact as ZFC
from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_zipfactor_eocd_parser as ZIP_PARSER

MAX_LOGICAL_BYTES = 512 * 1024 * 1024
DEFAULT_LEVEL = 3


class ProfileNotEligible(RuntimeError):
    pass


_LOCAL_SIGNATURE_FIELDS = (
    "version", "flags", "method", "mtime", "mdate", "name", "extra",
)
_CENTRAL_SIGNATURE_FIELDS = (
    "made", "needed", "flags", "method", "mtime", "mdate", "name", "extra", "comment",
    "disk", "internal_attr", "external_attr",
)
_EOCD_SIGNATURE_FIELDS = ("disk", "disk_cd", "comment")


def _same_framing_signature(reference: dict, candidate: dict) -> bool:
    """Exact BASE._signature equivalence without allocating nested signature tuples.

    ZIP-factor admission cares only about the static framing fields owned by ``BASE._signature``. Dynamic CRC,
    compressed/uncompressed sizes, payload bytes and physical local offsets intentionally do not participate. Direct
    comparison against the first accepted parsed member preserves that law exactly while avoiding a complete nested
    tuple allocation for every subsequent source ZIP in the source-scan hot path.
    """
    ref_locals = reference["locals"]
    candidate_locals = candidate["locals"]
    if len(ref_locals) != len(candidate_locals):
        return False
    for left, right in zip(ref_locals, candidate_locals, strict=True):
        for field in _LOCAL_SIGNATURE_FIELDS:
            if left[field] != right[field]:
                return False

    ref_centrals = reference["centrals"]
    candidate_centrals = candidate["centrals"]
    if len(ref_centrals) != len(candidate_centrals):
        return False
    for left, right in zip(ref_centrals, candidate_centrals, strict=True):
        for field in _CENTRAL_SIGNATURE_FIELDS:
            if left[field] != right[field]:
                return False

    ref_eocd = reference["eocd"]
    candidate_eocd = candidate["eocd"]
    return all(ref_eocd[field] == candidate_eocd[field] for field in _EOCD_SIGNATURE_FIELDS)


def _scan(
    root: Path,
    *,
    parse_zip: Callable[[bytes], dict | None] = ZIP_PARSER.parse_zip,
) -> tuple[bytes, list[tuple[str, dict]], dict]:
    """Scan once using structural admission and the shipping parser by default.

    ``parse_zip`` exists only as an explicit differential-test seam. Production callers do not override it; oracles
    can compare the mature semantic owner without mutating module globals or changing concurrent build behavior.
    No filename, suffix, benchmark identity or path pattern participates in ZIP-factor eligibility.
    """
    root = Path(root)
    if not root.is_dir():
        raise ProfileNotEligible("ZIP-factor fused source must be a directory tree")
    entries: list[list] = []
    items: list[tuple[str, dict]] = []
    inode_first: dict[tuple[int, int], str] = {}
    logical_bytes = 0
    signature_reference = None

    def reserve() -> None:
        if len(entries) >= FS.DEFAULT_MAX_MANIFEST_ENTRIES:
            raise ProfileNotEligible("ZIP-factor filesystem entry count exceeds policy")

    def walk(abs_dir: Path, prefix: str = "") -> None:
        nonlocal logical_bytes, signature_reference
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
                entries.append([rel, "d", *fields, None])
                walk(path, rel)
                continue
            if stat.S_ISLNK(st.st_mode):
                target = os.readlink(path)
                if "\x00" in target:
                    raise ProfileNotEligible("ZIP-factor symlink target contains NUL")
                entries.append([rel, "l", *fields, target])
                continue
            if not stat.S_ISREG(st.st_mode):
                raise ProfileNotEligible(f"ZIP-factor special file: {rel}")
            if FS._is_sparse(st):
                raise ProfileNotEligible(f"ZIP-factor sparse file: {rel}")
            inode = (int(getattr(st, "st_dev", 0)), int(getattr(st, "st_ino", 0)))
            if st.st_nlink > 1 and inode[1] and inode in inode_first:
                entries.append([rel, "h", *fields, inode_first[inode]])
                continue

            raw = path.read_bytes()
            parsed = parse_zip(raw)
            if parsed is None:
                # Keep the historical diagnostic phrase for downstream tests/log parsers while admission itself is
                # now content-derived. A misleading `.zip` suffix therefore cannot make unsupported bytes eligible.
                raise ProfileNotEligible(
                    "ZIP-factor graph-owned regular files must all be ZIPs with a supported structural encoding"
                )
            if signature_reference is None:
                signature_reference = parsed
            elif not _same_framing_signature(signature_reference, parsed):
                raise ProfileNotEligible(
                    "ZIP-factor framing layout drift: requires one shared structural framing signature"
                )

            digest = hashlib.sha256(raw).digest()
            if st.st_nlink > 1 and inode[1]:
                inode_first[inode] = rel
            entries.append([rel, "f", *fields, [len(raw), digest]])
            items.append((rel, parsed))
            logical_bytes += len(raw)
            if logical_bytes > MAX_LOGICAL_BYTES or len(items) > ZFC.MAX_FILES:
                raise ProfileNotEligible("ZIP-factor source exceeds content bounds")

    walk(root)
    if len(items) < 2:
        raise ProfileNotEligible("ZIP-factor requires at least two structurally compatible ZIP members")
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
        "admission": "supported-zip-structure+shared-framing-signature-v1",
        "path_identity_used_for_admission": False,
    }


def build(root: Path, out: Path, *, level: int = DEFAULT_LEVEL, group_size: int = 7) -> dict:
    manifest_raw, items, fs_stats = _scan(Path(root))
    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[index:index + group_size] for index in range(0, len(items), group_size)]
    group_raws = [ZFC._pack_group(group) for group in groups]
    decoded_manifest = FS.decode_manifest(
        manifest_raw,
        max_path_bytes=ZFC.MAX_PATH,
        max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
    )
    regular = decoded_manifest["regular"]
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular[rel][0] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > ZFC.MAX_DECODE or max_amp > ZFC.MAX_AMP:
        raise ProfileNotEligible("binary-control ZIP-factor locality ceiling")

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
        "groups": [
            [len(raw), hashlib.sha256(raw).digest(), [rel for rel, _item in group]]
            for group, raw in zip(groups, group_raws, strict=True)
        ],
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
    payload += BASE._blob(meta_blob)
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return {
        "archive_bytes": len(payload),
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
