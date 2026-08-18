from __future__ import annotations

"""Controlled selective-member evidence for the canonical CMPCT v0.30 release reader.

The general runtime gate already compares v0.30 with accepted v0.29 for create, full extract and peak RSS.  This
companion harness closes the remaining release-evidence surface: the promoted bounded member reader is timed in
a fresh process against a fresh-process full extraction of the *same canonical archive* and the exact same
member bytes.  The two operation orders are balanced to reduce hosted-runner ordering bias.

There is intentionally no invented selective-read latency ratio threshold.  The frozen v0.30 policy specifies
<=8x decoded-context locality, exact member integrity and controlled timing/RSS measurement, but it does not
pre-register a numeric selective/full-extract wall-clock ratio.  This harness therefore gates the normative
integrity/locality contract and preserves wall/RSS ratios as raw diagnostic evidence instead of moving a goalpost
after seeing the measurements.

Footnote: byte-identical v0.29 fallbacks are not silently converted into full extraction and called "selective".
The promoted member-reader surface raises for inherited representations, so those rows are retained as explicit
not-applicable evidence while new r25 representations are measured through the real bounded read path.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
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
    return sum(path.stat().st_size for path in source.rglob("*") if path.is_file())


def _member_target(source: Path) -> tuple[str, int, str]:
    files = sorted((path for path in source.rglob("*") if path.is_file()), key=lambda path: path.relative_to(source).as_posix())
    if not files:
        raise RuntimeError("selective-read workload has no regular files")
    # A largest-member target avoids manufacturing an easy tiny-read win.  Lexicographic tie-breaking keeps the
    # target deterministic across platforms and runners.
    target = min(files, key=lambda path: (-path.stat().st_size, path.relative_to(source).as_posix()))
    raw = target.read_bytes()
    return target.relative_to(source).as_posix(), len(raw), hashlib.sha256(raw).hexdigest()


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
        expected_tree = accepted[(suite, name)]["tree_sha256"]
        member, expected_member_bytes, expected_member_sha = _member_target(source)
        logical_tree_bytes = _tree_logical_bytes(source)
        archive = work_root / "archives" / f"{suite}-{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)

        packed = _run_worker(
            "--engine", "v030",
            "--op", "pack",
            "--source", str(source),
            "--archive", str(archive),
        )
        verified = _run_worker("--engine", "v030", "--op", "verify", "--archive", str(archive))
        if packed["tree_sha256"] != expected_tree or verified["tree_sha256"] != expected_tree:
            raise RuntimeError(f"canonical selective-read archive identity mismatch for {suite}/{name}")

        build_stats = packed.get("build_stats") or {}
        selected = str(build_stats.get("selected"))
        amp = float(build_stats.get("max_selected_member_read_amplification", 0.0))
        new_representation = selected in {"g04-overlay", "prefixgraph"}
        row = {
            "suite": suite,
            "name": name,
            "tree_sha256": expected_tree,
            "archive_bytes": int(packed["archive_bytes"]),
            "selected": selected,
            "format_revision": int(build_stats.get("format_revision", 24)),
            "format_profile": build_stats.get("format_profile"),
            "max_selected_member_read_amplification": amp,
            "member": member,
            "member_bytes": expected_member_bytes,
            "member_sha256": expected_member_sha,
            "logical_tree_bytes": logical_tree_bytes,
            "new_representation": new_representation,
        }

        if not new_representation:
            row.update(
                {
                    "measured": False,
                    "reason": "byte-identical-v029-fallback-has-no-promoted-v030-member-reader-operation",
                    "repetitions": [],
                }
            )
            rows.append(row)
            continue

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
                    measurements["member"] = {
                        "wall_s": float(result["wall_s"]),
                        "peak_rss_kib": int(result["peak_rss_kib"]),
                        "member_bytes": int(result["member_bytes"]),
                        "member_sha256": result["member_sha256"],
                        "stats": result.get("member_stats") or {},
                    }
                else:
                    destination = work_root / "extract" / f"{suite}-{name}-r{rep}"
                    result = _run_worker(
                        "--engine", "v030",
                        "--op", "extract",
                        "--archive", str(archive),
                        "--destination", str(destination),
                    )
                    if result["tree_sha256"] != expected_tree:
                        raise RuntimeError(f"full extraction identity mismatch for {suite}/{name}")
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

        row.update(
            {
                "measured": True,
                "reason": None,
                "repetitions": repetitions,
                "median_member_wall_s": statistics.median(item["member"]["wall_s"] for item in repetitions),
                "median_full_extract_wall_s": statistics.median(
                    item["full_extract"]["wall_s"] for item in repetitions
                ),
                "median_member_vs_full_extract_wall_ratio": statistics.median(
                    item["member_vs_full_extract_wall_ratio"] for item in repetitions
                ),
                "max_member_peak_rss_kib": max(item["member"]["peak_rss_kib"] for item in repetitions),
                "max_full_extract_peak_rss_kib": max(
                    item["full_extract"]["peak_rss_kib"] for item in repetitions
                ),
                "max_member_vs_full_extract_peak_rss_ratio": max(
                    item["member_vs_full_extract_peak_rss_ratio"] for item in repetitions
                ),
            }
        )
        rows.append(row)

    measured = [row for row in rows if row["measured"]]
    gate = {
        "exact_target_count": len(rows) == len(PERF.TARGETS),
        "new_representation_coverage": len(measured) >= 1,
        "all_measured_members_exact": all(
            all(
                rep["member"]["member_bytes"] == row["member_bytes"]
                and rep["member"]["member_sha256"] == row["member_sha256"]
                for rep in row["repetitions"]
            )
            for row in measured
        ),
        "all_measured_rows_within_locality_ceiling": all(
            row["max_selected_member_read_amplification"] <= MAX_MEMBER_READ_AMP for row in measured
        ),
        "all_measured_reads_are_strict_member_scope": all(
            row["member_bytes"] < row["logical_tree_bytes"] for row in measured
        ),
        "balanced_fresh_process_repetitions": all(
            [rep["execution_order"] for rep in row["repetitions"]] == [list(order) for order in OPERATION_ORDER]
            for row in measured
        ),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-canonical-selective-read-v1",
        "engine": "experiments/entropygraph_v030_canonical.py",
        "reader": "experiments/entropygraph_v030_member_reader.py",
        "release_facade": "cmpct-v030-r25-v1",
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
            "target_selection": "largest logical member; lexicographic tie-break",
            "maximum_member_read_amplification": MAX_MEMBER_READ_AMP,
            "timing_semantics": "fresh-process balanced member-vs-full-extract same-archive diagnostic",
            "timing_gate": (
                "no numeric selective wall/RSS ratio was preregistered; integrity and <=8x locality are normative, "
                "while raw wall/RSS comparisons are preserved without post-hoc threshold invention"
            ),
            "inherited_fallback_semantics": "explicit not-applicable; never relabeled full extraction as selective read",
        },
        "rows": rows,
        "totals": {
            "targets": len(rows),
            "measured_new_representation_rows": len(measured),
            "median_member_vs_full_extract_wall_ratio": (
                statistics.median(row["median_member_vs_full_extract_wall_ratio"] for row in measured)
                if measured
                else None
            ),
            "max_member_vs_full_extract_peak_rss_ratio": (
                max(row["max_member_vs_full_extract_peak_rss_ratio"] for row in measured) if measured else None
            ),
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-canonical-selective-read-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-canonical-selective-read.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 selective-read integrity/locality gate failed")


if __name__ == "__main__":
    main()
