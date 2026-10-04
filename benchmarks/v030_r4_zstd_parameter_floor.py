from __future__ import annotations

"""Exact optimistic floor over the measured Zstd-parameter family.

Input is the durable JSON emitted by v030_r4_zstd_parameter_decomposition.py. For each distinct final
compression payload, every measured parameter variant is treated as an oracle-available choice. The
solver computes (a) the maximum physical-byte saving possible if the encoder could choose the best
measured variant per payload with perfect foresight, and (b) when the accepted v0.29 byte floor is
reachable, the minimum *measured marginal final-compression time* needed to become strictly smaller.

This is intentionally optimistic: negative timing deltas are clamped to zero and workload identity is
available to the oracle. Therefore failure to reach the floor is a strong representation/parameter-
family negative, while a reachable floor earns no product credit without a real bounded selector.
"""

import argparse
import json
from pathlib import Path


def _record_options(record: dict) -> list[tuple[int, float, str]]:
    base = record["variants"]["level15"]
    calls = int(record["calls"])
    options: list[tuple[int, float, str]] = []
    for name, variant in record["variants"].items():
        saving = max(0, (int(base["physical_payload_bytes"]) - int(variant["physical_payload_bytes"])) * calls)
        marginal = max(0.0, (float(variant["median_compress_s"]) - float(base["median_compress_s"])) * calls)
        options.append((saving, marginal, name))

    # Remove per-record choices that are weakly worse in both dimensions. This is exact because only
    # total saving and optimistic measured marginal time enter the downstream oracle.
    pareto = []
    for option in options:
        s, t, _ = option
        if any(
            os >= s and ot <= t and (os > s or ot < t)
            for os, ot, _ in options
        ):
            continue
        pareto.append(option)
    # Collapse exact duplicate points while retaining a stable representative name.
    unique: dict[tuple[int, float], str] = {}
    for s, t, name in sorted(pareto, key=lambda x: (x[0], x[1], x[2])):
        unique.setdefault((s, t), name)
    return [(s, t, name) for (s, t), name in unique.items()]


def _solve_row(row: dict) -> dict:
    strict_gap = max(0, int(row["fixed_level15_archive_bytes"]) - int(row["accepted_v029_bytes"]) + 1)
    max_possible_saving = sum(
        max(option[0] for option in _record_options(record))
        for record in row["raw_records"]
    )

    # State maps capped saving -> minimum optimistic marginal time. Savings above the strict target are
    # equivalent. Dominated states are pruned exactly after each record.
    frontier: dict[int, float] = {0: 0.0}
    for record in row["raw_records"]:
        options = _record_options(record)
        candidates: dict[int, float] = {}
        for saving, elapsed in frontier.items():
            for ds, dt, _ in options:
                ns = min(strict_gap, saving + ds) if strict_gap else 0
                nt = elapsed + dt
                if nt < candidates.get(ns, float("inf")):
                    candidates[ns] = nt
        pruned: dict[int, float] = {}
        best_time = float("inf")
        for saving in sorted(candidates, reverse=True):
            elapsed = candidates[saving]
            if elapsed < best_time:
                pruned[saving] = elapsed
                best_time = elapsed
        frontier = pruned

    reachable = strict_gap == 0 or strict_gap in frontier
    minimum_time = 0.0 if strict_gap == 0 else (frontier.get(strict_gap) if reachable else None)
    return {
        "workload": row["workload"],
        "accepted_v029_bytes": int(row["accepted_v029_bytes"]),
        "fixed_level15_archive_bytes": int(row["fixed_level15_archive_bytes"]),
        "strict_saving_required_to_beat_v029_bytes": strict_gap,
        "maximum_measured_parameter_family_saving_bytes": max_possible_saving,
        "optimistic_floor_archive_bytes": int(row["fixed_level15_archive_bytes"]) - max_possible_saving,
        "strict_v029_floor_reachable": reachable,
        "unclosable_shortfall_bytes": max(0, strict_gap - max_possible_saving),
        "minimum_optimistic_marginal_final_compress_s_to_beat_v029": minimum_time,
        "frontier_states": len(frontier),
    }


def analyze(data: dict) -> dict:
    if data.get("schema") != "cmpct-v030-r4-zstd-parameter-decomposition-v1":
        raise ValueError("unexpected decomposition schema")
    rows = [_solve_row(row) for row in data["rows"]]
    return {
        "schema": "cmpct-v030-r4-zstd-parameter-floor-v1",
        "source_commit": data.get("source_commit"),
        "input_schema": data.get("schema"),
        "rows": rows,
        "conclusions": {
            "office_floor_unreachable_with_measured_parameter_family": not next(r for r in rows if r["workload"] == "02_office_workspace")["strict_v029_floor_reachable"],
            "analytics_floor_reachable_with_oracle": next(r for r in rows if r["workload"] == "04_analytics_and_database")["strict_v029_floor_reachable"],
            "developer_floor_unreachable_with_measured_parameter_family": not next(r for r in rows if r["workload"] == "01_developer_repository")["strict_v029_floor_reachable"],
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "oracle_has_per_payload_perfect_foresight": True,
            "negative_timing_deltas_clamped_to_zero": True,
            "no_new_compression_measurements": True,
            "no_production_policy_changed": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
