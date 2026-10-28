from __future__ import annotations

"""Run the recoverable logs product-boundary proof with the physical-locality v2 writer."""

import argparse
import json
from pathlib import Path

from benchmarks import v030_logs_inverse_profile_productization as PROOF
from experiments import entropygraph_v030_logs_inverse_profile_v2 as PROFILE


def run(work_root: Path) -> dict:
    previous = PROOF.PROFILE
    PROOF.PROFILE = PROFILE
    try:
        result = PROOF.run(work_root)
    finally:
        PROOF.PROFILE = previous
    result = dict(result)
    result["schema"] = "cmpct-v030-logs-inverse-profile-productization-v2"
    result["physical_locality_writer"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-profile-product-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("recoverable physical-locality logs profile has not earned productization boundary")


if __name__ == "__main__":
    main()
