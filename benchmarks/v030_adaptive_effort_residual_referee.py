from __future__ import annotations

"""H-EFFORT-2: fixed-geometry residual referee for the existing C25EG08 effort policy.

Mission lock: docs/V030_ADAPTIVE_EFFORT_RESIDUAL_MISSION_LOCK_2026-09-13.md

This referee does not tune policy. It freezes the current Office/Analytics physical
geometry, proves level-1 byte identity, measures the full 1/3/6/9/12/15/19 effort
ladder, and then replays the historical C25EG08 policy exactly:

* retain the current payload as incumbent;
* never recompress hot stream roots;
* try levels 3, 6, 12, 19 in that order;
* continue after a strict win or tie;
* stop on the first strictly worse next effort.

Levels 9 and 15 are observation-only: they can falsify the assumption that the
historical stop rule sees the useful part of the effort curve, but they never enter
the policy decision. The level-19 result remains a counterfactual oracle, not a
product promotion candidate.
"""

import argparse
import json
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import tempfile
import time

from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks import v030_office_physical_economics_referee as OFFICE
from benchmarks import v030_physical_effort_attribution as H1
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05

V25 = EG05.V25
TARGETS = ("02_office_workspace", "04_analytics_and_database")
LEVELS = (1, 3, 6, 9, 12, 15, 19)
POLICY_LEVELS = (3, 6, 12, 19)
REPS = 3
EXPECTED_POLICY_GIT_BLOB = "dc76dbfb17b8157cf453c2bb21c27459b34b1b7c"


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _policy_blob() -> str:
    path = Path(EG08.__file__).resolve()
    try:
        return subprocess.check_output(
            ["git", "hash-object", str(path)], text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"cannot bind C25EG08 policy source: {exc}") from exc


def _run_level(units: list[dict], level: int) -> tuple[list[tuple[int, bytes]], float, float]:
    return H1._run_effort(units, int(level))


def _run_policy_once(units: list[dict], hot_indices: set[int]) -> tuple[list[tuple[int, bytes]], dict]:
    selected: list[tuple[int, bytes]] = []
    attempts = 0
    early_stops = 0
    selected_levels: dict[str, int] = {"current": 0, "3": 0, "6": 0, "12": 0, "19": 0}
    for row in units:
        pi = int(row["index"])
        best_codec = int(row["codec"])
        best_payload = row["payload"]
        best_size = len(best_payload)
        best_level = "current"
        if pi not in hot_indices:
            for level in POLICY_LEVELS:
                attempts += 1
                codec, payload = H1._encode(row["raw"], level)
                size = len(payload)
                if size <= best_size:
                    if size < best_size:
                        best_codec = codec
                        best_payload = payload
                        best_size = size
                        best_level = str(level)
                    continue
                early_stops += 1
                break
        selected_levels[best_level] = selected_levels.get(best_level, 0) + 1
        selected.append((best_codec, best_payload))
    return selected, {
        "attempts": attempts,
        "early_stops": early_stops,
        "selected_levels": selected_levels,
    }


def _run_policy(units: list[dict], hot_indices: set[int]) -> tuple[list[tuple[int, bytes]], dict, float, float]:
    cpu: list[float] = []
    wall: list[float] = []
    first: list[tuple[int, bytes]] | None = None
    first_stats: dict | None = None
    for _ in range(REPS):
        c0 = time.process_time(); w0 = time.perf_counter()
        selected, stats = _run_policy_once(units, hot_indices)
        cpu.append(time.process_time() - c0)
        wall.append(time.perf_counter() - w0)
        if first is None:
            first, first_stats = selected, stats
        elif len(first) != len(selected) or any(
            a[0] != b[0] or a[1] != b[1] for a, b in zip(first, selected)
        ):
            raise RuntimeError("historical adaptive effort policy is not deterministic within run")
    assert first is not None and first_stats is not None
    return first, first_stats, statistics.median(cpu), statistics.median(wall)


def _physical_bytes(encoded: list[tuple[int, bytes]]) -> int:
    return sum(V25.PH.size + len(payload) for _codec, payload in encoded)


