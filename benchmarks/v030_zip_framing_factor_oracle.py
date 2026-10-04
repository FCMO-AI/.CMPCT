from __future__ import annotations

"""ZIP framing-factor oracle for the v0.30 deflate-family frontier.

Earlier exact experiments bracketed the problem:
- raw-DEFLATE segmentation is comfortably faster than ZIP/Zstd but repeats too much ZIP framing to beat Zstd size;
- plaintext reinflate normalization beats Zstd size but spends far too long inflating/recompressing members.

This oracle keeps the fast boundary: it NEVER inflates an inner DEFLATE stream. Instead, it parses ordinary ZIP
local/central records and admits only families whose framing layout is identical apart from CRC/compressed-size/
uncompressed-size and offsets that are mechanically recomputable. The shared static ZIP structure is encoded once;
each bounded group stores only per-bundle dynamic fields plus the original compressed payload bytes. Restore rebuilds
local headers, central records and EOCD from those exact fields and must reproduce every source ZIP byte-for-byte.

The shared template is charged to selective reads. A member read therefore decodes its owning group plus the static
template; candidates exceeding <=8x amplification or <=8 MiB are rejected. Creation time includes source reads, ZIP
parsing, layout admission, factor serialization, Zstd compression, and archive publication. Extraction/verification is
outside the creation timer exactly as it is for the external ZIP/Zstd comparators, but exact reconstruction is still
mandatory before any candidate receives credit.

Research only: a positive result is a productization target, not canonical r25 authority. Shipping would still require
a fixed grammar, hostile-input bounds, Python/native/Android reader parity, integrity/recovery coverage and the full
release lock on one exact candidate.
"""

import argparse
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT

MAGIC = b"ZFF1"
TEMPLATE_MAGIC = b"ZFT1"
GROUP_MAGIC = b"ZFG1"
LOCAL = 0x04034B50
CENTRAL = 0x02014B50
EOCD = 0x06054B50
LEVELS = (1, 3, 6)
GROUP_SIZES = (6, 7)
MAX_AMP = 8.0
MAX_DECODE = 8 * 1024 * 1024


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
            raise ValueError("truncated uvarint")
        b = int(raw[at]); at += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, at
        shift += 7
    raise ValueError("oversized uvarint")


def _blob(raw: bytes) -> bytes:
    return _uvarint(len(raw)) + raw


def _read_blob(raw: memoryview, at: int) -> tuple[bytes, int]:
    n, at = _read_uvarint(raw, at)
    if n < 0 or at + n > len(raw):
        raise ValueError("truncated blob")
    return bytes(raw[at:at + n]), at + n


