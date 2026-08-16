"""CMPCT EntropyGraph II / Resemblance Compiler research engine.

This is deliberately not canonical revision-24 grammar.  It combines a bounded resemblance graph,
FastCDC-style stable units, measured depth-1 deltas, similarity ordering, adaptive decode-unit packing,
optional exact DEFLATE precompression through the pinned memory-safe preflate bridge, Merkle-authenticated
physical records, O(1) metadata lookup, and hard decode-size plus decoder-memory declarations.

The encoder is a *portfolio*: it also builds the inherited v0.25 EntropyGraph candidate and emits that
artifact unchanged whenever the new graph is not smaller.  Therefore a research size regression is not
papered over with a threshold; the inherited engine remains an exact fallback representation.

Footnote: portfolio selection spends extra creation CPU.  The benchmark reports that exported cost.  A
future learned/analytic cost model may skip obviously losing auditions, but prediction is never allowed
to replace final byte measurement when a candidate is admitted.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import importlib.util
import json
import msgpack
import os
from pathlib import Path
import shutil
import statistics
import struct
import subprocess
import tempfile
import time

from cmpct.resemblance import (
    choose_central_bases,
    delta_decode,
    delta_encode,
    fastcdc,
    lsh_candidates,
    similarity_order,
    similarity_sketch,
)

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "entropygraph_v025.py"
MAG = b"CMPNX8\0\0"
TAIL = b"CMNX8T\0\0"
# magic, metadata compressed/raw bytes, record count, maximum logical decode unit, decoder-memory
# ceiling, metadata SHA, Merkle root. The two ceilings are separate because a compressed transform can
# require more working memory than the logical object it eventually reconstructs.
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
PH = struct.Struct("<BQQI32s")  # codec, logical bytes, stored bytes, hot CRC32, logical SHA-256
CODEC_RAW = 0
CODEC_ZSTD = 1
CODEC_PREFLATE = 2
MAX_CHUNK = 512 * 1024
MAX_PACK = 2 * 1024 * 1024
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_DECODER_MEMORY = 96 * 1024 * 1024
MIN_DELTA = 1024
PREFLATE_EXTS = {".zip", ".jar", ".whl", ".docx", ".xlsx", ".pptx", ".png", ".pdf"}


def _load_base():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v025", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load inherited EntropyGraph engine")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
zc = BASE.zc
zd = BASE.zd
H = BASE.H


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _merkle_root(leaves: list[bytes]) -> bytes:
    """Binary Merkle root over physical payload hashes, domain separated from ordinary SHA identities."""
    if not leaves:
        return H(b"cmpct-merkle-empty-v1")
    level = [H(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [H(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def _bridge_path() -> Path | None:
    override = os.environ.get("CMPCT_PREFLATE_BRIDGE")
    if override:
        path = Path(override)
        return path if path.is_file() and os.access(path, os.X_OK) else None
    for path in (
        HERE.parent / "native" / "preflate-bridge" / "target" / "release" / "cmpct-preflate-bridge",
        Path.cwd() / "native" / "preflate-bridge" / "target" / "release" / "cmpct-preflate-bridge",
    ):
        if path.is_file() and os.access(path, os.X_OK):
            return path
    return None


def _preflate_pack(raw: bytes, suffix: str) -> bytes | None:
    bridge = _bridge_path()
    if bridge is None or len(raw) < 4096 or len(raw) > MAX_DECODE_UNIT or suffix.lower() not in PREFLATE_EXTS:
        return None
    with tempfile.TemporaryDirectory(prefix="cmpct-preflate-") as td:
        src = Path(td) / ("input" + suffix)
        dst = Path(td) / "packed.pflt"
        src.write_bytes(raw)
        proc = subprocess.run([str(bridge), "pack", str(src), str(dst)], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=90)
        if proc.returncode != 0 or not dst.is_file():
            return None
        return dst.read_bytes()


def _preflate_unpack(payload: bytes, expected_size: int) -> bytes:
    bridge = _bridge_path()
    if bridge is None:
        raise RuntimeError("archive requires the CMPCT preflate bridge")
    if expected_size > MAX_DECODE_UNIT:
        raise RuntimeError("preflate record exceeds declared decode unit")
    with tempfile.TemporaryDirectory(prefix="cmpct-preflate-") as td:
        src = Path(td) / "packed.pflt"
        dst = Path(td) / "restored.bin"
        src.write_bytes(payload)
        proc = subprocess.run([str(bridge), "unpack", str(src), str(dst)], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=90)
        if proc.returncode != 0 or not dst.is_file():
            raise RuntimeError("preflate reconstruction failed")
        out = dst.read_bytes()
    if len(out) != expected_size:
        raise RuntimeError("preflate reconstructed wrong length")
    return out


def _compress_record(raw: bytes, level: int = 19) -> tuple[int, bytes]:
    comp = zc(raw, level)
    if len(comp) + 8 < len(raw):
        return CODEC_ZSTD, comp
    return CODEC_RAW, raw


def _direct_cost(raw: bytes) -> int:
    _, payload = _compress_record(raw)
    return PH.size + len(payload)


def _pack_plan(nodes: list[bytes], sketches, root_ids: list[int], limit: int):
    order_local = similarity_order([sketches[i] for i in root_ids])
    order = [root_ids[i] for i in order_local]
    groups: list[list[int]] = []
    current: list[int] = []
    current_len = 0
    for node_id in order:
        n = len(nodes[node_id])
        if n > limit:
            if current:
                groups.append(current); current = []; current_len = 0
            groups.append([node_id])
            continue
        if current and current_len + n > limit:
            groups.append(current); current = []; current_len = 0
        current.append(node_id); current_len += n
    if current:
        groups.append(current)
    bytes_cost = 0
    decoded_weight = 0
    logical_weight = 0
    for group in groups:
        raw = b"".join(nodes[i] for i in group)
        _, payload = _compress_record(raw)
        bytes_cost += PH.size + len(payload)
        # Each independently requested member pays the containing pack decode cost. This metric makes
        # the ratio/locality trade explicit instead of treating a large solid block as free context.
        for i in group:
            decoded_weight += len(raw)
            logical_weight += max(1, len(nodes[i]))
    amplification = decoded_weight / max(1, logical_weight)
    return bytes_cost, amplification, groups


def _choose_pack_plan(nodes: list[bytes], sketches, root_ids: list[int]):
    trials = []
    for limit in (64, 128, 256, 512, 1024, 2048):
        value = limit * 1024
        cost, amp, groups = _pack_plan(nodes, sketches, root_ids, value)
        trials.append((cost, amp, value, groups))
    feasible = [row for row in trials if row[1] <= 8.0]
    chosen = min(feasible or trials, key=lambda row: (row[0], row[1], row[2]))
    baseline = next(row for row in trials if row[2] == 512 * 1024)
    # Footnote: wider context must earn a material byte win. Otherwise retain 512 KiB even if an equal
    # result happens to sort first, preventing locality churn for metadata crumbs.
    if chosen[2] > 512 * 1024 and baseline[0] - chosen[0] < max(1024, baseline[0] // 1000):
        chosen = baseline
    return chosen, [{"limit": limit, "bytes": cost, "read_amp": amp} for cost, amp, limit, _ in trials]


def _build_graph(root: Path, out: Path) -> dict:
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
            packed = _preflate_pack(raw, path.suffix)
        direct = _direct_cost(raw)
        if packed is not None and PH.size + len(packed) + 24 < direct:
            preflate_files[file_id] = packed
            preflate_wins += 1
        else:
            normal_files.append(file_id)

    # Logical files become bounded CDC nodes. Small files remain whole; large files cannot create an
    # unbounded delta/base object even if their content is pathologically boundary-resistant.
    node_bytes: list[bytes] = []
    node_hash_to_id: dict[bytes, int] = {}
    file_nodes: dict[int, list[int]] = {}
    exact_aliases = 0
    for file_id in normal_files:
        raw = raws[file_id]
        chunks = fastcdc(raw, min_size=32 * 1024, avg_size=128 * 1024, max_size=MAX_CHUNK) if len(raw) > MAX_CHUNK else [type("C", (), {"offset": 0, "length": len(raw)})()]
        refs = []
        for chunk in chunks:
            part = raw[chunk.offset:chunk.offset + chunk.length]
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
    measured: list[tuple[int, int, int]] = []
    delta_payloads: dict[tuple[int, int], tuple[bytes, dict]] = {}
    direct_costs = [_direct_cost(raw) for raw in node_bytes]
    auditions = 0
    for edge in candidate_edges:
        target = node_bytes[edge.target]
        base = node_bytes[edge.base]
        if min(len(target), len(base)) < MIN_DELTA:
            continue
        auditions += 1
        result = delta_encode(base, target, block=64, max_base_index=MAX_CHUNK)
        codec, payload = _compress_record(result.payload, 12)
        # Delta records are independent physical units; account for their header and a conservative
        # metadata allowance before calling an edge a win.
        delta_cost = PH.size + len(payload) + 24
        saving = direct_costs[edge.target] - delta_cost
        if saving >= max(128, direct_costs[edge.target] // 50) and result.stats.copied_bytes >= len(target) // 4:
            measured.append((edge.target, edge.base, saving))
            delta_payloads[(edge.target, edge.base)] = (result.payload, {
                "saving": saving,
                "copied": result.stats.copied_bytes,
                "literal": result.stats.literal_bytes,
                "shared_features": edge.shared_features,
            })

    assignment = choose_central_bases(len(node_bytes), measured)
    # If centrality selected a base for which another measured edge happened to carry better economics,
    # retain only the selected concrete edge. Bases themselves are never delta targets by construction.
    delta_nodes = set(assignment)
    root_ids = [i for i in range(len(node_bytes)) if i not in delta_nodes]
    (pack_cost, read_amp, pack_limit, groups), pack_trials = _choose_pack_plan(node_bytes, sketches, root_ids)

    records: list[tuple[int, int, bytes, int, bytes]] = []
    node_desc: list[list | None] = [None] * len(node_bytes)

    def add_record(codec: int, logical: bytes, payload: bytes | None = None) -> int:
        if payload is None:
            codec, payload = _compress_record(logical)
        assert payload is not None
        rec = (codec, len(logical), payload, binascii.crc32(logical) & 0xFFFFFFFF, H(logical))
        records.append(rec)
        return len(records) - 1

    # Similarity-ordered root packs are the physical bases. Each member keeps an O(1) slice descriptor.
    for group in groups:
        raw = b"".join(node_bytes[i] for i in group)
        record_id = add_record(*((lambda cp: (cp[0], raw, cp[1]))(_compress_record(raw))))
        offset = 0
        for node_id in group:
            length = len(node_bytes[node_id])
            node_desc[node_id] = ["direct", record_id, offset, length, H(node_bytes[node_id])]
            offset += length

    delta_savings = 0
    for target, base in sorted(assignment.items()):
        raw_delta, stats = delta_payloads[(target, base)]
        codec, payload = _compress_record(raw_delta, 12)
        record_id = add_record(codec, raw_delta, payload)
        node_desc[target] = ["delta", base, record_id, len(node_bytes[target]), H(node_bytes[target])]
        delta_savings += stats["saving"]

    file_desc: dict[str, list] = {}
    for file_id, rel in enumerate(rels):
        raw = raws[file_id]
        if file_id in preflate_files:
            packed = preflate_files[file_id]
            # Physical identity is the reconstructed file, while the Merkle leaf authenticates the
            # preflate payload itself before any decoder is invoked.
            record_id = len(records)
            records.append((CODEC_PREFLATE, len(raw), packed, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
            file_desc[rel] = ["preflate", record_id, len(raw), H(raw)]
        else:
            file_desc[rel] = ["nodes", file_nodes[file_id], len(raw), H(raw)]

    leaves = [H(payload) for _, _, payload, _, _ in records]
    merkle = _merkle_root(leaves)
    record_rel_offsets = []
    cursor = 0
    for _, _, payload, _, _ in records:
        record_rel_offsets.append(cursor)
        cursor += PH.size + len(payload)
    meta = {
        "v": 1,
        "engine": "EntropyGraph-II-Resemblance",
        "files": file_desc,
        "nodes": node_desc,
        "record_rel_offsets": record_rel_offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": treehash(root),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 1,
        "pack_limit": pack_limit,
        "pack_read_amplification": read_amp,
        "preflate_required": bool(preflate_files),
        "preflate_bridge_contract": "microsoft/preflate-rs 0.7.6 via pinned CMPCT bridge" if preflate_files else None,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    meta_comp = zc(meta_raw, 12)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT, MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, hh in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, hh))
            stream.write(payload)
        # Recovery metadata remains a real byte cost; the tail authenticates the same Merkle root.
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
        "delta_nodes": len(delta_nodes),
        "delta_estimated_savings": delta_savings,
        "adaptive_pack_limit": pack_limit,
        "pack_read_amplification": read_amp,
        "pack_trials": pack_trials,
        "preflate_attempts": preflate_attempts,
        "preflate_wins": preflate_wins,
        "merkle_leaves": len(leaves),
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
    }


def build(root: Path, out: Path) -> dict:
    """Build both inherited and new candidates and keep the smaller exact artifact."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-v028-portfolio-") as td:
        legacy = Path(td) / "legacy.cmpct"
        graph = Path(td) / "graph.cmpct"
        BASE.ROOT = root
        BASE.OUT = legacy
        legacy_stats = BASE.build()
        graph_stats = _build_graph(root, graph)
        if graph.stat().st_size < legacy.stat().st_size:
            shutil.copyfile(graph, out)
            selected = "resemblance"
        else:
            shutil.copyfile(legacy, out)
            selected = "entropygraph-v025-fallback"
        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "legacy_bytes": legacy.stat().st_size,
            "graph_bytes": graph.stat().st_size,
            "portfolio_create_s": time.perf_counter() - started,
            "legacy": legacy_stats,
            "graph": graph_stats,
        }


