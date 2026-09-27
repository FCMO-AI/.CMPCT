from __future__ import annotations

"""Counterfactual opportunity bound for the v0.30 external frontier.

This instrument never predicts a safe prefilter. It grants the current product an
impossible oracle: every row that ultimately publishes canonical r24 may replace
its measured complete-product create wall with the already-measured r24 child wall,
while preserving the exact published archive bytes. The result is an upper bound on
what *perfect* speculative-r25 suppression can accomplish without changing bytes.

The strict joint scoreboard is recomputed under that gift. If creation wins improve
but joint wins do not, representation/size debt is independently blocking the full
domination mission.

Research evidence only. This cannot authorize pruning, release, or a threshold.
"""

import argparse
import json
from pathlib import Path


def _lt(a, b) -> bool:
    return float(a) < float(b)


def run(doc: dict) -> dict:
    rows = []
    removed_wall = 0.0
    current_zip_create = current_zstd_create = current_joint = 0
    oracle_zip_create = oracle_zstd_create = oracle_joint = 0

    for source in doc["rows"]:
        label = source.get("label") or f"{source['suite']}/{source['name']}"
        formats = source["formats"]
        cmpct = formats["cmpct_v030"]
        zip9 = formats["zip_deflate9"]
        zstd = formats["tar_zstd19_solid"]
        profile = cmpct.get("candidate_profile") or {}

        current_create = float(cmpct["create_s"])
        oracle_create = current_create
        oracle_applied = False
        r24_create = profile.get("r24_create_s")
        if cmpct.get("selected") == "r24-fallback" and r24_create is not None:
            oracle_create = float(r24_create)
            oracle_applied = True
            removed_wall += max(0.0, current_create - oracle_create)

        cmpct_bytes = int(cmpct["archive_bytes"])
        zip_bytes = int(zip9["archive_bytes"])
        zstd_bytes = int(zstd["archive_bytes"])
        zip_create = float(zip9["create_s"])
        zstd_create = float(zstd["create_s"])

        cur_zip = _lt(current_create, zip_create)
        cur_zstd = _lt(current_create, zstd_create)
        cur_size = cmpct_bytes < zip_bytes and cmpct_bytes < zstd_bytes
        cur_joint = cur_size and cur_zip and cur_zstd

        ora_zip = _lt(oracle_create, zip_create)
        ora_zstd = _lt(oracle_create, zstd_create)
        ora_joint = cur_size and ora_zip and ora_zstd

        current_zip_create += int(cur_zip)
        current_zstd_create += int(cur_zstd)
        current_joint += int(cur_joint)
        oracle_zip_create += int(ora_zip)
        oracle_zstd_create += int(ora_zstd)
        oracle_joint += int(ora_joint)

        rows.append(
            {
                "label": label,
                "selected": cmpct.get("selected"),
                "cmpct_bytes": cmpct_bytes,
                "zstd19_size_delta_bytes": cmpct_bytes - zstd_bytes,
                "current_create_s": current_create,
                "oracle_create_s": oracle_create,
                "oracle_applied": oracle_applied,
                "oracle_removed_wall_s": max(0.0, current_create - oracle_create),
                "current_beats_zip_create": cur_zip,
                "current_beats_zstd19_create": cur_zstd,
                "oracle_beats_zip_create": ora_zip,
                "oracle_beats_zstd19_create": ora_zstd,
                "strict_size_win": cur_size,
                "current_strict_joint_win": cur_joint,
                "oracle_strict_joint_win": ora_joint,
                "joint_still_size_blocked": ora_zip and ora_zstd and not cur_size,
            }
        )

    return {
        "schema": "cmpct-v030-external-perfect-r25-suppression-bound-v1",
        "workload_count": len(rows),
        "current": {
            "strict_zip_create_wins": current_zip_create,
            "strict_zstd19_create_wins": current_zstd_create,
            "strict_joint_wins": current_joint,
        },
        "perfect_r25_suppression_oracle": {
            "scope": (
                "rows already observed to publish r24-fallback; replace complete-product "
                "create wall with measured r24 child wall; archive bytes remain unchanged"
            ),
            "aggregate_removed_wall_s": removed_wall,
            "strict_zip_create_wins": oracle_zip_create,
            "strict_zstd19_create_wins": oracle_zstd_create,
            "strict_joint_wins": oracle_joint,
            "create_delta_vs_current": {
                "zip": oracle_zip_create - current_zip_create,
                "zstd19": oracle_zstd_create - current_zstd_create,
            },
            "joint_delta_vs_current": oracle_joint - current_joint,
        },
        "rows": rows,
        "decision": (
            "PERFECT_R25_SUPPRESSION_IMPROVES_CREATE_BUT_NOT_JOINT"
            if (oracle_zip_create > current_zip_create or oracle_zstd_create > current_zstd_create)
            and oracle_joint == current_joint
            else "ORACLE_CHANGES_JOINT_FRONTIER"
            if oracle_joint != current_joint
            else "NO_CREATE_OR_JOINT_FRONTIER_CHANGE"
        ),
        "claim_boundary": (
            "Impossible retrospective upper bound only. It cannot identify a safe prefilter, "
            "authorize pruning, transfer timing to another source SHA, or grant product/release credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    doc = json.loads(args.input.read_text())
    result = run(doc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