def _parse_zip(raw: bytes) -> dict | None:
    """Parse a conservative no-descriptor ZIP subset without inflating payloads."""
    at = 0
    local_rows = []
    while at + 4 <= len(raw) and struct.unpack_from("<I", raw, at)[0] == LOCAL:
        if at + 30 > len(raw):
            return None
        (
            _sig, version, flags, method, mtime, mdate, crc, csize, usize, name_len, extra_len
        ) = struct.unpack_from("<IHHHHHIIIHH", raw, at)
        if flags & 0x0001 or flags & 0x0008 or method not in (0, 8):
            return None
        frame_end = at + 30 + name_len + extra_len
        payload_end = frame_end + csize
        if frame_end > len(raw) or payload_end > len(raw):
            return None
        name = raw[at + 30:at + 30 + name_len]
        extra = raw[at + 30 + name_len:frame_end]
        local_rows.append({
            "version": version, "flags": flags, "method": method, "mtime": mtime, "mdate": mdate,
            "crc": crc, "csize": csize, "usize": usize, "name": name, "extra": extra,
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
        (
            _sig, made, needed, flags, method, mtime, mdate, crc, csize, usize,
            name_len, extra_len, comment_len, disk, internal_attr, external_attr, local_offset,
        ) = fields
        body_at = at + 46
        end = body_at + name_len + extra_len + comment_len
        if end > len(raw):
            return None
        central_rows.append({
            "made": made, "needed": needed, "flags": flags, "method": method, "mtime": mtime,
            "mdate": mdate, "crc": crc, "csize": csize, "usize": usize,
            "name": raw[body_at:body_at + name_len],
            "extra": raw[body_at + name_len:body_at + name_len + extra_len],
            "comment": raw[body_at + name_len + extra_len:end],
            "disk": disk, "internal_attr": internal_attr, "external_attr": external_attr,
            "local_offset": local_offset,
        })
        at = end
    if len(central_rows) != len(local_rows) or at + 22 > len(raw):
        return None
    eocd = struct.unpack_from("<IHHHHIIH", raw, at)
    sig, disk, disk_cd, entries_disk, entries_total, cd_size, cd_offset, comment_len = eocd
    if sig != EOCD or entries_disk != len(local_rows) or entries_total != len(local_rows):
        return None
    if cd_offset != central_start or cd_size != at - central_start or at + 22 + comment_len != len(raw):
        return None
    comment = raw[at + 22:]

    for local, central in zip(local_rows, central_rows, strict=True):
        if (
            local["name"] != central["name"] or local["flags"] != central["flags"] or
            local["method"] != central["method"] or local["mtime"] != central["mtime"] or
            local["mdate"] != central["mdate"] or local["crc"] != central["crc"] or
            local["csize"] != central["csize"] or local["usize"] != central["usize"] or
            local["offset"] != central["local_offset"]
        ):
            return None
    return {
        "raw_size": len(raw), "locals": local_rows, "centrals": central_rows,
        "eocd": {"disk": disk, "disk_cd": disk_cd, "comment": comment},
    }


def _static_signature(item: dict) -> tuple:
    locals_sig = tuple((
        r["version"], r["flags"], r["method"], r["mtime"], r["mdate"], r["name"], r["extra"]
    ) for r in item["locals"])
    central_sig = tuple((
        r["made"], r["needed"], r["flags"], r["method"], r["mtime"], r["mdate"],
        r["name"], r["extra"], r["comment"], r["disk"], r["internal_attr"], r["external_attr"]
    ) for r in item["centrals"])
    e = item["eocd"]
    return locals_sig, central_sig, (e["disk"], e["disk_cd"], e["comment"])


def _parse_sources(root: Path) -> tuple[list[tuple[str, dict]] | None, float, str | None]:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.suffix.lower() != ".zip" for p in files):
        return None, time.perf_counter() - started, "not-all-zip"
    items = []
    signature = None
    for path in files:
        parsed = _parse_zip(path.read_bytes())
        if parsed is None:
            return None, time.perf_counter() - started, f"unsupported-zip:{path.name}"
        sig = _static_signature(parsed)
        if signature is None:
            signature = sig
        elif sig != signature:
            return None, time.perf_counter() - started, f"framing-layout-drift:{path.name}"
        items.append((path.relative_to(root).as_posix(), parsed))
    return items, time.perf_counter() - started, None


def _serialize_template(item: dict) -> bytes:
    out = bytearray(TEMPLATE_MAGIC)
    out += _uvarint(len(item["locals"]))
    for local, central in zip(item["locals"], item["centrals"], strict=True):
        out += _blob(local["name"]); out += _blob(local["extra"])
        for value in (
            local["version"], local["flags"], local["method"], local["mtime"], local["mdate"],
            central["made"], central["needed"], central["flags"], central["method"],
            central["mtime"], central["mdate"], central["disk"], central["internal_attr"],
            central["external_attr"],
        ):
            out += _uvarint(int(value))
        # Central name is required to equal the local name by admission; do not store it twice.
        out += _blob(central["extra"]); out += _blob(central["comment"])
    e = item["eocd"]
    out += _uvarint(int(e["disk"])); out += _uvarint(int(e["disk_cd"])); out += _blob(e["comment"])
    return bytes(out)


def _serialize_group(group: list[tuple[str, dict]]) -> bytes:
    out = bytearray(GROUP_MAGIC); out += _uvarint(len(group))
    for rel, item in group:
        out += _blob(rel.encode("utf-8")); out += _uvarint(int(item["raw_size"]))
        for local in item["locals"]:
            out += struct.pack("<III", int(local["crc"]), int(local["csize"]), int(local["usize"]))
            out += local["payload"]
    return bytes(out)


def _parse_template(raw: bytes) -> dict:
    view = memoryview(raw); at = 0
    if bytes(view[:4]) != TEMPLATE_MAGIC:
        raise ValueError("bad template magic")
    at = 4; count, at = _read_uvarint(view, at)
    rows = []
    for _ in range(count):
        name, at = _read_blob(view, at); local_extra, at = _read_blob(view, at)
        values = []
        for _ in range(14):
            value, at = _read_uvarint(view, at); values.append(value)
        central_extra, at = _read_blob(view, at); central_comment, at = _read_blob(view, at)
        rows.append({
            "name": name, "local_extra": local_extra,
            "version": values[0], "flags": values[1], "method": values[2], "mtime": values[3], "mdate": values[4],
            "made": values[5], "needed": values[6], "cflags": values[7], "cmethod": values[8],
            "cmtime": values[9], "cmdate": values[10], "disk": values[11], "internal_attr": values[12],
            "external_attr": values[13], "central_extra": central_extra, "central_comment": central_comment,
        })
    disk, at = _read_uvarint(view, at); disk_cd, at = _read_uvarint(view, at); comment, at = _read_blob(view, at)
    if at != len(view):
        raise ValueError("template trailing bytes")
    return {"rows": rows, "disk": disk, "disk_cd": disk_cd, "comment": comment}


def _rebuild_zip(template: dict, dynamics: list[tuple[int, int, int, bytes]]) -> bytes:
    if len(dynamics) != len(template["rows"]):
        raise ValueError("dynamic member count mismatch")
    out = io.BytesIO(); offsets = []
    for row, (crc, csize, usize, payload) in zip(template["rows"], dynamics, strict=True):
        if len(payload) != csize:
            raise ValueError("compressed payload length mismatch")
        offsets.append(out.tell())
        out.write(struct.pack(
            "<IHHHHHIIIHH", LOCAL, row["version"], row["flags"], row["method"], row["mtime"], row["mdate"],
            crc, csize, usize, len(row["name"]), len(row["local_extra"])
        ))
        out.write(row["name"]); out.write(row["local_extra"]); out.write(payload)
    cd_start = out.tell()
    for row, (crc, csize, usize, _payload), offset in zip(template["rows"], dynamics, offsets, strict=True):
        out.write(struct.pack(
            "<IHHHHHHIIIHHHHHII", CENTRAL, row["made"], row["needed"], row["cflags"], row["cmethod"],
            row["cmtime"], row["cmdate"], crc, csize, usize, len(row["name"]), len(row["central_extra"]),
            len(row["central_comment"]), row["disk"], row["internal_attr"], row["external_attr"], offset
        ))
        out.write(row["name"]); out.write(row["central_extra"]); out.write(row["central_comment"])
    cd_size = out.tell() - cd_start
    count = len(template["rows"])
    out.write(struct.pack(
        "<IHHHHIIH", EOCD, template["disk"], template["disk_cd"], count, count, cd_size, cd_start,
        len(template["comment"])
    ))
    out.write(template["comment"])
    return out.getvalue()


def _build_candidate(items: list[tuple[str, dict]], group_size: int, level: int, archive: Path, parse_s: float) -> dict:
    started = time.perf_counter()
    template_raw = _serialize_template(items[0][1])
    groups = [items[i:i + group_size] for i in range(0, len(items), group_size)]
    group_raws = [_serialize_group(group) for group in groups]
    factor_s = time.perf_counter() - started

    started = time.perf_counter()
    compressor = zstd.ZstdCompressor(level=level, threads=0)
    template_blob = compressor.compress(template_raw)
    group_blobs = [compressor.compress(raw) for raw in group_raws]
    out = io.BytesIO(); out.write(MAGIC); out.write(bytes([level, group_size])); out.write(_uvarint(len(template_raw))); out.write(_blob(template_blob)); out.write(_uvarint(len(group_blobs)))
    for raw_group, packed in zip(group_raws, group_blobs, strict=True):
        out.write(_uvarint(len(raw_group))); out.write(_blob(packed))
    archive.write_bytes(out.getvalue())
    compression_write_s = time.perf_counter() - started

    max_decode = max((len(template_raw) + len(raw) for raw in group_raws), default=len(template_raw))
    max_amp = 0.0
    for group, raw_group in zip(groups, group_raws, strict=True):
        smallest = min(int(item[1]["raw_size"]) for item in group)
        max_amp = max(max_amp, (len(template_raw) + len(raw_group)) / max(1, smallest))
    return {
        "group_size": group_size, "level": level, "archive_bytes": archive.stat().st_size,
        "source_parse_s": parse_s, "factor_serialize_s": factor_s, "compression_write_s": compression_write_s,
        "create_s": parse_s + factor_s + compression_write_s,
        "template_raw_bytes": len(template_raw), "group_raw_bytes": [len(raw) for raw in group_raws],
        "max_decode_unit_bytes": max_decode, "max_member_read_amplification": max_amp,
        "locality_green": max_decode <= MAX_DECODE and max_amp <= MAX_AMP,
    }


def _restore(archive: Path, out_root: Path) -> None:
    view = memoryview(archive.read_bytes()); at = 0
    if bytes(view[:4]) != MAGIC:
        raise ValueError("bad archive magic")
    at = 4
    if at + 2 > len(view):
        raise ValueError("truncated archive header")
    level = int(view[at]); _group_size = int(view[at + 1]); at += 2
    template_size, at = _read_uvarint(view, at); template_blob, at = _read_blob(view, at)
    template_raw = zstd.ZstdDecompressor().decompress(template_blob, max_output_size=template_size)
    if len(template_raw) != template_size:
        raise ValueError("template size mismatch")
    template = _parse_template(template_raw)
    group_count, at = _read_uvarint(view, at)
    del level  # profile evidence only; decompression is self-describing.
    out_root.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for _ in range(group_count):
        raw_size, at = _read_uvarint(view, at); packed, at = _read_blob(view, at)
        group = memoryview(zstd.ZstdDecompressor().decompress(packed, max_output_size=raw_size))
        if len(group) != raw_size or bytes(group[:4]) != GROUP_MAGIC:
            raise ValueError("bad group")
        gat = 4; file_count, gat = _read_uvarint(group, gat)
        for _ in range(file_count):
            rel_b, gat = _read_blob(group, gat); expected_raw, gat = _read_uvarint(group, gat)
            rel = rel_b.decode("utf-8")
            if not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
                raise ValueError("unsafe/duplicate restored path")
            dynamics = []
            for _row in template["rows"]:
                if gat + 12 > len(group):
                    raise ValueError("truncated dynamic fields")
                crc, csize, usize = struct.unpack_from("<III", group, gat); gat += 12
                if gat + csize > len(group):
                    raise ValueError("truncated compressed payload")
                payload = bytes(group[gat:gat + csize]); gat += csize
                dynamics.append((crc, csize, usize, payload))
            restored = _rebuild_zip(template, dynamics)
            if len(restored) != expected_raw:
                raise ValueError("restored ZIP size mismatch")
            target = out_root / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(restored)
            seen.add(rel)
        if gat != len(group):
            raise ValueError("group trailing bytes")
    if at != len(view):
        raise ValueError("archive trailing bytes")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    corpus = work_root / "corpus"; CORPUS.build(corpus); source = corpus / "04_deflate_family"
    expected_tree = CORPUS.tree_hash(source)

    with tempfile.TemporaryDirectory(prefix="cmpct-zff-", dir=work_root) as td_raw:
        td = Path(td_raw); stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)
        items, parse_s, reason = _parse_sources(stage)
        candidates = []
        if items is not None:
            for group_size in GROUP_SIZES:
                for level in LEVELS:
                    archive = td / f"candidate-g{group_size}-l{level}.zff"
                    c = _build_candidate(items, group_size, level, archive, parse_s)
                    restored = td / f"restore-g{group_size}-l{level}"; restored.mkdir(); _restore(archive, restored)
                    c["tree_verified"] = CORPUS.tree_hash(restored) == expected_tree
                    # Stronger than tree identity: every nested ZIP must be restored byte-for-byte.
                    c["all_zip_bytes_exact"] = all(
                        (restored / path.relative_to(stage)).read_bytes() == path.read_bytes()
                        for path in sorted(p for p in stage.rglob("*") if p.is_file())
                    )
                    c["beats_zip_size"] = c["archive_bytes"] < zip_result["archive_bytes"]
                    c["beats_zstd19_size"] = c["archive_bytes"] < zstd_result["archive_bytes"]
                    c["beats_zip_create"] = c["create_s"] < zip_result["create_s"]
                    c["beats_zstd19_create"] = c["create_s"] < zstd_result["create_s"]
                    c["viable"] = c["tree_verified"] and c["all_zip_bytes_exact"] and c["locality_green"] and all(c[k] for k in (
                        "beats_zip_size", "beats_zstd19_size", "beats_zip_create", "beats_zstd19_create"
                    ))
                    candidates.append(c)
        viable = [c for c in candidates if c["viable"]]
        best = min(viable, key=lambda c: (c["archive_bytes"], c["create_s"])) if viable else None
        return {
            "schema": "cmpct-v030-zip-framing-factor-oracle-v1",
            "claim_boundary": "research-only ZIP framing factorization; no canonical/native/Android promotion implied",
            "workload": "resemblance_hostile_v1/04_deflate_family", "tree_sha256": expected_tree,
            "source_parse_s": parse_s, "parse_rejection": reason, "source_zip_files": len(items) if items else 0,
            "zip": zip_result, "tar_zstd19": zstd_result, "candidates": candidates, "viable_candidate": best,
            "gate": {
                "source_admitted": items is not None,
                "all_candidates_exact_tree": bool(candidates) and all(c["tree_verified"] for c in candidates),
                "all_candidates_exact_zip_bytes": bool(candidates) and all(c["all_zip_bytes_exact"] for c in candidates),
                "all_candidates_locality_green": bool(candidates) and all(c["locality_green"] for c in candidates),
                "four_way_win_found": best is not None,
            },
        }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zip-framing-factor-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zip-framing-factor.json")); a = p.parse_args()
    result = run(a.work_root)
    g = result["gate"]; g["passed"] = g["source_admitted"] and g["all_candidates_exact_tree"] and g["all_candidates_exact_zip_bytes"] and g["all_candidates_locality_green"]
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"zip": result["zip"], "zstd": result["tar_zstd19"], "viable_candidate": result["viable_candidate"], "gate": g}, indent=2), flush=True)
    if not g["passed"]:
        raise SystemExit("ZIP framing-factor oracle correctness/locality gate failed")


if __name__ == "__main__":
    main()
