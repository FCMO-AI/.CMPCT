"""Compact productization candidate for the r25 ZIP framing-factor profile.

This variant removes identity/path duplication exposed by the first canonical product-boundary measurement.
Canonical filesystem-manifest identities are the single owner of user-file size/SHA. Group metadata stores each
logical path once; group payloads store only changing ZIP fields and original compressed member payloads.
Metadata itself is Zstd-compressed. The representation remains pre-selector until exact evidence and native/Android
parity are complete.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import struct

import msgpack
import zstandard as zstd

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_profile as BASE

MAGIC = b"CMP25Z2\0"
PROFILE = "zip-framing-factor-compact-v2"
REVISION = 25
VERSION = 2
MAX_META = 8 * 1024 * 1024
MAX_DECODE = 8 * 1024 * 1024
MAX_AMP = 8.0
MAX_FILES = 65_535
MAX_PATH = 16 * 1024
GROUP_MAGIC = b"ZCG2"


class ProfileNotEligible(RuntimeError):
    pass


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _pack_group(group: list[tuple[str, dict]]) -> bytes:
    out = bytearray(GROUP_MAGIC)
    out += BASE._uvarint(len(group))
    for _rel, item in group:
        for local in item["locals"]:
            out += struct.pack("<III", int(local["crc"]), int(local["csize"]), int(local["usize"]))
            out += local["payload"]
    if len(out) > MAX_DECODE:
        raise ProfileNotEligible("compact ZIP-factor group exceeds decode-unit policy")
    return bytes(out)


def _decode_manifest(raw: bytes) -> dict:
    try:
        return FS.decode_manifest(raw, max_path_bytes=MAX_PATH, max_entries=MAX_FILES + 1024)
    except Exception as exc:
        raise ProfileNotEligible("compact ZIP-factor requires valid canonical filesystem manifest") from exc


def build(staged_root: Path, out: Path, *, level: int = 6, group_size: int = 7) -> dict:
    staged_root = Path(staged_root); out = Path(out)
    manifest_path = staged_root / FS.FILESYSTEM_MANIFEST
    if not manifest_path.is_file():
        raise ProfileNotEligible("compact ZIP-factor requires canonical filesystem manifest")
    manifest_raw = manifest_path.read_bytes()
    decoded = _decode_manifest(manifest_raw)
    regular = decoded["regular"]
    files = sorted(p for p in staged_root.rglob("*") if p.is_file() and p != manifest_path)
    if not 2 <= len(files) <= MAX_FILES or len(files) != len(regular):
        raise ProfileNotEligible("compact ZIP-factor regular-file envelope")

    items: list[tuple[str, dict]] = []
    signature = None
    for path in files:
        rel = path.relative_to(staged_root).as_posix()
        BASE._safe_rel(rel)
        if path.suffix.lower() != ".zip" or rel not in regular:
            raise ProfileNotEligible("compact ZIP-factor accepts only manifest-owned ZIP regular files")
        raw = path.read_bytes()
        expected_size, expected_sha = regular[rel]
        if len(raw) != expected_size or _sha(raw) != expected_sha:
            raise ProfileNotEligible("source changed after filesystem manifest capture")
        parsed = BASE._parse_zip(raw)
        if parsed is None:
            raise ProfileNotEligible(f"unsupported ZIP structure: {rel}")
        sig = BASE._signature(parsed)
        if signature is None:
            signature = sig
        elif sig != signature:
            raise ProfileNotEligible(f"ZIP framing layout drift: {rel}")
        items.append((rel, parsed))

    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[i:i + group_size] for i in range(0, len(items), group_size)]
    group_raws = [_pack_group(group) for group in groups]
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular[rel][0] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > MAX_DECODE or max_amp > MAX_AMP:
        raise ProfileNotEligible("compact ZIP-factor locality ceiling")

    compressor = zstd.ZstdCompressor(level=level, threads=0)
    manifest_blob = compressor.compress(manifest_raw)
    template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]
    meta = {
        "v": VERSION,
        "profile": PROFILE,
        "level": level,
        "manifest_raw": len(manifest_raw),
        "manifest_sha": _sha(manifest_raw),
        "template_raw": len(template_raw),
        "template_sha": _sha(template_raw),
        "groups": [[len(raw), _sha(raw), [rel for rel, _item in group]] for group, raw in zip(groups, group_raws, strict=True)],
        "max_decode_unit": max_decode,
        "max_member_read_amplification": float(max_amp),
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_META:
        raise ProfileNotEligible("compact ZIP-factor metadata exceeds policy")
    meta_blob = compressor.compress(meta_raw)
    payload = bytearray(MAGIC)
    payload += struct.pack("<I", len(meta_raw))
    payload += BASE._blob(meta_blob)
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return {
        "archive_bytes": out.stat().st_size,
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "user_files": len(files),
        "groups": len(groups),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": level,
        "group_size": group_size,
        "raw_meta_bytes": len(meta_raw),
        "compressed_meta_bytes": len(meta_blob),
    }


def _open(archive: Path) -> tuple[dict, bytes, dict, bytes, list[bytes]]:
    raw = memoryview(Path(archive).read_bytes())
    if len(raw) < 12 or bytes(raw[:8]) != MAGIC:
        raise RuntimeError("not a compact ZIP-factor profile")
    meta_raw_size = struct.unpack_from("<I", raw, 8)[0]
    if meta_raw_size > MAX_META:
        raise RuntimeError("compact ZIP-factor metadata declaration")
    at = 12
    meta_blob, at = BASE._read_blob(raw, at)
    meta_raw = zstd.ZstdDecompressor().decompress(meta_blob, max_output_size=meta_raw_size)
    if len(meta_raw) != meta_raw_size:
        raise RuntimeError("compact ZIP-factor metadata size mismatch")
    try:
        meta = msgpack.unpackb(meta_raw, raw=False, strict_map_key=True, max_map_len=32,
                               max_array_len=MAX_FILES * 3 + 1024, max_bin_len=MAX_META, max_str_len=MAX_PATH)
    except Exception as exc:
        raise RuntimeError("invalid compact ZIP-factor metadata") from exc
    if not isinstance(meta, dict) or meta.get("v") != VERSION or meta.get("profile") != PROFILE:
        raise RuntimeError("unsupported compact ZIP-factor metadata")
    groups = meta.get("groups")
    if not isinstance(groups, list) or not 1 <= len(groups) <= MAX_FILES:
        raise RuntimeError("compact ZIP-factor group declaration")
    manifest_blob, at = BASE._read_blob(raw, at)
    template_blob, at = BASE._read_blob(raw, at)
    blobs = []
    for _ in groups:
        blob, at = BASE._read_blob(raw, at); blobs.append(blob)
    if at != len(raw):
        raise RuntimeError("compact ZIP-factor trailing archive bytes")
    manifest_raw = zstd.ZstdDecompressor().decompress(manifest_blob, max_output_size=int(meta["manifest_raw"]))
    template_raw = zstd.ZstdDecompressor().decompress(template_blob, max_output_size=int(meta["template_raw"]))
    if _sha(manifest_raw) != bytes(meta["manifest_sha"]) or _sha(template_raw) != bytes(meta["template_sha"]):
        raise RuntimeError("compact ZIP-factor direct-member authentication")
    manifest = FS.decode_manifest(manifest_raw, max_path_bytes=MAX_PATH, max_entries=MAX_FILES + 1024)
    return meta, manifest_raw, manifest, template_raw, blobs


def verify_and_identities(archive: Path) -> dict:
    meta, manifest_raw, manifest, template_raw, blobs = _open(archive)
    template = BASE._parse_template(template_raw)
    identities = {FS.FILESYSTEM_MANIFEST: (len(manifest_raw), _sha(manifest_raw))}
    max_amp = 1.0
    max_decode = len(manifest_raw)
    seen: set[str] = set()
    for desc, blob in zip(meta["groups"], blobs, strict=True):
        if not isinstance(desc, list) or len(desc) != 3:
            raise RuntimeError("compact ZIP-factor group metadata")
        raw_size = int(desc[0]); expected_sha = bytes(desc[1]); paths = desc[2]
        if not isinstance(paths, list) or not paths:
            raise RuntimeError("compact ZIP-factor path index")
        group_raw = zstd.ZstdDecompressor().decompress(blob, max_output_size=raw_size)
        if len(group_raw) != raw_size or _sha(group_raw) != expected_sha:
            raise RuntimeError("compact ZIP-factor group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != GROUP_MAGIC:
            raise RuntimeError("bad compact ZIP-factor group magic")
        at = 4; count, at = BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("compact ZIP-factor group count")
        context = len(template_raw) + len(group_raw)
        max_decode = max(max_decode, context)
        if context > MAX_DECODE:
            raise RuntimeError("compact ZIP-factor decode-unit ceiling")
        for rel in paths:
            if not isinstance(rel, str) or rel in seen or rel not in manifest["regular"]:
                raise RuntimeError("compact ZIP-factor logical path mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated compact ZIP-factor dynamics")
                crc, csize, usize = struct.unpack_from("<III", view, at); at += 12
                if csize > MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated compact ZIP-factor payload")
                payload = bytes(view[at:at + csize]); at += csize
                dynamics.append((crc, csize, usize, payload))
            restored = BASE._rebuild_zip(template, dynamics)
            expected_size, expected_file_sha = manifest["regular"][rel]
            if len(restored) != expected_size or _sha(restored) != expected_file_sha:
                raise RuntimeError(f"compact ZIP-factor reconstructed identity: {rel}")
            amp = context / max(1, len(restored))
            if amp > MAX_AMP:
                raise RuntimeError(f"compact ZIP-factor locality ceiling: {rel}")
            max_amp = max(max_amp, amp); seen.add(rel); identities[rel] = (len(restored), expected_file_sha)
        if at != len(view):
            raise RuntimeError("compact ZIP-factor group trailing bytes")
    if seen != set(manifest["regular"]):
        raise RuntimeError("compact ZIP-factor manifest/content membership mismatch")
    return {
        "ok": True,
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "manifest_raw": manifest_raw,
        "manifest": manifest,
        "identities": identities,
        "verified_user_files": len(seen),
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_decode,
    }


def strong_verify(archive: Path) -> dict:
    try:
        result = verify_and_identities(archive)
        return {k: v for k, v in result.items() if k not in {"manifest_raw", "manifest", "identities"}}
    except Exception as exc:
        return {"ok": False, "format_revision": REVISION, "format_profile": PROFILE, "error": repr(exc)}
