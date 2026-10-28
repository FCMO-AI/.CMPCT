"""CMPCT v0.30 research oracle — Geometry as a physical overlay on accepted v0.29.

The standalone Geometry seed proved that reversible byte geometry can expose large entropy wins, but a
parallel whole-artifact representation throws away Mosaic's already-proven logical graph whenever Geometry
wins.  This oracle asks the compositional question instead: can the *physical records* of the accepted
attempt-5 graph be transformed while the logical files/nodes/delta/mosaic descriptions remain unchanged?

For an eligible physical record the writer auditions fixed byte lanes and recurrent-delimiter geometry,
compresses the transformed bytes with the same Zstd-19 primitive, and records an inverse descriptor.  The
physical CRC32/SHA-256 continue to name the exact **pre-transform v0.29 record bytes**.  Decode is therefore:

    authenticated payload -> ordinary codec -> inverse Geometry -> original v0.29 record bytes

The unchanged attempt-5 logical graph consumes those bytes afterward.  Untouched records retain their exact
original payload bytes and physical headers.  The complete overlay archive, including new metadata and its
recovery copy, must beat the accepted v0.29 artifact or the build publishes v0.29 byte-for-byte.

Footnote: ``CMPNX14`` is an experimental measurement grammar, not canonical revision 24.  Its verifier
materializes an ordinary attempt-5 *verification view* from the inversed records and delegates logical-graph
verification to the accepted attempt-5 reader.  Promotion requires a native/shared streaming reader rather
than this deliberately conservative oracle adapter.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import time

import msgpack

from experiments import entropygraph_v029_release as BASE
from experiments import entropygraph_v029_residual_pack as A5

H = A5.H
zc = A5.zc
zd = A5.zd
PH = A5.PH
CODEC_RAW = A5.CODEC_RAW
CODEC_ZSTD = A5.CODEC_ZSTD
CODEC_PREFLATE = A5.CODEC_PREFLATE
MAX_DECODE_UNIT = A5.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = A5.MAX_DECODER_MEMORY

MAG = b"CMPNX14\0"
TAIL = b"CMN14T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")

LANE_WIDTHS = (2, 4, 8, 16)
MIN_RECORD_BYTES = 16 * 1024
MAX_OVERLAY_RECORD = 2 * 1024 * 1024
MAX_MEMBER_READ_AMP = 8.0
MIN_PAYLOAD_SAVING = 128
MAX_DELIMITER_CANDIDATES = 4
MIN_DELIMITER_OCCURRENCES = 64
MAX_DELIMITER_SEGMENTS = 65_536
MAX_DELIMITER_REGULARITY = 0.50
MAX_DELIMITER_CELL_SCANS = 8 * MAX_OVERLAY_RECORD


def treehash(root: Path) -> str:
    return A5.treehash(root)


def _merkle_root(leaves: list[bytes]) -> bytes:
    return A5.V028._merkle_root(leaves)


def lane_forward(raw: bytes, width: int) -> bytes:
    if width not in LANE_WIDTHS:
        raise ValueError("unsupported Geometry overlay lane width")
    full = len(raw) - (len(raw) % width)
    body = raw[:full]
    return b"".join(body[lane::width] for lane in range(width)) + raw[full:]


def lane_inverse(stored: bytes, width: int, logical_size: int) -> bytes:
    if width not in LANE_WIDTHS or logical_size < 0 or len(stored) != logical_size:
        raise RuntimeError("invalid Geometry overlay lane descriptor")
    full = logical_size - (logical_size % width)
    rows = full // width
    body = stored[:full]
    out = bytearray(full)
    for lane in range(width):
        start = lane * rows
        out[lane:full:width] = body[start:start + rows]
    out.extend(stored[full:])
    return bytes(out)


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative Geometry overlay varint")
    while True:
        byte = value & 0x7F
        value >>= 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return


def _get_varint(buf: bytes, pos: int) -> tuple[int, int]:
    value = shift = 0
    for _ in range(10):
        if pos >= len(buf):
            raise RuntimeError("short Geometry overlay varint")
        byte = buf[pos]; pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise RuntimeError("overlong Geometry overlay varint")


def _delimiter_cell_work(raw: bytes, delimiter: int) -> int:
    parts = raw.split(bytes((delimiter,)))
    return len(parts) * max(map(len, parts), default=0)


def _delimiter_rank(raw: bytes) -> list[int]:
    positions: list[list[int]] = [[] for _ in range(256)]
    for index, byte in enumerate(raw):
        positions[byte].append(index)
    ranked: list[tuple[float, int]] = []
    for byte, pos in enumerate(positions):
        count = len(pos)
        if count < MIN_DELIMITER_OCCURRENCES or count + 1 > MAX_DELIMITER_SEGMENTS:
            continue
        gaps: list[int] = []
        previous = -1
        for current in pos:
            gaps.append(current - previous - 1); previous = current
        gaps.append(len(raw) - previous - 1)
        mean = sum(gaps) / len(gaps)
        variance = sum((gap - mean) ** 2 for gap in gaps) / len(gaps)
        score = math.sqrt(variance) / (mean + 1.0) + 8.0 / math.sqrt(count)
        if score <= MAX_DELIMITER_REGULARITY and _delimiter_cell_work(raw, byte) <= MAX_DELIMITER_CELL_SCANS:
            ranked.append((score, byte))
    ranked.sort()
    return [byte for _, byte in ranked[:MAX_DELIMITER_CANDIDATES]]


def delimiter_forward(raw: bytes, delimiter: int) -> bytes:
    if not 0 <= delimiter <= 255 or len(raw) > MAX_OVERLAY_RECORD:
        raise ValueError("invalid Geometry overlay delimiter input")
    parts = raw.split(bytes((delimiter,)))
    if len(parts) > MAX_DELIMITER_SEGMENTS or len(parts) * max(map(len, parts), default=0) > MAX_DELIMITER_CELL_SCANS:
        raise ValueError("Geometry overlay delimiter work budget exceeded")
    out = bytearray(b"DGO1"); out.append(delimiter); _put_varint(out, len(parts))
    for part in parts:
        _put_varint(out, len(part))
    for column in range(max(map(len, parts), default=0)):
        for part in parts:
            if column < len(part):
                out.append(part[column])
    return bytes(out)


def delimiter_inverse(encoded: bytes, logical_size: int) -> bytes:
    if not encoded.startswith(b"DGO1") or len(encoded) < 6 or logical_size < 0 or logical_size > MAX_OVERLAY_RECORD:
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = _get_varint(encoded, 5)
    if count < 1 or count > MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")
    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = _get_varint(encoded, pos)
        if length > MAX_OVERLAY_RECORD or logical_members + length > MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length); logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    if count * max(lengths, default=0) > MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")
    rows = [bytearray(length) for length in lengths]
    cursor = 0
    for column in range(max(lengths, default=0)):
        for index, length in enumerate(lengths):
            if column < length:
                rows[index][column] = body[cursor]; cursor += 1
    if cursor != len(body):
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes((delimiter,)).join(bytes(row) for row in rows)


def _compress_transformed(raw: bytes) -> tuple[int, bytes]:
    compressed = zc(raw, 19)
    return (CODEC_ZSTD, compressed) if len(compressed) < len(raw) else (CODEC_RAW, raw)


def _read_base_records(path: Path) -> tuple[dict, list[tuple[int, int, bytes, int, bytes]]]:
    stream, meta, record_start, offsets, _ = A5._open(path)
    records = []
    try:
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short accepted-v0.29 record header")
            codec, usize, csize, crc, logical_sha = PH.unpack(header)
            payload = stream.read(csize)
            if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("accepted-v0.29 physical leaf mismatch")
            record = (codec, usize, payload, crc, logical_sha)
            A5._decode_record(record)  # authenticate the exact original physical bytes before audition.
            records.append(record)
    finally:
        stream.close()
    return meta, records


def _record_member_lengths(meta: dict, record_count: int) -> dict[int, list[int]]:
    users: dict[int, list[int]] = {record_id: [] for record_id in range(record_count)}
    nodes = meta.get("nodes")
    files = meta.get("files")
    if not isinstance(nodes, list) or not isinstance(files, dict):
        raise RuntimeError("accepted-v0.29 graph metadata shape")
    for desc in nodes:
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed accepted-v0.29 node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 5:
            record_id, logical_size = desc[1], desc[3]
        elif kind in ("delta", "mosaic") and len(desc) == 5:
            record_id, logical_size = desc[2], desc[3]
        elif kind == "delta_pack" and len(desc) == 7:
            record_id, logical_size = desc[2], desc[5]
        elif kind == "pack_mosaic" and len(desc) == 7:
            record_id, logical_size = desc[1], desc[5]
        else:
            raise RuntimeError(f"unexpected accepted-v0.29 node kind: {kind}")
        if not isinstance(record_id, int) or not 0 <= record_id < record_count:
            raise RuntimeError("accepted-v0.29 record reference out of range")
        users[record_id].append(max(1, int(logical_size)))
    for desc in files.values():
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed accepted-v0.29 file descriptor")
        if desc[0] == "preflate":
            record_id, logical_size = desc[1], desc[2]
            if not isinstance(record_id, int) or not 0 <= record_id < record_count:
                raise RuntimeError("accepted-v0.29 preflate record reference out of range")
            users[record_id].append(max(1, int(logical_size)))
        elif desc[0] != "nodes":
            raise RuntimeError("unexpected accepted-v0.29 file kind")
    return users


def _audition_record(
    record_id: int,
    record: tuple[int, int, bytes, int, bytes],
    member_lengths: list[int],
) -> tuple[tuple[int, int, bytes, int, bytes], list | None, dict]:
    raw = A5._decode_record(record)
    amp = max((len(raw) / length for length in member_lengths), default=float("inf"))
    baseline_payload = record[2]
    stats = {"record_id": record_id, "raw_bytes": len(raw), "baseline_payload_bytes": len(baseline_payload),
             "max_member_read_amplification": amp, "selected": "none", "payload_saving_bytes": 0}
    if not (MIN_RECORD_BYTES <= len(raw) <= MAX_OVERLAY_RECORD) or amp > MAX_MEMBER_READ_AMP:
        return record, None, stats

    best_payload = baseline_payload
    best: tuple[str, int, bytes, int, bytes] | None = None  # kind, param, physical, codec, payload
    for width in LANE_WIDTHS:
        transformed = lane_forward(raw, width)
        if lane_inverse(transformed, width, len(raw)) != raw:
            raise RuntimeError("Geometry overlay lane inverse failed")
        codec, payload = _compress_transformed(transformed)
        if len(baseline_payload) - len(payload) >= MIN_PAYLOAD_SAVING and len(payload) < len(best_payload):
            best_payload = payload; best = ("lane", width, transformed, codec, payload)
    for delimiter in _delimiter_rank(raw):
        transformed = delimiter_forward(raw, delimiter)
        if delimiter_inverse(transformed, len(raw)) != raw:
            raise RuntimeError("Geometry overlay delimiter inverse failed")
        codec, payload = _compress_transformed(transformed)
        if len(baseline_payload) - len(payload) >= MIN_PAYLOAD_SAVING and len(payload) < len(best_payload):
            best_payload = payload; best = ("delimiter", delimiter, transformed, codec, payload)
    if best is None:
        return record, None, stats

    kind, param, physical, codec, payload = best
    # PH.usize is the post-codec/pre-inverse byte count. CRC/SHA remain bound to original v0.29 record bytes.
    transformed_record = (codec, len(physical), payload, binascii.crc32(raw) & 0xFFFFFFFF, H(raw))
    descriptor = [kind, int(param), len(raw)]
    stats.update({"selected": kind, "param": int(param), "payload_saving_bytes": len(baseline_payload) - len(payload),
                  "candidate_payload_bytes": len(payload), "physical_transform_bytes": len(physical)})
    return transformed_record, descriptor, stats


def _write_overlay(base_meta: dict, records: list[tuple[int, int, bytes, int, bytes]], transforms: list[list | None], out: Path) -> dict:
    leaves = [H(record[2]) for record in records]
    merkle = _merkle_root(leaves)
    offsets: list[int] = []
    cursor = 0
    for record in records:
        offsets.append(cursor); cursor += PH.size + len(record[2])
    meta = dict(base_meta)
    base_engine = meta.get("engine")
    meta.update({
        "engine": "EntropyGraph-II-v029-GeometryOverlay-v1",
        "overlay_base_engine": base_engine,
        "record_rel_offsets": offsets,
        "record_leaf_sha256": leaves,
        "physical_geometry": transforms,
        "max_geometry_overlay_record": MAX_OVERLAY_RECORD,
        "max_geometry_member_read_amplification": MAX_MEMBER_READ_AMP,
        "geometry_lane_widths": list(LANE_WIDTHS),
        "max_geometry_delimiter_candidates": MAX_DELIMITER_CANDIDATES,
        "max_geometry_delimiter_segments": MAX_DELIMITER_SEGMENTS,
        "max_geometry_delimiter_cell_scans": MAX_DELIMITER_CELL_SCANS,
    })
    meta_raw = msgpack.packb(meta, use_bin_type=True); meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha)); stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))
    return {"meta_raw_bytes": len(meta_raw), "meta_comp_bytes": len(meta_comp), "records": len(records)}


def _open_overlay(path: Path) -> tuple[object, dict, int, list[int]]:
    stream = path.open("rb")
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short Geometry overlay header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid Geometry overlay declaration")
        if max_decode > MAX_DECODE_UNIT or max_memory > MAX_DECODER_MEMORY:
            raise RuntimeError("Geometry overlay resource declaration exceeds policy")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short Geometry overlay metadata")
        raw = zd(comp, mus)
        if len(raw) != mus or H(raw) != meta_sha:
            raise RuntimeError("Geometry overlay metadata authentication")
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        leaves = meta.get("record_leaf_sha256"); offsets = meta.get("record_rel_offsets")
        transforms = meta.get("physical_geometry")
        if meta.get("engine") != "EntropyGraph-II-v029-GeometryOverlay-v1":
            raise RuntimeError("unsupported Geometry overlay engine")
        if not isinstance(leaves, list) or not isinstance(offsets, list) or not isinstance(transforms, list):
            raise RuntimeError("Geometry overlay record table shape")
        if len(leaves) != count or len(offsets) != count or len(transforms) != count:
            raise RuntimeError("Geometry overlay record-count mismatch")
        if _merkle_root(list(leaves)) != merkle:
            raise RuntimeError("Geometry overlay Merkle mismatch")
        if offsets and (offsets[0] != 0 or any(not isinstance(v, int) or v < 0 for v in offsets)):
            raise RuntimeError("Geometry overlay offsets malformed")
        if any(offsets[i] >= offsets[i + 1] for i in range(len(offsets) - 1)):
            raise RuntimeError("Geometry overlay offsets not strictly increasing")
        return stream, meta, HDR.size + mcs, list(offsets)
    except Exception:
        stream.close(); raise


def _decode_overlay_records(path: Path) -> tuple[dict, list[bytes]]:
    stream, meta, record_start, offsets = _open_overlay(path)
    originals: list[bytes] = []
    try:
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short Geometry overlay physical header")
            codec, usize, csize, crc, original_sha = PH.unpack(header)
            if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
                raise RuntimeError("Geometry overlay physical resource bound")
            payload = stream.read(csize)
            if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
                raise RuntimeError("Geometry overlay payload authentication")
            if codec == CODEC_RAW:
                physical = payload
            elif codec == CODEC_ZSTD:
                physical = zd(payload, usize)
            elif codec == CODEC_PREFLATE:
                physical = A5.V028._preflate_unpack(payload, usize)
            else:
                raise RuntimeError("unknown Geometry overlay physical codec")
            if len(physical) != usize:
                raise RuntimeError("Geometry overlay physical size mismatch")
            transform = meta["physical_geometry"][record_id]
            if transform is None:
                original = physical
            elif isinstance(transform, list) and len(transform) == 3 and transform[0] == "lane":
                original = lane_inverse(physical, int(transform[1]), int(transform[2]))
            elif isinstance(transform, list) and len(transform) == 3 and transform[0] == "delimiter":
                original = delimiter_inverse(physical, int(transform[2]))
            else:
                raise RuntimeError("malformed Geometry overlay transform descriptor")
            if (binascii.crc32(original) & 0xFFFFFFFF) != crc or H(original) != original_sha:
                raise RuntimeError("Geometry overlay inverse did not reproduce accepted-v0.29 record")
            originals.append(original)
    finally:
        stream.close()
    return meta, originals


def _write_attempt5_verification_view(meta: dict, originals: list[bytes], out: Path) -> None:
    records = []
    for raw in originals:
        codec, payload = A5._compress_record(raw, 19)
        records.append((codec, len(raw), payload, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
    leaves = [H(record[2]) for record in records]
    offsets: list[int] = []; cursor = 0
    for record in records:
        offsets.append(cursor); cursor += PH.size + len(record[2])
    clean = dict(meta)
    clean["engine"] = clean.get("overlay_base_engine")
    for key in (
        "overlay_base_engine", "physical_geometry", "max_geometry_overlay_record",
        "max_geometry_member_read_amplification", "geometry_lane_widths",
        "max_geometry_delimiter_candidates", "max_geometry_delimiter_segments",
        "max_geometry_delimiter_cell_scans",
    ):
        clean.pop(key, None)
    clean["record_rel_offsets"] = offsets; clean["record_leaf_sha256"] = leaves
    merkle = _merkle_root(leaves)
    meta_raw = msgpack.packb(clean, use_bin_type=True); meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(A5.HDR.pack(A5.MAG, len(meta_comp), len(meta_raw), len(records), A5.MAX_DECODE_UNIT,
                                 A5.MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha)); stream.write(payload)
        stream.write(meta_comp)
        stream.write(A5.FTR.pack(A5.TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return BASE.strong_verify(archive)
    meta, originals = _decode_overlay_records(archive)
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-overlay-verify-") as td:
        view = Path(td) / "attempt5-view.cmpct"
        _write_attempt5_verification_view(meta, originals, view)
        result = A5.strong_verify(view)
    if result.get("tree_sha256") != meta.get("tree_sha256"):
        raise RuntimeError("Geometry overlay logical tree mismatch")
    return {
        "ok": True,
        "tree_sha256": result["tree_sha256"],
        "engine": "EntropyGraph-II-v029-GeometryOverlay-v1",
        "records": len(originals),
        "transformed_records": sum(item is not None for item in meta["physical_geometry"]),
        "max_geometry_member_read_amplification": meta["max_geometry_member_read_amplification"],
    }


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-overlay-") as td:
        temp = Path(td); base_path = temp / "v029.cmpct"; overlay_path = temp / "overlay.cmpct"
        base_stats = BASE.build(root, base_path)
        with base_path.open("rb") as stream:
            base_magic = stream.read(8)
        if base_magic != A5.MAG:
            shutil.copyfile(base_path, out)
            return {
                "selected": "v029-fallback-non-attempt5", "archive_bytes": out.stat().st_size,
                "v029_bytes": base_path.stat().st_size, "overlay_bytes": None, "saving_vs_v029_bytes": 0,
                "transformed_records": 0, "portfolio_create_s": time.perf_counter() - started,
                "v029": base_stats,
            }

        base_meta, base_records = _read_base_records(base_path)
        users = _record_member_lengths(base_meta, len(base_records))
        records = []; transforms = []; auditions = []
        for record_id, record in enumerate(base_records):
            chosen, transform, stats = _audition_record(record_id, record, users[record_id])
            records.append(chosen); transforms.append(transform); auditions.append(stats)
        write_stats = _write_overlay(base_meta, records, transforms, overlay_path)
        overlay_verify = strong_verify(overlay_path)
        if not overlay_verify.get("ok") or overlay_verify.get("tree_sha256") != treehash(root):
            raise RuntimeError("Geometry overlay failed exact logical verification before selection")

        base_bytes = base_path.stat().st_size; overlay_bytes = overlay_path.stat().st_size
        if overlay_bytes < base_bytes:
            shutil.copyfile(overlay_path, out); selected = "geometry-overlay"
        else:
            shutil.copyfile(base_path, out); selected = "v029-fallback"
        transformed = [row for row in auditions if row["selected"] != "none"]
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v029_bytes": base_bytes,
            "overlay_bytes": overlay_bytes,
            "saving_vs_v029_bytes": base_bytes - out.stat().st_size,
            "raw_overlay_delta_vs_v029_bytes": overlay_bytes - base_bytes,
            "transformed_records": len(transformed),
            "lane_records": sum(row["selected"] == "lane" for row in transformed),
            "delimiter_records": sum(row["selected"] == "delimiter" for row in transformed),
            "transform_payload_saving_bytes": sum(row["payload_saving_bytes"] for row in transformed),
            "max_selected_member_read_amplification": max((row["max_member_read_amplification"] for row in transformed), default=0.0),
            "overlay_meta_raw_bytes": write_stats["meta_raw_bytes"],
            "overlay_meta_comp_bytes": write_stats["meta_comp_bytes"],
            "portfolio_create_s": time.perf_counter() - started,
            "tree_sha256": treehash(root),
            "auditions": auditions,
            "v029": base_stats,
        }


def _safe_relpath(rel: str) -> PurePosixPath:
    # Kept for the future native/streaming reader contract; the oracle delegates logical extraction to A5.
    if not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe Geometry overlay path")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe Geometry overlay path")
    return parsed


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 Geometry overlay research oracle")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack": print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    else: print(json.dumps(strong_verify(args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
