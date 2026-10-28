"""CMPCT multi-root mosaic full-artifact research engine.

This module deliberately remains outside canonical revision-24 grammar.  It asks the next question after
``cmpct.mosaic`` survived two primitive gates: does multi-root target reuse still win after paying real
EntropyGraph root packing, physical-record headers, metadata, Merkle authentication, redundant recovery
metadata, and conservative selective-read cost?

The integration is intentionally conservative.  It starts from EntropyGraph II's already-selected
**depth-1 single-delta targets and direct root set**.  A target may upgrade from one root to a bounded
mosaic of those same direct roots only when the complete mosaic record wins bytes and stays within the
8x per-target physical decode budget.  Root selection and packing therefore do not get silently changed
to favor the new idea.

Footnote: the outer portfolio builds the complete v0.28 candidate too and copies it byte-for-byte when
the mosaic graph is not smaller.  A research archive-size regression is therefore impossible by
selection; creation CPU remains an exported cost and must be measured before any release proposal.
"""
from __future__ import annotations

import argparse
import binascii
import importlib.util
import json
import msgpack
import os
from pathlib import Path
import shutil
import statistics
import struct
import tempfile
import time

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import (
    choose_central_bases,
    delta_decode,
    delta_encode,
    fastcdc,
    lsh_candidates,
    similarity_sketch,
)

HERE = Path(__file__).resolve().parent
V028_PATH = HERE / "entropygraph_v028.py"
MAG = b"CMPNX9\0\0"
TAIL = b"CMNX9T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
PH = struct.Struct("<BQQI32s")
MAX_MOSAIC_BASES = 4
MAX_MOSAIC_SOURCE_INDEX = 8 * 1024 * 1024
MAX_READ_AMP = 8.0
MOSAIC_METADATA_BASE = 24
MOSAIC_METADATA_PER_ROOT = 8


def _load_v028():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v028_for_mosaic", V028_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load EntropyGraph II engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V028 = _load_v028()
H = V028.H
zc = V028.zc
zd = V028.zd
CODEC_RAW = V028.CODEC_RAW
CODEC_ZSTD = V028.CODEC_ZSTD
CODEC_PREFLATE = V028.CODEC_PREFLATE
MAX_CHUNK = V028.MAX_CHUNK
MAX_DECODE_UNIT = V028.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = V028.MAX_DECODER_MEMORY
MIN_DELTA = V028.MIN_DELTA
PREFLATE_EXTS = V028.PREFLATE_EXTS


def treehash(root: Path) -> str:
    return V028.treehash(root)


def _direct_cost(raw: bytes) -> int:
    return V028._direct_cost(raw)


def _compress_record(raw: bytes, level: int = 19) -> tuple[int, bytes]:
    return V028._compress_record(raw, level)


def _pack_lookup(groups: list[list[int]], nodes: list[bytes]) -> dict[int, tuple[int, int]]:
    """Map each direct root to `(physical group id, decoded group bytes)`."""
    out: dict[int, tuple[int, int]] = {}
    for group_id, group in enumerate(groups):
        decoded = sum(len(nodes[node_id]) for node_id in group)
        for node_id in group:
            out[node_id] = (group_id, decoded)
    return out


def _target_read_amp(target_len: int, raw_delta_len: int, base_ids: list[int],
                     pack_lookup: dict[int, tuple[int, int]]) -> float:
    groups: dict[int, int] = {}
    for base_id in base_ids:
        group_id, decoded = pack_lookup[base_id]
        groups[group_id] = decoded
    return (sum(groups.values()) + raw_delta_len) / max(1, target_len)