def _one(source: Path, item: dict, work: Path) -> dict:
    profile = work / "profile"
    v1_raw, implicit_raw, fs_stats = OFFICE.profile_controls(source, profile)
    base = work / "physical-base.cmpct"
    base_stats, base_cpu, base_wall = OFFICE.timed(lambda: OFFICE.physical_base(profile, base))
    current = work / "current-implicit.cmpct"
    OFFICE.embedded_copy(base, current, implicit_raw)
    components = OFFICE.parsed(current)
    verify = OFFICE.verify_controlled("adaptive-effort-current", current, source, v1_raw, implicit=True)

    units, physical = H1._physical_units(base)
    meta, _physical_region = EG05._parse_physical_region(base.read_bytes())
    stream_indices, hot_indices = EG08._stream_roles(meta, len(units))

    ladder: dict[int, dict] = {}
    encoded: dict[int, list[tuple[int, bytes]]] = {}
    for level in LEVELS:
        out, cpu, wall = _run_level(units, level)
        encoded[level] = out
        ladder[level] = {
            "physical_bytes": _physical_bytes(out),
            "median_cpu_s": cpu,
            "median_wall_s": wall,
        }

    exact_rows = []
    level1_exact = True
    for row, enc in zip(units, encoded[1]):
        exact = int(row["codec"]) == int(enc[0]) and row["payload"] == enc[1]
        level1_exact = level1_exact and exact
        exact_rows.append({
            "index": int(row["index"]),
            "usize": int(row["usize"]),
            "stored_codec": int(row["codec"]),
            "stored_payload_bytes": len(row["payload"]),
            "level1_codec": int(enc[0]),
            "level1_payload_bytes": len(enc[1]),
            "exact": exact,
        })
    if ladder[1]["physical_bytes"] != int(components["physical_region_bytes"]):
        level1_exact = False

    policy, policy_stats, policy_cpu, policy_wall = _run_policy(units, hot_indices)
    policy_physical = _physical_bytes(policy)
    l1_physical = int(ladder[1]["physical_bytes"])
    l19_physical = int(ladder[19]["physical_bytes"])
    oracle_saving = l1_physical - l19_physical
    recovered = l1_physical - policy_physical
    oracle_share = recovered / oracle_saving if oracle_saving > 0 else 1.0
    residual = policy_physical - l19_physical

    # Hostile review of the stop law. Reconstruct where it stopped from the measured
    # full ladder, then ask whether a later policy rung or observation-only rung was
    # actually better than the selected payload.
    stop_missed = []
    intermediate_missed = []
    residual_rows = []
    for i, row in enumerate(units):
        pi = int(row["index"])
        current_size = len(row["payload"])
        selected_size = len(policy[i][1])
        l19_size = len(encoded[19][i][1])
        residual_i = selected_size - l19_size
        if residual_i > 0:
            residual_rows.append({
                "index": pi,
                "usize": int(row["usize"]),
                "hot_stream_root": pi in hot_indices,
                "policy_payload_bytes": selected_size,
                "level19_payload_bytes": l19_size,
                "residual_bytes": residual_i,
            })
        if pi in hot_indices:
            continue

        best = current_size
        stop_at: int | None = None
        for level in POLICY_LEVELS:
            size = len(encoded[level][i][1])
            if size <= best:
                best = min(best, size)
            else:
                stop_at = level
                break
        if stop_at is not None:
            later = [level for level in POLICY_LEVELS if level > stop_at]
            later_best = min((len(encoded[level][i][1]) for level in later), default=best)
            if later_best < selected_size:
                stop_missed.append({
                    "index": pi,
                    "stop_level": stop_at,
                    "policy_payload_bytes": selected_size,
                    "later_policy_best_bytes": later_best,
                    "missed_bytes": selected_size - later_best,
                })

        intermediate_best = min(len(encoded[level][i][1]) for level in (9, 15))
        if intermediate_best < selected_size:
            intermediate_missed.append({
                "index": pi,
                "policy_payload_bytes": selected_size,
                "level9_payload_bytes": len(encoded[9][i][1]),
                "level15_payload_bytes": len(encoded[15][i][1]),
                "missed_bytes": selected_size - intermediate_best,
            })

    residual_rows.sort(key=lambda x: x["residual_bytes"], reverse=True)
    residual_total = sum(x["residual_bytes"] for x in residual_rows)
    hot_residual_rows = [x for x in residual_rows if x["hot_stream_root"]]
    cold_residual_rows = [x for x in residual_rows if not x["hot_stream_root"]]
    hot_residual = sum(x["residual_bytes"] for x in hot_residual_rows)
    cold_residual = sum(x["residual_bytes"] for x in cold_residual_rows)
    top5_residual = sum(x["residual_bytes"] for x in residual_rows[:5])
    current_total = int(components["archive_bytes"])
    policy_total = current_total - l1_physical + policy_physical
    l19_total = current_total - l1_physical + l19_physical

    return {
        "name": item["name"],
        "tree_sha256": item["tree_sha256"],
        "logical_bytes": item["logical_bytes"],
        "files": item["files"],
        "current_complete_bytes": current_total,
        "policy_counterfactual_complete_bytes": policy_total,
        "level19_counterfactual_complete_bytes": l19_total,
        "current_components": components,
        "current_verify": verify,
        "filesystem_stats": fs_stats,
        "physical_base_build_cpu_s": base_cpu,
        "physical_base_build_wall_s": base_wall,
        "physical_base_stats": base_stats,
        "pack_count": int(physical["pack_count"]),
        "stream_pack_count": len(stream_indices),
        "hot_stream_root_pack_count": len(hot_indices),
        "level1_exact_reproduction": level1_exact,
        "exact_rows": exact_rows,
        "ladder": {str(k): v for k, v in ladder.items()},
        "policy_levels": list(POLICY_LEVELS),
        "policy_physical_bytes": policy_physical,
        "policy_median_cpu_s": policy_cpu,
        "policy_median_wall_s": policy_wall,
        "policy_stats": policy_stats,
        "oracle_level19_physical_bytes": l19_physical,
        "oracle_saving_vs_level1_bytes": oracle_saving,
        "policy_recovered_vs_level1_bytes": recovered,
        "policy_share_of_level19_oracle": oracle_share,
        "policy_residual_vs_level19_bytes": residual,
        "policy_vs_level19_cpu_ratio": policy_cpu / max(float(ladder[19]["median_cpu_s"]), 1e-12),
        "policy_vs_level19_wall_ratio": policy_wall / max(float(ladder[19]["median_wall_s"]), 1e-12),
        "policy_recovered_bytes_per_cpu_s": recovered / max(policy_cpu, 1e-12),
        "level19_recovered_bytes_per_cpu_s": oracle_saving / max(float(ladder[19]["median_cpu_s"]), 1e-12),
        "selected_raw_pack_count": sum(1 for codec, _payload in policy if codec == 0),
        "stop_rule_missed_pack_count": len(stop_missed),
        "stop_rule_missed_bytes": sum(x["missed_bytes"] for x in stop_missed),
        "stop_rule_misses": stop_missed,
        "observation_only_9_15_better_pack_count": len(intermediate_missed),
        "observation_only_9_15_missed_bytes": sum(x["missed_bytes"] for x in intermediate_missed),
        "observation_only_9_15_misses": intermediate_missed,
        "residual_pack_count": len(residual_rows),
        "hot_residual_pack_count": len(hot_residual_rows),
        "hot_residual_bytes": hot_residual,
        "hot_residual_share": hot_residual / residual_total if residual_total > 0 else 0.0,
        "cold_residual_pack_count": len(cold_residual_rows),
        "cold_residual_bytes": cold_residual,
        "cold_residual_share": cold_residual / residual_total if residual_total > 0 else 0.0,
        "top5_residual_bytes": top5_residual,
        "top5_residual_share": top5_residual / residual_total if residual_total > 0 else 0.0,
        "largest_residual_packs": residual_rows[:20],
        "counterfactual_note": "policy and level19 bytes reuse identical raw physical units; neither is product promotion evidence",
    }


