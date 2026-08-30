from __future__ import annotations

"""Exact full-build A/B for reusing the shipping Logs structural preflight.

The public v0.30 facade already computes ``logs_source_prefilter`` in its shared
front door before dispatching the promoted Logs terminal.  The terminal helper
currently recomputes the same proof.  This oracle changes no product bytes or
admission law: the candidate arm memoizes only that already-produced structural
proof for the duration of one public ``CANON.build`` call.

Promotion signal requires exact archive identity, exact verified tree identity,
and a material wall-clock reduction.  The ordinary external ZIP/Zstd authority
remains unchanged and this oracle cannot unlock release by itself.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS

ROUNDS = 16
MIN_DELTA_MS = 2.0
MIN_RELATIVE_IMPROVEMENT = 0.004


def _prepare_source(work_root: Path) -> Path:
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_logs_prefilter_reuse_neutral",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_logs_prefilter_reuse_repair",
    )
    repair.install_generation_hooks(neutral)
    root = work_root / "neutral"
    neutral.build(root)
    repair.normalize_root(root)
    source = root / "05_logs_and_telemetry"
    if not source.is_dir():
        raise RuntimeError("frozen Logs workload is missing")
    return source


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(stage: Path, out: Path, *, reuse: bool) -> dict:
    original = LOGS.logs_source_prefilter
    cache: dict[str, dict] = {}

    def memoized(root: Path) -> dict:
        key = str(Path(root).resolve())
        if key not in cache:
            cache[key] = original(root)
        return cache[key]

    if reuse:
        LOGS.logs_source_prefilter = memoized
    started = time.perf_counter()
    try:
        stats = dict(CANON.build(stage, out))
    finally:
        elapsed = time.perf_counter() - started
        LOGS.logs_source_prefilter = original
    verified = dict(CANON.strong_verify(out))
    if not verified.get("ok"):
        raise RuntimeError(f"candidate failed strong verification: {verified!r}")
    if stats.get("selected") != "logs-inverse":
        raise RuntimeError(f"Logs workload did not select promoted terminal: {stats.get('selected')!r}")
    return {
        "create_s": elapsed,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha(out),
        "tree_sha256": verified.get("tree_sha256") or verified.get("user_tree_sha256"),
        "prefilter_calls_with_real_scan": len(cache) if reuse else None,
    }


def _zip_once(stage: Path, work: Path, index: int) -> dict:
    archive = work / f"zip-{index}.zip"
    extracted = work / f"zip-out-{index}"
    return dict(EXT._zip(stage, archive, extracted))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = _prepare_source(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-prefilter-abba-", dir=work_root) as td:
        temp = Path(td)
        stage = EXT._normalized_stage(source, temp)
        expected_tree = EXT._tree(stage)
        rows: list[dict] = []
        for round_index in range(ROUNDS):
            order = (False, True, True, False) if round_index % 2 == 0 else (True, False, False, True)
            for arm_index, reuse in enumerate(order):
                out = temp / f"cmpct-{round_index}-{arm_index}.cmpct"
                row = _one(stage, out, reuse=reuse)
                row.update({"round": round_index, "arm_index": arm_index, "arm": "reuse" if reuse else "baseline"})
                if row["tree_sha256"] != expected_tree:
                    raise RuntimeError("CMPCT verified tree identity drift")
                rows.append(row)

        zip_rows = [_zip_once(stage, temp, index) for index in range(12)]

    baseline = [row for row in rows if row["arm"] == "baseline"]
    candidate = [row for row in rows if row["arm"] == "reuse"]
    identities = {(row["archive_bytes"], row["archive_sha256"], row["tree_sha256"]) for row in rows}
    if len(identities) != 1:
        raise RuntimeError(f"prefilter reuse changed product identity: {sorted(identities)!r}")
    base_median = statistics.median(row["create_s"] for row in baseline)
    cand_median = statistics.median(row["create_s"] for row in candidate)
    zip_median = statistics.median(row["create_s"] for row in zip_rows)
    delta_s = base_median - cand_median
    relative = delta_s / base_median if base_median > 0 else 0.0
    promotion = {
        "exact_product_identity": len(identities) == 1,
        "candidate_real_prefilter_scans_exactly_one": all(row["prefilter_calls_with_real_scan"] == 1 for row in candidate),
        "minimum_absolute_reduction": delta_s >= MIN_DELTA_MS / 1000.0,
        "minimum_relative_reduction": relative >= MIN_RELATIVE_IMPROVEMENT,
    }
    promotion["passed"] = all(promotion.values())
    archive_bytes, archive_sha256, tree_sha256 = next(iter(identities))
    return {
        "schema": "cmpct-v030-logs-prefilter-reuse-abba-v1",
        "rounds": ROUNDS,
        "samples_per_arm": len(baseline),
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_sha256,
        "tree_sha256": tree_sha256,
        "baseline_median_create_s": base_median,
        "reuse_median_create_s": cand_median,
        "delta_ms": delta_s * 1000.0,
        "relative_improvement": relative,
        "zip_deflate9_median_create_s": zip_median,
        "candidate_vs_zip_delta_ms": (cand_median - zip_median) * 1000.0,
        "candidate_strictly_faster_than_zip": cand_median < zip_median,
        "promotion_gate": promotion,
        "claim_boundary": "A/B ownership oracle only; canonical external competitor and release authorities remain unchanged",
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-prefilter-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-prefilter-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "archive_bytes", "baseline_median_create_s", "reuse_median_create_s", "delta_ms",
        "relative_improvement", "zip_deflate9_median_create_s", "candidate_vs_zip_delta_ms",
        "candidate_strictly_faster_than_zip", "promotion_gate",
    )}, indent=2), flush=True)
    if not result["promotion_gate"]["passed"]:
        raise SystemExit("Logs prefilter reuse did not meet promotion threshold")


if __name__ == "__main__":
    main()
