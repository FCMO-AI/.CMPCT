from __future__ import annotations

"""H-EFFORT-4 observational pack-economics referee.

Frozen by docs/V030_ADAPTIVE_EFFORT_ECONOMICS_MISSION_LOCK_2026-09-13.md.
This instrument does not implement or tune a selector. It measures exact per-pack
size/CPU curves at levels 1/3/6/9/12/19, reconstructs the historical first-worse
stop, and exposes where later recovery and sequential-ladder CPU futility occur.
"""

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tempfile
import time

from benchmarks import v030_adaptive_effort_recovery_probe_referee as H3
from benchmarks import v030_adaptive_effort_residual_referee as H2
from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks import v030_office_physical_economics_referee as OFFICE
from benchmarks import v030_physical_effort_attribution as H1
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

LEVELS = (1, 3, 6, 9, 12, 19)
POLICY_LEVELS = (3, 6, 12, 19)
REPS = 3
EXPECTED_NAMES = H3.EXPECTED_CURRENT15_NAMES
PRIMARY = H3.PRIMARY
EXPECTED_POLICY_GIT_BLOB = H2.EXPECTED_POLICY_GIT_BLOB


def _measure(raw: bytes, level: int) -> dict:
    first = None
    cpus: list[float] = []
    walls: list[float] = []
    for _ in range(REPS):
        c0 = time.process_time()
        w0 = time.perf_counter()
        codec, payload = H1._encode(raw, level)
        cpus.append(time.process_time() - c0)
        walls.append(time.perf_counter() - w0)
        identity = (int(codec), payload)
        if first is None:
            first = identity
        elif identity != first:
            raise RuntimeError(f"level {level} encode is nondeterministic")
    assert first is not None
    return {
        "level": level,
        "codec": first[0],
        "bytes": len(first[1]),
        "cpu_s": statistics.median(cpus),
        "wall_s": statistics.median(walls),
    }


def _historical(curve: dict[int, dict]) -> dict:
    incumbent_level = 1
    incumbent_bytes = int(curve[1]["bytes"])
    cumulative_cpu = 0.0
    cumulative_wall = 0.0
    first_worse_level = None
    attempted: list[int] = []
    for level in POLICY_LEVELS:
        attempted.append(level)
        cumulative_cpu += float(curve[level]["cpu_s"])
        cumulative_wall += float(curve[level]["wall_s"])
        size = int(curve[level]["bytes"])
        if size <= incumbent_bytes:
            if size < incumbent_bytes:
                incumbent_level = level
                incumbent_bytes = size
            continue
        first_worse_level = level
        break
    return {
        "chosen_level": incumbent_level,
        "chosen_bytes": incumbent_bytes,
        "first_worse_level": first_worse_level,
        "attempted_levels": attempted,
        "cumulative_cpu_s": cumulative_cpu,
        "cumulative_wall_s": cumulative_wall,
    }


def _pack_row(workload: str, index: int, raw: bytes, hot: bool) -> dict:
    curve_rows = [_measure(raw, level) for level in LEVELS]
    curve = {int(row["level"]): row for row in curve_rows}
    hist = _historical(curve)

    all_sizes = {level: int(curve[level]["bytes"]) for level in LEVELS}
    best_level = min(LEVELS, key=lambda level: (all_sizes[level], level))
    best_bytes = all_sizes[best_level]
    hist_bytes = int(hist["chosen_bytes"])
    missed = max(0, hist_bytes - best_bytes)
    first_worse = hist["first_worse_level"]

    later_levels = tuple(level for level in LEVELS if first_worse is not None and level > int(first_worse))
    later_best_level = None
    later_best_bytes = hist_bytes
    if later_levels:
        later_best_level = min(later_levels, key=lambda level: (all_sizes[level], level))
        later_best_bytes = all_sizes[later_best_level]
    later_recovery = first_worse is not None and later_best_bytes < hist_bytes

    l9_detects = bool(first_worse is not None and int(first_worse) < 9 and all_sizes[9] < hist_bytes)
    post_l9_headroom = max(0, all_sizes[9] - min(all_sizes[12], all_sizes[19])) if l9_detects else 0

    direct_l19_cpu = float(curve[19]["cpu_s"])
    ladder_cpu = float(hist["cumulative_cpu_s"])
    l1_ratio = all_sizes[1] / max(1, len(raw))
    l3_ratio = all_sizes[3] / max(1, len(raw))
    l6_ratio = all_sizes[6] / max(1, len(raw))

    return {
        "workload": workload,
        "pack_index": index,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "hot_role": hot,
        "curve": curve_rows,
        "observables": {
            "level1_ratio": l1_ratio,
            "level3_ratio": l3_ratio,
            "level6_ratio": l6_ratio,
            "l3_delta_vs_l1": all_sizes[3] - all_sizes[1],
            "l6_delta_vs_l3": all_sizes[6] - all_sizes[3],
            "l9_delta_vs_historical_incumbent": all_sizes[9] - hist_bytes,
        },
        "historical": hist,
        "oracle": {
            "best_level": best_level,
            "best_bytes": best_bytes,
            "missed_bytes": missed,
            "later_recovery_after_first_worse": later_recovery,
            "later_best_level": later_best_level,
            "later_best_bytes": later_best_bytes,
            "l9_detects_later_recovery": l9_detects,
            "post_l9_headroom_bytes": post_l9_headroom,
            "ladder_cpu_minus_direct_l19_s": ladder_cpu - direct_l19_cpu,
            "ladder_cpu_over_l19": ladder_cpu / max(direct_l19_cpu, 1e-12),
        },
    }


