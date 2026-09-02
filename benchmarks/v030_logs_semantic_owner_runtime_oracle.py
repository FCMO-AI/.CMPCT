from __future__ import annotations

"""Exact-product A/B for the promoted one-session logs extractor.

The canonical logs representation already wins the external creation/size contract. This oracle changes no archive
bytes and grants no release credit. It measures only the extraction ownership boundary: the pre-promotion mature
logs extraction semantics versus the productized one-session extractor on the frozen neutral-hostile logs workload.
Every timed round must reproduce the exact source tree. The candidate must improve median extraction by at least
10% across 11 order-rotated rounds before it emits a promotion signal.

Custody note: the production Logs candidate now delegates its public ``extract`` to the fused implementation. Using
that rebound symbol as the baseline would time fused-vs-fused and silently erase the comparator. The baseline below
therefore reconstructs the exact pre-promotion extraction path preserved by commit 9f761a13's parent: bounded
manifest/budget/symlink checks followed by the mature LOGS extractor. It uses today's canonical cross-platform
symlink predicate; this changes safety custody, not the performance hypothesis or +10% threshold.
"""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as BASELINE
from experiments import entropygraph_v030_release_product_logs_runtime as FUSED

ROUNDS = 11
MIN_IMPROVEMENT_FRACTION = 0.10


def _archive_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mature_pre_promotion_extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = BASELINE.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    """Frozen comparator: exact pre-fused Logs extraction with current canonical safety policy."""
    archive = Path(archive)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")
    decoded = BASELINE._logs_manifest(archive)
    user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
    if user_bytes > max_output_bytes:
        raise RuntimeError("logs extraction exceeds caller output budget")
    if safe_symlinks:
        for row in decoded["manifest"]["entries"]:
            if row[1] == "l" and BASELINE.FS._unsafe_symlink_target(row[7]):
                raise RuntimeError(f"unsafe r25 symlink target in {row[0]!r}")
    BASELINE.LOGS.extract(archive, dst)


def _extract_once(fn, archive: Path, dst: Path, expected_tree: str) -> float:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    gc.collect()
    started = time.perf_counter()
    fn(archive, dst)
    elapsed = time.perf_counter() - started
    got = BASELINE.treehash(dst)
    if got != expected_tree:
        raise RuntimeError(f"logs extraction tree mismatch: {got} != {expected_tree}")
    return elapsed


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    corpus_root = work_root / "corpus"
    CORPUS.corpus_logs(corpus_root)
    source = corpus_root / "05_logs_and_telemetry"
    if not source.is_dir():
        raise RuntimeError("frozen logs workload was not generated")
    expected_tree = BASELINE.treehash(source)

    archive = work_root / "logs.cmpct"
    build_stats = BASELINE.build(source, archive)
    verified = BASELINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"logs candidate failed exact strong verification: {verified!r}")
    if not BASELINE._is_logs_archive(archive):
        raise RuntimeError("frozen logs workload did not select the promoted logs representation")

    # Untimed warm-up removes import/page-cache asymmetry without hiding any per-operation extraction work.
    _extract_once(_mature_pre_promotion_extract, archive, work_root / "warm-baseline", expected_tree)
    _extract_once(FUSED.extract, archive, work_root / "warm-fused", expected_tree)

    baseline_s: list[float] = []
    fused_s: list[float] = []
    all_exact = True
    order: list[str] = []
    for round_index in range(ROUNDS):
        if round_index % 2 == 0:
            pair = (("baseline", _mature_pre_promotion_extract, baseline_s), ("fused", FUSED.extract, fused_s))
        else:
            pair = (("fused", FUSED.extract, fused_s), ("baseline", _mature_pre_promotion_extract, baseline_s))
        order.extend(label for label, _fn, _samples in pair)
        for label, fn, samples in pair:
            dst = work_root / f"round-{round_index:02d}-{label}"
            samples.append(_extract_once(fn, archive, dst, expected_tree))
            all_exact = all_exact and BASELINE.treehash(dst) == expected_tree

    baseline_median = statistics.median(baseline_s)
    fused_median = statistics.median(fused_s)
    improvement = (baseline_median - fused_median) / baseline_median
    promotion = all_exact and fused_median < baseline_median and improvement >= MIN_IMPROVEMENT_FRACTION

    return {
        "schema": "cmpct-v030-logs-semantic-owner-runtime-v1",
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "claim_boundary": (
            "archive-byte-neutral exact-product extraction A/B for the promoted logs profile; "
            "research/productization evidence only; final release authority remains separate"
        ),
        "comparator": "pre-promotion mature Logs extraction reconstructed from 9f761a13 parent with current canonical symlink safety",
        "candidate": "one-session fused Logs extraction",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _archive_sha256(archive),
        "selected": build_stats.get("selected"),
        "source_tree_sha256": expected_tree,
        "strong_verify": verified,
        "fused_extract": {
            "rounds": ROUNDS,
            "order": order,
            "baseline_s": baseline_s,
            "candidate_s": fused_s,
            "baseline_median_s": baseline_median,
            "candidate_median_s": fused_median,
            "saved_s": baseline_median - fused_median,
            "improvement_fraction": improvement,
            "minimum_improvement_fraction": MIN_IMPROVEMENT_FRACTION,
            "all_exact": all_exact,
            "one_authenticated_archive_session": True,
            "graph_identities_match_fs_manifest": True,
            "promotion_signal": promotion,
        },
        "experiment_valid": True,
        "promotion_signal": promotion,
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-semantic-owner-runtime-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-logs-semantic-owner-runtime.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fused_extract": result["fused_extract"], "release_credit": False}, indent=2), flush=True)
    if not result["fused_extract"]["promotion_signal"]:
        raise SystemExit("logs one-session extraction did not clear the exact-product promotion gate")


if __name__ == "__main__":
    main()
