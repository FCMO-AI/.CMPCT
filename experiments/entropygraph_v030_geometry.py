"""CMPCT v0.30 research seed — Geometry Compiler.

Geometry extends the Lattice hypothesis from fixed byte lanes to a bounded, byte-only transform portfolio.
The writer may expose either fixed-width lanes or recurrent delimiter geometry *before* ordinary Zstandard
compression, but every choice is measured on the actual bytes and a complete accepted-v0.29 archive remains
the workload-level fallback.

The delimiter transform is intentionally semantic-blind.  Candidate separator bytes are discovered from
regular spacing in the byte stream, not from extensions, MIME types, JSON/log parsers, or corpus identity.
For one candidate byte, the exact segment lengths are stored and segment positions are transposed column-
major.  The inverse therefore reconstructs the original bytes including every separator exactly.

Footnote: CMPNX13 is research-only.  Canonical r24 does not change.  Promotion would still require the
normal independent conformance, malformed-input, native-reader, recovery, portability, timing and direct-
base release gates.  The point of this module is to prove or kill the representation mechanism first.
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
import statistics
import struct
import tempfile
import time

import msgpack

from experiments import entropygraph_v030_lattice as L

H = L.H
zc = L.zc
zd = L.zd
PH = L.PH
BASE = L.BASE
CODEC_RAW = L.CODEC_RAW
CODEC_ZSTD = L.CODEC_ZSTD
MAX_CHUNK = L.MAX_CHUNK
MAX_DECODE_UNIT = L.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = L.MAX_DECODER_MEMORY

MAG = b"CMPNX13\0"
TAIL = b"CMN13T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")

LANE_WIDTHS = (2, 4, 8, 16)
MIN_NODE_BYTES = 16 * 1024
MIN_PAYLOAD_SAVING = 64
MAX_DELIMITER_CANDIDATES = 4
MIN_DELIMITER_OCCURRENCES = 64
MAX_DELIMITER_SEGMENTS = 65_536
MAX_DELIMITER_REGULARITY = 0.50


def treehash(root: Path) -> str:
    return L.treehash(root)


def _put_varint(out: bytearray, value: int) -> None:
    if value < 0:
        raise ValueError("negative Geometry varint")
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
            raise RuntimeError("short Geometry varint")
        byte = buf[pos]; pos += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, pos
        shift += 7
    raise RuntimeError("overlong Geometry varint")


def _delimiter_rank(raw: bytes) -> list[int]:
    """Return at most four separator bytes whose gap pattern is unusually regular.

    Footnote: one pass records positions for all byte values, so candidate discovery is O(n), not
    256 independent scans.  The score penalizes gap variance and tiny sample counts; compression itself
    still makes the final admission decision, so this heuristic can only nominate work, never force it.
    """
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
            gaps.append(current - previous - 1)
            previous = current
        gaps.append(len(raw) - previous - 1)
        mean = sum(gaps) / len(gaps)
        variance = sum((gap - mean) ** 2 for gap in gaps) / len(gaps)
        score = math.sqrt(variance) / (mean + 1.0) + 8.0 / math.sqrt(count)
        if score <= MAX_DELIMITER_REGULARITY:
            ranked.append((score, byte))
    ranked.sort()
    return [byte for _, byte in ranked[:MAX_DELIMITER_CANDIDATES]]


def delimiter_forward(raw: bytes, delimiter: int) -> bytes:
    if not 0 <= delimiter <= 255:
        raise ValueError("invalid Geometry delimiter")
    parts = raw.split(bytes((delimiter,)))
    if len(parts) > MAX_DELIMITER_SEGMENTS:
        raise ValueError("Geometry delimiter segment cap exceeded")
    out = bytearray(b"DGT1")
    out.append(delimiter)
    _put_varint(out, len(parts))
    for part in parts:
        _put_varint(out, len(part))
    max_length = max(map(len, parts), default=0)
    for column in range(max_length):
        for part in parts:
            if column < len(part):
                out.append(part[column])
    return bytes(out)


def delimiter_inverse(encoded: bytes, logical_size: int) -> bytes:
    """Reverse one bounded delimiter transform and reject resource/shape inconsistencies first."""
    if not encoded.startswith(b"DGT1") or len(encoded) < 6:
        raise RuntimeError("invalid Geometry delimiter magic")
    delimiter = encoded[4]
    count, pos = _get_varint(encoded, 5)
    if count < 1 or count > MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry delimiter segment count out of bounds")
    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = _get_varint(encoded, pos)
        if length > MAX_CHUNK or logical_members + length > MAX_CHUNK:
            raise RuntimeError("Geometry delimiter length budget exceeded")
        lengths.append(length)
        logical_members += length
    if logical_members + count - 1 != logical_size or logical_size > MAX_CHUNK:
        raise RuntimeError("Geometry delimiter logical-size mismatch")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry delimiter body-size mismatch")
    rows = [bytearray(length) for length in lengths]
    cursor = 0
    for column in range(max(lengths, default=0)):
        for index, length in enumerate(lengths):
            if column < length:
                if cursor >= len(body):
                    raise RuntimeError("short Geometry delimiter body")
                rows[index][column] = body[cursor]
                cursor += 1
    if cursor != len(body):
        raise RuntimeError("trailing Geometry delimiter body")
    return bytes((delimiter,)).join(bytes(row) for row in rows)


def _compress_physical(raw: bytes) -> tuple[int, bytes]:
    compressed = zc(raw, 19)
    return (CODEC_ZSTD, compressed) if len(compressed) < len(raw) else (CODEC_RAW, raw)


def _encode_node(raw: bytes) -> dict:
    base_codec, base_payload = _compress_physical(raw)
    best = {
        "kind": "direct", "param": 0, "physical": raw, "codec": base_codec,
        "payload": base_payload, "payload_bytes": len(base_payload), "saving": 0,
    }
    if len(raw) < MIN_NODE_BYTES:
        return best

    for width in LANE_WIDTHS:
        transformed = L.lane_forward(raw, width)
        if L.lane_inverse(transformed, width, len(raw)) != raw:
            raise RuntimeError("Geometry lane inverse failed")
        codec, payload = _compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving >= MIN_PAYLOAD_SAVING and (len(payload), 0, width) < (best["payload_bytes"], 0 if best["kind"] == "lane" else 1, best["param"]):
            best = {"kind": "lane", "param": width, "physical": transformed, "codec": codec,
                    "payload": payload, "payload_bytes": len(payload), "saving": saving}

    for delimiter in _delimiter_rank(raw):
        transformed = delimiter_forward(raw, delimiter)
        # Builder-independent shape protection: the inverse is executed before a transform is allowed
        # to become benchmark evidence.  A later golden vector independently fixes the byte contract.
        if delimiter_inverse(transformed, len(raw)) != raw:
            raise RuntimeError("Geometry delimiter inverse failed")
        codec, payload = _compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving >= MIN_PAYLOAD_SAVING and (len(payload), delimiter) < (best["payload_bytes"], best["param"]):
            best = {"kind": "delimiter", "param": delimiter, "physical": transformed, "codec": codec,
                    "payload": payload, "payload_bytes": len(payload), "saving": saving}
    return best


def _merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return H(b"cmpct-geometry-merkle-empty-v1")
    level = [H(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [H(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def _build_geometry(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    nodes: list[bytes] = []
    by_hash: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    aliases = 0
    for file_id, raw in enumerate(raws):
        refs: list[int] = []
        for part in L._balanced_chunks(raw):
            digest = H(part); node_id = by_hash.get(digest)
            if node_id is not None and nodes[node_id] == part:
                aliases += 1
            else:
                node_id = len(nodes); by_hash[digest] = node_id; nodes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    records: list[tuple[int, int, bytes, int, bytes]] = []
    descriptors: list[list] = []
    lane_nodes = delimiter_nodes = payload_saving = 0
    delimiter_histogram: dict[int, int] = {}
    for raw in nodes:
        chosen = _encode_node(raw)
        physical = chosen["physical"]; payload = chosen["payload"]; codec = int(chosen["codec"])
        if len(physical) > MAX_DECODE_UNIT:
            raise RuntimeError("Geometry physical node exceeds decode ceiling")
        record_id = len(records)
        records.append((codec, len(physical), payload, binascii.crc32(physical) & 0xFFFFFFFF, H(physical)))
        kind = chosen["kind"]
        if kind == "lane":
            descriptors.append(["lane", record_id, int(chosen["param"]), len(raw), H(raw)]); lane_nodes += 1
        elif kind == "delimiter":
            descriptors.append(["delimiter", record_id, len(raw), H(raw)]); delimiter_nodes += 1
            delimiter = int(chosen["param"]); delimiter_histogram[delimiter] = delimiter_histogram.get(delimiter, 0) + 1
        else:
            descriptors.append(["direct", record_id, len(raw), H(raw)])
        payload_saving += int(chosen["saving"])

    file_desc = {rel: [file_nodes[file_id], len(raws[file_id]), H(raws[file_id])]
                 for file_id, rel in enumerate(rels)}
    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = _merkle_root(leaves)
    offsets: list[int] = []; cursor = 0
    for _, _, payload, _, _ in records:
        offsets.append(cursor); cursor += PH.size + len(payload)
    meta = {
        "v": 1, "engine": "Geometry-Compiler-v1", "files": file_desc, "nodes": descriptors,
        "record_rel_offsets": offsets, "record_leaf_sha256": leaves, "tree_sha256": treehash(root),
        "max_chunk": MAX_CHUNK, "max_decode_unit": MAX_DECODE_UNIT, "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 0, "max_read_amplification": 1.0, "lane_widths": list(LANE_WIDTHS),
        "max_delimiter_candidates": MAX_DELIMITER_CANDIDATES, "max_delimiter_segments": MAX_DELIMITER_SEGMENTS,
        "max_delimiter_regularity": MAX_DELIMITER_REGULARITY,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True); meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha)); stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))
    return {
        "create_s": time.perf_counter() - started, "graph_bytes": out.stat().st_size, "files": len(files),
        "unique_nodes": len(nodes), "exact_chunk_aliases": aliases, "lane_nodes": lane_nodes,
        "delimiter_nodes": delimiter_nodes, "transform_payload_saving_bytes": payload_saving,
        "delimiter_histogram": {str(key): value for key, value in sorted(delimiter_histogram.items())},
        "max_read_amplification": 1.0, "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-geometry-v030-") as td:
        temp = Path(td); base_path = temp / "v029.cmpct"; geometry_path = temp / "geometry.cmpct"
        base_stats = BASE.build(root, base_path); geometry_stats = _build_geometry(root, geometry_path)
        if geometry_path.stat().st_size < base_path.stat().st_size:
            shutil.copyfile(geometry_path, out); selected = "geometry"
        else:
            shutil.copyfile(base_path, out); selected = "v029-fallback"
        base_bytes = base_path.stat().st_size; candidate_bytes = out.stat().st_size
        return {"selected": selected, "archive_bytes": candidate_bytes, "v029_bytes": base_bytes,
                "geometry_graph_bytes": geometry_path.stat().st_size,
                "saving_vs_v029_bytes": base_bytes - candidate_bytes,
                "smaller_than_v029_pct": (base_bytes - candidate_bytes) / max(1, base_bytes) * 100.0,
                "portfolio_create_s": time.perf_counter() - started, "v029": base_stats, "geometry": geometry_stats}


def _decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                 expected_count: int | None = None) -> tuple[dict, list[int]]:
    if raw_size > MAX_DECODE_UNIT:
        raise RuntimeError("Geometry metadata exceeds decode ceiling")
    raw = zd(comp, raw_size)
    if H(raw) != expected_sha:
        raise RuntimeError("Geometry metadata authentication")
    meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) != 0:
        raise RuntimeError("unsupported Geometry metadata")
    if int(meta.get("max_chunk", MAX_CHUNK + 1)) > MAX_CHUNK:
        raise RuntimeError("Geometry chunk ceiling exceeds policy")
    if int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1)) > MAX_DECODE_UNIT:
        raise RuntimeError("Geometry decode ceiling exceeds policy")
    if int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1)) > MAX_DECODER_MEMORY:
        raise RuntimeError("Geometry memory ceiling exceeds policy")
    if int(meta.get("max_delimiter_candidates", MAX_DELIMITER_CANDIDATES + 1)) > MAX_DELIMITER_CANDIDATES:
        raise RuntimeError("Geometry delimiter candidate budget exceeds policy")
    if int(meta.get("max_delimiter_segments", MAX_DELIMITER_SEGMENTS + 1)) > MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry delimiter segment budget exceeds policy")
    leaves = list(meta.get("record_leaf_sha256", [])); offsets = [int(x) for x in meta.get("record_rel_offsets", [])]
    if expected_count is not None and len(leaves) != expected_count:
        raise RuntimeError("Geometry record-count mismatch")
    if len(offsets) != len(leaves) or _merkle_root(leaves) != expected_merkle:
        raise RuntimeError("Geometry record table / Merkle mismatch")
    if offsets != sorted(offsets) or any(value < 0 for value in offsets):
        raise RuntimeError("Geometry record offsets are not monotonic")
    return meta, offsets


def _open(path: Path):
    stream = path.open("rb"); primary_error: Exception | None = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size: raise RuntimeError("short Geometry header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid Geometry primary declaration")
        comp = stream.read(mcs)
        if len(comp) != mcs: raise RuntimeError("short Geometry primary metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle, count)
        if int(meta["max_decode_unit"]) != max_decode or int(meta["max_decoder_memory"]) != max_memory:
            raise RuntimeError("Geometry header/meta resource mismatch")
        return stream, meta, HDR.size + mcs, offsets
    except Exception as exc:
        primary_error = exc
    try:
        stream.seek(-FTR.size, os.SEEK_END); footer_offset = stream.tell(); footer = stream.read(FTR.size)
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid Geometry tail declaration")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size: raise RuntimeError("Geometry tail metadata offset")
        stream.seek(meta_offset); comp = stream.read(mcs)
        if len(comp) != mcs: raise RuntimeError("short Geometry tail metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle)
        stream.seek(0); header = stream.read(HDR.size)
        if len(header) != HDR.size: raise RuntimeError("cannot recover Geometry record start")
        _, primary_mcs, _, _, _, _, _, _ = HDR.unpack(header)
        if primary_mcs > MAX_DECODE_UNIT: raise RuntimeError("Geometry primary declaration exceeds bound")
        return stream, meta, HDR.size + primary_mcs, offsets
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated Geometry metadata: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _materialize_files(path: Path) -> tuple[dict[str, bytes], dict]:
    stream, meta, record_start, offsets = _open(path)
    records: dict[int, bytes] = {}; node_cache: dict[int, bytes] = {}; nodes = list(meta["nodes"])
    leaves = list(meta["record_leaf_sha256"])
    def record(record_id: int) -> bytes:
        if record_id in records: return records[record_id]
        if not 0 <= record_id < len(offsets): raise RuntimeError("Geometry record id out of range")
        stream.seek(record_start + offsets[record_id]); header = stream.read(PH.size)
        if len(header) != PH.size: raise RuntimeError("short Geometry physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("Geometry physical record exceeds resource bound")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != leaves[record_id]: raise RuntimeError("Geometry payload authentication")
        raw = payload if codec == CODEC_RAW else zd(payload, usize) if codec == CODEC_ZSTD else None
        if raw is None: raise RuntimeError("unknown Geometry physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("Geometry physical integrity")
        records[record_id] = raw; return raw
    def node(node_id: int) -> bytes:
        if node_id in node_cache: return node_cache[node_id]
        if not 0 <= node_id < len(nodes): raise RuntimeError("Geometry node id out of range")
        desc = nodes[node_id]
        if not isinstance(desc, list) or not desc: raise RuntimeError("malformed Geometry node")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc; raw = record(int(record_id))
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            raw = L.lane_inverse(record(int(record_id)), int(width), int(logical_size))
        elif kind == "delimiter" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = delimiter_inverse(record(int(record_id)), int(logical_size))
        else:
            raise RuntimeError("unknown or malformed Geometry node kind")
        if len(raw) != int(logical_size) or len(raw) > MAX_CHUNK or H(raw) != expected:
            raise RuntimeError("Geometry logical node integrity")
        node_cache[node_id] = raw; return raw
    output: dict[str, bytes] = {}
    try:
        for rel, desc in meta["files"].items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3: raise RuntimeError("malformed Geometry file")
            node_ids, logical_size, expected = desc
            data = b"".join(node(int(node_id)) for node_id in node_ids)
            if len(data) != int(logical_size) or H(data) != expected: raise RuntimeError("Geometry logical file integrity")
            output[rel] = data
    finally:
        stream.close()
    return output, meta


def _safe_relpath(rel: str) -> PurePosixPath:
    if not rel or "\\" in rel or "\x00" in rel: raise RuntimeError("unsafe Geometry path syntax")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe Geometry extraction path")
    return parsed


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream: magic = stream.read(8)
    if magic != MAG:
        BASE.extract(archive, dst); return
    files, _ = _materialize_files(archive); shutil.rmtree(dst, ignore_errors=True); dst.mkdir(parents=True)
    for rel, data in files.items():
        safe = _safe_relpath(rel); target = dst.joinpath(*safe.parts); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream: magic = stream.read(8)
    if magic != MAG: return BASE.strong_verify(archive)
    files, meta = _materialize_files(archive); tree = hashlib.sha256()
    for rel in sorted(files):
        rb = rel.encode(); data = files[rel]; tree.update(len(rb).to_bytes(4, "little")); tree.update(rb)
        tree.update(len(data).to_bytes(8, "little")); tree.update(data)
    got = tree.hexdigest()
    if got != meta.get("tree_sha256"): raise RuntimeError("Geometry tree identity mismatch")
    return {"ok": True, "files": len(files), "tree_sha256": got, "engine": meta.get("engine")}


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT Geometry Compiler v0.30 research seed")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack": print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract": extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    else: print(json.dumps(strong_verify(args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
