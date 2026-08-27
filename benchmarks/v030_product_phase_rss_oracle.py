from __future__ import annotations

"""Fresh-process phase decomposition for v0.30 release-product peak RSS.

Runtime authority currently observes a large pack-RSS regression even though serializing the r24 prebuild does not
materially reduce memory.  This oracle asks a narrower causal question without changing product behavior: how much
peak resident memory is owned by (a) canonical r24 construction alone, (b) canonical profile/manifest capture alone,
and (c) the complete promoted release product?

Each measured arm runs in a fresh Python process after importing the same promoted product/base modules.  The worker
captures ``ru_maxrss`` immediately before and immediately after the timed operation; mandatory semantic checks happen
after that measurement so they cannot inflate the operation peak recorded here.  The parent uses the exact frozen
Shifted/Logs/ML runtime corpora and validates their accepted v0.29 source identities before launching workers.

This is diagnostic evidence only.  It changes no scheduling, archive bytes, selector, grammar, integrity, locality,
decode budget, RSS release threshold or publication rule, and it can never grant release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_release_performance as PERF
from benchmarks import v030_release_generalization as GENERAL

ROOT = Path(__file__).resolve().parents[1]
ROUNDS = 2
MODES = ("r24", "profile", "full")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _worker(mode: str, source: Path, work_root: Path) -> dict:
    # Import both surfaces before the baseline sample so import/module ownership is identical across arms.
    from experiments import entropygraph_v030_release_product as product
    from experiments import entropygraph_v030_release_product_base as base

    baseline_rss = _rss_kib()
    source = Path(source)
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    archive = work_root / f"{mode}.cmpct"
    started = time.perf_counter()

    if mode == "r24":
        stats = dict(base._locality_bounded_r24_build(source, archive))
        operation = {"archive_bytes": archive.stat().st_size, "build_stats": stats}
    elif mode == "profile":
        staging = work_root / "profile-staging"
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True, exist_ok=True)
        try:
            stats = dict(base._ORIGINAL_PREPARE_PROFILE_TREE(source, staging))
            eligible = True
            reason = None
        except base.ProfileNotEligible as exc:
            stats = {}
            eligible = False
            reason = str(exc)
        operation = {
            "profile_eligible": eligible,
            "profile_not_eligible_reason": reason,
            "profile_stats": stats,
        }
    elif mode == "full":
        stats = dict(product.build(source, archive))
        operation = {"archive_bytes": archive.stat().st_size, "build_stats": stats}
    else:  # pragma: no cover - argparse constrains this.
        raise ValueError(mode)

    wall_s = time.perf_counter() - started
    operation_peak_rss = _rss_kib()

    # Correctness happens after the operation RSS/timer snapshots.
    source_tree = product.treehash(source)
    if mode in {"r24", "full"}:
        verified = dict(product.strong_verify(archive))
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError(f"{mode} archive failed semantic verification: {verified!r}")
        operation.update(
            {
                "archive_sha256": _sha256_file(archive),
                "verified_tree_sha256": verified.get("tree_sha256"),
            }
        )

    return {
        "mode": mode,
        "source_tree_sha256": source_tree,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline_rss,
        "operation_peak_rss_kib": operation_peak_rss,
        "incremental_peak_rss_kib": max(0, operation_peak_rss - baseline_rss),
        **operation,
    }


def _run_worker(mode: str, source: Path, work_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-mode",
            mode,
            "--source",
            str(source),
            "--work-root",
            str(work_root),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"phase-RSS worker produced no JSON for {mode}: stderr={proc.stderr!r}")
    return json.loads(lines[-1])


def _ratio(num: float, den: float) -> float | None:
    return None if den <= 0 else float(num) / float(den)


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []

    for suite, name in PERF.TARGETS:
        source = roots[(suite, name)]
        expected_tree = str(accepted[(suite, name)]["tree_sha256"])
        if GENERAL._historical_treehash(source) != expected_tree:
            raise RuntimeError(f"phase-RSS source drift for {suite}/{name}")

        repetitions = []
        # Rotate which expensive arm runs first. Every arm is still a fresh process.
        orders = (MODES, tuple(reversed(MODES)))
        for rep, order in enumerate(orders):
            measured = {}
            for mode in order:
                arm_root = work_root / "arms" / f"{suite}-{name}-r{rep}-{mode}"
                measured[mode] = _run_worker(mode, source, arm_root)
                if measured[mode]["source_tree_sha256"] != product_tree_for_source(source):
                    raise RuntimeError(f"{mode} changed source semantics for {suite}/{name}")
            for mode in ("r24", "full"):
                other = repetitions[0][mode] if repetitions else None
                if other is not None:
                    if measured[mode]["archive_sha256"] != other["archive_sha256"]:
                        raise RuntimeError(f"{mode} archive drift across RSS repetitions for {suite}/{name}")
                    if measured[mode]["archive_bytes"] != other["archive_bytes"]:
                        raise RuntimeError(f"{mode} archive-size drift across RSS repetitions for {suite}/{name}")
            repetitions.append(measured)

        med = {}
        for mode in MODES:
            med[mode] = {
                "wall_s": statistics.median(rep[mode]["wall_s"] for rep in repetitions),
                "baseline_rss_kib": statistics.median(rep[mode]["baseline_rss_kib"] for rep in repetitions),
                "operation_peak_rss_kib": statistics.median(rep[mode]["operation_peak_rss_kib"] for rep in repetitions),
                "incremental_peak_rss_kib": statistics.median(rep[mode]["incremental_peak_rss_kib"] for rep in repetitions),
            }
        full_inc = med["full"]["incremental_peak_rss_kib"]
        isolated_max = max(med["r24"]["incremental_peak_rss_kib"], med["profile"]["incremental_peak_rss_kib"])
        rows.append(
            {
                "target": f"{suite}/{name}",
                "expected_historical_tree_sha256": expected_tree,
                "repetitions": repetitions,
                "median": med,
                "full_to_r24_incremental_ratio": _ratio(full_inc, med["r24"]["incremental_peak_rss_kib"]),
                "full_to_profile_incremental_ratio": _ratio(full_inc, med["profile"]["incremental_peak_rss_kib"]),
                "full_to_max_isolated_incremental_ratio": _ratio(full_inc, isolated_max),
            }
        )

    return {
        "schema": "cmpct-v030-product-phase-rss-v1",
        "rounds": ROUNDS,
        "rows": rows,
        "contract": {
            "fresh_process_per_arm": True,
            "operation_rss_snapshot_precedes_correctness_checks": True,
            "archive_bytes_changed": False,
            "selector_changed": False,
            "scheduling_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "rss_release_threshold_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
        },
        "experiment_valid": len(rows) == len(PERF.TARGETS),
        "promotion_signal": False,
        "selector_change": False,
        "release_credit": False,
    }


def product_tree_for_source(source: Path) -> str:
    # Kept outside the timed worker; used only to ensure an arm did not mutate its source.
    from experiments import entropygraph_v030_release_product as product

    return product.treehash(source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-product-phase-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-product-phase-rss.json"))
    parser.add_argument("--worker-mode", choices=MODES)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()

    if args.worker_mode:
        if args.source is None:
            raise SystemExit("--source is required with --worker-mode")
        print(json.dumps(_worker(args.worker_mode, args.source, args.work_root), separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": [
                    {
                        "target": row["target"],
                        "median": row["median"],
                        "full_to_max_isolated_incremental_ratio": row["full_to_max_isolated_incremental_ratio"],
                    }
                    for row in result["rows"]
                ],
                "experiment_valid": result["experiment_valid"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("product phase RSS experiment invalid")


if __name__ == "__main__":
    main()
