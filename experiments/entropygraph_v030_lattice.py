"""CMPCT v0.30 research seed — Lattice lane-transform portfolio.

Lattice deliberately starts as a *parallel representation*, not a mutation of accepted Mosaic attempt #5.
It builds a simple independently decodable direct graph whose nodes may use a measured reversible byte-lane
transform before ordinary Zstandard compression, then selects the smaller complete artifact against the
accepted v0.29 release engine. This keeps the first experiment causally sharp: any byte win comes from
layout transformation / chunk policy, while every losing workload preserves v0.29 byte-for-byte.

Footnote: lane selection is content-driven. File extensions never choose a transform. The writer auditions
bounded widths and keeps one only when the compressed physical payload wins by a frozen minimum margin.
Canonical revision-24 grammar is untouched; CMPNX12 is research-only until the usual conformance, native,
hostile-input, recovery and portability gates are earned.
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

from experiments import entropygraph_v029_release as BASE

H = BASE.H
zc = BASE.zc
zd = BASE.zd
PH = BASE.PH
CODEC_RAW = 0
CODEC_ZSTD = 1
MAX_CHUNK = int(BASE.MAX_CHUNK)
MAX_DECODE_UNIT = int(BASE.MAX_DECODE_UNIT)
MAX_DECODER_MEMORY = int(BASE.MAX_DECODER_MEMORY)
MAX_READ_AMP = float(BASE.MAX_READ_AMP)

MAG = b"CMPNX12\0"
TAIL = b"CMN12T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")

LANE_WIDTHS = (2, 4, 8, 16)
LANE_MIN_BYTES = 16 * 1024
MIN_LANE_PAYLOAD_SAVING = 64


def treehash(root: Path) -> str:
    return BASE.accepted.BASE.treehash(root)


def _merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return H(b"cmpct-lattice-merkle-empty-v1")
    level = [H(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [H(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def lane_forward(raw: bytes, width: int) -> bytes:
    """Transpose complete fixed-width byte lanes and preserve a short tail verbatim.

    Footnote: the transform never interprets numeric types. ``width`` is just a reversible byte geometry,
    which keeps the primitive useful for arbitrary files and prevents extension/type folklore from entering
    the reader contract.
    """
    if width not in LANE_WIDTHS:
        raise ValueError("unsupported lattice lane width")
    full = len(raw) - (len(raw) % width)
    body = raw[:full]
    tail = raw[full:]
    return b"".join(body[lane::width] for lane in range(width)) + tail


def lane_inverse(stored: bytes, width: int, logical_size: int) -> bytes:
    if width not in LANE_WIDTHS or logical_size < 0 or len(stored) != logical_size:
        raise ValueError("invalid lattice lane descriptor")
    full = logical_size - (logical_size % width)
    rows = full // width
    body = stored[:full]
    tail = stored[full:]
    out = bytearray(full)
    for lane in range(width):
        start = lane * rows
        end = start + rows
        out[lane:full:width] = body[start:end]
    out.extend(tail)
    return bytes(out)


def _balanced_chunks(raw: bytes) -> list[bytes]:
    """Split a file into <=512 KiB pieces without creating an avoidably tiny final fragment.

    The inherited research graph uses CDC because resemblance stability is its mission. Lattice is an
    independent direct representation, so it instead minimizes reset/metadata fragmentation while keeping
    the same maximum node size. Complete-artifact fallback decides which model wins for the real bytes.
    """
    if len(raw) <= MAX_CHUNK:
        return [raw]
    count = math.ceil(len(raw) / MAX_CHUNK)
    base, extra = divmod(len(raw), count)
    chunks: list[bytes] = []
    offset = 0
    for index in range(count):
        length = base + (1 if index < extra else 0)
        chunks.append(raw[offset: offset + length])
        offset += length
    if offset != len(raw) or any(len(chunk) > MAX_CHUNK for chunk in chunks):
        raise RuntimeError("balanced lattice chunking violated its hard ceiling")
    return chunks


def _compress_physical(raw: bytes) -> tuple[int, bytes]:
    compressed = zc(raw, 19)
    if len(compressed) < len(raw):
        return CODEC_ZSTD, compressed
    return CODEC_RAW, raw


def _encode_node(raw: bytes) -> dict:
    base_codec, base_payload = _compress_physical(raw)
    best = {
        "kind": "direct", "width": 0, "physical": raw, "codec": base_codec,
        "payload": base_payload, "payload_bytes": len(base_payload),
        "baseline_payload_bytes": len(base_payload), "payload_saving": 0,
    }
    if len(raw) < LANE_MIN_BYTES:
        return best

    for width in LANE_WIDTHS:
        transformed = lane_forward(raw, width)
        # Independent inverse checking prevents a matching writer/reader bug from being mistaken for a
        # compression win during the very first mechanism experiment.
        if lane_inverse(transformed, width, len(raw)) != raw:
            raise RuntimeError("lattice lane transform failed independent inverse check")
        codec, payload = _compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving < MIN_LANE_PAYLOAD_SAVING:
            continue
        metric = (len(payload), width)
        incumbent = (best["payload_bytes"], best["width"] or 1 << 30)
        if metric < incumbent:
            best = {
                "kind": "lane", "width": width, "physical": transformed, "codec": codec,
                "payload": payload, "payload_bytes": len(payload),
                "baseline_payload_bytes": len(base_payload), "payload_saving": saving,
            }
    return best


def _build_lattice(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    nodes: list[bytes] = []
    node_by_hash: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    aliases = 0
    for file_id, raw in enumerate(raws):
        refs: list[int] = []
        for part in _balanced_chunks(raw):
            digest = H(part)
            node_id = node_by_hash.get(digest)
            if node_id is not None and nodes[node_id] == part:
                aliases += 1
            else:
                node_id = len(nodes)
                node_by_hash[digest] = node_id
                nodes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    records: list[tuple[int, int, bytes, int, bytes]] = []
    node_desc: list[list] = []
    lane_nodes = 0
    lane_payload_saving = 0
    width_counts = {width: 0 for width in LANE_WIDTHS}

    for raw in nodes:
        chosen = _encode_node(raw)
        physical = chosen["physical"]
        payload = chosen["payload"]
        codec = int(chosen["codec"])
        if len(physical) > MAX_DECODE_UNIT:
            raise RuntimeError("lattice physical node exceeds decode ceiling")
        record_id = len(records)
        records.append((codec, len(physical), payload, binascii.crc32(physical) & 0xFFFFFFFF, H(physical)))
        if chosen["kind"] == "lane":
            width = int(chosen["width"])
            node_desc.append(["lane", record_id, width, len(raw), H(raw)])
            lane_nodes += 1
            width_counts[width] += 1
            lane_payload_saving += int(chosen["payload_saving"])
        else:
            node_desc.append(["direct", record_id, len(raw), H(raw)])

    file_desc = {
        rel: [file_nodes[file_id], len(raws[file_id]), H(raws[file_id])]
        for file_id, rel in enumerate(rels)
    }
    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = _merkle_root(leaves)
    offsets: list[int] = []
    cursor = 0
    for _, _, payload, _, _ in records:
        offsets.append(cursor)
        cursor += PH.size + len(payload)

    meta = {
        "v": 1, "engine": "Lattice-Lane-Transform-v1", "files": file_desc, "nodes": node_desc,
        "record_rel_offsets": offsets, "record_leaf_sha256": leaves, "tree_sha256": treehash(root),
        "max_chunk": MAX_CHUNK, "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY, "max_dependency_depth": 0,
        "max_read_amplification": 1.0, "lane_widths": list(LANE_WIDTHS),
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    return {
        "create_s": time.perf_counter() - started, "graph_bytes": out.stat().st_size,
        "files": len(files), "unique_nodes": len(nodes), "exact_chunk_aliases": aliases,
        "lane_nodes": lane_nodes, "lane_payload_saving_bytes": lane_payload_saving,
        "lane_width_counts": width_counts, "max_read_amplification": 1.0,
        "max_decode_unit": MAX_DECODE_UNIT, "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    """Tournament complete Lattice bytes against the accepted v0.29 release artifact."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-lattice-v030-") as td:
        temp = Path(td)
        base_path = temp / "v029.cmpct"
        lattice_path = temp / "lattice.cmpct"
        base_stats = BASE.build(root, base_path)
        lattice_stats = _build_lattice(root, lattice_path)
        if lattice_path.stat().st_size < base_path.stat().st_size:
            shutil.copyfile(lattice_path, out)
            selected = "lattice"
        else:
            shutil.copyfile(base_path, out)
            selected = "v029-fallback"
        base_bytes = base_path.stat().st_size
        candidate_bytes = out.stat().st_size
        return {
            "selected": selected, "archive_bytes": candidate_bytes, "v029_bytes": base_bytes,
            "lattice_graph_bytes": lattice_path.stat().st_size,
            "saving_vs_v029_bytes": base_bytes - candidate_bytes,
            "smaller_than_v029_pct": (base_bytes - candidate_bytes) / max(1, base_bytes) * 100.0,
            "portfolio_create_s": time.perf_counter() - started, "v029": base_stats, "lattice": lattice_stats,
        }


