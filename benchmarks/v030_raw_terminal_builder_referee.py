from __future__ import annotations

"""H-EFFORT-6: byte-identity and fresh-process performance court for EG09 RAW terminal."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_current15_stable_corpus as CORPUS

BASELINE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
CANDIDATE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v9"
EXPECTED_NAMES = (
    "01_developer_repository",
    "02_office_workspace",
    "03_media_library",
    "04_analytics_and_database",
    "05_logs_and_telemetry",
    "06_incremental_backups",
    "07_incompressible_and_encrypted_like",
    "08_many_tiny_files",
    "09_ml_artifacts",
    "10_large_mixed_binary",
)
REPS = 3


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _child(module_name: str, source: Path, archive: Path) -> dict:
    import importlib
    module = importlib.import_module(module_name)
    result = module.build(source, archive)
    return {
        "module": module_name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "total_build_cpu_s": float(result["total_build_cpu_s"]),
        "total_build_wall_s": float(result["total_build_wall_s"]),
        "process_peak_rss_kib": int(result["process_peak_rss_kib"]),
        "verified": result["verified"],
        "locality": result["locality"],
        "adaptive_effort": result["adaptive_effort"],
    }


def _run_fresh(module_name: str, source: Path, archive: Path, result_path: Path) -> dict:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--module",
        module_name,
        "--source",
        str(source),
        "--archive",
        str(archive),
        "--child-out",
        str(result_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode:
        raise RuntimeError(
            f"child failed module={module_name} rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return json.loads(result_path.read_text())


def _semantic_identity(base: dict, cand: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if base["archive_bytes"] != cand["archive_bytes"]:
        errors.append("archive byte length differs")
    if base["archive_sha256"] != cand["archive_sha256"]:
        errors.append("archive SHA-256 differs")
    for key in ("max_decode_unit_bytes", "max_member_read_amplification", "member_count"):
        if base["locality"].get(key) != cand["locality"].get(key):
            errors.append(f"locality field differs: {key}")
    if not base["verified"].get("ok") or not cand["verified"].get("ok"):
        errors.append("strong verification failed")

    base_rows = {int(row["index"]): row for row in base["adaptive_effort"]["packs"]}
    cand_rows = {int(row["index"]): row for row in cand["adaptive_effort"]["packs"]}
    if base_rows.keys() != cand_rows.keys():
        errors.append("pack index set differs")
    else:
        for index in base_rows:
            b = base_rows[index]; c = cand_rows[index]
            if c.get("raw_terminal"):
                if int(c["current_codec"]) != 0 or c.get("hot_stream_root") or c.get("tried"):
                    errors.append(f"invalid RAW terminal execution at pack {index}")
            else:
                for key in (
                    "hot_stream_root", "raw_sha256", "current_codec", "current_payload_bytes",
                    "selected_codec", "selected_payload_bytes", "selected_level", "saved_bytes", "tried",
                ):
                    if b.get(key) != c.get(key):
                        errors.append(f"non-RAW inherited ladder drift pack={index} field={key}")
                        break
    return not errors, errors


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def _parent(out_path: Path, work_root: Path) -> dict:
    corpus_root = work_root / "corpus"
    manifest = CORPUS.build(corpus_root)
    by = {item["name"]: item for item in manifest["corpora"]}
    if tuple(sorted(by)) != tuple(sorted(EXPECTED_NAMES)):
        raise RuntimeError(f"stable substrate drift: {sorted(by)!r}")

    workload_results: list[dict] = []
    semantic_errors: list[dict] = []
    rss_errors: list[dict] = []

    for name in EXPECTED_NAMES:
        source = corpus_root / name
        runs = {"baseline": [], "candidate": []}
        for rep in range(REPS):
            order = [("baseline", BASELINE), ("candidate", CANDIDATE)]
            if rep % 2:
                order.reverse()
            paired: dict[str, dict] = {}
            for label, module in order:
                archive = work_root / "runs" / name / f"r{rep}-{label}.cmpct"
                archive.parent.mkdir(parents=True, exist_ok=True)
                result_path = archive.with_suffix(".json")
                row = _run_fresh(module, source, archive, result_path)
                row["rep"] = rep
                runs[label].append(row)
                paired[label] = row

            ok, errors = _semantic_identity(paired["baseline"], paired["candidate"])
            if not ok:
                semantic_errors.append({"workload": name, "rep": rep, "errors": errors})

            brss = int(paired["baseline"]["process_peak_rss_kib"])
            crss = int(paired["candidate"]["process_peak_rss_kib"])
            allowed = max(int(brss * 1.05), brss + 4096)
            if crss > allowed:
                rss_errors.append(
                    {"workload": name, "rep": rep, "baseline_kib": brss, "candidate_kib": crss, "allowed_kib": allowed}
                )

        bcpu = _median(runs["baseline"], "total_build_cpu_s")
        ccpu = _median(runs["candidate"], "total_build_cpu_s")
        bwall = _median(runs["baseline"], "total_build_wall_s")
        cwall = _median(runs["candidate"], "total_build_wall_s")
        raw_skips = [int(row["adaptive_effort"].get("raw_terminal_skips", 0)) for row in runs["candidate"]]
        attempts_saved = [
            int(b["adaptive_effort"]["effort_attempts"]) - int(c["adaptive_effort"]["effort_attempts"])
            for b, c in zip(runs["baseline"], runs["candidate"], strict=True)
        ]
        workload_results.append(
            {
                "name": name,
                "baseline_median_cpu_s": bcpu,
                "candidate_median_cpu_s": ccpu,
                "baseline_median_wall_s": bwall,
                "candidate_median_wall_s": cwall,
                "cpu_improvement_fraction": (bcpu - ccpu) / max(bcpu, 1e-12),
                "wall_improvement_fraction": (bwall - cwall) / max(bwall, 1e-12),
                "candidate_raw_terminal_skips": raw_skips,
                "effort_attempts_saved": attempts_saved,
                "runs": runs,
            }
        )

    base_cpu = sum(row["baseline_median_cpu_s"] for row in workload_results)
    cand_cpu = sum(row["candidate_median_cpu_s"] for row in workload_results)
    base_wall = sum(row["baseline_median_wall_s"] for row in workload_results)
    cand_wall = sum(row["candidate_median_wall_s"] for row in workload_results)
    cpu_frac = (base_cpu - cand_cpu) / max(base_cpu, 1e-12)
    wall_frac = (base_wall - cand_wall) / max(base_wall, 1e-12)
    cpu_abs = base_cpu - cand_cpu

    per_workload_cpu_regression = []
    for row in workload_results:
        base = row["baseline_median_cpu_s"]
        cand = row["candidate_median_cpu_s"]
        if base >= 0.100 and cand - base > max(base * 0.05, 0.050):
            per_workload_cpu_regression.append(
                {"workload": row["name"], "baseline_s": base, "candidate_s": cand, "delta_s": cand - base}
            )

    if semantic_errors:
        verdict = "RAW_TERMINAL_BUILDER_INVALID"
    elif cpu_frac >= 0.05 and wall_frac >= 0.05 and cpu_abs >= 0.250 and not per_workload_cpu_regression and not rss_errors:
        verdict = "RAW_TERMINAL_BUILDER_MATERIAL"
    else:
        verdict = "RAW_TERMINAL_BUILDER_VALID_LOW_YIELD"

    return {
        "schema": "cmpct-v030-raw-terminal-builder-referee-v1",
        "mission_lock": "docs/V030_RAW_TERMINAL_BUILDER_MISSION_LOCK_2026-09-13.md",
        "baseline_module": BASELINE,
        "candidate_module": CANDIDATE,
        "repetitions": REPS,
        "substrate_manifest": manifest,
        "summary": {
            "verdict": verdict,
            "baseline_sum_median_cpu_s": base_cpu,
            "candidate_sum_median_cpu_s": cand_cpu,
            "cpu_improvement_fraction": cpu_frac,
            "cpu_saved_s": cpu_abs,
            "baseline_sum_median_wall_s": base_wall,
            "candidate_sum_median_wall_s": cand_wall,
            "wall_improvement_fraction": wall_frac,
            "semantic_error_count": len(semantic_errors),
            "rss_error_count": len(rss_errors),
            "per_workload_cpu_regression_count": len(per_workload_cpu_regression),
            "total_raw_terminal_skips_across_reps": sum(
                sum(row["candidate_raw_terminal_skips"]) for row in workload_results
            ),
            "total_effort_attempts_saved_across_reps": sum(
                sum(row["effort_attempts_saved"]) for row in workload_results
            ),
        },
        "semantic_errors": semantic_errors,
        "rss_errors": rss_errors,
        "per_workload_cpu_regressions": per_workload_cpu_regression,
        "workloads": workload_results,
        "status": "research Builder evidence only; no release/product credit",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--module")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--child-out", type=Path)
    ap.add_argument("--out", type=Path, default=Path("raw-terminal-builder.json"))
    ap.add_argument("--work-root", type=Path)
    args = ap.parse_args()

    if args.child:
        row = _child(args.module, args.source, args.archive)
        args.child_out.parent.mkdir(parents=True, exist_ok=True)
        args.child_out.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        return

    if args.work_root is None:
        with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-6-") as td:
            result = _parent(args.out, Path(td))
    else:
        args.work_root.mkdir(parents=True, exist_ok=True)
        result = _parent(args.out, args.work_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    if result["summary"]["verdict"] == "RAW_TERMINAL_BUILDER_INVALID":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
