from __future__ import annotations

"""Research-only exact-byte PrefixGraph invariant-hash A/B.

Every anchor audition receives the same immutable ``raws`` and ``direct_payloads`` but
the historical serializer re-runs SHA-256 over those objects for every candidate.  This
oracle wraps the existing semantic owner rather than reimplementing it: on the first
serializer call it caches only the digests of those two immutable object sets, and all
other bytes (prefix trials, metadata, recovery copies) continue through the historical
``H`` function unchanged.

The A/B uses the serial semantic owner deliberately so the temporary monkeypatch is not
shared across threads.  It is a causal CPU diagnostic, not a shipping scheduler.  Exact
archive bytes/SHA/tree are mandatory and the experiment grants zero release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_prefixgraph as PG

ROUNDS = 3
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
MIN_SPEEDUP_FRACTION = 0.08


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_baseline(source: Path, archive: Path) -> dict:
    started = time.perf_counter()
    stats = dict(PG.build(source, archive))
    return {"wall_s": time.perf_counter() - started, "stats": stats, "bytes": archive.stat().st_size, "sha256": _sha(archive)}


def _build_cached(source: Path, archive: Path) -> dict:
    original_serializer = PG._serialize_candidate
    original_h = PG.H
    invariant: dict[int, tuple[bytes, bytes]] = {}

    def cached_serializer(rels, raws, direct_payloads, expected_tree, anchor):
        if not invariant:
            for obj in list(raws) + list(direct_payloads):
                invariant[id(obj)] = (obj, original_h(obj))

        def cached_h(data: bytes) -> bytes:
            hit = invariant.get(id(data))
            if hit is not None and hit[0] is data:
                return hit[1]
            return original_h(data)

        PG.H = cached_h
        try:
            return original_serializer(rels, raws, direct_payloads, expected_tree, anchor)
        finally:
            PG.H = original_h

    PG._serialize_candidate = cached_serializer
    try:
        started = time.perf_counter()
        stats = dict(PG.build(source, archive))
        wall = time.perf_counter() - started
    finally:
        PG._serialize_candidate = original_serializer
        PG.H = original_h
    return {"wall_s": wall, "stats": stats, "bytes": archive.stat().st_size, "sha256": _sha(archive)}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    expected_tree = PG.treehash(source)
    pairs = []
    baseline_times = []
    cached_times = []
    reference = None
    for rep in range(ROUNDS):
        order = ("baseline", "cached") if rep % 2 == 0 else ("cached", "baseline")
        row = {"round": rep, "order": list(order)}
        for kind in order:
            archive = work_root / "archives" / f"r{rep}-{kind}.cmpnxp1"
            archive.parent.mkdir(parents=True, exist_ok=True)
            measured = _build_baseline(source, archive) if kind == "baseline" else _build_cached(source, archive)
            verified = PG.strong_verify(archive)
            if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
                raise RuntimeError(f"PrefixGraph {kind} verification failed: {verified!r}")
            identity = (int(measured["bytes"]), str(measured["sha256"]), str(verified["tree_sha256"]))
            if reference is None:
                reference = identity
            elif identity != reference:
                raise RuntimeError(f"PrefixGraph invariant hash cache changed archive identity: {identity!r} != {reference!r}")
            row[kind] = measured
        baseline_times.append(float(row["baseline"]["wall_s"]))
        cached_times.append(float(row["cached"]["wall_s"]))
        pairs.append(row)

    baseline_median = float(statistics.median(baseline_times))
    cached_median = float(statistics.median(cached_times))
    speedup = 1.0 - cached_median / max(baseline_median, 1e-9)
    signal = speedup >= MIN_SPEEDUP_FRACTION
    return {
        "schema": "cmpct-v030-prefixgraph-invariant-hash-cache-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": list(TARGET),
        "rounds": ROUNDS,
        "archive_bytes": int(reference[0]),
        "archive_sha256": str(reference[1]),
        "tree_sha256": str(reference[2]),
        "baseline_median_wall_s": baseline_median,
        "cached_median_wall_s": cached_median,
        "speedup_fraction": float(speedup),
        "pairs": pairs,
        "contract": {
            "release_credit": False,
            "production_change": False,
            "candidate_set_changed": False,
            "anchor_nomination_changed": False,
            "complete_byte_tournament_changed": False,
            "archive_grammar_changed": False,
            "hash_algorithm_changed": False,
            "cached_objects": "immutable raw files and anchor-independent direct payloads only",
            "minimum_speedup_for_signal": MIN_SPEEDUP_FRACTION,
        },
        "gate": {"experiment_valid": True, "causal_signal": bool(signal), "passed": True},
        "claim_boundary": "A causal signal nominates explicit thread-safe digest plumbing for product A/B; this monkeypatch is never a production implementation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-hash-cache-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-hash-cache.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("baseline_median_wall_s", "cached_median_wall_s", "speedup_fraction", "gate")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
