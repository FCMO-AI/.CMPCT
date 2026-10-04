from __future__ import annotations

"""Per-pack compute attribution for the frozen Analytics high-effort population.

Mission: docs/V030_ANALYTICS_L19_COST_ATTRIBUTION_MISSION_2026-09-12.md
Research-only; no selector/release credit.
"""

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

import msgpack

from benchmarks import v030_analytics_reusable_zstd_context_referee as REUSE
from experiments import entropygraph_v025 as V25

ROUNDS = 3
EXPECTED = 45
TOPS = (1, 4, 8, 12, 24)


def _worker(fixture: Path, round_index: int, output: Path) -> None:
    packs = msgpack.unpackb(fixture.read_bytes(), raw=False)
    if len(packs) != EXPECTED:
        raise RuntimeError(f"fixture drift {len(packs)} != {EXPECTED}")
    # Deterministic rotation prevents one fixed pack from always seeing the same thermal/order position.
    shift = (round_index * 13) % len(packs)
    ordered = packs[shift:] + packs[:shift]
    rows = []
    for i, row in enumerate(ordered):
        raw = bytes(row["raw"])
        # Alternate which level is measured first by pack/round to reduce directional cache bias.
        levels = (15, 19) if (i + round_index) % 2 == 0 else (19, 15)
        measured = {}
        for level in levels:
            c0 = time.process_time(); w0 = time.perf_counter()
            payload = V25.zc(raw, level)
            measured[level] = {
                "csize": len(payload),
                "cpu_s": time.process_time() - c0,
                "wall_s": time.perf_counter() - w0,
            }
        rows.append({
            "sha256": bytes(row["sha256"]).hex(),
            "usize": int(row["usize"]),
            "l15_csize": measured[15]["csize"],
            "l19_csize": measured[19]["csize"],
            "l15_cpu_s": measured[15]["cpu_s"],
            "l19_cpu_s": measured[19]["cpu_s"],
            "l15_wall_s": measured[15]["wall_s"],
            "l19_wall_s": measured[19]["wall_s"],
        })
    output.write_text(json.dumps({"round": round_index, "rows": rows}, indent=2) + "\n")


def _child(fixture: Path, root: Path, ri: int) -> dict:
    out = root / f"round-{ri}.json"
    cp = subprocess.run([
        sys.executable, str(Path(__file__).resolve()), "--worker", "--fixture", str(fixture.resolve()),
        "--round-index", str(ri), "--worker-output", str(out.resolve()),
    ], text=True, capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"round {ri} failed rc={cp.returncode}\n{cp.stdout}\n{cp.stderr}")
    return json.loads(out.read_text())


