"""Strict policy layer for the EntropyGraph-II research engine.

The first full hostile benchmark proved the resemblance mechanism but also falsified one locality
assumption: for populations of tiny objects, even a 64 KiB solid pack can exceed the declared 8x
weighted read-amplification budget. The original selector treated "no feasible pack" as permission to
pick the smallest byte result, which could choose a much larger pack and violate the contract.

This module makes an independent-record layout an explicit candidate with amplification exactly 1.0,
then admits only pack plans whose measured amplification is <= 8x. It also bounds metadata and physical
record declarations before the local reader can allocate from attacker-controlled sizes.

Footnote: keeping this as a narrow policy layer preserves the already-audited research grammar while
making the failed hypothesis visible in repository history instead of silently rewriting the original
experiment after evidence existed.
"""
from __future__ import annotations

import importlib.util
import msgpack
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "entropygraph_v028.py"


def _load_base():
    spec = importlib.util.spec_from_file_location("cmpct_entropygraph_v028_strict_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load EntropyGraph-II base engine")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
READ_AMPLIFICATION_BUDGET = 8.0
MAX_METADATA = 64 * 1024 * 1024
MAX_RECORDS = 1_000_000

# Save the already-tested grammar implementations before replacing their policy hooks. The delegated
# extractor/strong verifier resolve module globals at call time, so patching `_open_graph` below safely
# upgrades those callers without duplicating the reconstruction grammar.
_ORIGINAL_EXTRACT = BASE._extract_graph


def _independent_plan(nodes: list[bytes], root_ids: list[int]):
    """Store each root as its own independently decodable record.

    Footnote: this is the always-feasible locality floor. It may spend more framing bytes than a solid
    pack, but one logical root never forces unrelated root bytes to be decoded, so weighted read
    amplification is exactly 1.0 by construction.
    """
    groups = [[node_id] for node_id in sorted(root_ids)]
    cost = sum(BASE._direct_cost(nodes[node_id]) for node_id in root_ids)
    return cost, 1.0, 0, groups


def strict_choose_pack_plan(nodes: list[bytes], sketches, root_ids: list[int]):
    trials = [_independent_plan(nodes, root_ids)]
    for limit_kib in (64, 128, 256, 512, 1024, 2048):
        limit = limit_kib * 1024
        cost, amp, groups = BASE._pack_plan(nodes, sketches, root_ids, limit)
        trials.append((cost, amp, limit, groups))

    feasible = [row for row in trials if row[1] <= READ_AMPLIFICATION_BUDGET]
    if not feasible:
        # The independent plan is mathematically 1x, so this is an internal invariant failure rather
        # than a reason to weaken the public budget.
        raise RuntimeError("no locality-feasible EntropyGraph-II plan")
    chosen = min(feasible, key=lambda row: (row[0], row[1], row[2]))

    baseline = next((row for row in feasible if row[2] == 512 * 1024), None)
    if chosen[2] > 512 * 1024 and baseline is not None:
        material_win = baseline[0] - chosen[0]
        if material_win < max(1024, baseline[0] // 1000):
            chosen = baseline

    diagnostics = [
        {
            "limit": limit,
            "bytes": cost,
            "read_amp": amp,
            "feasible": amp <= READ_AMPLIFICATION_BUDGET,
        }
        for cost, amp, limit, _ in trials
    ]
    return chosen, diagnostics


def _decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                 expected_count: int | None = None, declared_decode: int | None = None,
                 declared_memory: int | None = None):
    if len(comp) > MAX_METADATA or raw_size < 0 or raw_size > MAX_METADATA:
        raise RuntimeError("EntropyGraph-II metadata exceeds strict parser limit")
    raw = BASE.zd(comp, raw_size)
    if BASE.H(raw) != expected_sha:
        raise RuntimeError("metadata authentication")
    meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if meta.get("v") != 1 or int(meta.get("max_dependency_depth", 99)) > 1:
        raise RuntimeError("unsupported graph metadata")
    meta_decode = int(meta.get("max_decode_unit", BASE.MAX_DECODE_UNIT + 1))
    meta_memory = int(meta.get("max_decoder_memory", BASE.MAX_DECODER_MEMORY + 1))
    if meta_decode > BASE.MAX_DECODE_UNIT or (declared_decode is not None and meta_decode != declared_decode):
        raise RuntimeError("archive decode ceiling exceeds implementation policy")
    if meta_memory > BASE.MAX_DECODER_MEMORY or (declared_memory is not None and meta_memory != declared_memory):
        raise RuntimeError("archive decoder-memory ceiling exceeds implementation policy")
    leaves = list(meta.get("record_leaf_sha256", []))
    offsets = list(meta.get("record_rel_offsets", []))
    if len(leaves) > MAX_RECORDS or len(offsets) != len(leaves):
        raise RuntimeError("record table exceeds strict parser limit")
    if expected_count is not None and (expected_count > MAX_RECORDS or len(leaves) != expected_count):
        raise RuntimeError("record-count mismatch")
    if BASE._merkle_root(leaves) != expected_merkle:
        raise RuntimeError("Merkle root mismatch")
    previous = -1
    for offset in offsets:
        if not isinstance(offset, int) or offset < 0 or offset <= previous:
            # Empty record tables are legal; otherwise generated physical records are strictly ordered.
            raise RuntimeError("record offsets are not strictly increasing")
        previous = offset
    return meta, offsets


