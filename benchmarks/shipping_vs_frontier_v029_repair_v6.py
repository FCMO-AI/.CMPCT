#!/usr/bin/env python3
from __future__ import annotations

"""Repair-v6 custody wrapper for the v0.29 shipping-vs-frontier benchmark.

The August 17 accepted public v0.29 frontier is immutable historical evidence. Five
neutral/hostile source identities were later replaced by the independently reproduced
repair-v6 benchmark substrate. This wrapper overlays only those accepted source-tree /
inherited-v0.28 byte identities before running the existing shipping comparison.

No historical file is rewritten and no v0.30 hurdle is changed. The accepted portable
v0.29 aggregate moves by exactly the already-custodied -2,290 B repair delta, from
137,501,815 B to 137,499,525 B.
"""

import argparse
import copy
import json
from pathlib import Path

import shipping_vs_frontier_v029 as BASE


REPAIR_HISTORY = BASE.general.ROOT / "benchmarks" / "history" / "2026-08-19-neutral-hostile-determinism-repair-v6.json"
EXPECTED_HISTORICAL_TOTAL = 137_501_815
EXPECTED_REPAIRED_TOTAL = 137_499_525
EXPECTED_REPAIR_DELTA = -2_290
EXPECTED_V030_ABSOLUTE_HURDLE = 687_783


_ORIGINAL_ACCEPTED_ROWS = BASE._accepted_rows


def _accepted_rows_repair_v6() -> tuple[dict[tuple[str, str], dict], dict]:
    historical_rows, historical_record = _ORIGINAL_ACCEPTED_ROWS()
    rows = {key: dict(value) for key, value in historical_rows.items()}
    record = copy.deepcopy(historical_record)

    portable = record.get("portable_frontier") or {}
    historical_total = int(portable.get("candidate_bytes", -1))
    if historical_total != EXPECTED_HISTORICAL_TOTAL:
        raise RuntimeError(
            f"historical v0.29 aggregate identity changed unexpectedly: "
            f"{historical_total} != {EXPECTED_HISTORICAL_TOTAL}"
        )

    repair = json.loads(REPAIR_HISTORY.read_text(encoding="utf-8"))
    if repair.get("schema") != "cmpct-neutral-hostile-v1-determinism-repair-v6-accepted-v1":
        raise RuntimeError("repair-v6 evidence has an unexpected schema")
    if repair.get("accepted") is not True:
        raise RuntimeError("repair-v6 evidence is not accepted")
    decision = repair.get("decision") or {}
    if decision.get("historical_record_rewritten") is not False:
        raise RuntimeError("repair-v6 must preserve the historical record")
    if decision.get("hurdle_lowered") is not False:
        raise RuntimeError("repair-v6 must not lower the v0.30 hurdle")
    if int(decision.get("absolute_v030_saving_hurdle_bytes", -1)) != EXPECTED_V030_ABSOLUTE_HURDLE:
        raise RuntimeError("repair-v6 v0.30 absolute hurdle drifted")

    observed_delta = 0
    overlay_rows = []
    for fixed in repair.get("rows") or []:
        key = ("neutral_hostile_v1", fixed["name"])
        if key not in rows:
            raise RuntimeError(f"repair-v6 row is absent from historical v0.29 frontier: {key}")
        historical = rows[key]
        old_bytes = int(historical["candidate_bytes"])
        new_bytes = int(fixed["v028_candidate_bytes"])
        declared_delta = int(fixed["candidate_byte_delta_vs_predecessor"])
        if new_bytes - old_bytes != declared_delta:
            raise RuntimeError(
                f"repair-v6 delta mismatch for {key}: {new_bytes - old_bytes} != {declared_delta}"
            )
        historical["tree_sha256"] = fixed["tree_sha256"]
        historical["files"] = int(fixed["files"])
        historical["logical_bytes"] = int(fixed["logical_bytes"])
        historical["candidate_bytes"] = new_bytes
        historical["benchmark_identity"] = "neutral-hostile-repair-v6"
        observed_delta += declared_delta
        overlay_rows.append(
            {
                "suite": key[0],
                "name": key[1],
                "tree_sha256": fixed["tree_sha256"],
                "candidate_bytes": new_bytes,
                "delta_vs_historical_bytes": declared_delta,
            }
        )

    repaired_total = sum(int(row["candidate_bytes"]) for row in rows.values())
    if observed_delta != EXPECTED_REPAIR_DELTA:
        raise RuntimeError(f"repair-v6 aggregate delta drifted: {observed_delta} != {EXPECTED_REPAIR_DELTA}")
    if repaired_total != EXPECTED_REPAIRED_TOTAL:
        raise RuntimeError(f"repair-v6 aggregate identity drifted: {repaired_total} != {EXPECTED_REPAIRED_TOTAL}")
    if repaired_total - historical_total != EXPECTED_REPAIR_DELTA:
        raise RuntimeError("repair-v6 aggregate arithmetic is inconsistent")

    portable["candidate_bytes"] = repaired_total
    record["portable_frontier"] = portable
    record["accepted_identity_overlay"] = {
        "schema": repair["schema"],
        "record": "benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json",
        "accepted": True,
        "historical_record_rewritten": False,
        "historical_candidate_bytes": historical_total,
        "candidate_bytes": repaired_total,
        "delta_vs_historical_bytes": observed_delta,
        "absolute_v030_saving_hurdle_bytes": EXPECTED_V030_ABSOLUTE_HURDLE,
        "hurdle_lowered": False,
        "rows": overlay_rows,
    }
    return rows, record


def run(work_root: Path) -> dict:
    BASE._accepted_rows = _accepted_rows_repair_v6
    result = BASE.run(work_root)
    overlay = result["frontier_source"].get("accepted_identity_overlay")
    if overlay is None:
        overlay = _accepted_rows_repair_v6()[1]["accepted_identity_overlay"]
        result["frontier_source"]["accepted_identity_overlay"] = overlay
    result["benchmark_contract"]["frontier_acceptance_lock"] = (
        "immutable 2026-08-17 accepted v0.29 frontier plus accepted repair-v6 source-identity overlay"
    )
    result["benchmark_contract"]["historical_frontier_record"] = (
        "benchmarks/history/2026-08-17-mosaic-v029-public.json"
    )
    result["benchmark_contract"]["accepted_identity_overlay"] = overlay["record"]
    result["frontier_source"]["candidate_bytes"] = EXPECTED_REPAIRED_TOTAL
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Shipping_vs_Frontier"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.work_root)
    text = json.dumps(result, indent=2)
    print(json.dumps(result["totals"], indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