def _build_mosaic_graph(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    preflate_files: dict[int, bytes] = {}
    normal_files: list[int] = []
    preflate_attempts = 0
    preflate_wins = 0
    for file_id, (path, raw) in enumerate(zip(files, raws)):
        packed = None
        if path.suffix.lower() in PREFLATE_EXTS and 4096 <= len(raw) <= MAX_DECODE_UNIT:
            preflate_attempts += 1
            packed = V028._preflate_pack(raw, path.suffix)
        direct = _direct_cost(raw)
        if packed is not None and PH.size + len(packed) + 24 < direct:
            preflate_files[file_id] = packed
            preflate_wins += 1
        else:
            normal_files.append(file_id)

    node_bytes: list[bytes] = []
    node_hash_to_id: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    exact_aliases = 0
    for file_id in normal_files:
        raw = raws[file_id]
        chunks = (
            fastcdc(raw, min_size=32 * 1024, avg_size=128 * 1024, max_size=MAX_CHUNK)
            if len(raw) > MAX_CHUNK
            else [type("C", (), {"offset": 0, "length": len(raw)})()]
        )
        refs = []
        for chunk in chunks:
            part = raw[chunk.offset : chunk.offset + chunk.length]
            hh = H(part)
            node_id = node_hash_to_id.get(hh)
            if node_id is not None and node_bytes[node_id] == part:
                exact_aliases += 1
            else:
                node_id = len(node_bytes)
                node_hash_to_id[hh] = node_id
                node_bytes.append(part)
            refs.append(node_id)
        file_nodes[file_id] = refs

    sketches = [similarity_sketch(raw) for raw in node_bytes]
    candidate_edges = lsh_candidates(sketches, max_bucket=48, max_candidates=8)
    direct_costs = [_direct_cost(raw) for raw in node_bytes]
    measured: list[tuple[int, int, int]] = []
    edge_payloads: dict[tuple[int, int], tuple[bytes, dict]] = {}
    per_target_edges: dict[int, list[tuple[int, int, int, int]]] = {}
    auditions = 0
    for edge in candidate_edges:
        target = node_bytes[edge.target]
        base = node_bytes[edge.base]
        if min(len(target), len(base)) < MIN_DELTA:
            continue
        auditions += 1
        result = delta_encode(base, target, block=64, max_base_index=MAX_CHUNK)
        codec, payload = _compress_record(result.payload, 12)
        delta_cost = PH.size + len(payload) + 24
        saving = direct_costs[edge.target] - delta_cost
        stats = {
            "saving": saving,
            "stored_cost": delta_cost,
            "copied": result.stats.copied_bytes,
            "literal": result.stats.literal_bytes,
            "shared_features": edge.shared_features,
        }
        edge_payloads[(edge.target, edge.base)] = (result.payload, stats)
        # Mosaic discovery keeps weak-but-real component roots that v0.28 would not independently
        # promote.  The candidate list is still bounded by the inherited LSH max_candidates=8 gate.
        if result.stats.copied_bytes >= max(4096, len(target) // 20) and saving > 0:
            per_target_edges.setdefault(edge.target, []).append(
                (edge.base, saving, result.stats.copied_bytes, edge.shared_features)
            )
        if saving >= max(128, direct_costs[edge.target] // 50) and result.stats.copied_bytes >= len(target) // 4:
            measured.append((edge.target, edge.base, saving))

    # Preserve EntropyGraph II's centrality/root decision exactly.  Mosaic is allowed to improve an
    # already-depth-1 target; it does not get to redesign root placement in this first full-artifact test.
    assignment = choose_central_bases(len(node_bytes), measured)
    delta_nodes = set(assignment)
    root_ids = [i for i in range(len(node_bytes)) if i not in delta_nodes]
    (pack_cost, pack_read_amp, pack_limit, groups), pack_trials = V028._choose_pack_plan(
        node_bytes, sketches, root_ids
    )
    pack_lookup = _pack_lookup(groups, node_bytes)

    records: list[tuple[int, int, bytes, int, bytes]] = []
    node_desc: list[list | None] = [None] * len(node_bytes)

    def add_record(codec: int, logical: bytes, payload: bytes | None = None) -> int:
        if payload is None:
            codec, payload = _compress_record(logical)
        assert payload is not None
        records.append((codec, len(logical), payload, binascii.crc32(logical) & 0xFFFFFFFF, H(logical)))
        return len(records) - 1

    for group in groups:
        raw = b"".join(node_bytes[i] for i in group)
        codec, payload = _compress_record(raw)
        record_id = add_record(codec, raw, payload)
        offset = 0
        for node_id in group:
            length = len(node_bytes[node_id])
            node_desc[node_id] = ["direct", record_id, offset, length, H(node_bytes[node_id])]
            offset += length

    single_nodes = 0
    mosaic_nodes = 0
    mosaic_savings = 0
    mosaic_read_amps: list[float] = []
    mosaic_auditions = 0
    for target, selected_base in sorted(assignment.items()):
        raw_single, single_stats = edge_payloads[(target, selected_base)]
        single_codec, single_payload = _compress_record(raw_single, 12)
        single_cost = PH.size + len(single_payload) + 24

        candidates = []
        for base_id, saving, copied, shared in per_target_edges.get(target, []):
            if base_id in pack_lookup:
                candidates.append((base_id, saving, copied, shared))
        if selected_base not in {row[0] for row in candidates}:
            candidates.append((selected_base, single_stats["saving"], single_stats["copied"], single_stats["shared_features"]))
        candidates.sort(key=lambda row: (-row[1], -row[2], -row[3], row[0]))
        candidate_ids = [row[0] for row in candidates[:MAX_MOSAIC_BASES]]

        chosen_mosaic = None
        if len(candidate_ids) >= 2 and sum(len(node_bytes[i]) for i in candidate_ids) <= MAX_MOSAIC_SOURCE_INDEX:
            mosaic_auditions += 1
            result = mosaic_delta_encode(
                [node_bytes[i] for i in candidate_ids],
                node_bytes[target],
                block=64,
                max_bases=MAX_MOSAIC_BASES,
                max_source_index=MAX_MOSAIC_SOURCE_INDEX,
                max_matches_per_key=16,
            )
            used_slots = used_base_slots(result.stats)
            used_ids = [candidate_ids[slot] for slot in used_slots]
            if len(used_ids) >= 2:
                mcodec, mpayload = _compress_record(result.payload, 12)
                mosaic_cost = PH.size + len(mpayload) + MOSAIC_METADATA_BASE + MOSAIC_METADATA_PER_ROOT * len(candidate_ids)
                target_amp = _target_read_amp(len(node_bytes[target]), len(result.payload), used_ids, pack_lookup)
                if (
                    target_amp <= MAX_READ_AMP
                    and result.stats.copied_bytes >= len(node_bytes[target]) // 3
                    and mosaic_cost + max(128, single_cost // 100) < single_cost
                ):
                    # Exact decode is the admission oracle.  The archive is never written with a mosaic
                    # edge that has only been judged by sketches or by a byte-count estimate.
                    restored = mosaic_delta_decode(
                        [node_bytes[i] for i in candidate_ids],
                        result.payload,
                        expected_size=len(node_bytes[target]),
                        max_bases=MAX_MOSAIC_BASES,
                        max_source_bytes=MAX_MOSAIC_SOURCE_INDEX,
                        max_output=MAX_CHUNK,
                    )
                    if restored != node_bytes[target]:
                        raise RuntimeError("mosaic admission reconstruction mismatch")
                    chosen_mosaic = (candidate_ids, result.payload, mcodec, mpayload, mosaic_cost, target_amp)

        if chosen_mosaic is None:
            record_id = add_record(single_codec, raw_single, single_payload)
            node_desc[target] = ["delta", selected_base, record_id, len(node_bytes[target]), H(node_bytes[target])]
            single_nodes += 1
        else:
            candidate_ids, raw_mosaic, mcodec, mpayload, mosaic_cost, target_amp = chosen_mosaic
            record_id = add_record(mcodec, raw_mosaic, mpayload)
            node_desc[target] = ["mosaic", candidate_ids, record_id, len(node_bytes[target]), H(node_bytes[target])]
            mosaic_nodes += 1
            mosaic_savings += single_cost - mosaic_cost
            mosaic_read_amps.append(target_amp)

    file_desc: dict[str, list] = {}
    for file_id, rel in enumerate(rels):
        raw = raws[file_id]
        if file_id in preflate_files:
            packed = preflate_files[file_id]
            record_id = len(records)
            records.append((CODEC_PREFLATE, len(raw), packed, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
            file_desc[rel] = ["preflate", record_id, len(raw), H(raw)]
        else:
            file_desc[rel] = ["nodes", file_nodes[file_id], len(raw), H(raw)]

    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = V028._merkle_root(leaves)
    record_rel_offsets = []
    cursor = 0
    for _, _, payload, _, _ in records:
        record_rel_offsets.append(cursor)
        cursor += PH.size + len(payload)

    meta = {
        "v": 1,
        "engine": "EntropyGraph-II-MultiRoot-Mosaic",
        "files": file_desc,
        "nodes": node_desc,
        "record_rel_offsets": record_rel_offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": treehash(root),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 1,
        "max_mosaic_bases": MAX_MOSAIC_BASES,
        "max_mosaic_source_index": MAX_MOSAIC_SOURCE_INDEX,
        "pack_limit": pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(mosaic_read_amps, default=0.0),
        "preflate_required": bool(preflate_files),
        "preflate_bridge_contract": "microsoft/preflate-rs 0.7.6 via pinned CMPCT bridge" if preflate_files else None,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, hh in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, hh))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    return {
        "create_s": time.perf_counter() - started,
        "graph_bytes": out.stat().st_size,
        "files": len(files),
        "unique_nodes": len(node_bytes),
        "exact_chunk_aliases": exact_aliases,
        "similarity_candidates": len(candidate_edges),
        "delta_auditions": auditions,
        "single_delta_nodes": single_nodes,
        "mosaic_auditions": mosaic_auditions,
        "mosaic_nodes": mosaic_nodes,
        "mosaic_estimated_record_savings": mosaic_savings,
        "adaptive_pack_limit": pack_limit,
        "pack_read_amplification": pack_read_amp,
        "max_mosaic_read_amplification": max(mosaic_read_amps, default=0.0),
        "pack_trials": pack_trials,
        "preflate_attempts": preflate_attempts,
        "preflate_wins": preflate_wins,
        "merkle_leaves": len(leaves),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    """Build the complete v0.28 portfolio and mosaic graph, then keep the smaller exact artifact."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-mosaic-full-") as td:
        v028_path = Path(td) / "v028.cmpct"
        mosaic_path = Path(td) / "mosaic.cmpct"
        v028_stats = V028.build(root, v028_path)
        mosaic_stats = _build_mosaic_graph(root, mosaic_path)
        if mosaic_path.stat().st_size < v028_path.stat().st_size:
            shutil.copyfile(mosaic_path, out)
            selected = "mosaic"
        else:
            shutil.copyfile(v028_path, out)
            selected = "v028-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "v028_bytes": v028_path.stat().st_size,
            "mosaic_graph_bytes": mosaic_path.stat().st_size,
            "smaller_than_v028_pct": (v028_path.stat().st_size - out.stat().st_size) / max(1, v028_path.stat().st_size) * 100.0,
            "portfolio_create_s": time.perf_counter() - started,
            "v028": v028_stats,
            "mosaic": mosaic_stats,
        }


def _open_mosaic(path: Path):
    stream = path.open("rb")

    def decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                    expected_count: int | None = None, declared_decode: int | None = None,
                    declared_memory: int | None = None):
        raw = zd(comp, raw_size)
        if H(raw) != expected_sha:
            raise RuntimeError("metadata authentication")
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) > 1:
            raise RuntimeError("unsupported mosaic metadata")
        if int(meta.get("max_mosaic_bases", MAX_MOSAIC_BASES + 1)) > MAX_MOSAIC_BASES:
            raise RuntimeError("mosaic base count exceeds implementation policy")
        if int(meta.get("max_mosaic_source_index", MAX_MOSAIC_SOURCE_INDEX + 1)) > MAX_MOSAIC_SOURCE_INDEX:
            raise RuntimeError("mosaic source bound exceeds implementation policy")
        meta_decode = int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1))
        meta_memory = int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1))
        if meta_decode > MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
            raise RuntimeError("archive decode ceiling exceeds implementation policy")
        if meta_memory > MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
            raise RuntimeError("archive decoder-memory ceiling exceeds implementation policy")
        leaves = list(meta.get("record_leaf_sha256", []))
        if expected_count is not None and len(leaves) != expected_count:
            raise RuntimeError("record-count mismatch")
        if V028._merkle_root(leaves) != expected_merkle:
            raise RuntimeError("Merkle root mismatch")
        offsets = list(meta.get("record_rel_offsets", []))
        if len(offsets) != len(leaves):
            raise RuntimeError("record table mismatch")
        return meta, offsets

    primary_error: Exception | None = None
    try:
        stream.seek(0)
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short mosaic header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG:
            raise RuntimeError("not mosaic research archive")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short primary metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle, count, max_decode, max_memory)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as exc:
        primary_error = exc

    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        if len(footer) != FTR.size:
            raise RuntimeError("short mosaic footer")
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL:
            raise RuntimeError("tail magic")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short tail metadata")
        meta, offsets = decode_meta(comp, mus, meta_sha, merkle)
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated mosaic metadata: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _extract_mosaic(path: Path, dst: Path) -> None:
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    stream, meta, record_start, offsets, _ = _open_mosaic(path)
    record_cache: dict[int, bytes] = {}
    node_cache: dict[int, bytes] = {}
    nodes = meta["nodes"]

    def record(record_id: int) -> bytes:
        if record_id in record_cache:
            return record_cache[record_id]
        if not 0 <= record_id < len(offsets):
            raise RuntimeError("record id out of range")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT:
            raise RuntimeError("physical record exceeds declared decode unit")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != meta["record_leaf_sha256"][record_id]:
            raise RuntimeError("physical Merkle leaf mismatch")
        if codec == CODEC_RAW:
            raw = payload
        elif codec == CODEC_ZSTD:
            raw = zd(payload, usize)
        elif codec == CODEC_PREFLATE:
            raw = V028._preflate_unpack(payload, usize)
        else:
            raise RuntimeError("unknown physical codec")
        if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("physical record integrity")
        record_cache[record_id] = raw
        return raw

    def node(node_id: int) -> bytes:
        if node_id in node_cache:
            return node_cache[node_id]
        if not 0 <= node_id < len(nodes):
            raise RuntimeError("node id out of range")
        desc = nodes[node_id]
        kind = desc[0]
        if kind == "direct":
            _, record_id, offset, length, expected = desc
            pack = record(record_id)
            if offset > len(pack) or length > len(pack) - offset:
                raise RuntimeError("direct slice bounds")
            raw = pack[offset : offset + length]
        elif kind == "delta":
            _, base_id, record_id, length, expected = desc
            if nodes[base_id][0] != "direct":
                raise RuntimeError("delta dependency depth")
            raw = delta_decode(node(base_id), record(record_id), expected_size=length, max_output=MAX_CHUNK)
        elif kind == "mosaic":
            _, base_ids, record_id, length, expected = desc
            if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= MAX_MOSAIC_BASES:
                raise RuntimeError("mosaic base list bounds")
            if len(set(base_ids)) != len(base_ids) or any(not isinstance(base_id, int) for base_id in base_ids):
                raise RuntimeError("invalid mosaic base list")
            if any(not 0 <= base_id < len(nodes) or nodes[base_id][0] != "direct" for base_id in base_ids):
                raise RuntimeError("mosaic dependency depth")
            bases = [node(base_id) for base_id in base_ids]
            raw = mosaic_delta_decode(
                bases,
                record(record_id),
                expected_size=length,
                max_bases=MAX_MOSAIC_BASES,
                max_source_bytes=MAX_MOSAIC_SOURCE_INDEX,
                max_output=MAX_CHUNK,
            )
        else:
            raise RuntimeError("unknown node description")
        if H(raw) != expected:
            raise RuntimeError("node SHA-256 mismatch")
        node_cache[node_id] = raw
        return raw

    try:
        for rel, desc in sorted(meta["files"].items()):
            if desc[0] == "preflate":
                raw = record(desc[1]); expected_size = desc[2]; expected = desc[3]
            elif desc[0] == "nodes":
                raw = b"".join(node(node_id) for node_id in desc[1]); expected_size = desc[2]; expected = desc[3]
            else:
                raise RuntimeError("unknown file description")
            if len(raw) != expected_size or H(raw) != expected:
                raise RuntimeError("file reconstruction mismatch")
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    finally:
        stream.close()


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == MAG:
        _extract_mosaic(archive, dst)
    else:
        V028.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return V028.strong_verify(archive)
    stream, meta, _, offsets, merkle = _open_mosaic(archive)
    stream.close()
    with tempfile.TemporaryDirectory(prefix="cmpct-mosaic-verify-") as td:
        dst = Path(td)
        _extract_mosaic(archive, dst)
        got = treehash(dst)
    if got != meta["tree_sha256"]:
        raise RuntimeError("logical tree root mismatch")
    return {
        "ok": True,
        "tree_sha256": got,
        "merkle_root": merkle.hex(),
        "records": len(offsets),
        "max_decode_unit": meta["max_decode_unit"],
        "max_decoder_memory": meta["max_decoder_memory"],
        "max_mosaic_bases": meta["max_mosaic_bases"],
    }


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT bounded multi-root mosaic full-artifact research engine")
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
        print(json.dumps(strong_verify(args.archive), indent=2))
    elif args.cmd == "bench":
        print(json.dumps(bench(args.source, args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