def strict_open_graph(path: Path):
    """Open CMPNX8 with bounded primary and tail metadata before decompression allocation."""
    stream = path.open("rb")
    primary_error: Exception | None = None
    try:
        header = stream.read(BASE.HDR.size)
        if len(header) != BASE.HDR.size:
            raise RuntimeError("short EntropyGraph-II header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = BASE.HDR.unpack(header)
        if magic != BASE.MAG:
            raise RuntimeError("not EntropyGraph-II")
        if mcs > MAX_METADATA or mus > MAX_METADATA or count > MAX_RECORDS:
            raise RuntimeError("primary metadata declaration exceeds strict parser limit")
        if max_decode > BASE.MAX_DECODE_UNIT or max_memory > BASE.MAX_DECODER_MEMORY:
            raise RuntimeError("archive resource declaration exceeds implementation policy")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short primary metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle, count, max_decode, max_memory)
        return stream, meta, BASE.HDR.size + mcs, offsets, merkle
    except Exception as exc:
        primary_error = exc

    try:
        if path.stat().st_size < BASE.FTR.size:
            raise RuntimeError("short EntropyGraph-II footer")
        stream.seek(-BASE.FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(BASE.FTR.size)
        if len(footer) != BASE.FTR.size:
            raise RuntimeError("short EntropyGraph-II footer")
        magic, mcs, mus, meta_sha, merkle = BASE.FTR.unpack(footer)
        if magic != BASE.TAIL or mcs > MAX_METADATA or mus > MAX_METADATA:
            raise RuntimeError("tail metadata declaration exceeds strict parser limit")
        meta_offset = footer_offset - mcs
        if meta_offset < BASE.HDR.size:
            raise RuntimeError("tail metadata offset")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short tail metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle)
        return stream, meta, BASE.HDR.size + mcs, offsets, merkle
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(
            f"no authenticated bounded metadata copy: primary={primary_error!r}; tail={tail_error!r}"
        ) from tail_error


