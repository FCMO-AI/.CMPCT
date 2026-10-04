from __future__ import annotations

"""Product-boundary proof for the recoverable v0.30 logs inverse-edge profile prototype."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as B
from benchmarks import v030_logs_inverse_edge_oracle as BASE
from experiments import entropygraph_v030_logs_inverse_profile as PROFILE


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    workload, accepted = BASE._build_target_root(work_root)
    expected_tree = B._tree(workload)

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-profile-product-", dir=work_root) as td:
        root = Path(td)
        stage = B._normalized_stage(workload, root)
        zip_result = B._zip(stage, root / "baseline.zip", root / "zip-out")
        zstd_result = B._tar_zstd(stage, root / "baseline.tar.zst", root / "zstd-out", root)
        B._verify_extracted(root / "zip-out", expected_tree, "zip")
        B._verify_extracted(root / "zstd-out", expected_tree, "tar-zstd19")

        archive = root / "candidate.cmpct"
        started = time.perf_counter()
        build_stats = PROFILE.build(stage, archive)
        verify = PROFILE.strong_verify(archive)
        create_and_verify_s = time.perf_counter() - started
        extracted = root / "candidate-out"
        PROFILE.extract(archive, extracted)
        B._verify_extracted(extracted, expected_tree, "logs-inverse-profile")
        recovery = PROFILE.recovery_probe(archive)

    accepted_bytes = int(accepted["accepted_v029_bytes"])
    result = {
        "schema": "cmpct-v030-logs-inverse-profile-productization-v1",
        "claim_boundary": "recoverable bounded profile prototype; selector/native/Android promotion still prohibited",
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "accepted_v029_bytes": accepted_bytes,
        "timing_boundary": "profile-build+mandatory-complete-strong-verification",
        "candidate": {
            **build_stats,
            "create_and_verify_s": create_and_verify_s,
            "strong_verify": verify,
            "tree_verified": True,
            "recovery": recovery,
        },
        "zip": zip_result,
        "tar_zstd19": zstd_result,
    }
    candidate = result["candidate"]
    gates = {
        "no_regression_vs_v029": candidate["archive_bytes"] <= accepted_bytes,
        "strictly_smaller_than_zip": candidate["archive_bytes"] < zip_result["archive_bytes"],
        "strictly_smaller_than_zstd19": candidate["archive_bytes"] < zstd_result["archive_bytes"],
        "strictly_faster_than_zip": create_and_verify_s < zip_result["create_s"],
        "strictly_faster_than_zstd19": create_and_verify_s < zstd_result["create_s"],
        "strong_verify_green": verify.get("ok") is True,
        "tree_verified": True,
        "locality_green": verify["max_member_read_amplification"] <= 8.0 and verify["max_decode_unit_bytes"] <= 8 * 1024 * 1024,
        "primary_recovers_from_tail": recovery["primary_damage"].get("ok") is True and recovery["primary_damage"].get("recovery_route") == "tail",
        "tail_recovers_from_primary": recovery["tail_damage"].get("ok") is True and recovery["tail_damage"].get("recovery_route") == "primary",
        "both_metadata_copies_fail_closed": recovery["both_failed_closed"] is True,
        "single_payload_copy": build_stats["payload_copies"] == 1,
        "two_control_copies": build_stats["recovery_control_copies"] == 2,
    }
    gates["passed"] = all(gates.values())
    result["gate"] = gates
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("recoverable logs inverse profile has not earned productization boundary")


if __name__ == "__main__":
    main()
