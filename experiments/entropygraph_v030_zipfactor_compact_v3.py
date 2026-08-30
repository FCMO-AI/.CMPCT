"""Binary-control revision-25 ZIP framing-factor candidate.

This pre-selector profile removes compressed MessagePack control metadata from compact-v2. The canonical
filesystem manifest remains the single owner of logical paths and user-file identities. A fixed bounded binary
header stores only direct-member sizes/digests and per-group raw size/digest/member-count descriptors; group
membership is derived from the authenticated manifest's sorted regular-file order. This reduces both archive
bytes and creation/parser work without changing ZIP reconstruction, locality, or filesystem semantics.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct

import zstandard as zstd

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_zipfactor_fused as FUSED

MAGIC = b"CMP25Z3\0"
PROFILE = "zip-framing-factor-binary-control-v3"
REVISION = 25
VERSION = 3
MAX_DECODE = 8 * 1024 * 1024
MAX_AMP = 8.0
MAX_FILES = 65_535
MAX_PATH = 16 * 1024
MAX_COMPRESSED_BLOB = MAX_DECODE + 1024 * 1024
GROUP_MAGIC = b"ZCG2"
_HEADER = struct.Struct("<I32sI32sH")
_GROUP = struct.Struct("<I32sH")


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
        raise ProfileNotEligible("binary-control ZIP-factor group exceeds decode-unit policy")
    return bytes(out)


def _decompress(blob: bytes, raw_size: int, label: str) -> bytes:
    if raw_size < 0 or raw_size > MAX_DECODE or len(blob) > MAX_COMPRESSED_BLOB:
        raise RuntimeError(f"binary-control ZIP-factor {label} declaration exceeds policy")
    raw = zstd.ZstdDecompressor().decompress(blob, max_output_size=raw_size)
    if len(raw) != raw_size:
        raise RuntimeError(f"binary-control ZIP-factor {label} size mismatch")
    return raw


def build(root: Path, out: Path, *, level: int = 6, group_size: int = 7) -> dict:
    root = Path(root)
    out = Path(out)
    if group_size < 1 or group_size > MAX_FILES:
        raise ProfileNotEligible("binary-control ZIP-factor group size exceeds policy")
    manifest_raw, items, fs_stats = FUSED._scan(root)
    if not 2 <= len(items) <= MAX_FILES:
        raise ProfileNotEligible("binary-control ZIP-factor regular-file envelope")

    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[index:index + group_size] for index in range(0, len(items), group_size)]
    group_raws = [_pack_group(group) for group in groups]
    regular_sizes = {rel: int(item["raw_size"]) for rel, item in items}
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular_sizes[rel] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > MAX_DECODE or max_amp > MAX_AMP:
        raise ProfileNotEligible("binary-control ZIP-factor locality ceiling")

    compressor = zstd.ZstdCompressor(level=level, threads=0)
    manifest_blob = compressor.compress(manifest_raw)
    template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]

    control = bytearray(
        _HEADER.pack(
            len(manifest_raw),
            _sha(manifest_raw),
            len(template_raw),
            _sha(template_raw),
            len(groups),
        )
    )
    for group, raw in zip(groups, group_raws, strict=True):
        control += _GROUP.pack(len(raw), _sha(raw), len(group))

    payload = bytearray(MAGIC)
    payload += control
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return {
        "archive_bytes": len(payload),
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "user_files": len(items),
        "groups": len(groups),
        "control_bytes": len(control),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": level,
        "group_size": group_size,
        "fused_source_scan": True,
        **fs_stats,
    }


def _open(archive: Path | bytes | bytearray | memoryview) -> tuple[bytes, dict, bytes, list[tuple[int, bytes, list[str], bytes]]]:
    """Open either an on-disk V3 archive or already-resident exact candidate bytes."""
    if isinstance(archive, (bytes, bytearray, memoryview)):
        raw = memoryview(archive)
    else:
        raw = memoryview(Path(archive).read_bytes())
    if len(raw) < len(MAGIC) + _HEADER.size or bytes(raw[: len(MAGIC)]) != MAGIC:
        raise RuntimeError("not a binary-control ZIP-factor profile")
    at = len(MAGIC)
    manifest_size, manifest_sha, template_size, template_sha, group_count = _HEADER.unpack_from(raw, at)
    at += _HEADER.size
    if manifest_size > MAX_DECODE or template_size > MAX_DECODE or not 1 <= group_count <= MAX_FILES:
        raise RuntimeError("binary-control ZIP-factor fixed header exceeds policy")

    descriptors: list[tuple[int, bytes, int]] = []
    for _ in range(group_count):
        if at + _GROUP.size > len(raw):
            raise RuntimeError("truncated binary-control ZIP-factor group descriptor")
        raw_size, raw_sha, member_count = _GROUP.unpack_from(raw, at)
        at += _GROUP.size
        if raw_size > MAX_DECODE or not 1 <= member_count <= MAX_FILES:
            raise RuntimeError("binary-control ZIP-factor group descriptor exceeds policy")
        descriptors.append((raw_size, raw_sha, member_count))

    manifest_blob, at = BASE._read_blob(raw, at)
    template_blob, at = BASE._read_blob(raw, at)
    group_blobs: list[bytes] = []
    for _ in range(group_count):
        blob, at = BASE._read_blob(raw, at)
        group_blobs.append(blob)
    if at != len(raw):
        raise RuntimeError("binary-control ZIP-factor trailing archive bytes")

    manifest_raw = _decompress(manifest_blob, manifest_size, "manifest")
    template_raw = _decompress(template_blob, template_size, "template")
    if _sha(manifest_raw) != manifest_sha or _sha(template_raw) != template_sha:
        raise RuntimeError("binary-control ZIP-factor direct-member authentication")
    manifest = FS.decode_manifest(manifest_raw, max_path_bytes=MAX_PATH, max_entries=MAX_FILES + 1024)
    regular_paths = sorted(manifest["regular"])
    if sum(member_count for _raw_size, _raw_sha, member_count in descriptors) != len(regular_paths):
        raise RuntimeError("binary-control ZIP-factor manifest/group membership mismatch")

    groups: list[tuple[int, bytes, list[str], bytes]] = []
    cursor = 0
    for (raw_size, raw_sha, member_count), blob in zip(descriptors, group_blobs, strict=True):
        paths = regular_paths[cursor:cursor + member_count]
        cursor += member_count
        groups.append((raw_size, raw_sha, paths, blob))
    return manifest_raw, manifest, template_raw, groups


def verify_and_identities(archive: Path | bytes | bytearray | memoryview) -> dict:
    """Verify an on-disk archive or exact resident V3 bytes through the same bounded semantic owner."""
    manifest_raw, manifest, template_raw, groups = _open(archive)
    template = BASE._parse_template(template_raw)
    identities = {FS.FILESYSTEM_MANIFEST: (len(manifest_raw), _sha(manifest_raw))}
    seen: set[str] = set()
    max_amp = 1.0
    max_decode = len(manifest_raw)

    for raw_size, expected_group_sha, paths, blob in groups:
        group_raw = _decompress(blob, raw_size, "group")
        if _sha(group_raw) != expected_group_sha:
            raise RuntimeError("binary-control ZIP-factor group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != GROUP_MAGIC:
            raise RuntimeError("bad binary-control ZIP-factor group magic")
        at = 4
        count, at = BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("binary-control ZIP-factor group count mismatch")
        context = len(template_raw) + len(group_raw)
        if context > MAX_DECODE:
            raise RuntimeError("binary-control ZIP-factor decode-unit ceiling")
        max_decode = max(max_decode, context)

        for rel in paths:
            if rel in seen or rel not in manifest["regular"]:
                raise RuntimeError("binary-control ZIP-factor logical path mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor dynamics")
                crc, csize, usize = struct.unpack_from("<III", view, at)
                at += 12
                if csize > MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor payload")
                payload = bytes(view[at:at +csize])
                at += csize
                dynamics.append((crc, csize, usize, payload))
            restored = BASE._rebuild_zip(template, dynamics)
            expected_size, expected_sha = manifest["regular"][rel]
            got_sha = _sha(restored)
            if len(restored) != expected_size or got_sha != expected_sha:
                raise RuntimeError(f"binary-control ZIP-factor reconstructed identity mismatch: {rel}")
            amp = context / max(1, len(restored))
            if amp > MAX_AMP:
                raise RuntimeError(f"binary-control ZIP-factor locality ceiling: {rel}")
            max_amp = max(max_amp, amp)
            seen.add(rel)
            identities[rel] = (len(restored), got_sha)
        if at != len(view):
            raise RuntimeError("binary-control ZIP-factor group trailing bytes")

    if seen != set(manifest["regular"]):
        raise RuntimeError("binary-control ZIP-factor manifest/content membership mismatch")
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
        return {key: value for key, value in result.items() if key not in {"manifest_raw", "manifest", "identities"}}
    except Exception as exc:
        return {"ok": False, "format_revision": REVISION, "format_profile": PROFILE, "error": repr(exc)}