def _open_graph(path: Path):
    stream = path.open("rb")

    def decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                    expected_count: int | None = None, declared_decode: int | None = None,
                    declared_memory: int | None = None):
        raw = zd(comp, raw_size)
        if H(raw) != expected_sha:
            raise RuntimeError("metadata authentication")
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) > 1:
            raise RuntimeError("unsupported graph metadata")
        meta_decode = int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1))
        meta_memory = int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1))
        if meta_decode > MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
            raise RuntimeError("archive decode ceiling exceeds implementation policy")
        if meta_memory > MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
            raise RuntimeError("archive decoder-memory ceiling exceeds implementation policy")
        leaves = list(meta.get("record_leaf_sha256", []))
        if expected_count is not None and len(leaves) != expected_count:
            raise RuntimeError("record-count mismatch")
        if _merkle_root(leaves) != expected_merkle:
            raise RuntimeError("Merkle root mismatch")
        offsets = list(meta.get("record_rel_offsets", []))
        if len(offsets) != len(leaves):
            raise RuntimeError("record table mismatch")
        return meta, offsets

    # Footnote: the tail copy is an operational recovery path, not decorative redundancy. Primary
    # damage is allowed to fail closed into the authenticated footer copy, reproducing the recovery
    # invariant already learned by the inherited EntropyGraph engine.
    primary_error: Exception | None = None
    try:
        stream.seek(0)
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short EntropyGraph-II header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG:
            raise RuntimeError("not EntropyGraph-II")
        if max_decode > MAX_DECODE_UNIT:
            raise RuntimeError("archive decode ceiling exceeds implementation policy")
        if max_memory > MAX_DECODER_MEMORY:
            raise RuntimeError("archive decoder-memory ceiling exceeds implementation policy")
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
            raise RuntimeError("short EntropyGraph-II footer")
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
        # The physical record table begins at the same fixed header + compressed-metadata boundary;
        # tail recovery does not need any untrusted offset from the damaged primary header.
        return stream, meta, HDR.size + mcs, offsets, merkle
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated metadata copy: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _extract_graph(path: Path, dst: Path) -> None:
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    stream, meta, record_start, offsets, _ = _open_graph(path)
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
            raw = _preflate_unpack(payload, usize)
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
        if desc[0] == "direct":
            _, record_id, offset, length, expected = desc
            pack = record(record_id)
            if offset > len(pack) or length > len(pack) - offset:
                raise RuntimeError("direct slice bounds")
            raw = pack[offset:offset + length]
        elif desc[0] == "delta":
            _, base_id, record_id, length, expected = desc
            base_desc = nodes[base_id]
            if base_desc[0] != "direct":
                raise RuntimeError("delta dependency depth")
            raw_delta = record(record_id)
            raw = delta_decode(node(base_id), raw_delta, expected_size=length, max_output=MAX_CHUNK)
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
        _extract_graph(archive, dst)
        return
    BASE.OUT = archive
    BASE.extract(dst)


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        BASE.OUT = archive
        return BASE.strong_verify()
    stream, meta, record_start, offsets, merkle = _open_graph(archive)
    stream.close()
    with tempfile.TemporaryDirectory(prefix="cmpct-v028-verify-") as td:
        dst = Path(td)
        _extract_graph(archive, dst)
        got = treehash(dst)
    if got != meta["tree_sha256"]:
        raise RuntimeError("logical tree root mismatch")
    return {"ok": True, "tree_sha256": got, "merkle_root": merkle.hex(), "records": len(offsets),
            "max_decode_unit": meta["max_decode_unit"], "max_decoder_memory": meta["max_decoder_memory"]}


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter(); strong_verify(out); samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT EntropyGraph II resemblance research engine")
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
