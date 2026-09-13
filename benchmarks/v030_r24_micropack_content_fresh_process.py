from __future__ import annotations

"""Fresh-process creation economics for path-blind content-economic micro-packs.

Mission lock
============
Current-15 transfer established 8 strict wins / 7 exact ties and zero losses for
the unchanged path-blind content-economic policy.  The next falsifiable risk is
that the cheap Zstd-1 audition merely moved cost into creation.  This referee
therefore executes same-grammar independent, extension-bucket and content-
economic arms in separate fresh Python processes over identical pre-generated
source trees.

A content-economic timing regression against independent is confirmed only when
its median verified-creation time exceeds the repository same-runner envelope:
>5% *and* >3 ms.  Stored bytes, <=8x locality, reconstruction, recovery and the
admission rule are fixed.  RSS is recorded from the fresh worker process but is
diagnostic until common import/runtime state is separately attributed.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder, _arm

ROUNDS = 3
RELATIVE_REGRESSION = 0.05
ABSOLUTE_REGRESSION_S = 0.003
VARIANTS = ("independent", "extension", "content_economic")
BUILDERS = {
    "independent": SAME.NoMicroPackBuilder,
    "extension": BASE.LocalityDerivedBuilder,
    "content_economic": ContentEconomicBuilder,
}


def _worker(source: Path, work: Path, variant: str) -> dict:
    if variant not in BUILDERS:
        raise ValueError(variant)
    shutil.rmtree(work, ignore_errors=True)
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    arm = _arm(BUILDERS[variant], source, work)
    cpu = time.process_time() - cpu0
    wall = time.perf_counter() - wall0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux ru_maxrss is KiB. Hosted referee is Linux-only by workflow contract.
    return {
        "variant": variant,
        "archive_bytes": int(arm["archive_bytes"]),
        "verified_creation_cpu_s": cpu,
        "verified_creation_wall_s": wall,
        "peak_rss_kib": int(rss),
        "groups": int(arm["groups"]),
        "group_members": int(arm["group_members"]),
        "locality_pass": bool(arm["locality_pass"]),
        "max_member_amplification": float(arm["max_member_amplification"]),
        "max_decode_unit_bytes": int(arm["max_decode_unit_bytes"]),
        "strong_tree_exact": bool(arm["strong_tree_exact"]),
        "payload_exact": bool(arm["payload_exact"]),
        "tail_recovery": bool(arm["tail_recovery"]),
        "audit": arm.get("audit", {}),
    }


def _run_child(source: Path, work: Path, variant: str) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "benchmarks.v030_r24_micropack_content_fresh_process",
        "--worker",
        "--source",
        str(source),
        "--work-root",
        str(work),
        "--variant",
        variant,
    ]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    outer0 = time.perf_counter()
    cp = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    outer_wall = time.perf_counter() - outer0
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError(f"empty child output for {variant}: stderr={cp.stderr[-2000:]}")
    row = json.loads(lines[-1])
    row["fresh_process_outer_wall_s"] = outer_wall
    row["stderr_tail"] = cp.stderr[-1000:]
    return row


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(r[key]) for r in rows))


def _summarize(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("no rows")
    byte_set = {int(r["archive_bytes"]) for r in rows}
    if len(byte_set) != 1:
        raise RuntimeError(f"non-deterministic archive bytes: {sorted(byte_set)}")
    invariant_keys = ("locality_pass", "strong_tree_exact", "payload_exact", "tail_recovery")
    if not all(all(bool(r[k]) for k in invariant_keys) for r in rows):
        raise RuntimeError("fresh-process invariant failure")
    return {
        "rounds": len(rows),
        "archive_bytes": int(rows[0]["archive_bytes"]),
        "median_cpu_s": _median(rows, "verified_creation_cpu_s"),
        "median_wall_s": _median(rows, "verified_creation_wall_s"),
        "median_outer_wall_s": _median(rows, "fresh_process_outer_wall_s"),
        "median_peak_rss_kib": int(statistics.median(int(r["peak_rss_kib"]) for r in rows)),
        "max_peak_rss_kib": max(int(r["peak_rss_kib"]) for r in rows),
        "groups": int(rows[0]["groups"]),
        "group_members": int(rows[0]["group_members"]),
        "max_member_amplification": max(float(r["max_member_amplification"]) for r in rows),
        "max_decode_unit_bytes": max(int(r["max_decode_unit_bytes"]) for r in rows),
        "audition_cpu_s_median": float(statistics.median(float(r.get("audit", {}).get("audition_cpu_s", 0.0)) for r in rows)),
        "audition_wall_s_median": float(statistics.median(float(r.get("audit", {}).get("audition_wall_s", 0.0)) for r in rows)),
        "raw_rounds": rows,
    }


def _timing_debt(candidate: dict, control: dict, key: str) -> dict:
    c = float(candidate[key]); b = float(control[key])
    delta = c - b
    relative = (c / b - 1.0) if b > 0 else 0.0
    return {
        "candidate_s": c,
        "control_s": b,
        "delta_s": delta,
        "relative": relative,
        "confirmed_regression": delta > ABSOLUTE_REGRESSION_S and relative > RELATIVE_REGRESSION,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus = work_root / "corpus"
    ATTR._build_sources(corpus)
    sources = {
        "origin_developer": corpus / "01_developer_repository",
        "origin_tiny_files": corpus / "08_many_tiny_files",
    }
    result_rows = {}
    for source_name, source in sources.items():
        raw = {v: [] for v in VARIANTS}
        # Rotate order each round so runner drift cannot systematically favor one arm.
        for round_idx in range(ROUNDS):
            order = VARIANTS[round_idx:] + VARIANTS[:round_idx]
            for variant in order:
                row = _run_child(
                    source,
                    work_root / "workers" / source_name / f"r{round_idx}-{variant}",
                    variant,
                )
                row["round"] = round_idx
                raw[variant].append(row)
        arms = {variant: _summarize(rows) for variant, rows in raw.items()}
        content = arms["content_economic"]
        independent = arms["independent"]
        extension = arms["extension"]
        result_rows[source_name] = {
            "arms": arms,
            "delta_vs_independent_bytes": content["archive_bytes"] - independent["archive_bytes"],
            "delta_vs_extension_bytes": content["archive_bytes"] - extension["archive_bytes"],
            "cpu_vs_independent": _timing_debt(content, independent, "median_cpu_s"),
            "wall_vs_independent": _timing_debt(content, independent, "median_wall_s"),
            "outer_wall_vs_independent": _timing_debt(content, independent, "median_outer_wall_s"),
            "cpu_vs_extension": _timing_debt(content, extension, "median_cpu_s"),
            "wall_vs_extension": _timing_debt(content, extension, "median_wall_s"),
        }

    density_losses = [name for name, row in result_rows.items() if row["delta_vs_independent_bytes"] > 0]
    timing_debt = [
        name for name, row in result_rows.items()
        if row["cpu_vs_independent"]["confirmed_regression"] or row["wall_vs_independent"]["confirmed_regression"]
    ]
    locality_failures = [
        name for name, row in result_rows.items()
        if row["arms"]["content_economic"]["max_member_amplification"] > BASE.LOCALITY_BUDGET + 1e-9
    ]
    if density_losses or locality_failures:
        verdict = "RETIRE_CONTENT_FRESH_PROCESS"
    elif timing_debt:
        verdict = "CONTENT_FRESH_PROCESS_REHABILITATION_REQUIRED"
    else:
        verdict = "CONTENT_FRESH_PROCESS_ECONOMICS_SURVIVE"

    return {
        "schema": "cmpct-v030-r24-content-micropack-fresh-process-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "path_signal_used": False,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "rounds": ROUNDS,
        "timing_regression_confidence": {
            "relative": RELATIVE_REGRESSION,
            "absolute_s": ABSOLUTE_REGRESSION_S,
            "rule": "confirmed only when candidate slowdown exceeds both thresholds",
        },
        "rss_credit": False,
        "rss_note": "Fresh worker ru_maxrss includes common Python/import/runtime state; report diagnostics only until attributed.",
        "sources": result_rows,
        "density_losses_vs_independent": density_losses,
        "timing_debt_vs_independent": timing_debt,
        "locality_failures": locality_failures,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--variant", choices=VARIANTS)
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-content-fresh-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-content-fresh.json"))
    args = ap.parse_args()
    if args.worker:
        if args.source is None or args.variant is None:
            raise SystemExit("--worker requires --source and --variant")
        print(json.dumps(_worker(args.source, args.work_root, args.variant), sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "density_losses_vs_independent": result["density_losses_vs_independent"],
        "timing_debt_vs_independent": result["timing_debt_vs_independent"],
        "locality_failures": result["locality_failures"],
        "sources": {
            name: {
                "delta_i": row["delta_vs_independent_bytes"],
                "delta_e": row["delta_vs_extension_bytes"],
                "ind_cpu": row["arms"]["independent"]["median_cpu_s"],
                "ext_cpu": row["arms"]["extension"]["median_cpu_s"],
                "content_cpu": row["arms"]["content_economic"]["median_cpu_s"],
                "ind_wall": row["arms"]["independent"]["median_wall_s"],
                "ext_wall": row["arms"]["extension"]["median_wall_s"],
                "content_wall": row["arms"]["content_economic"]["median_wall_s"],
                "ind_rss": row["arms"]["independent"]["median_peak_rss_kib"],
                "ext_rss": row["arms"]["extension"]["median_peak_rss_kib"],
                "content_rss": row["arms"]["content_economic"]["median_peak_rss_kib"],
                "content_decode": row["arms"]["content_economic"]["max_decode_unit_bytes"],
            }
            for name, row in result["sources"].items()
        },
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
