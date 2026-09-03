from __future__ import annotations

"""Applicability-aware successor to the frozen v2 discovery-source transfer instrument.

V3 deliberately reuses v2 execution/measurement mechanics and changes only the preregistered validity and
terminal interpretation for legitimate zero-call delta-path states.
"""

import argparse
import json
import math
import os
from pathlib import Path

from benchmarks import v030_discovery_runtime_matrix_transfer_v2 as V2

PREREG = "docs/v030-rnd/R25_SHIFTED_DISCOVERY_RUNTIME_MATRIX_TRANSFER_V3_PREREG.md"


def _delta_state(item: dict) -> tuple[bool, str]:
    calls = int(item["delta_calls"])
    wall = float(item["delta_s"])
    if calls < 0 or not math.isfinite(wall) or wall < 0:
        return False, "invalid"
    if calls == 0:
        return (wall == 0.0), "delta_path_not_exercised"
    return (wall > 0.0), "delta_path_exercised"


def _self_check_validity_model() -> None:
    assert _delta_state({"delta_calls": 0, "delta_s": 0.0}) == (True, "delta_path_not_exercised")
    assert _delta_state({"delta_calls": 1, "delta_s": 0.001}) == (True, "delta_path_exercised")
    assert _delta_state({"delta_calls": 0, "delta_s": 0.001})[0] is False
    assert _delta_state({"delta_calls": 1, "delta_s": 0.0})[0] is False
    assert _delta_state({"delta_calls": -1, "delta_s": 0.0})[0] is False
    assert _delta_state({"delta_calls": 1, "delta_s": float("nan")})[0] is False


def run(work_root: Path) -> dict:
    raw = V2.run(work_root)
    invalid: list[str] = []

    for target in raw["targets"]:
        suite = target["suite"]
        name = target["name"]
        for row in target["rows"]:
            baseline = row["baseline"]
            candidate = row["inherited-only"]
            for kind, item in (("baseline", baseline), ("inherited-only", candidate)):
                child = float(item["child_s"])
                if not item["verify_ok"]:
                    invalid.append(f"{suite}/{name}:rep-{row['rep']}:{kind}:verify")
                if item["tree_sha256"] != target["tree_sha256"]:
                    invalid.append(f"{suite}/{name}:rep-{row['rep']}:{kind}:tree_identity")
                if not math.isfinite(child) or child <= 0:
                    invalid.append(f"{suite}/{name}:rep-{row['rep']}:{kind}:positive_child")
                delta_ok, delta_state = _delta_state(item)
                item["v3_delta_state"] = delta_state
                if not delta_ok:
                    invalid.append(f"{suite}/{name}:rep-{row['rep']}:{kind}:delta_state")
            if int(candidate["delta_calls"]) > int(baseline["delta_calls"]):
                invalid.append(f"{suite}/{name}:rep-{row['rep']}:candidate_delta_call_growth")

        for kind in ("baseline", "inherited-only"):
            sizes = {int(row[kind]["archive_bytes"]) for row in target["rows"]}
            shas = {row[kind]["archive_sha256"] for row in target["rows"]}
            if len(sizes) != 1 or len(shas) != 1:
                invalid.append(f"{suite}/{name}:{kind}:archive-nondeterministic")

    if invalid:
        decision = "INVALID"
    else:
        all_identical = all(target["byte_identical"] for target in raw["targets"])
        any_real_reduction = any(
            int(row["inherited-only"]["delta_calls"]) < int(row["baseline"]["delta_calls"])
            for target in raw["targets"] for row in target["rows"]
        )
        any_larger = any(int(target["byte_delta"]) > 0 for target in raw["targets"])
        any_smaller = any(int(target["byte_delta"]) < 0 for target in raw["targets"])
        if all_identical and any_real_reduction:
            decision = "DISCOVERY_SOURCE_RUNTIME_MATRIX_BYTE_DEAD"
        elif any_smaller and not any_larger:
            decision = "DISCOVERY_SOURCE_RUNTIME_MATRIX_ALTERNATE_SMALLER"
        else:
            decision = "DISCOVERY_SOURCE_TRANSFER_MIXED"

    return {
        "schema": "cmpct-v030-discovery-runtime-matrix-transfer-v3",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "preregistration": PREREG,
        "decision": decision,
        "invalid_reasons": invalid,
        "targets": raw["targets"],
        "v2_diagnostic_invalid_reasons": raw["invalid_reasons"],
        "contract": {
            "targets": raw["contract"]["targets"],
            "repetitions": raw["contract"]["repetitions"],
            "single_ablation": raw["contract"]["single_ablation"],
            "product_changed": False,
            "release_credit": False,
            "supersedes": "cmpct-v030-discovery-runtime-matrix-transfer-v2",
            "validity_change": "zero calls + zero delta wall is valid non-applicability; candidate call growth invalid",
        },
        "release_credit": False,
    }


def main() -> None:
    _self_check_validity_model()
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": result["decision"],
        "invalid_reasons": result["invalid_reasons"],
        "targets": [
            {
                "target": f"{row['suite']}/{row['name']}",
                "byte_delta": row["byte_delta"],
                "delta_call_reduction_fraction": row["delta_call_reduction_fraction"],
                "child_wall_ratio": row["child_wall_ratio"],
                "delta_wall_ratio": row["delta_wall_ratio"],
            }
            for row in result["targets"]
        ],
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
