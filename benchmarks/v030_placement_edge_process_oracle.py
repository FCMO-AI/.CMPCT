from __future__ import annotations

"""Exact-byte oracle for process-parallel Placement edge auditions on the pathological large-binary row.

The v0.30 shared G0-G4 substrate deliberately retains attempt-5's pre-fallback Placement/Residual graph.  That is
necessary because Geometry can only audition authenticated Placement/Residual physical records; simply applying
v0.29's outer single-file fast reject would delete a possible G0-G4 winner.  The expensive part is therefore the
Placement graph search itself, not a disposable verification pass.

This diagnostic keeps the Placement compiler unchanged and only memoizes one pure, independent loop: each
``delta_encode(base, target)`` + level-12 physical compression audition over the already-determined broad edge
set.  The candidate computes those exact auditions in bounded spawned workers, then invokes the original
attempt-5 ``build_graph`` with exact-result caches installed.  All later central-base selection, pack planning,
mosaic subset search, placement economics, residual packing, record ordering and serialization remain owned by
the existing compiler.

The candidate runs inside a spawned parent process and creates its own spawned edge pool, matching the nested
process topology of the promoted v0.30 shared builder.  Promotion is NOT automatic: this oracle is exploratory
and requires exact graph bytes/SHA/tree plus a very large wall-clock win on the known pathological row before a
production integration should even be considered.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
import time
from types import SimpleNamespace

from benchmarks import v030_release_generalization as GENERAL

TARGET = "10_large_mixed_binary"
MIN_IMPROVEMENT_PCT = 30.0
MIN_SAVED_S = 120.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _modules():
    # Import through the promoted release graph so the exact v0.30 shared attempt-5 module identity is exercised.
    from experiments import entropygraph_v030_release_product as product

    a5 = product.C.SHARED.A5
    a4 = a5.A4
    impl = a4.IMPL
    return product, a5, a4, impl


def _placement_edge_worker(payload):
    target_id, base_id, shared, target, base = payload
    _product, _a5, _a4, impl = _modules()
    result = impl.delta_encode(base, target, block=64, max_base_index=impl.MAX_CHUNK)
    codec, compressed = impl._compress_record(result.payload, 12)
    return {
        "target_id": target_id,
        "base_id": base_id,
        "shared": shared,
        "base": base,
        "target": target,
        "delta": result.payload,
        "copied": int(result.stats.copied_bytes),
        "literal": int(result.stats.literal_bytes),
        "codec": int(codec),
        "compressed": compressed,
    }


def _placement_nodes_and_edges(root: Path):
    """Reproduce only the deterministic pre-audition discovery prefix of Placement._build_graph."""
    _product, _a5, _a4, impl = _modules()
    files = sorted(path for path in Path(root).rglob("*") if path.is_file())
    raws = [path.read_bytes() for path in files]

    normal_files: list[int] = []
    for file_id, (path, raw) in enumerate(zip(files, raws)):
        packed = None
        if path.suffix.lower() in impl.PREFLATE_EXTS and 4096 <= len(raw) <= impl.MAX_DECODE_UNIT:
            packed = impl.V028._preflate_pack(raw, path.suffix)
        direct = impl._direct_cost(raw)
        if packed is None or impl.PH.size + len(packed) + 24 >= direct:
            normal_files.append(file_id)

    nodes: list[bytes] = []
    node_hash_to_id: dict[bytes, int] = {}
    for file_id in normal_files:
        raw = raws[file_id]
        chunks = (
            impl.fastcdc(raw, min_size=32 * 1024, avg_size=128 * 1024, max_size=impl.MAX_CHUNK)
            if len(raw) > impl.MAX_CHUNK
            else [SimpleNamespace(offset=0, length=len(raw))]
        )
        for chunk in chunks:
            part = raw[chunk.offset : chunk.offset + chunk.length]
            hh = impl.H(part)
            node_id = node_hash_to_id.get(hh)
            if node_id is None or nodes[node_id] != part:
                node_hash_to_id[hh] = len(nodes)
                nodes.append(part)

    sketches = [impl.similarity_sketch(raw) for raw in nodes]
    inherited_edges = impl.lsh_candidates(sketches, max_bucket=48, max_candidates=8)
    inherited_pairs = {(edge.target, edge.base): edge.shared_features for edge in inherited_edges}
    broad_pairs = dict(inherited_pairs)
    for target_id, base_id, shared in impl._position_independent_candidates(sketches, nodes):
        broad_pairs[(target_id, base_id)] = max(shared, broad_pairs.get((target_id, base_id), 0))

    payloads = []
    for (target_id, base_id), shared in sorted(broad_pairs.items()):
        target = nodes[target_id]
        base = nodes[base_id]
        if min(len(target), len(base)) < impl.MIN_DELTA:
            continue
        payloads.append((target_id, base_id, int(shared), target, base))
    return nodes, payloads


def _precompute_edges(root: Path) -> tuple[dict, dict, dict]:
    nodes, payloads = _placement_nodes_and_edges(root)
    if not payloads:
        return {}, {}, {"nodes": len(nodes), "edges": 0, "workers": 0, "precompute_s": 0.0}

    started = time.perf_counter()
    ctx = mp.get_context("spawn")
    workers = min(4, len(payloads))
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        rows = list(pool.map(_placement_edge_worker, payloads, chunksize=1))
    elapsed = time.perf_counter() - started

    delta_cache = {}
    compression_cache = {}
    for row in rows:
        # Full byte keys deliberately avoid probabilistic cache identity. The original compiler rebuilds equal
        # node bytes in its own pass, and Python bytes equality gives exact cache lookup semantics.
        delta_cache[(row["base"], row["target"])] = SimpleNamespace(
            payload=row["delta"],
            stats=SimpleNamespace(copied_bytes=row["copied"], literal_bytes=row["literal"]),
        )
        compression_cache[(row["delta"], 12)] = (row["codec"], row["compressed"])
    return delta_cache, compression_cache, {
        "nodes": len(nodes),
        "edges": len(rows),
        "workers": workers,
        "precompute_s": elapsed,
    }


@contextmanager
def _cached_placement_edges(root: Path):
    _product, _a5, _a4, impl = _modules()
    original_delta = impl.delta_encode
    original_compress = impl._compress_record
    delta_cache, compression_cache, cache_stats = _precompute_edges(root)

    def cached_delta(base, target, *, block, max_base_index):
        if block == 64 and max_base_index == impl.MAX_CHUNK:
            hit = delta_cache.get((base, target))
            if hit is not None:
                return hit
        return original_delta(base, target, block=block, max_base_index=max_base_index)

    def cached_compress(raw: bytes, level: int = 19):
        hit = compression_cache.get((raw, level))
        if hit is not None:
            return hit
        return original_compress(raw, level)

    impl.delta_encode = cached_delta
    impl._compress_record = cached_compress
    try:
        yield cache_stats
    finally:
        impl.delta_encode = original_delta
        impl._compress_record = original_compress


def _variant_worker(payload):
    variant, source_text, out_text = payload
    source = Path(source_text)
    out = Path(out_text)
    _product, a5, _a4, _impl = _modules()
    started = time.perf_counter()
    cache_stats = None
    if variant == "baseline":
        stats = dict(a5.build_graph(source, out))
    elif variant == "process-edge-cache":
        with _cached_placement_edges(source) as cache_stats:
            stats = dict(a5.build_graph(source, out))
    else:
        raise ValueError(variant)
    elapsed = time.perf_counter() - started
    verified = a5.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"{variant} attempt-5 graph failed strong verification: {verified!r}")
    return {
        "variant": variant,
        "create_s": elapsed,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "tree_sha256": verified.get("tree_sha256"),
        "selected_residual": stats.get("residual_selected"),
        "mosaic_nodes": stats.get("mosaic_nodes"),
        "single_delta_nodes": stats.get("single_delta_nodes"),
        "residual_pack_records": stats.get("residual_pack_records"),
        "cache": cache_stats,
    }


def _run_nested_variant(variant: str, source: Path, out: Path) -> dict:
    # attempt-5 normally runs as one spawned child of the v0.30 shared portfolio. Reproduce that parent topology;
    # the process-edge candidate then spawns its bounded edge workers from inside this child.
    ctx = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as pool:
        return dict(pool.submit(_variant_worker, (variant, str(source), str(out))).result())


def _build_target(root: Path) -> Path:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_placement_edge_oracle_neutral",
    )
    target_parent = root / "neutral"
    target_parent.mkdir(parents=True, exist_ok=True)
    neutral.corpus_disk(target_parent)
    target = target_parent / TARGET
    if not target.is_dir():
        raise RuntimeError("large mixed binary target was not generated")
    files = [path for path in target.rglob("*") if path.is_file()]
    if len(files) != 1 or files[0].stat().st_size != 32 * 1024 * 1024:
        raise RuntimeError("large mixed binary target shape drift")
    return target


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = _build_target(work_root)
    baseline_path = work_root / "baseline-attempt5.cmpct"
    candidate_path = work_root / "process-edge-attempt5.cmpct"

    baseline = _run_nested_variant("baseline", source, baseline_path)
    candidate = _run_nested_variant("process-edge-cache", source, candidate_path)
    byte_identical = (
        baseline["archive_bytes"] == candidate["archive_bytes"]
        and baseline["archive_sha256"] == candidate["archive_sha256"]
        and baseline["tree_sha256"] == candidate["tree_sha256"]
    )
    if not byte_identical:
        raise RuntimeError(f"process-parallel edge auditions changed attempt-5 graph: {baseline!r} vs {candidate!r}")

    saved = float(baseline["create_s"]) - float(candidate["create_s"])
    pct = saved / max(float(baseline["create_s"]), 1e-9) * 100.0
    material = saved >= MIN_SAVED_S and pct >= MIN_IMPROVEMENT_PCT
    gate = {
        "exact_target_shape": True,
        "byte_identical": byte_identical,
        "tree_identical": baseline["tree_sha256"] == candidate["tree_sha256"],
        "material_speedup": material,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-placement-edge-process-oracle-v1",
        "engine": "v0.30 shared attempt-5 Placement/Residual graph",
        "target": TARGET,
        "hypothesis": "parallelize exact independent Placement delta-edge auditions without changing compiler decisions",
        "contract": {
            "exact_graph_bytes_required": True,
            "strong_verify_required": True,
            "nested_spawn_topology": True,
            "minimum_improvement_pct": MIN_IMPROVEMENT_PCT,
            "minimum_saved_s": MIN_SAVED_S,
            "exploratory_only": True,
            "no_release_threshold_changed": True,
        },
        "baseline": baseline,
        "candidate": candidate,
        "saved_s": saved,
        "improvement_pct": pct,
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-placement-edge-process-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-placement-edge-process.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("Placement process-edge oracle did not earn promotion")


if __name__ == "__main__":
    main()