def _preflight_physical_records(path: Path) -> None:
    """Reject oversized/truncated physical declarations before payload reads allocate memory."""
    stream, meta, record_start, offsets, _ = strict_open_graph(path)
    file_size = path.stat().st_size
    try:
        for record_id, rel_offset in enumerate(offsets):
            start = record_start + rel_offset
            if start < record_start or start > file_size - BASE.PH.size:
                raise RuntimeError("physical record header outside archive")
            stream.seek(start)
            header = stream.read(BASE.PH.size)
            if len(header) != BASE.PH.size:
                raise RuntimeError("short physical header")
            codec, usize, csize, crc, logical_sha = BASE.PH.unpack(header)
            if codec not in (BASE.CODEC_RAW, BASE.CODEC_ZSTD, BASE.CODEC_PREFLATE):
                raise RuntimeError("unknown physical codec")
            if usize > BASE.MAX_DECODE_UNIT:
                raise RuntimeError("physical record exceeds declared decode unit")
            if csize > BASE.MAX_DECODER_MEMORY:
                raise RuntimeError("stored physical record exceeds decoder-memory ceiling")
            payload_start = start + BASE.PH.size
            if csize > file_size - payload_start:
                raise RuntimeError("physical record payload exceeds archive bounds")
    finally:
        stream.close()


def strict_extract_graph(path: Path, dst: Path) -> None:
    _preflight_physical_records(path)
    _ORIGINAL_EXTRACT(path, dst)


# `_build_graph`, `_extract_graph` and `strong_verify` resolve these symbols from their defining module
# at runtime. Patch policy before delegation so all strict callers inherit the bounded implementations.
BASE._choose_pack_plan = strict_choose_pack_plan
BASE._open_graph = strict_open_graph
BASE._extract_graph = strict_extract_graph

# Re-export the grammar and reader surface used by benchmarks/tests/remote tooling.
MAG = BASE.MAG
TAIL = BASE.TAIL
HDR = BASE.HDR
FTR = BASE.FTR
PH = BASE.PH
CODEC_RAW = BASE.CODEC_RAW
CODEC_ZSTD = BASE.CODEC_ZSTD
CODEC_PREFLATE = BASE.CODEC_PREFLATE
MAX_CHUNK = BASE.MAX_CHUNK
MAX_PACK = BASE.MAX_PACK
MAX_DECODE_UNIT = BASE.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = BASE.MAX_DECODER_MEMORY
H = BASE.H
zc = BASE.zc
zd = BASE.zd
_merkle_root = BASE._merkle_root
_preflate_unpack = BASE._preflate_unpack
_open_graph = strict_open_graph
_extract_graph = strict_extract_graph


def treehash(root: Path) -> str:
    return BASE.treehash(root)


def _build_graph(root: Path, out: Path) -> dict:
    stats = BASE._build_graph(root, out)
    if stats["pack_read_amplification"] > READ_AMPLIFICATION_BUDGET:
        raise RuntimeError("EntropyGraph-II emitted a pack above the hard read-amplification budget")
    stats["read_amplification_budget"] = READ_AMPLIFICATION_BUDGET
    stats["strict_locality_policy"] = True
    return stats


def build(root: Path, out: Path) -> dict:
    # Reproduce the portfolio shell so the strict graph candidate, not the historical base graph, is
    # compared against inherited v0.25.
    import shutil
    import tempfile
    import time

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-v028-strict-portfolio-") as td:
        legacy = Path(td) / "legacy.cmpct"
        graph = Path(td) / "graph.cmpct"
        BASE.BASE.ROOT = root
        BASE.BASE.OUT = legacy
        legacy_stats = BASE.BASE.build()
        graph_stats = _build_graph(root, graph)
        if graph.stat().st_size < legacy.stat().st_size:
            shutil.copyfile(graph, out)
            # Preserve the benchmark schema's historical value; strictness is separately explicit in
            # graph_stats so downstream reports do not miscount a successful resemblance selection.
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


def extract(archive: Path, dst: Path) -> None:
    return BASE.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    # The delegated verifier now reaches strict_open_graph + strict_extract_graph through patched globals.
    return BASE.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    import statistics
    import time

    result = build(root, out)
    samples = []
    for _ in range(3):
        t0 = time.perf_counter()
        strong_verify(out)
        samples.append(time.perf_counter() - t0)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = treehash(root)
    return result
