from __future__ import annotations

"""Compatibility surface for the portable CMPCT1 Genesis measurement contract.

The original V2 prototype duplicated the sealed executor in order to add a path-independent
scientific identity.  V1 now owns that capability directly, so keeping two execution loops
would create a worse risk: future fixes could land in one executor but not the other.

This module therefore preserves the V2 output contract while delegating corpus sealing,
adapter execution, mutation checks, raw persistence, validation, and the authoritative
execution loop to V1.  Before delegation it independently seals the adapter manifest so a
correct contender checkout cannot be paired with a substituted executable command.  The
calendar/switch denial is mirrored before manifest parsing so premature calls still fail on
the temporal authority, not on incidental file state.

It adds no contender logic, comparison, scoring, or winner selection.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from benchmarks.one import one_genesis_gate_measurement_executor as v1
from benchmarks.one.one_genesis_gate_executor_preflight import V029_SHA, V030_SHA

HARNESS_ADAPTER = (v1.ROOT / "benchmarks" / "one" / "one_genesis_certified_adapter.py").resolve()
CONTENDERS = ("cmpct1", "v0.29", "v0.30")


def _harness_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(v1.ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def _validate_adapter_manifest(path: Path, candidate_sha: str) -> dict[str, Any]:
    """Fail closed if source-bound adapter orchestration was substituted after binding."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Genesis adapter manifest is unreadable") from exc
    if payload.get("schema") != "cmpct-one-genesis-adapters-v1":
        raise RuntimeError("Genesis adapter manifest has wrong schema")
    if payload.get("harness_sha") != _harness_head():
        raise RuntimeError("Genesis adapter manifest harness SHA differs from executing harness")
    if payload.get("candidate_sha") != candidate_sha:
        raise RuntimeError("Genesis adapter manifest candidate SHA differs from requested candidate")
    if payload.get("frozen_comparators") != {"v0.29": V029_SHA, "v0.30": V030_SHA}:
        raise RuntimeError("Genesis adapter manifest frozen comparator authority differs")
    if payload.get("execution_authorized") is not False:
        raise RuntimeError("Genesis adapter manifest must remain non-authorizing")
    if payload.get("comparisons_executed") is not False or payload.get("scoring_executed") is not False:
        raise RuntimeError("Genesis adapter manifest contains post-measurement state")
    if payload.get("winner_selected") is not False:
        raise RuntimeError("Genesis adapter manifest contains winner-selection state")

    adapters = payload.get("adapters")
    if not isinstance(adapters, dict) or set(adapters) != set(CONTENDERS):
        raise RuntimeError("Genesis adapter manifest must define exactly three contenders")
    expected_command = [sys.executable, str(HARNESS_ADAPTER)]
    checkouts: list[Path] = []
    for contender in CONTENDERS:
        row = adapters.get(contender)
        if not isinstance(row, dict):
            raise RuntimeError(f"{contender}: Genesis adapter row is not an object")
        command = row.get("command")
        if command != expected_command:
            raise RuntimeError(f"{contender}: Genesis adapter command differs from certified harness adapter")
        checkout_raw = row.get("checkout")
        if not isinstance(checkout_raw, str) or not checkout_raw:
            raise RuntimeError(f"{contender}: Genesis adapter checkout is missing")
        checkouts.append(Path(checkout_raw).resolve())
    if len(set(checkouts)) != len(CONTENDERS):
        raise RuntimeError("Genesis adapter manifest aliases contender checkouts")
    return payload


def _precheck_real_gate(now_value: str | None, execute_real_gate: bool) -> None:
    now = v1._now(now_value)
    if not v1._gate_open(now):
        raise RuntimeError("real Genesis contender execution is calendar-locked until 2026-09-11 America/Mexico_City")
    if not execute_real_gate:
        raise RuntimeError("real Genesis execution requires explicit --execute-real-gate")


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
    if not fixture:
        _precheck_real_gate(now_value, execute_real_gate)
        if adapters_path is None:
            raise RuntimeError("real Genesis execution requires an adapter manifest")
        _validate_adapter_manifest(adapters_path, candidate_sha)

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
