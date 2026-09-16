from __future__ import annotations

"""Run the logs inverse product-boundary proof with canonical filesystem semantics included in the artifact."""

import argparse
import json
from pathlib import Path
import subprocess

from benchmarks import v030_logs_inverse_profile_productization as PROOF
from experiments import entropygraph_v030_logs_inverse_profile_v3 as PROFILE


def run(work_root: Path) -> dict:
    previous = PROOF.PROFILE
    PROOF.PROFILE = PROFILE
    try:
        result = PROOF.run(work_root)
    finally:
        PROOF.PROFILE = previous
    result = dict(result)
    result["schema"] = "cmpct-v030-logs-inverse-profile-productization-v3"
    result["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    result["canonical_filesystem_manifest"] = True
    result["claim_boundary"] = (
        "recoverable bounded logs profile with canonical r25 filesystem manifest; selector/native/Android "
        "promotion still prohibited"
    )
    result["gate"] = dict(result["gate"])
    result["gate"]["canonical_filesystem_manifest"] = (
        result["candidate"].get("canonical_filesystem_manifest") is True
        and result["candidate"]["strong_verify"].get("canonical_filesystem_manifest") is True
    )
    result["gate"]["passed"] = all(result["gate"].values())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product-v3-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product-v3.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_commit": result["source_commit"], "candidate": result["candidate"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical-filesystem logs inverse profile has not earned productization boundary")


if __name__ == "__main__":
    main()
