"""Exact complete-artifact oracle for deleting hierarchical G04 search when flat Geometry is sufficient.

The frozen ML workload currently spends most of its v0.30 creation wall time inside hierarchical G04 audition even
though the hierarchy contributes only a few KiB beyond the cheaper flat lane/delimiter transforms.  This oracle
asks the release-relevant question directly: can the complete canonical product omit hierarchical auditions and
still preserve semantic identity, stay at or below accepted v0.29 bytes, and materially reduce complete create
wall time?

The experiment targets a frozen workload only as an oracle.  No benchmark identity enters shipping policy.  A
positive result is permission to design a generic structural terminal/admission law; it is not release credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
REPETITIONS = 3
MIN_COMPLETE_CREATE_SPEEDUP = 0.20


def _tree_sha(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode()
        data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "big")); h.update(rel)
        h.update(len(data).to_bytes(8, "big")); h.update(data)
    return h.hexdigest()


def _candidate_build(root: Path, archive: Path) -> tuple[dict, float]:
    """Build the ordinary product with only the canonical private hierarchy audition replaced by flat audition."""
    C = PRODUCT.C
    G = C.SHARED.G
    original = G._audition_record
    flat = G.O._audition_record

    def flat_only(record_id, record, member_lengths):
        # Same locality admission and exact flat transform law as the first stage of the owning G04 audition.
        return flat(record_id, record, member_lengths)

    G._audition_record = flat_only
    started = time.perf_counter_ns()
    try:
        stats = dict(PRODUCT.build(root, archive))
    finally:
        elapsed = (time.perf_counter_ns() - started) / 1e9
        G._audition_record = original
    return stats, elapsed


def _baseline_build(root: Path, archive: Path) -> tuple[dict, float]:
    started = time.perf_counter_ns()
    stats = dict(PRODUCT.build(root, archive))
    return stats, (time.perf_counter_ns() - started) / 1e9


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_sha = _tree_sha(source)

    # Accepted v0.29 is the immutable byte floor.  Build it once through the benchmark worker used by authority.
    v029 = work_root / "accepted-v029.cmpct"
    v029_stats = PERF._run_worker(
        "--engine", "v029", "--op", "pack", "--source", str(source), "--archive", str(v029)
    )
    accepted_v029_bytes = v029.stat().st_size

    baseline_times: list[float] = []
    candidate_times: list[float] = []
    baseline_bytes: list[int] = []
    candidate_bytes: list[int] = []
    baseline_sha: list[str] = []
    candidate_sha: list[str] = []
    baseline_stats = None
    candidate_stats = None

    for rep in range(REPETITIONS):
        baseline = work_root / f"baseline-{rep}.cmpct"
        candidate = work_root / f"flat-{rep}.cmpct"
        if rep % 2:
            candidate_stats, ct = _candidate_build(source, candidate)
            baseline_stats, bt = _baseline_build(source, baseline)
        else:
            baseline_stats, bt = _baseline_build(source, baseline)
            candidate_stats, ct = _candidate_build(source, candidate)
        baseline_times.append(bt); candidate_times.append(ct)
        baseline_bytes.append(baseline.stat().st_size); candidate_bytes.append(candidate.stat().st_size)
        baseline_sha.append(hashlib.sha256(baseline.read_bytes()).hexdigest())
        candidate_sha.append(hashlib.sha256(candidate.read_bytes()).hexdigest())
        bverify = PRODUCT.strong_verify(baseline)
        cverify = PRODUCT.strong_verify(candidate)
        if not bverify.get("ok") or not cverify.get("ok"):
            raise RuntimeError(f"strong verification failed: baseline={bverify!r} candidate={cverify!r}")
        btree = work_root / f"baseline-tree-{rep}"
        ctree = work_root / f"candidate-tree-{rep}"
        PRODUCT.extract(baseline, btree); PRODUCT.extract(candidate, ctree)
        if _tree_sha(btree) != source_sha or _tree_sha(ctree) != source_sha:
            raise RuntimeError("flat-only candidate changed logical tree")

    if len(set(baseline_bytes)) != 1 or len(set(candidate_bytes)) != 1:
        raise RuntimeError("nondeterministic complete archive size")
    if len(set(baseline_sha)) != 1 or len(set(candidate_sha)) != 1:
        raise RuntimeError("nondeterministic complete archive bytes")

    baseline_median = statistics.median(baseline_times)
    candidate_median = statistics.median(candidate_times)
    ratio = candidate_median / max(baseline_median, 1e-12)
    candidate_size = candidate_bytes[0]
    baseline_size = baseline_bytes[0]
    gates = {
        "accepted_v029_floor_preserved": candidate_size <= accepted_v029_bytes,
        "semantic_tree_identity": True,
        "strong_verification": True,
        "deterministic_complete_bytes": True,
        "complete_create_speedup_at_least_20pct": ratio <= 1.0 - MIN_COMPLETE_CREATE_SPEEDUP,
    }
    gates["passed"] = all(gates.values())
    return {
        "schema": "cmpct-v030-g04-flat-terminal-oracle-v1",
        "research_only": True,
        "target": list(TARGET),
        "source_tree_sha256": source_sha,
        "accepted_v029": {"archive_bytes": accepted_v029_bytes, "worker": v029_stats},
        "shipping_baseline": {
            "archive_bytes": baseline_size,
            "archive_sha256": baseline_sha[0],
            "median_complete_create_s": baseline_median,
            "times_s": baseline_times,
            "stats": baseline_stats,
        },
        "flat_only": {
            "archive_bytes": candidate_size,
            "archive_sha256": candidate_sha[0],
            "byte_delta_vs_shipping": candidate_size - baseline_size,
            "byte_margin_vs_v029": accepted_v029_bytes - candidate_size,
            "median_complete_create_s": candidate_median,
            "times_s": candidate_times,
            "candidate_to_shipping_create_ratio": ratio,
            "speedup_fraction": 1.0 - ratio,
            "stats": candidate_stats,
        },
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-flat-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-flat.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "accepted_v029_bytes": result["accepted_v029"]["archive_bytes"],
        "shipping": {k: result["shipping_baseline"][k] for k in ("archive_bytes", "median_complete_create_s")},
        "flat_only": {k: result["flat_only"][k] for k in ("archive_bytes", "byte_delta_vs_shipping", "byte_margin_vs_v029", "median_complete_create_s", "candidate_to_shipping_create_ratio", "speedup_fraction")},
        "gates": result["gates"],
    }, indent=2))
    if not result["gates"]["passed"]:
        raise SystemExit("flat-only G04 did not cross the preregistered complete-artifact gate")


if __name__ == "__main__":
    main()