def _verdict(rows: list[dict], policy_blob: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if policy_blob != EXPECTED_POLICY_GIT_BLOB:
        return "EFFORT_ATTRIBUTION_INVALID", [
            f"C25EG08 policy blob drifted: {policy_blob} != {EXPECTED_POLICY_GIT_BLOB}"
        ]
    if not all(bool(r["level1_exact_reproduction"]) for r in rows):
        return "EFFORT_ATTRIBUTION_INVALID", ["level-1 failed exact physical reproduction"]

    shares = [float(r["policy_share_of_level19_oracle"]) for r in rows]
    cpu_ratios = [float(r["policy_vs_level19_cpu_ratio"]) for r in rows]
    if all(s >= 0.95 for s in shares) and all(c < 0.80 for c in cpu_ratios):
        return "EXISTING_EFFORT_POLICY_SUFFICIENT", reasons
    if any(s < 0.80 for s in shares):
        reasons.append("existing policy captured <80% of the level-19 oracle on at least one target")
        return "EFFORT_POLICY_INSUFFICIENT", reasons
    if all(s >= 0.95 for s in shares) and any(c >= 0.80 for c in cpu_ratios):
        reasons.append("byte recovery is high but policy consumes >=80% of level-19 compression CPU")
        return "EFFORT_POLICY_INSUFFICIENT", reasons
    reasons.append("policy captured >=80% but <95% of the oracle on at least one target; inspect localized residual")
    return "EFFORT_POLICY_RESIDUAL_LOCALIZED", reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("adaptive-effort-residual.json"))
    args = ap.parse_args()
    policy_blob = _policy_blob()

    with tempfile.TemporaryDirectory(prefix="cmpct-adaptive-effort-residual-") as td:
        root = Path(td)
        corpus = root / "corpus"
        manifest = CORPUS.build(corpus)
        by_name = {x["name"]: x for x in manifest["corpora"]}
        if any(name not in by_name for name in TARGETS):
            raise RuntimeError("stable current15 target drift")

        rows = []
        for name in TARGETS:
            work = root / ("work-" + name)
            work.mkdir()
            rows.append(_one(corpus / name, by_name[name], work))

        verdict, reasons = _verdict(rows, policy_blob)
        receipt = {
            "schema": "cmpct-v030-adaptive-effort-residual-v1",
            "verdict": verdict,
            "verdict_reasons": reasons,
            "policy_module": "experiments/entropygraph_v030_federated_adaptive_effort_candidate_v8.py",
            "policy_git_blob": policy_blob,
            "expected_policy_git_blob": EXPECTED_POLICY_GIT_BLOB,
            "levels_measured": list(LEVELS),
            "policy_levels": list(POLICY_LEVELS),
            "repetitions": REPS,
            "zstd_version": H1._zstd_version(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "process_peak_rss_kib": _rss_kib(),
            "rows": rows,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt, sort_keys=True))
        if verdict == "EFFORT_ATTRIBUTION_INVALID":
            raise SystemExit(2)


if __name__ == "__main__":
    main()
