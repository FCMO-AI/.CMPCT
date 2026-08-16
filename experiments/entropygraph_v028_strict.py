"""Strict policy layer for the EntropyGraph-II research engine.

The first full hostile benchmark proved the resemblance mechanism but also falsified one locality
assumption: for populations of tiny objects, even a 64 KiB solid pack can exceed the declared 8x
weighted read-amplification budget. The original selector treated "no feasible pack" as permission to
pick the smallest byte result, which could choose a much larger pack and violate the contract.

This module makes an independent-record layout an explicit candidate with amplification exactly 1.0,
then admits only pack plans whose measured amplification is <= 8x. It deliberately reuses the same
CMPNX8 grammar/reader and the same inherited-v0.25 portfolio fallback; only encoder policy changes.

Footnote: keeping this as a narrow policy layer preserves the already-audited research grammar while
making the failed hypothesis visible in repository history instead of silently rewriting the original
experiment after evidence existed.
"""
from __future__ import annotations

import importlib.util
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


# `_build_graph` resolves this symbol from its defining module at runtime. Patch the policy before any
# delegated build so every caller of this strict engine receives the hard locality contract.
BASE._choose_pack_plan = strict_choose_pack_plan

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
_open_graph = BASE._open_graph
_extract_graph = BASE._extract_graph


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
