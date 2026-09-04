from __future__ import annotations

"""Controlled selective-member evidence for the canonical CMPCT v0.30 product API.

Each preregistered workload is built through the final canonical product facade, its public ``list_members``
operation selects the largest regular user-visible member, and its public ``read_member`` operation is timed in
a fresh process against full extraction of the same archive. Both canonical r24 fallback and revision-25
profiles are measured; neither is relabeled not-applicable.

Locality is normative only when it is observed from the actual member operation. Missing operation accounting is
a hard error. Build/archive declarations may corroborate the measurement, but they never replace it and never
default to ``0.0``.

There is intentionally no invented selective/full-extract latency threshold. Exact member integrity and <=8x
decoded-context amplification are frozen gates; wall-time and RSS ratios remain raw diagnostic evidence until a
numeric speed threshold is preregistered before measurement.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import statistics
import subprocess
import sys

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_perf_worker_canonical.py"
OPERATION_ORDER = (("member", "extract"), ("extract", "member"))
MAX_MEMBER_READ_AMP = GENERAL.MAX_MEMBER_READ_AMP


def _run_worker(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(WORKER), *args],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"selective-read worker produced no JSON: stderr={completed.stderr!r}")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"selective-read worker final line was not JSON: {lines[-1]!r}; stderr={completed.stderr!r}"
        ) from exc


def _tree_logical_bytes(source: Path) -> int:
    return sum(path.stat().st_size for path in source.rglob("*") if path.is_file() and not path.is_symlink())


def _member_target(source: Path, members: list[dict]) -> tuple[str, int, str]:
    candidates = []
    for row in members:
        if row.get("kind") != "file":
            continue
        rel = row.get("path")
        if not isinstance(rel, str) or not rel or rel.startswith(".__cmpct_r25_internal__/"):
            continue
        path = source / rel
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(mode) or path.is_symlink():
            continue
        size = int(row.get("size", -1))
        if size != path.stat().st_size:
            raise RuntimeError(f"canonical product member-size declaration drift: {rel}: {size} != {path.stat().st_size}")
        candidates.append((rel, size, path))
    if not candidates:
        raise RuntimeError("canonical product archive exposes no regular user-visible member")
    rel, size, target = min(candidates, key=lambda item: (-item[1], item[0]))
    raw = target.read_bytes()
    return rel, size, hashlib.sha256(raw).hexdigest()


def _observed_amp(stats: dict) -> float:
    if stats.get("locality_observed_from_actual_product_operation") is not True:
        raise RuntimeError("member operation did not prove observed locality accounting")
    value = stats.get("max_member_read_amplification")
    if value is None:
        raise RuntimeError("member operation omitted max_member_read_amplification")
    value = float(value)
    if value <= 0:
        raise RuntimeError(f"member operation returned invalid locality amplification: {value}")
    return value


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator) / max(float(denominator), 1e-9)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root)
    rows = []

    for suite, name in PERF.TARGETS:
        source = roots[(suite, name)]
        historical_tree = accepted[(suite, name)]["tree_sha256"]
        logical_tree_bytes = _tree_logical_bytes(source)
        archive = work_root / "archives" / f"{suite}-{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)

        packed = _run_worker(
            "--engine", "v030",
            "--op", "pack",
            "--source", str(source),
            "--archive", str(archive),
        )
        expected_product_tree = packed.get("tree_sha256")
        if not isinstance(expected_product_tree, str) or len(expected_product_tree) != 64:
            raise RuntimeError(f"canonical pack omitted product user-tree identity for {suite}/{name}")
        verified = _run_worker("--engine", "v030", "--op", "verify", "--archive", str(archive))
        if verified.get("tree_sha256") != expected_product_tree:
            raise RuntimeError(
                f"canonical selective-read product-tree identity mismatch for {suite}/{name}: "
                f"{verified.get('tree_sha256')} != {expected_product_tree}"
            )

        listed = _run_worker("--engine", "v030", "--op", "members", "--archive", str(archive))
        member, expected_member_bytes, expected_member_sha = _member_target(source, listed.get("members") or [])
        build_stats = packed.get("build_stats") or {}
        row = {
            "suite": suite,
            "name": name,
            "historical_tree_sha256": historical_tree,
            "product_tree_sha256": expected_product_tree,
            "archive_bytes": int(packed["archive_bytes"]),
            "selected": build_stats.get("selected"),
            "format_revision": build_stats.get("format_revision"),
            "format_profile": build_stats.get("format_profile"),
            "member": member,
            "member_bytes": expected_member_bytes,
            "member_sha256": expected_member_sha,
            "logical_tree_bytes": logical_tree_bytes,
            "measured": True,
        }

        repetitions = []
        for rep, order in enumerate(OPERATION_ORDER):
            measurements = {}
            for operation in order:
                if operation == "member":
                    result = _run_worker(
                        "--engine", "v030",
                        "--op", "member",
                        "--archive", str(archive),
                        "--member", member,
                    )
                    if int(result["member_bytes"]) != expected_member_bytes or result["member_sha256"] != expected_member_sha:
                        raise RuntimeError(f"selective member identity mismatch for {suite}/{name}:{member}")
                    stats = result.get("member_stats")
                    if not isinstance(stats, dict):
                        raise RuntimeError("canonical member operation omitted stats object")
                    amp = _observed_amp(stats)
                    measurements["member"] = {
                        "wall_s": float(result["wall_s"]),
                        "peak_rss_kib": int(result["peak_rss_kib"]),
                        "member_bytes": int(result["member_bytes"]),
                        "member_sha256": result["member_sha256"],
                        "observed_member_read_amplification": amp,
                        "stats": stats,
                    }
                else:
                    destination = work_root / "extract" / f"{suite}-{name}-r{rep}"
                    result = _run_worker(
                        "--engine", "v030",
                        "--op", "extract",
                        "--archive", str(archive),
                        "--destination", str(destination),
                    )
                    if result.get("tree_sha256") != expected_product_tree:
                        raise RuntimeError(f"full product extraction identity mismatch for {suite}/{name}")
                    measurements["extract"] = {
                        "wall_s": float(result["wall_s"]),
                        "peak_rss_kib": int(result["peak_rss_kib"]),
                        "tree_sha256": result["tree_sha256"],
                    }
            member_measure = measurements["member"]
            extract_measure = measurements["extract"]
            repetitions.append(
                {
                    "rep": rep,
                    "execution_order": list(order),
                    "member": member_measure,
                    "full_extract": extract_measure,
                    "member_vs_full_extract_wall_ratio": _ratio(member_measure["wall_s"], extract_measure["wall_s"]),
                    "member_vs_full_extract_peak_rss_ratio": _ratio(
                        member_measure["peak_rss_kib"], extract_measure["peak_rss_kib"]
                    ),
                }
            )

        observed_amps = [item["member"]["observed_member_read_amplification"] for item in repetitions]
        row.update(
            {
                "repetitions": repetitions,
                "max_observed_member_read_amplification": max(observed_amps),
                "median_member_wall_s": statistics.median(item["member"]["wall_s"] for item in repetitions),
                "median_full_extract_wall_s": statistics.median(item["full_extract"]["wall_s"] for item in repetitions),
                "median_member_vs_full_extract_wall_ratio": statistics.median(
                    item["member_vs_full_extract_wall_ratio"] for item in repetitions
                ),
                "max_member_peak_rss_kib": max(item["member"]["peak_rss_kib"] for item in repetitions),
                "max_full_extract_peak_rss_kib": max(item["full_extract"]["peak_rss_kib"] for item in repetitions),
                "max_member_vs_full_extract_peak_rss_ratio": max(
                    item["member_vs_full_extract_peak_rss_ratio"] for item in repetitions
                ),
            }
        )
        rows.append(row)

    gate = {
        "exact_target_count": len(rows) == len(PERF.TARGETS),
        "all_canonical_product_profiles_measured": all(row["measured"] for row in rows),
        "all_targets_are_regular_user_visible_members": all(
            row["member"] and not row["member"].startswith(".__cmpct_r25_internal__/") for row in rows
        ),
        "all_members_exact": all(
            all(
                rep["member"]["member_bytes"] == row["member_bytes"]
                and rep["member"]["member_sha256"] == row["member_sha256"]
                for rep in row["repetitions"]
            )
            for row in rows
        ),
        "all_locality_is_operation_observed": all(
            all(rep["member"]["stats"].get("locality_observed_from_actual_product_operation") is True for rep in row["repetitions"])
            for row in rows
        ),
        "all_rows_within_locality_ceiling": all(
            row["max_observed_member_read_amplification"] <= MAX_MEMBER_READ_AMP for row in rows
        ),
        "all_reads_are_strict_member_scope": all(row["member_bytes"] < row["logical_tree_bytes"] for row in rows),
        "balanced_fresh_process_repetitions": all(
            [rep["execution_order"] for rep in row["repetitions"]] == [list(order) for order in OPERATION_ORDER]
            for row in rows
        ),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-canonical-selective-read-v2",
        "engine": "experiments/entropygraph_v030_canonical.py",
        "reader": "canonical-product-read_member-with-operation-observation",
        "provenance": {
            "source_sha": os.environ.get("GITHUB_SHA") or os.environ.get("CMPCT_SOURCE_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "python": sys.version,
            "platform": platform.platform(),
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
        },
        "contract": {
            "targets": [list(item) for item in PERF.TARGETS],
            "operation_order": [list(item) for item in OPERATION_ORDER],
            "target_selection": "largest public list_members row with kind=file and regular non-symlink source path",
            "maximum_member_read_amplification": MAX_MEMBER_READ_AMP,
            "locality_source": "observed decode context from the actual canonical read_member operation",
            "missing_locality_behavior": "hard failure; no numeric default",
            "profile_coverage": "measure whichever canonical product profile build selects, including genuine r24 fallback",
            "timing_semantics": "fresh-process balanced member-vs-full-extract same-archive diagnostic",
            "timing_gate": (
                "no numeric selective wall/RSS ratio was preregistered; integrity and <=8x locality are normative, "
                "while raw wall/RSS comparisons are preserved without post-hoc threshold invention"
            ),
        },
        "rows": rows,
        "totals": {
            "targets": len(rows),
            "measured_product_rows": len(rows),
            "max_observed_member_read_amplification": max(row["max_observed_member_read_amplification"] for row in rows),
            "median_member_vs_full_extract_wall_ratio": statistics.median(
                row["median_member_vs_full_extract_wall_ratio"] for row in rows
            ),
            "max_member_vs_full_extract_peak_rss_ratio": max(
                row["max_member_vs_full_extract_peak_rss_ratio"] for row in rows
            ),
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-selective-read-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-selective-read.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 selective-read integrity/locality gate failed")


if __name__ == "__main__":
    main()