def _decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                 expected_count: int | None = None, declared_decode: int | None = None,
                 declared_memory: int | None = None) -> tuple[dict, list[int]]:
    if raw_size > MAX_DECODE_UNIT:
        raise RuntimeError("lattice metadata exceeds decode ceiling")
    raw = zd(comp, raw_size)
    if H(raw) != expected_sha:
        raise RuntimeError("lattice metadata authentication")
    meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) != 0:
        raise RuntimeError("unsupported lattice metadata")
    if int(meta.get("max_chunk", MAX_CHUNK + 1)) > MAX_CHUNK:
        raise RuntimeError("lattice chunk ceiling exceeds policy")
    meta_decode = int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1))
    meta_memory = int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1))
    if meta_decode > MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
        raise RuntimeError("lattice decode ceiling exceeds policy")
    if meta_memory > MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
        raise RuntimeError("lattice memory ceiling exceeds policy")
    leaves = list(meta.get("record_leaf_sha256", []))
    offsets = [int(value) for value in meta.get("record_rel_offsets", [])]
    if expected_count is not None and len(leaves) != expected_count:
        raise RuntimeError("lattice record-count mismatch")
    if len(offsets) != len(leaves) or _merkle_root(leaves) != expected_merkle:
        raise RuntimeError("lattice record table / Merkle mismatch")
    if offsets != sorted(offsets) or any(value < 0 for value in offsets):
        raise RuntimeError("lattice record offsets are not monotonic")
    return meta, offsets


