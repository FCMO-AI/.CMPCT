from __future__ import annotations

"""Decisive payload-floor instrument for the Shifted native base+patch R4 family.

The base+patch oracle already prices honest construction and emits complete verified
artifacts.  This instrument asks a narrower question before any further engineering:
if every byte of path/integrity/framing metadata were made free, could the encoded
anchor+patch payload itself be strictly smaller than the same-run solid Zstd-19
competitor?

A non-negative payload gap is a proof that framing work cannot make this family win
and therefore retires the single-anchor native-patch representation.  A negative gap
only rehabilitates framing/metadata as a possible debt; it grants no release credit.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_shifted_zstd_patch_oracle as BASE

SCHEMA = "cmpct-v030-shifted-zstd-patch-payload-floor-v1"


def run(work_root: Path) -> dict:
    evidence = BASE.run(work_root)
    zstd_bytes = int(evidence["comparators"]["tar_zstd19_solid"]["archive_bytes"])
    rows = []
    for arm in evidence["arms"]:
        payload_bytes = int(arm["anchor_zstd19_bytes"]) + int(arm["patch_blob_total"])
        framing_bytes = int(arm["archive_bytes"]) - payload_bytes
        payload_gap = payload_bytes - zstd_bytes
        rows.append(
            {
                "level": int(arm["level"]),
                "archive_bytes": int(arm["archive_bytes"]),
                "payload_bytes": payload_bytes,
                "framing_bytes": framing_bytes,
                "payload_gap_to_zstd19_bytes": payload_gap,
                "payload_can_strictly_beat_zstd19_if_framing_were_free": payload_gap < 0,
                "tree_verified": bool(arm["tree_verified"]),
                "artifact_sha256": arm["artifact_sha256"],
            }
        )

    best = min(rows, key=lambda row: (row["payload_bytes"], row["level"]))
    impossible = int(best["payload_gap_to_zstd19_bytes"]) >= 0
    return {
        "schema": SCHEMA,
        "target": evidence["target"],
        "contract": {
            "research_only": True,
            "release_credit": False,
            "benchmark_identity_used_in_representation": False,
            "optimistic_bound_excludes_all_path_integrity_and_framing_bytes": True,
            "base_oracle_prices_complete_construction": True,
            "same_run_solid_zstd19_comparator": True,
        },
        "tree_sha256": evidence["tree_sha256"],
        "zstd19_bytes": zstd_bytes,
        "arms": rows,
        "summary": {
            "best_payload_level": int(best["level"]),
            "best_payload_bytes": int(best["payload_bytes"]),
            "best_payload_gap_to_zstd19_bytes": int(best["payload_gap_to_zstd19_bytes"]),
            "best_current_framing_bytes": int(best["framing_bytes"]),
            "single_anchor_native_patch_payload_floor_cannot_beat_zstd19": impossible,
            "decision_if_verified": "RETIRE_FAMILY" if impossible else "REHABILITATE_DEBT",
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