def run(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    fixture, prep = REUSE._prepare_fixture(work_root)
    rounds = [_child(fixture, work_root, ri) for ri in range(ROUNDS)]

    by_hash: dict[str, list[dict]] = {}
    for rr in rounds:
        for row in rr["rows"]:
            by_hash.setdefault(row["sha256"], []).append(row)
    if len(by_hash) != EXPECTED or any(len(v) != ROUNDS for v in by_hash.values()):
        raise RuntimeError("per-pack round coverage drift")

    packs = []
    for hh, rr in by_hash.items():
        usizes = {int(x["usize"]) for x in rr}; s15 = {int(x["l15_csize"]) for x in rr}; s19 = {int(x["l19_csize"]) for x in rr}
        if len(usizes) != 1 or len(s15) != 1 or len(s19) != 1:
            raise RuntimeError(f"determinism drift {hh}")
        m15 = statistics.median(float(x["l15_cpu_s"]) for x in rr)
        m19 = statistics.median(float(x["l19_cpu_s"]) for x in rr)
        saving = next(iter(s15)) - next(iter(s19))
        packs.append({
            "sha256": hh, "usize": next(iter(usizes)), "l15_csize": next(iter(s15)), "l19_csize": next(iter(s19)),
            "saving_bytes": saving,
            "median_l15_cpu_s": m15, "median_l19_cpu_s": m19,
            "median_l15_wall_s": statistics.median(float(x["l15_wall_s"]) for x in rr),
            "median_l19_wall_s": statistics.median(float(x["l19_wall_s"]) for x in rr),
            "incremental_l19_cpu_s": m19 - m15,
            "l19_cpu_per_kib_saved": m19 / max(saving / 1024, 1e-12),
        })

    ranked = sorted(packs, key=lambda x: x["median_l19_cpu_s"], reverse=True)
    total_cpu = sum(x["median_l19_cpu_s"] for x in ranked)
    total_raw = sum(x["usize"] for x in ranked)
    total_saving = sum(x["saving_bytes"] for x in ranked)
    concentration = {}
    for n in TOPS:
        group = ranked[:n]
        concentration[str(n)] = {
            "cpu_fraction": sum(x["median_l19_cpu_s"] for x in group) / max(total_cpu, 1e-12),
            "raw_fraction": sum(x["usize"] for x in group) / max(total_raw, 1),
            "saving_fraction": sum(x["saving_bytes"] for x in group) / max(total_saving, 1),
            "cpu_s": sum(x["median_l19_cpu_s"] for x in group),
            "saving_bytes": sum(x["saving_bytes"] for x in group),
        }

    buckets = {}
    for lo, hi, label in ((0, 262144, "lt256k"), (262144, 524288, "256k_to_512k"), (524288, 1 << 60, "ge512k")):
        group = [x for x in packs if lo <= x["usize"] < hi]
        buckets[label] = {
            "pack_count": len(group), "raw_bytes": sum(x["usize"] for x in group),
            "l19_cpu_s": sum(x["median_l19_cpu_s"] for x in group), "saving_bytes": sum(x["saving_bytes"] for x in group),
        }

    top12 = concentration["12"]["cpu_fraction"]
    verdict = "CONCENTRATED_TARGET_HOT_PACKS" if top12 >= 0.70 else "DIFFUSE_OPTIMIZE_HIGH_EFFORT_ENGINE"
    return {
        "schema": "cmpct-v030-analytics-l19-cost-attribution-v1", "release_credit": False, "experiment_valid": True,
        "target": "neutral_hostile_v1/04_analytics_and_database", "rounds": ROUNDS, "fixture": prep,
        "total_median_l19_cpu_s_sum": total_cpu, "total_median_l15_cpu_s_sum": sum(x["median_l15_cpu_s"] for x in packs),
        "total_saving_bytes": total_saving, "concentration": concentration, "size_buckets": buckets,
        "packs_by_l19_cpu_desc": ranked, "verdict": verdict,
        "gate": {"top12_cpu_fraction_at_least_0_70": top12 >= 0.70},
        "contract": {"frozen_admission_population": True, "path_extension_labels_absent": True,
                     "fresh_child_per_round": True, "fixed_levels_only": [15,19], "no_selector_change": True,
                     "no_archive_or_release_credit": True},
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-analytics-l19-cost-work")); ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-analytics-l19-cost.json")); ap.add_argument("--worker", action="store_true"); ap.add_argument("--fixture", type=Path); ap.add_argument("--round-index", type=int); ap.add_argument("--worker-output", type=Path); args = ap.parse_args()
    if args.worker:
        if args.fixture is None or args.round_index is None or args.worker_output is None: raise SystemExit("worker args missing")
        _worker(args.fixture, args.round_index, args.worker_output); return
    import shutil
    shutil.rmtree(args.work_root, ignore_errors=True); args.work_root.mkdir(parents=True)
    r = run(args.work_root); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(r, indent=2)+"\n")
    print(json.dumps({"verdict":r["verdict"],"total_l19_cpu_s":r["total_median_l19_cpu_s_sum"],"total_saving_bytes":r["total_saving_bytes"],"concentration":r["concentration"],"gate":r["gate"]}, indent=2), flush=True)


if __name__ == "__main__": main()
