from __future__ import annotations

"""Same-run shipping/control/consumed-candidate eviction RSS oracle for r24 streaming finalization v3."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_r24_streaming_finalize_rss_oracle as V1
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_r24_streaming_finalize as V2
from experiments import entropygraph_v030_r24_streaming_finalize_v3 as V3

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-v030-r24-streaming-finalize-rss-v3"
TARGETS = V1.TARGETS
ROUNDS = 2
VARIANTS = ("shipping", "control", "evict")
OPERATIONS = ("r24", "full")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _owner_receipt() -> dict:
    v2_path = Path(V2.__file__).resolve()
    v3_path = Path(V3.__file__).resolve()
    if V3.CONTROL_CLASS is not V2.StreamingFinalizeBuilder:
        raise RuntimeError("v3 control semantic-owner drift")
    if not issubclass(V3.EVICT_CLASS, V2.StreamingFinalizeBuilder):
        raise RuntimeError("v3 eviction owner no longer subclasses v2 semantic owner")
    if int(V3.SPOOL_MEMORY_BYTES) != 1024 * 1024 or int(V3.MAX_IN_FLIGHT_FACTOR) != 1:
        raise RuntimeError("v3 inherited spool/in-flight contract drift")
    return {
        "control_class": f"{V3.CONTROL_CLASS.__module__}.{V3.CONTROL_CLASS.__name__}",
        "evict_class": f"{V3.EVICT_CLASS.__module__}.{V3.EVICT_CLASS.__name__}",
        "v2_module": str(v2_path.relative_to(ROOT)),
        "v2_module_sha256": _sha256_file(v2_path),
        "v3_module": str(v3_path.relative_to(ROOT)),
        "v3_module_sha256": _sha256_file(v3_path),
        "spool_memory_bytes": int(V3.SPOOL_MEMORY_BYTES),
        "max_in_flight_factor": int(V3.MAX_IN_FLIGHT_FACTOR),
        "single_intervention": "evict consumed Candidate shell from Builder.cands after encode completion",
    }


def _worker(variant: str, operation: str, source: Path, work_root: Path) -> dict:
    if variant == "shipping":
        row = V1._worker("shipping", operation, source, work_root)
    else:
        V1.StreamingFinalizeBuilder = V3.CONTROL_CLASS if variant == "control" else V3.EVICT_CLASS
        row = V1._worker("streaming", operation, source, work_root)
    row = dict(row)
    row["variant"] = variant
    row["semantic_owner"] = _owner_receipt() if variant != "shipping" else None
    return row


def _run_worker(variant: str, operation: str, source: Path, work_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-variant",
            variant,
            "--worker-operation",
            operation,
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
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def _ratio(num: float, den: float) -> float | None:
    return None if den <= 0 else num / den


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    accepted = GENERAL._accepted_v029_rows()
    rows = []

    orders = (
        ("shipping", "control", "evict"),
        ("evict", "control", "shipping"),
    )
    for suite, name in TARGETS:
        source = roots[(suite, name)]
        expected = str(accepted[(suite, name)]["tree_sha256"])
        if GENERAL._historical_treehash(source) != expected:
            raise RuntimeError(f"source drift for {suite}/{name}")

        reps = []
        for rep, order in enumerate(orders):
            measured = {}
            for variant in order:
                measured[variant] = {}
                for operation in OPERATIONS:
                    measured[variant][operation] = _run_worker(
                        variant,
                        operation,
                        source,
                        work_root / "arms" / f"{suite}-{name}-r{rep}-{variant}-{operation}",
                    )
            for operation in OPERATIONS:
                identity = (
                    measured["shipping"][operation]["archive_bytes"],
                    measured["shipping"][operation]["archive_sha256"],
                    measured["shipping"][operation]["tree_sha256"],
                )
                for variant in ("control", "evict"):
                    candidate = measured[variant][operation]
                    if identity != (candidate["archive_bytes"], candidate["archive_sha256"], candidate["tree_sha256"]):
                        raise RuntimeError(f"byte/tree drift for {suite}/{name}/{operation}/{variant}")
            reps.append(measured)

        med = {}
        for variant in VARIANTS:
            med[variant] = {}
            for operation in OPERATIONS:
                med[variant][operation] = {
                    "wall_s": statistics.median(rep[variant][operation]["wall_s"] for rep in reps),
                    "incremental_peak_rss_kib": statistics.median(
                        rep[variant][operation]["incremental_peak_rss_kib"] for rep in reps
                    ),
                    "operation_peak_rss_kib": statistics.median(
                        rep[variant][operation]["operation_peak_rss_kib"] for rep in reps
                    ),
                }

        rows.append(
            {
                "target": f"{suite}/{name}",
                "repetitions": reps,
                "median": med,
                "evict_full_rss_to_shipping": _ratio(
                    med["evict"]["full"]["incremental_peak_rss_kib"],
                    med["shipping"]["full"]["incremental_peak_rss_kib"],
                ),
                "evict_r24_rss_to_shipping": _ratio(
                    med["evict"]["r24"]["incremental_peak_rss_kib"],
                    med["shipping"]["r24"]["incremental_peak_rss_kib"],
                ),
                "evict_full_wall_to_shipping": _ratio(
                    med["evict"]["full"]["wall_s"], med["shipping"]["full"]["wall_s"]
                ),
                "evict_full_rss_to_control": _ratio(
                    med["evict"]["full"]["incremental_peak_rss_kib"],
                    med["control"]["full"]["incremental_peak_rss_kib"],
                ),
                "evict_full_wall_to_control": _ratio(
                    med["evict"]["full"]["wall_s"], med["control"]["full"]["wall_s"]
                ),
            }
        )

    shifted = next(row for row in rows if row["target"].endswith("/01_shifted_versions"))
    exact = all(
        rep["shipping"][operation]["archive_sha256"]
        == rep[variant][operation]["archive_sha256"]
        for row in rows
        for rep in row["repetitions"]
        for operation in OPERATIONS
        for variant in ("control", "evict")
    )
    wall_ok = all((row["evict_full_wall_to_shipping"] or 99) <= 1.05 for row in rows)
    promotion_signal = bool(
        exact
        and wall_ok
        and shifted["evict_full_rss_to_shipping"] is not None
        and shifted["evict_full_rss_to_shipping"] <= 0.75
        and shifted["evict_r24_rss_to_shipping"] is not None
        and shifted["evict_r24_rss_to_shipping"] <= 0.50
    )

    shell_ratio = shifted["evict_full_rss_to_control"]
    shell_wall = shifted["evict_full_wall_to_control"]
    if shell_ratio is None or shell_wall is None:
        shell_decision = "INVALID_RATIO"
    elif shell_wall > 1.05:
        shell_decision = "CANDIDATE_SHELL_EVICTION_WALL_REGRESSION"
    elif shell_ratio <= 0.98:
        shell_decision = "CANDIDATE_SHELL_RETENTION_SUPPORTED"
    elif shell_ratio >= 0.99:
        shell_decision = "CANDIDATE_SHELL_RETENTION_RETIRED_AS_MATERIAL_OWNER"
    else:
        shell_decision = "AMBIGUOUS_SMALL_EFFECT"

    return {
        "schema": SCHEMA,
        "rounds": ROUNDS,
        "targets": [f"{suite}/{name}" for suite, name in TARGETS],
        "semantic_owner": _owner_receipt(),
        "rows": rows,
        "contract": {
            "archive_bytes_changed": False,
            "r24_policy_changed": False,
            "selector_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "rss_release_threshold_changed": False,
            "bounded_encode_in_flight": True,
            "spool_memory_bytes": int(V3.SPOOL_MEMORY_BYTES),
            "max_in_flight_factor": int(V3.MAX_IN_FLIGHT_FACTOR),
            "promotion_shifted_full_rss_max_ratio": 0.75,
            "promotion_shifted_r24_rss_max_ratio": 0.50,
            "maximum_full_wall_regression_ratio": 1.05,
            "shell_support_evict_to_control_max_ratio": 0.98,
            "shell_retire_evict_to_control_min_ratio": 0.99,
        },
        "experiment_valid": exact,
        "promotion_signal": promotion_signal,
        "shell_decision": shell_decision,
        "selector_change": False,
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss-v3-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-streaming-rss-v3.json"))
    parser.add_argument("--worker-variant", choices=VARIANTS)
    parser.add_argument("--worker-operation", choices=OPERATIONS)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()

    if args.worker_variant:
        if args.source is None or args.worker_operation is None:
            raise SystemExit("worker requires --source and --worker-operation")
        print(json.dumps(_worker(args.worker_variant, args.worker_operation, args.source, args.work_root), separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "semantic_owner": result["semantic_owner"],
                "rows": [
                    {
                        "target": row["target"],
                        "evict_full_rss_to_shipping": row["evict_full_rss_to_shipping"],
                        "evict_r24_rss_to_shipping": row["evict_r24_rss_to_shipping"],
                        "evict_full_wall_to_shipping": row["evict_full_wall_to_shipping"],
                        "evict_full_rss_to_control": row["evict_full_rss_to_control"],
                        "evict_full_wall_to_control": row["evict_full_wall_to_control"],
                    }
                    for row in result["rows"]
                ],
                "shell_decision": result["shell_decision"],
                "promotion_signal": result["promotion_signal"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("streaming-finalize v3 experiment invalid")


if __name__ == "__main__":
    main()
