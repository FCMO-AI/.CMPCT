"""Bounded revision-25 ZIP framing-factor content profile.

This is the product-side extraction of the successful framing-factor research.  It contains no benchmark/corpus
imports and does not select itself into the canonical product.  The owning canonical tournament may audition it
only after native/Android parity and release evidence are wired.

The profile is intentionally narrow:
* all user regular files must be ordinary non-encrypted ZIPs with one identical static framing layout;
* the canonical r25 filesystem manifest is stored as a separately authenticated direct member;
* inner DEFLATE payloads are never inflated or recompressed;
* groups are independently Zstd-compressed and the shared ZIP template is charged to every selective read;
* every declared raw unit is bounded by 8 MiB and every member read must remain <=8x decoded context.

The archive can therefore reconstruct each source ZIP byte-for-byte while retaining bounded random access.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path, PurePosixPath
import struct

import msgpack
import zstandard as zstd

from experiments import entropygraph_v030_product_fs as FS

MAGIC = b"CMP25ZF\0"
REVISION = 25
PROFILE = "zip-framing-factor-v1"
VERSION = 1
LOCAL = 0x04034B50
CENTRAL = 0x02014B50
EOCD = 0x06054B50
TEMPLATE_MAGIC = b"ZFT1"
GROUP_MAGIC = b"ZFG1"
MAX_META = 8 * 1024 * 1024
MAX_DECODE = 8 * 1024 * 1024
MAX_AMP = 8.0
MAX_FILES = 65_535
MAX_PATH = 16 * 1024
DEFAULT_LEVEL = 1
DEFAULT_GROUP_SIZE = 7


class ProfileNotEligible(RuntimeError):
    pass


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _safe_rel(rel: str) -> str:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe ZIP-factor path")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe ZIP-factor path")
    if len(rel.encode("utf-8", "surrogateescape")) > MAX_PATH:
        raise RuntimeError("ZIP-factor path exceeds policy")
    return rel


def _uvarint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative uvarint")
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        out.append(b | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _read_uvarint(raw: memoryview, at: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if at >= len(raw):
            raise RuntimeError("truncated ZIP-factor uvarint")
        b = int(raw[at]); at += 1
        value |= (b & 0x7F) << shift
        if not b & 0x80:
            return value, at
        shift += 7
    raise RuntimeError("oversized ZIP-factor uvarint")


def _blob(raw: bytes) -> bytes:
    return _uvarint(len(raw)) + raw


def _read_blob(raw: memoryview, at: int) -> tuple[bytes, int]:
    size, at = _read_uvarint(raw, at)
    if size > MAX_DECODE or at + size > len(raw):
        raise RuntimeError("ZIP-factor blob exceeds/truncates policy")
    return bytes(raw[at:at + size]), at + size


def _parse_zip(raw: bytes) -> dict | None:
    at = 0
    local_rows = []
    while at + 4 <= len(raw) and struct.unpack_from("<I", raw, at)[0] == LOCAL:
        if at + 30 > len(raw):
            return None
        fields = struct.unpack_from("<IHHHHHIIIHH", raw, at)
        _sig, version, flags, method, mtime, mdate, crc, csize, usize, name_len, extra_len = fields
        if flags & 0x0001 or flags & 0x0008 or method not in (0, 8):
            return None
        frame_end = at + 30 + name_len + extra_len
        payload_end = frame_end + csize
        if payload_end > len(raw):
            return None
        local_rows.append({
            "version": version, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": raw[at + 30:at + 30 + name_len],
            "extra": raw[at + 30 + name_len:frame_end],
            "payload": raw[frame_end:payload_end], "offset": at,
        })
        at = payload_end
    if not local_rows:
        return None
    central_rows = []
    central_start = at
    while at + 4 <= len(raw) and struct.unpack_from("<I", raw, at)[0] == CENTRAL:
        if at + 46 > len(raw):
            return None
        fields = struct.unpack_from("<IHHHHHHIIIHHHHHII", raw, at)
        (_sig, made, needed, flags, method, mtime, mdate, crc, csize, usize,
         name_len, extra_len, comment_len, disk, internal_attr, external_attr, local_offset) = fields
        body = at + 46
        end = body + name_len + extra_len + comment_len
        if end > len(raw):
            return None
        central_rows.append({
            "made": made, "needed": needed, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize,
            "name": raw[body:body + name_len],
            "extra": raw[body + name_len:body + name_len + extra_len],
            "comment": raw[body + name_len + extra_len:end],
            "disk": disk, "internal_attr": internal_attr, "external_attr": external_attr,
            "local_offset": local_offset,
        })
        at = end
    if len(central_rows) != len(local_rows) or at + 22 > len(raw):
        return None
    sig, disk, disk_cd, entries_disk, entries_total, cd_size, cd_offset, comment_len = struct.unpack_from("<IHHHHIIH", raw, at)
    if sig != EOCD or entries_disk != len(local_rows) or entries_total != len(local_rows):
        return None
    if cd_offset != central_start or cd_size != at - central_start or at + 22 + comment_len != len(raw):
        return None
    for local, central in zip(local_rows, central_rows, strict=True):
        if any((
            local["name"] != central["name"], local["flags"] != central["flags"],
            local["method"] != central["method"], local["mtime"] != central["mtime"],
            local["mdate"] != central["mdate"], local["crc"] != central["crc"],
            local["csize"] != central["csize"], local["usize"] != central["usize"],
            local["offset"] != central["local_offset"],
        )):
            return None
    return {"raw_size": len(raw), "locals": local_rows, "centrals": central_rows,
            "eocd": {"disk": disk, "disk_cd": disk_cd, "comment": raw[at + 22:]}}


def _signature(item: dict) -> tuple:
    return (
        tuple((r["version"], r["flags"], r["method"], r["mtime"], r["mdate"], r["name"], r["extra"]) for r in item["locals"]),
        tuple((r["made"], r["needed"], r["flags"], r["method"], r["mtime"], r["mdate"], r["name"], r["extra"], r["comment"], r["disk"], r["internal_attr"], r["external_attr"]) for r in item["centrals"]),
        (item["eocd"]["disk"], item["eocd"]["disk_cd"], item["eocd"]["comment"]),
    )


def _serialize_template(item: dict) -> bytes:
    out = bytearray(TEMPLATE_MAGIC); out += _uvarint(len(item["locals"]))
    for local, central in zip(item["locals"], item["centrals"], strict=True):
        out += _blob(local["name"]); out += _blob(local["extra"])
        for value in (local["version"], local["flags"], local["method"], local["mtime"], local["mdate"],
                      central["made"], central["needed"], central["flags"], central["method"], central["mtime"],
                      central["mdate"], central["disk"], central["internal_attr"], central["external_attr"]):
            out += _uvarint(int(value))
        out += _blob(central["extra"]); out += _blob(central["comment"])
    out += _uvarint(int(item["eocd"]["disk"])); out += _uvarint(int(item["eocd"]["disk_cd"])); out += _blob(item["eocd"]["comment"])
    if len(out) > MAX_DECODE:
        raise ProfileNotEligible("ZIP-factor template exceeds decode-unit policy")
    return bytes(out)


def _serialize_group(group: list[tuple[str, dict]]) -> bytes:
    out = bytearray(GROUP_MAGIC); out += _uvarint(len(group))
    for rel, item in group:
        out += _blob(rel.encode("utf-8")); out += _uvarint(int(item["raw_size"])); out += _sha(item["source_raw"])
        for local in item["locals"]:
            out += struct.pack("<III", int(local["crc"]), int(local["csize"]), int(local["usize"])); out += local["payload"]
    if len(out) > MAX_DECODE:
        raise ProfileNotEligible("ZIP-factor group exceeds decode-unit policy")
    return bytes(out)


def _parse_template(raw: bytes) -> dict:
    view = memoryview(raw)
    if bytes(view[:4]) != TEMPLATE_MAGIC:
        raise RuntimeError("bad ZIP-factor template magic")
    at = 4; count, at = _read_uvarint(view, at)
    if count > 65_535:
        raise RuntimeError("ZIP-factor member count exceeds policy")
    rows = []
    for _ in range(count):
        name, at = _read_blob(view, at); local_extra, at = _read_blob(view, at); values = []
        for _ in range(14):
            value, at = _read_uvarint(view, at); values.append(value)
        central_extra, at = _read_blob(view, at); central_comment, at = _read_blob(view, at)
        rows.append({"name": name, "local_extra": local_extra, "version": values[0], "flags": values[1],
                     "method": values[2], "mtime": values[3], "mdate": values[4], "made": values[5],
                     "needed": values[6], "cflags": values[7], "cmethod": values[8], "cmtime": values[9],
                     "cmdate": values[10], "disk": values[11], "internal_attr": values[12],
                     "external_attr": values[13], "central_extra": central_extra, "central_comment": central_comment})
    disk, at = _read_uvarint(view, at); disk_cd, at = _read_uvarint(view, at); comment, at = _read_blob(view, at)
    if at != len(view):
        raise RuntimeError("ZIP-factor template trailing bytes")
    return {"rows": rows, "disk": disk, "disk_cd": disk_cd, "comment": comment}


def _rebuild_zip(template: dict, dynamics: list[tuple[int, int, int, bytes]]) -> bytes:
    if len(dynamics) != len(template["rows"]):
        raise RuntimeError("ZIP-factor dynamic member count mismatch")
    out = io.BytesIO(); offsets = []
    for row, (crc, csize, usize, payload) in zip(template["rows"], dynamics, strict=True):
        if len(payload) != csize:
            raise RuntimeError("ZIP-factor compressed payload length mismatch")
        offsets.append(out.tell())
        out.write(struct.pack("<IHHHHHIIIHH", LOCAL, row["version"], row["flags"], row["method"], row["mtime"], row["mdate"], crc, csize, usize, len(row["name"]), len(row["local_extra"])))
        out.write(row["name"]); out.write(row["local_extra"]); out.write(payload)
    cd_start = out.tell()
    for row, (crc, csize, usize, _payload), offset in zip(template["rows"], dynamics, offsets, strict=True):
        out.write(struct.pack("<IHHHHHHIIIHHHHHII", CENTRAL, row["made"], row["needed"], row["cflags"], row["cmethod"], row["cmtime"], row["cmdate"], crc, csize, usize, len(row["name"]), len(row["central_extra"]), len(row["central_comment"]), row["disk"], row["internal_attr"], row["external_attr"], offset))
        out.write(row["name"]); out.write(row["central_extra"]); out.write(row["central_comment"])
    cd_size = out.tell() - cd_start; count = len(template["rows"])
    out.write(struct.pack("<IHHHHIIH", EOCD, template["disk"], template["disk_cd"], count, count, cd_size, cd_start, len(template["comment"])))
    out.write(template["comment"])
    return out.getvalue()


def _decompress(blob: bytes, raw_size: int) -> bytes:
    if raw_size < 0 or raw_size > MAX_DECODE:
        raise RuntimeError("ZIP-factor raw-size declaration exceeds policy")
    raw = zstd.ZstdDecompressor().decompress(blob, max_output_size=raw_size)
    if len(raw) != raw_size:
        raise RuntimeError("ZIP-factor decoded-size mismatch")
    return raw


def build(staged_root: Path, out: Path, *, level: int = DEFAULT_LEVEL, group_size: int = DEFAULT_GROUP_SIZE) -> dict:
    staged_root = Path(staged_root); out = Path(out)
    manifest_path = staged_root / FS.FILESYSTEM_MANIFEST
    if not manifest_path.is_file():
        raise ProfileNotEligible("ZIP-factor profile requires canonical filesystem manifest")
    manifest_raw = manifest_path.read_bytes()
    if len(manifest_raw) > FS.MAX_MANIFEST_BYTES:
        raise ProfileNotEligible("filesystem manifest exceeds policy")
    files = sorted(p for p in staged_root.rglob("*") if p.is_file() and p != manifest_path)
    if not 2 <= len(files) <= MAX_FILES:
        raise ProfileNotEligible("ZIP-factor file-count envelope")
    items = []; signature = None
    for path in files:
        rel = _safe_rel(path.relative_to(staged_root).as_posix())
        if path.suffix.lower() != ".zip":
            raise ProfileNotEligible("ZIP-factor user tree must contain only ZIP regular files")
        source_raw = path.read_bytes(); parsed = _parse_zip(source_raw)
        if parsed is None:
            raise ProfileNotEligible(f"unsupported ZIP structure: {rel}")
        parsed["source_raw"] = source_raw
        sig = _signature(parsed)
        if signature is None: signature = sig
        elif sig != signature: raise ProfileNotEligible(f"ZIP framing layout drift: {rel}")
        items.append((rel, parsed))
    template_raw = _serialize_template(items[0][1])
    groups = [items[i:i + group_size] for i in range(0, len(items), group_size)]
    group_raws = [_serialize_group(group) for group in groups]
    max_amp = max((len(template_raw) + len(raw)) / max(1, min(item[1]["raw_size"] for item in group)) for group, raw in zip(groups, group_raws, strict=True))
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    if max_amp > MAX_AMP or max_decode > MAX_DECODE:
        raise ProfileNotEligible("ZIP-factor locality ceiling")
    compressor = zstd.ZstdCompressor(level=level, threads=0)
    manifest_blob = compressor.compress(manifest_raw); template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]
    meta = {
        "v": VERSION, "profile": PROFILE, "level": level, "group_size": group_size,
        "manifest_raw": len(manifest_raw), "manifest_sha": _sha(manifest_raw),
        "template_raw": len(template_raw), "template_sha": _sha(template_raw),
        "groups": [[len(raw), _sha(raw), [rel for rel, _item in group], [int(item["raw_size"]) for _rel, item in group]] for group, raw in zip(groups, group_raws, strict=True)],
        "max_decode_unit": max_decode, "max_member_read_amplification": float(max_amp),
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_META:
        raise ProfileNotEligible("ZIP-factor metadata exceeds policy")
    payload = bytearray(MAGIC); payload += struct.pack("<I", len(meta_raw)); payload += meta_raw
    payload += _blob(manifest_blob); payload += _blob(template_blob)
    for blob in group_blobs: payload += _blob(blob)
    out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(payload)
    return {"archive_bytes": out.stat().st_size, "format_revision": REVISION, "format_profile": PROFILE,
            "user_files": len(files), "groups": len(groups), "max_decode_unit_bytes": max_decode,
            "max_member_read_amplification": max_amp, "level": level, "group_size": group_size}


def _open(archive: Path) -> tuple[dict, bytes, bytes, list[bytes]]:
    raw = memoryview(Path(archive).read_bytes())
    if bytes(raw[:8]) != MAGIC or len(raw) < 12:
        raise RuntimeError("not a canonical ZIP-factor profile")
    meta_len = struct.unpack_from("<I", raw, 8)[0]
    if meta_len > MAX_META or 12 + meta_len > len(raw):
        raise RuntimeError("ZIP-factor metadata declaration")
    try: meta = msgpack.unpackb(bytes(raw[12:12 + meta_len]), raw=False, strict_map_key=True, max_map_len=32, max_array_len=MAX_FILES * 4 + 1024, max_bin_len=MAX_META, max_str_len=MAX_PATH)
    except Exception as exc: raise RuntimeError("invalid ZIP-factor metadata") from exc
    if not isinstance(meta, dict) or meta.get("v") != VERSION or meta.get("profile") != PROFILE:
        raise RuntimeError("unsupported ZIP-factor profile metadata")
    groups = meta.get("groups")
    if not isinstance(groups, list) or not 1 <= len(groups) <= MAX_FILES:
        raise RuntimeError("ZIP-factor group declaration")
    at = 12 + meta_len; manifest_blob, at = _read_blob(raw, at); template_blob, at = _read_blob(raw, at); blobs = []
    for _ in groups:
        blob, at = _read_blob(raw, at); blobs.append(blob)
    if at != len(raw): raise RuntimeError("ZIP-factor trailing archive bytes")
    manifest = _decompress(manifest_blob, int(meta["manifest_raw"])); template = _decompress(template_blob, int(meta["template_raw"]))
    if _sha(manifest) != bytes(meta["manifest_sha"]) or _sha(template) != bytes(meta["template_sha"]):
        raise RuntimeError("ZIP-factor authenticated direct member mismatch")
    return meta, manifest, template, blobs


def read_member_with_stats(archive: Path, rel: str) -> tuple[bytes, dict]:
    rel = _safe_rel(rel); meta, manifest, template_raw, blobs = _open(archive)
    if rel == FS.FILESYSTEM_MANIFEST:
        return manifest, {"logical_bytes": len(manifest), "decoded_context_bytes": len(manifest), "decoded_context_amplification": 1.0, "format_profile": PROFILE}
    group_index = None; file_index = None
    for gi, desc in enumerate(meta["groups"]):
        paths = desc[2]
        if rel in paths:
            group_index = gi; file_index = paths.index(rel); break
    if group_index is None or file_index is None: raise KeyError(rel)
    desc = meta["groups"][group_index]; group_raw = _decompress(blobs[group_index], int(desc[0]))
    if _sha(group_raw) != bytes(desc[1]): raise RuntimeError("ZIP-factor group authentication")
    view = memoryview(group_raw)
    if bytes(view[:4]) != GROUP_MAGIC: raise RuntimeError("bad ZIP-factor group magic")
    at = 4; count, at = _read_uvarint(view, at); template = _parse_template(template_raw); selected = None
    for idx in range(count):
        rel_b, at = _read_blob(view, at); expected_size, at = _read_uvarint(view, at)
        if at + 32 > len(view): raise RuntimeError("truncated ZIP-factor source digest")
        expected_sha = bytes(view[at:at + 32]); at += 32; dynamics = []
        for _row in template["rows"]:
            if at + 12 > len(view): raise RuntimeError("truncated ZIP-factor dynamics")
            crc, csize, usize = struct.unpack_from("<III", view, at); at += 12
            if csize > MAX_DECODE or at + csize > len(view): raise RuntimeError("truncated ZIP-factor compressed payload")
            payload = bytes(view[at:at + csize]); at += csize; dynamics.append((crc, csize, usize, payload))
        current_rel = rel_b.decode("utf-8")
        if idx == file_index:
            if current_rel != rel: raise RuntimeError("ZIP-factor group index/path mismatch")
            restored = _rebuild_zip(template, dynamics)
            if len(restored) != expected_size or _sha(restored) != expected_sha: raise RuntimeError("ZIP-factor reconstructed member identity")
            selected = restored
    if at != len(view): raise RuntimeError("ZIP-factor group trailing bytes")
    if selected is None: raise KeyError(rel)
    context = len(template_raw) + len(group_raw); amp = context / max(1, len(selected))
    if context > MAX_DECODE or amp > MAX_AMP: raise RuntimeError("ZIP-factor selective-read locality ceiling")
    return selected, {"logical_bytes": len(selected), "decoded_context_bytes": context, "decoded_context_amplification": amp, "format_profile": PROFILE}


def content_identities(archive: Path) -> dict[str, tuple[int, bytes]]:
    meta, manifest, _template, _blobs = _open(archive)
    result = {FS.FILESYSTEM_MANIFEST: (len(manifest), _sha(manifest))}
    for desc in meta["groups"]:
        for rel, size in zip(desc[2], desc[3], strict=True):
            raw, _stats = read_member_with_stats(archive, rel); result[str(rel)] = (int(size), _sha(raw))
    return result


def strong_verify(archive: Path) -> dict:
    try:
        identities = content_identities(archive)
        for rel, (size, digest) in identities.items():
            raw, stats = read_member_with_stats(archive, rel)
            if len(raw) != size or _sha(raw) != digest or stats["decoded_context_amplification"] > MAX_AMP:
                raise RuntimeError(f"ZIP-factor strong verification failed: {rel}")
        return {"ok": True, "format_revision": REVISION, "format_profile": PROFILE, "verified_files": len(identities), "max_member_read_amplification": max(read_member_with_stats(archive, rel)[1]["decoded_context_amplification"] for rel in identities)}
    except Exception as exc:
        return {"ok": False, "format_revision": REVISION, "format_profile": PROFILE, "error": repr(exc)}
