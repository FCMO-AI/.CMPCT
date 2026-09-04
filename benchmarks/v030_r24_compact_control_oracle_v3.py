from __future__ import annotations

"""Evidence-safe execution wrapper for the r24 compact-control frontier.

v1 contains the measurement and semantic round-trip experiment. v2 only repairs scratch-directory setup. The
v1 gate accidentally includes its own initially-false ``experiment_valid`` value when computing validity, making
every otherwise-valid experiment fail. This wrapper changes no corpus, timing boundary, compact representation,
compression level, payload record, recovery-copy count or promotion hurdle. It recomputes experiment validity only
from the independent invariants and treats a clean four-way miss as durable negative research evidence.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_compact_control_oracle as BASE

_ORIGINAL_MEASURE_TARGET = BASE._measure_target


def _measure_target_with_workdir(source: Path, work: Path) -> dict:
    Path(work).mkdir(parents=True, exist_ok=True)
    return _ORIGINAL_MEASURE_TARGET(source, work)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    BASE._measure_target = _measure_target_with_workdir
    try:
        result = BASE.run(work_root)
    finally:
        BASE._measure_target = _ORIGINAL_MEASURE_TARGET

    target = result["target"]
    experiment_valid = all(
        (
            bool(target["semantic_index_roundtrip_exact"]),
            bool(target["two_authenticated_control_copies_retained"]),
            bool(target["physical_payload_records_unchanged"]),
            bool(target["projected_size_deterministic"]),
            bool(target["tree_deterministic"]),
            bool(target["comparator_sizes_deterministic"]),
        )
    )
    promotion_earned = experiment_valid and bool(target["strict_four_way_potential"])
    result["schema"] = "cmpct-v030-r24-compact-control-oracle-v3"
    result["gate"] = {
        "target_semantic_roundtrip_exact": bool(target["semantic_index_roundtrip_exact"]),
        "target_two_recovery_copies_retained": bool(target["two_authenticated_control_copies_retained"]),
        "target_payload_records_unchanged": bool(target["physical_payload_records_unchanged"]),
        "target_measurement_deterministic": bool(
            target["projected_size_deterministic"]
            and target["tree_deterministic"]
            and target["comparator_sizes_deterministic"]
        ),
        "experiment_valid": experiment_valid,
        "target_strict_four_way_potential": bool(target["strict_four_way_potential"]),
        "promotion_earned": promotion_earned,
    }
    result["contract"]["negative_result_policy"] = (
        "a valid measured rejection is green research evidence; production promotion still requires a strict "
        "size+creation win against both ZIP and Zstd plus ordinary release authority"
    )
    result["diagnosis"] = {
        "compact_control_total_saving_bytes": 2 * int(target["saving_per_control_copy_bytes"]),
        "remaining_zstd_size_deficit_bytes": int(target["projected_two_copy_archive_bytes"]) - int(target["zstd19_bytes"]),
        "creation_already_beats_zip": float(target["median_conservative_projected_create_s"]) < float(target["median_zip_create_s"]),
        "creation_already_beats_zstd19": float(target["median_conservative_projected_create_s"]) < float(target["median_zstd19_create_s"]),
        "next_frontier": "payload/container tiny-file overhead; control-plane compaction alone is insufficient",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-compact-control.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target": result["target"], "diagnosis": result["diagnosis"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("r24 compact-control experiment invalid")


if __name__ == "__main__":
    main()
