from __future__ import annotations

"""Exact-byte combined RSS frontier for Shifted: streaming r24 + PrefixGraph worker caps.

Two independent diagnostics found different owners of the Shifted peak: the byte-identical
r24 streaming finalizer removes a large in-memory physical-payload materialization, while
PrefixGraph's exact 1/2/4-worker frontier shows that concurrent anchor auditions account
for most isolated PrefixGraph RSS. Neither isolated change retired the full-product RSS
red. This oracle composes them without changing candidate bytes, admission, tie law,
grammar, integrity, locality, recovery, or release thresholds.

The canonical profile clone intentionally keeps the base PrefixGraph semantic owner for
reader grammar. For this ephemeral scheduling A/B only, the release-candidate builder is
redirected to the already-proven bounded parallel wrapper after binding that wrapper's
base module to canonical magic/tail bytes. Thus worker count changes construction schedule
only; the ordinary canonical reader remains an independent exact-byte verifier.

Every arm runs in a fresh process, must publish the exact same complete archive/tree, and
is judged against the existing <=0.75 full-RSS / <=1.05 wall-time promotion boundary.
The experiment is research-only even when it emits a promotion signal.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_r24_streaming_finalize_rss_oracle as STREAM

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 2
ARMS = (
    ("shipping", "shipping", None),
    ("streaming-w4", "streaming", 4),
    ("streaming-w3", "streaming", 3),
    ("streaming-w2", "streaming", 2),
    ("streaming-w1", "streaming", 1),
)


def _worker(variant: str, workers: int | None, source: Path, work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product

    if workers is not None:
        if workers not in (1, 2, 3, 4):
            raise ValueError(workers)
        from experiments import entropygraph_v030_prefixgraph_parallel as pg_parallel

        # Fresh subprocess only: make the bounded wrapper emit the canonical PrefixGraph
        # profile while retaining the canonical private base module as the independent
        # reader/verifier. Exact final archive identity below must prove this is schedule-only.
        pg_parallel.BASE.MAGIC = product.C.PG.MAGIC
        pg_parallel.BASE.TAIL = product.C.PG.TAIL
        pg_parallel.MAGIC = product.C.PG.MAGIC
        pg_parallel.TAIL = product.C.PG.TAIL
        pg_parallel.MAX_ANCHOR_WORKERS = workers
        product.C.RC.PG = pg_parallel

    result = STREAM._worker(variant, "full", source, work_root)
    result["prefixgraph_worker_cap"] = workers
    result["r24_finalize"] = variant
    return result


def _run_worker(variant: str, workers: int | None, source: Path, work_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    argv = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker-variant",
        variant,
        "--source",
        str(source),
        "--work-root",
        str(work_root),
    ]
    if workers is not None:
        argv.extend(("--worker-count", str(workers)))
    proc = subprocess.run(argv, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def _ratio(num: float, den: float) -> float | None:
    return None if den <= 0 else num / den


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]
    accepted = GENERAL._accepted_v029_rows()[TARGET]
    expected_tree = str(accepted["tree_sha256"])
    if GENERAL._historical_treehash(source) != expected_tree:
        raise RuntimeError("Shifted source drift")

    rounds = []
    arm_names = [row[0] for row in ARMS]
    orders = (arm_names, list(reversed(arm_names)))
    arm_by_name = {name: (variant, workers) for name, variant, workers in ARMS}
    for rep, order in enumerate(orders):
        measured = {}
        for name in order:
            variant, workers = arm_by_name[name]
            measured[name] = _run_worker(
                variant,
                workers,
                source,
                work_root / "arms" / f"r{rep}-{name}",
            )
        identities = {
            (row["archive_bytes"], row["archive_sha256"], row["tree_sha256"])
            for row in measured.values()
        }
        if len(identities) != 1:
            raise RuntimeError(f"combined frontier changed complete archive identity: {identities!r}")
        rounds.append({"round": rep, "order": order, "measurements": measured})

    summary = {}
    for name in arm_names:
        summary[name] = {
            "median_wall_s": statistics.median(r["measurements"][name]["wall_s"] for r in rounds),
            "median_incremental_peak_rss_kib": statistics.median(
                r["measurements"][name]["incremental_peak_rss_kib"] for r in rounds
            ),
            "archive_bytes": rounds[0]["measurements"][name]["archive_bytes"],
            "archive_sha256": rounds[0]["measurements"][name]["archive_sha256"],
        }
    baseline = summary["shipping"]
    for name, row in summary.items():
        row["wall_ratio_vs_shipping"] = _ratio(row["median_wall_s"], baseline["median_wall_s"])
        row["rss_ratio_vs_shipping"] = _ratio(
            row["median_incremental_peak_rss_kib"], baseline["median_incremental_peak_rss_kib"]
        )

    eligible = [
        name
        for name in arm_names
        if name != "shipping"
        and (summary[name]["rss_ratio_vs_shipping"] or 99) <= 0.75
        and (summary[name]["wall_ratio_vs_shipping"] or 99) <= 1.05
    ]
    promotion_arm = min(
        eligible,
        key=lambda name: (
            summary[name]["rss_ratio_vs_shipping"],
            summary[name]["wall_ratio_vs_shipping"],
            name,
        ),
        default=None,
    )
    exact = len({row["archive_sha256"] for row in summary.values()}) == 1
    return {
        "schema": "cmpct-v030-shifted-streaming-prefix-workers-v2",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "rounds": rounds,
        "summary": summary,
        "contract": {
            "archive_bytes_changed": False,
            "candidate_set_changed": False,
            "selector_changed": False,
            "tie_law_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "recovery_changed": False,
            "rss_threshold_changed": False,
            "promotion_full_rss_max_ratio": 0.75,
            "maximum_full_wall_regression_ratio": 1.05,
            "r24_streaming_finalize": "byte-identical bounded spool",
            "prefixgraph_change": "ephemeral canonical-profile bounded-wrapper scheduler only",
            "shipping_arm_unchanged": True,
        },
        "exact_archive_identity_all_arms": exact,
        "experiment_valid": exact,
        "promotion_signal": promotion_arm is not None,
        "promotion_arm": promotion_arm,
        "release_credit": False,
        "claim_boundary": "Combined scheduling/materialization research A/B only; a positive arm requires separate productization and all exact-candidate release authorities.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-streaming-prefix-workers-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-streaming-prefix-workers.json"))
    p.add_argument("--worker-variant", choices=("shipping", "streaming"))
    p.add_argument("--worker-count", type=int)
    p.add_argument("--source", type=Path)
    args = p.parse_args()
    if args.worker_variant:
        if args.source is None:
            raise SystemExit("worker requires --source")
        if args.worker_variant == "streaming" and args.worker_count is None:
            raise SystemExit("streaming worker requires --worker-count")
        print(json.dumps(_worker(args.worker_variant, args.worker_count, args.source, args.work_root), separators=(",", ":"), default=str))
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "promotion_signal": result["promotion_signal"], "promotion_arm": result["promotion_arm"]}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("combined Shifted frontier invalid")


if __name__ == "__main__":
    main()