def _workload_rows(source: Path, item: dict, work: Path) -> list[dict]:
    profile = work / "profile"
    if item["name"] in PRIMARY:
        OFFICE.profile_controls(source, profile)
    else:
        H3._explicit_profile_controls(source, profile)
    base = work / "base.cmpct"
    OFFICE.physical_base(profile, base)
    units, _ = H1._physical_units(base)
    meta, _ = H2.EG05._parse_physical_region(base.read_bytes())
    _, hot = EG08._stream_roles(meta, len(units))
    return [
        _pack_row(item["name"], int(row["index"]), row["raw"], int(row["index"]) in hot)
        for row in units
    ]


def _aggregate(rows: list[dict]) -> dict:
    by_workload: dict[str, list[dict]] = {}
    for row in rows:
        by_workload.setdefault(row["workload"], []).append(row)

    def stats(group: list[dict]) -> dict:
        missed = sum(int(r["oracle"]["missed_bytes"]) for r in group)
        recovery_missed = sum(
            int(r["oracle"]["missed_bytes"])
            for r in group
            if r["oracle"]["later_recovery_after_first_worse"]
        )
        l9_visible_missed = sum(
            int(r["oracle"]["missed_bytes"])
            for r in group
            if r["oracle"]["l9_detects_later_recovery"]
        )
        post_l9 = sum(int(r["oracle"]["post_l9_headroom_bytes"]) for r in group)
        ladder_dominated = [r for r in group if float(r["oracle"]["ladder_cpu_minus_direct_l19_s"]) > 0]
        return {
            "packs": len(group),
            "hot_packs": sum(1 for r in group if r["hot_role"]),
            "packs_with_historical_missed_headroom": sum(1 for r in group if int(r["oracle"]["missed_bytes"]) > 0),
            "historical_missed_bytes": missed,
            "packs_with_later_recovery_after_first_worse": sum(1 for r in group if r["oracle"]["later_recovery_after_first_worse"]),
            "missed_bytes_on_later_recovery_packs": recovery_missed,
            "packs_where_l9_detects_recovery": sum(1 for r in group if r["oracle"]["l9_detects_later_recovery"]),
            "missed_bytes_where_l9_detects_recovery": l9_visible_missed,
            "post_l9_headroom_bytes_after_l9_detection": post_l9,
            "packs_where_historical_ladder_cpu_exceeds_direct_l19": len(ladder_dominated),
            "raw_bytes_where_ladder_cpu_exceeds_direct_l19": sum(int(r["raw_bytes"]) for r in ladder_dominated),
            "total_ladder_cpu_s": sum(float(r["historical"]["cumulative_cpu_s"]) for r in group),
            "total_direct_l19_cpu_s": sum(float(next(x["cpu_s"] for x in r["curve"] if int(x["level"]) == 19)) for r in group),
        }

    return {
        "overall": stats(rows),
        "workloads": {name: stats(group) for name, group in sorted(by_workload.items())},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("adaptive-effort-economics.json"))
    args = ap.parse_args()

    blob = H2._policy_blob()
    if blob != EXPECTED_POLICY_GIT_BLOB:
        raise RuntimeError(f"historical policy source drift: {blob}")

    with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-4-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = CORPUS.build(corpus)
        by = {item["name"]: item for item in manifest["corpora"]}
        observed = tuple(sorted(by))
        expected = tuple(sorted(EXPECTED_NAMES))
        if observed != expected:
            raise RuntimeError(f"stable substrate drift: expected={expected!r} observed={observed!r}")
        rows: list[dict] = []
        for name in EXPECTED_NAMES:
            rows.extend(_workload_rows(corpus / name, by[name], root / name))

    out = {
        "schema": "cmpct-v030-adaptive-effort-economics-referee-v1",
        "status": "R0/R3 observational research evidence; no selector/release/R4 credit",
        "historical_policy_blob": blob,
        "levels": list(LEVELS),
        "repetitions": REPS,
        "substrate_names": list(EXPECTED_NAMES),
        "primary": sorted(PRIMARY),
        "rows": rows,
        "aggregate": _aggregate(rows),
        "adjudication": "UNADJUDICATED_CAUSAL_CENSUS",
        "note": "No shipping thresholds or classifier are fit by this instrument; hostile review must adjudicate transfer structure before any Builder.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out["aggregate"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
