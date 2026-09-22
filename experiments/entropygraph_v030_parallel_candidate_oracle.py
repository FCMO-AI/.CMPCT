"""Measure whether independent v0.30 complete candidates should build concurrently.

This is a research oracle, not a release-path mutation. It preserves the current G0-G4 and PrefixGraph
builders byte-for-byte and asks one narrow question: after PrefixGraph eligibility has been established,
can the two independent complete artifacts be constructed in parallel without changing either artifact?

The oracle is deliberately fail-closed on semantics. A timing result is valid only when sequential and
parallel construction produce byte-identical G0-G4 and PrefixGraph candidates. Timing alone can never
promote the mechanism. The research gate is frozen at >=20% and >=5 seconds saved; a valid measurement
below either threshold is a REJECT, not an invitation to tune the threshold.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import tempfile
import time

from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC

MIN_SAVED_RATIO = 0.20
MIN_SAVED_SECONDS = 5.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_g04(source: str, output: str) -> dict:
    return G04.build(Path(source), Path(output))


def _build_prefixgraph(source: str, output: str) -> dict:
    return PG.build(Path(source), Path(output))


def measure(source: Path, work_root: Path) -> dict:
    source = source.resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    expected_tree = RC.treehash(source)
    eligible, reject_reason = RC._prefixgraph_eligibility(source, expected_tree)
    if not eligible:
        return {
            "schema": "cmpct-v030-parallel-candidate-oracle-v1",
            "decision": "REJECT",
            "reason": f"prefixgraph-ineligible:{reject_reason}",
            "tree_sha256": expected_tree,
            "byte_identity": None,
        }

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-parallel-oracle-", dir=work_root) as td:
        root = Path(td)
        seq_g04 = root / "seq-g04.cmpct"
        seq_pg = root / "seq-prefixgraph.cmpct"
        par_g04 = root / "par-g04.cmpct"
        par_pg = root / "par-prefixgraph.cmpct"

        seq_started = time.perf_counter()
        seq_g04_stats = G04.build(source, seq_g04)
        seq_pg_stats = PG.build(source, seq_pg)
        sequential_s = time.perf_counter() - seq_started

        # Spawn instead of fork so the benchmark does not inherit warmed mutable Python module state from
        # the sequential measurement. The filesystem cache is still shared, so this is mechanism evidence,
        # not a standalone release timing claim; balanced repetition belongs in the promotion benchmark.
        ctx = mp.get_context("spawn")
        par_started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=2, mp_context=ctx) as pool:
            g04_future = pool.submit(_build_g04, str(source), str(par_g04))
            pg_future = pool.submit(_build_prefixgraph, str(source), str(par_pg))
            par_g04_stats = g04_future.result()
            par_pg_stats = pg_future.result()
        parallel_s = time.perf_counter() - par_started

        seq_g04_sha = _sha256(seq_g04)
        par_g04_sha = _sha256(par_g04)
        seq_pg_sha = _sha256(seq_pg)
        par_pg_sha = _sha256(par_pg)
        byte_identity = (
            seq_g04.stat().st_size == par_g04.stat().st_size
            and seq_pg.stat().st_size == par_pg.stat().st_size
            and seq_g04_sha == par_g04_sha
            and seq_pg_sha == par_pg_sha
        )
        if not byte_identity:
            raise RuntimeError("parallel candidate construction changed candidate bytes")

        saved_s = sequential_s - parallel_s
        saved_ratio = saved_s / sequential_s if sequential_s > 0 else 0.0
        passed = saved_s >= MIN_SAVED_SECONDS and saved_ratio >= MIN_SAVED_RATIO

        return {
            "schema": "cmpct-v030-parallel-candidate-oracle-v1",
            "decision": "PASS" if passed else "REJECT",
            "reason": None if passed else "below-frozen-materiality-gate",
            "tree_sha256": expected_tree,
            "byte_identity": True,
            "sequential_s": sequential_s,
            "parallel_s": parallel_s,
            "saved_s": saved_s,
            "saved_ratio": saved_ratio,
            "minimum_saved_s": MIN_SAVED_SECONDS,
            "minimum_saved_ratio": MIN_SAVED_RATIO,
            "g04_bytes": seq_g04.stat().st_size,
            "prefixgraph_bytes": seq_pg.stat().st_size,
            "g04_sha256": seq_g04_sha,
            "prefixgraph_sha256": seq_pg_sha,
            "sequential_g04_selected": seq_g04_stats.get("selected"),
            "parallel_g04_selected": par_g04_stats.get("selected"),
            "sequential_prefixgraph_records": len(seq_pg_stats.get("records", [])) if isinstance(seq_pg_stats, dict) else None,
            "parallel_prefixgraph_records": len(par_pg_stats.get("records", [])) if isinstance(par_pg_stats, dict) else None,
            "claim_boundary": (
                "research scheduler oracle only; valid only with exact candidate byte identity; promotion requires "
                "balanced repeated timing on the authoritative workload matrix"
            ),
        }


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 parallel complete-candidate research oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