def _open(path: Path):
    stream = path.open("rb")
    primary_error: Exception | None = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short lattice header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG:
            raise RuntimeError("not lattice research archive")
        if mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("lattice primary metadata length exceeds bound")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short lattice primary metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle, count, max_decode, max_memory)
        return stream, meta, HDR.size + mcs, offsets
    except Exception as exc:
        primary_error = exc

    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short lattice footer")
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid lattice tail declaration")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("lattice tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short lattice tail metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle)
        # Tail metadata authenticates the object table; the primary header still supplies the physical
        # record start. A corrupt declaration can therefore make recovery fail closed, but never redirect
        # a record read outside the archive's bounded authenticated payload table.
        stream.seek(0)
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("cannot recover lattice record start")
        _, primary_mcs, _, _, _, _, _, _ = HDR.unpack(header)
        if primary_mcs > MAX_DECODE_UNIT:
            raise RuntimeError("lattice primary metadata declaration exceeds recovery bound")
        return stream, meta, HDR.size + primary_mcs, offsets
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated lattice metadata: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _materialize_files(path: Path) -> tuple[dict[str, bytes], dict]:
    stream, meta, record_start, offsets = _open(path)
    record_cache: dict[int, bytes] = {}
    node_cache: dict[int, bytes] = {}
    nodes = list(meta["nodes"])
    leaves = list(meta["record_leaf_sha256"])

    def record(record_id: int) -> bytes:
        if record_id in record_cache:
            return record_cache[record_id]
        if not 0 <= record_id < len(offsets):
            raise RuntimeError("lattice record id out of range")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short lattice physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("lattice physical record exceeds resource bound")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != leaves[record_id]:
            raise RuntimeError("lattice physical payload authentication")
        if codec == CODEC_RAW:
            raw = payload
        elif codec == CODEC_ZSTD:
            raw = zd(payload, usize)
        else:
            raise RuntimeError("unknown lattice physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("lattice physical record integrity")
        record_cache[record_id] = raw
        return raw

    def node(node_id: int) -> bytes:
        if node_id in node_cache:
            return node_cache[node_id]
        if not 0 <= node_id < len(nodes):
            raise RuntimeError("lattice node id out of range")
        desc = nodes[node_id]
        if not isinstance(desc, list) or not desc:
            raise RuntimeError("malformed lattice node descriptor")
        kind = desc[0]
        if kind == "direct" and len(desc) == 4:
            _, record_id, logical_size, expected = desc
            raw = record(int(record_id))
            if len(raw) != int(logical_size):
                raise RuntimeError("lattice direct logical size mismatch")
        elif kind == "lane" and len(desc) == 5:
            _, record_id, width, logical_size, expected = desc
            physical = record(int(record_id))
            raw = lane_inverse(physical, int(width), int(logical_size))
        else:
            raise RuntimeError("unknown or malformed lattice node kind")
        if len(raw) > MAX_CHUNK or H(raw) != expected:
            raise RuntimeError("lattice logical node integrity")
        node_cache[node_id] = raw
        return raw

    output: dict[str, bytes] = {}
    try:
        for rel, desc in meta["files"].items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
                raise RuntimeError("malformed lattice file descriptor")
            node_ids, logical_size, expected = desc
            if not isinstance(node_ids, list):
                raise RuntimeError("malformed lattice file node list")
            data = b"".join(node(int(node_id)) for node_id in node_ids)
            if len(data) != int(logical_size) or H(data) != expected:
                raise RuntimeError("lattice logical file integrity")
            output[rel] = data
    finally:
        stream.close()
    return output, meta


def _safe_relpath(rel: str) -> PurePosixPath:
    """Validate one archive path lexically before extraction touches the host filesystem.

    Footnote: research grammar is not permission to borrow a security invariant. Absolute paths, empty
    path components, Windows separators and ``..`` traversal are rejected before destination joining,
    so a malformed authenticated metadata object cannot escape the extraction root.
    """
    if not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe lattice path syntax")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe lattice extraction path")
    return parsed


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        BASE.extract(archive, dst)
        return
    files, _ = _materialize_files(archive)
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    for rel, data in files.items():
        safe = _safe_relpath(rel)
        target = dst.joinpath(*safe.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return BASE.strong_verify(archive)
    files, meta = _materialize_files(archive)
    tree = hashlib.sha256()
    for rel in sorted(files):
        rb = rel.encode(); data = files[rel]
        tree.update(len(rb).to_bytes(4, "little")); tree.update(rb)
        tree.update(len(data).to_bytes(8, "little")); tree.update(data)
    got = tree.hexdigest()
    if got != meta.get("tree_sha256"):
        raise RuntimeError("lattice tree identity mismatch")
    return {"ok": True, "files": len(files), "tree_sha256": got, "engine": meta.get("engine")}


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples: list[float] = []
    for _ in range(3):
        started = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - started)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT Lattice v0.30 research seed")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("bench"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
