from __future__ import annotations

"""Compatibility surface for the portable CMPCT1 Genesis measurement contract.

The original V2 prototype duplicated the sealed executor in order to add a path-independent
scientific identity.  V1 now owns that capability directly, so keeping two execution loops
would create a worse risk: future fixes could land in one executor but not the other.

This module therefore preserves the V2 output contract while delegating all corpus sealing,
adapter execution, mutation checks, raw persistence, validation, and calendar locks to the
single V1 execution path.  It adds no contender logic, comparison, scoring, or winner
selection.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.one import one_genesis_gate_measurement_executor as v1


def execute(
    *,
    candidate_sha: str,
    raw_dir: Path,
    now_value: str | None,
    fixture: bool,
    execute_real_gate: bool,
    adapters_path: Path | None,
    work_root: Path | None,
) -> dict[str, Any]:
    """Run the single sealed executor and expose the stable V2 evidence labels."""
    result = v1.execute(
        candidate_sha=candidate_sha,
        raw_dir=raw_dir,
        now_value=now_value,
        fixture=fixture,
        execute_real_gate=execute_real_gate,
        adapters_path=adapters_path,
        work_root=work_root,
    )

    result["evidence_contract"] = "portable-physical-input-identity-v2"
    state = dict(result["execution_state"])
    state["scientific_input_identity_executed"] = not fixture
    result["execution_state"] = state

    if not fixture:
        seal = dict(result["physical_input_seal"])
        scientific = str(seal["scientific_identity_sha256"])
        if not scientific.startswith("sha256:"):
            scientific = "sha256:" + scientific
        seal["scientific_identity_sha256"] = scientific
        seal["sha256_semantics"] = "diagnostic-file-receipt-only; includes runner-local path"
        seal["scientific_identity_semantics"] = (
            "authoritative cross-run identity of the exact 15 physical workload trees"
        )
        result["physical_input_seal"] = seal

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--execute-real-gate", action="store_true")
    parser.add_argument("--adapters", type=Path)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()

    result = execute(
        candidate_sha=args.candidate_sha,
        raw_dir=args.raw_dir,
        now_value=args.now,
        fixture=args.fixture,
        execute_real_gate=args.execute_real_gate,
        adapters_path=args.adapters,
        work_root=args.work_root,
    )
    v1._write(args.output, result)
    print(json.dumps({
        "schema": result["schema"],
        "evidence_contract": result["evidence_contract"],
        "candidate": result["cmpct1_candidate_sha"],
        "gate_open": result["gate_open"],
        "synthetic": result["synthetic"],
        "workloads": len(result["workloads"]),
        "scientific_input_identity_executed": result["execution_state"]["scientific_input_identity_executed"],
        "scoring_executed": result["execution_state"]["scoring_executed"],
    }, indent=2))


if __name__ == "__main__":
    main()
