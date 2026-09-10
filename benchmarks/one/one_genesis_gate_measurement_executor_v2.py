from __future__ import annotations

"""Portable-evidence wrapper for the CMPCT1 Genesis raw-measurement executor.

V1 already owns and rechecks the exact physical exam trees. V2 keeps that contract but
splits two different identities that V1 currently conflates:

* ``physical-input-seal.json`` is a diagnostic receipt. It intentionally records the
  runner-local ``work_root`` and therefore its file SHA-256 is not portable.
* ``physical-input-scientific-identity.json`` hashes only suite/name/files/logical bytes/
  tree SHA-256, so identical exam bytes have one scientific identity across machines.

Both receipts are persisted before the first real contender runs. The diagnostic file
hash is retained for exact-source forensics; only the scientific identity is admissible
as the cross-run identity of the 15-workload exam.

This module deliberately reuses V1's corpus generation, raw validation, adapter contract
and calendar/explicit-activation locks. It adds no contender logic, comparison, scoring,
or winner selection.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from benchmarks.one import one_genesis_gate_measurement_executor as v1
from benchmarks.one.one_genesis_gate_executor_preflight import V029_SHA, V030_SHA, build_plan
from benchmarks.one.one_genesis_physical_seal_identity import scientific_identity_receipt


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
    """Execute V1 semantics with a portable scientific input identity.

    Fixture mode remains contender-free. Real mode persists both the diagnostic seal and
    its path-independent scientific identity before any adapter is invoked.
    """
    if not v1._looks_like_sha(candidate_sha):
        raise RuntimeError("candidate SHA must be a 40-hex commit")
    now = v1._now(now_value)
    opened = v1._gate_open(now)

    preflight = build_plan(candidate_sha, now=now)
    if preflight.get("decision") != "EXECUTOR_PREFLIGHT_READY":
        raise RuntimeError("Genesis executor preflight is not READY: " + "; ".join(preflight.get("errors", [])))

    if fixture:
        if execute_real_gate or adapters_path is not None or work_root is not None:
            raise RuntimeError("fixture mode cannot accept real-execution inputs")
    else:
        if not opened:
            raise RuntimeError("real Genesis contender execution is calendar-locked until 2026-09-11 America/Mexico_City")
        if not execute_real_gate:
            raise RuntimeError("real Genesis execution requires explicit --execute-real-gate")
        if adapters_path is None or work_root is None:
            raise RuntimeError("real Genesis execution requires --adapters and --work-root")

    sources = {"cmpct1": candidate_sha, "v0.29": V029_SHA, "v0.30": V030_SHA}
    raw_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, dict[str, Any]] = {}
    adapter_manifest: dict[str, Any] = {}

    physical_seal_path: Path | None = None
    physical_seal_file_digest: str | None = None
    scientific_identity_path: Path | None = None
    scientific_identity_digest: str | None = None

    if not fixture:
        adapter_manifest = v1._load(adapters_path)  # type: ignore[arg-type]
        if adapter_manifest.get("schema") != "cmpct-one-genesis-adapters-v1":
            raise RuntimeError("invalid Genesis adapter manifest schema")
        if set(adapter_manifest.get("adapters", {})) != set(v1.CONTENDERS):
            raise RuntimeError("adapter manifest must define exactly cmpct1, v0.29, v0.30")

        assert work_root is not None
        physical_seal = v1._seal_physical_inputs(work_root)
        physical_seal_path = raw_dir / "physical-input-seal.json"
        v1._write(physical_seal_path, physical_seal)
        physical_seal_file_digest = "sha256:" + v1._sha256(physical_seal_path)

        scientific = scientific_identity_receipt(physical_seal)
        scientific_rows = scientific.get("scientific_identity", {}).get("rows", [])
        if len(scientific_rows) != 15:
            raise RuntimeError("scientific physical-input identity did not bind exactly 15 workloads")
        scientific_identity_path = raw_dir / "physical-input-scientific-identity.json"
        v1._write(scientific_identity_path, scientific)
        scientific_identity_digest = "sha256:" + str(scientific["scientific_identity_sha256"])

    # Sequential persistence is intentional: a later failure cannot erase earlier raw evidence.
    for contender in v1.CONTENDERS:
        raw_path = raw_dir / f"{contender.replace('.', '')}-raw.json"
        if fixture:
            payload = v1._fixture_output(contender, sources[contender])
            v1._write(raw_path, payload)
        else:
            assert work_root is not None
            v1._assert_physical_inputs_unchanged(work_root)
            payload = v1._adapter_output(
                contender,
                sources[contender],
                adapter_manifest["adapters"][contender],
                work_root,
                raw_path,
            )
            v1._assert_physical_inputs_unchanged(work_root)
        v1._validate_raw(payload, contender, sources[contender], synthetic=fixture)
        outputs[contender] = payload

    frozen = v1._identity_rows()
    by_contender = {
        contender: {(row["suite"], row["name"]): row for row in outputs[contender]["rows"]}
        for contender in v1.CONTENDERS
    }
    joined_rows: list[dict[str, Any]] = []
    for identity in frozen:
        key = (identity["suite"], identity["name"])
        joined_rows.append(
            {
                **identity,
                "measurements": {
                    contender: by_contender[contender][key]["measurement"] for contender in v1.CONTENDERS
                },
            }
        )

    return {
        "schema": "cmpct-one-genesis-raw-measurements-v1",
        "evidence_contract": "portable-physical-input-identity-v2",
        "claim_boundary": "raw contender measurements only; no comparisons, scoring, or winner selection",
        "experimental_version": "ONE-G0.2",
        "cmpct1_candidate_sha": candidate_sha,
        "frozen_comparators": {"v0.29": V029_SHA, "v0.30": V030_SHA},
        "gate_open": opened,
        "synthetic": fixture,
        "production_eligible": not fixture,
        "physical_input_seal": (
            {
                "path": str(physical_seal_path.resolve()),
                "sha256": physical_seal_file_digest,
                "sha256_semantics": "diagnostic-file-receipt-only; includes runner-local path",
                "scientific_identity_path": str(scientific_identity_path.resolve()),
                "scientific_identity_sha256": scientific_identity_digest,
                "scientific_identity_semantics": "authoritative cross-run identity of the exact 15 physical workload trees",
                "all_15_identities_exact": True,
            }
            if physical_seal_path is not None and scientific_identity_path is not None
            else {"status": "not-executed-in-fixture"}
        ),
        "raw_files": [str((raw_dir / f"{name.replace('.', '')}-raw.json").resolve()) for name in v1.CONTENDERS],
        "workloads": joined_rows,
        "execution_state": {
            "physical_input_seal_executed": not fixture,
            "scientific_input_identity_executed": not fixture,
            "contender_measurement_executed": not fixture,
            "fixture_plumbing_executed": fixture,
            "comparisons_executed": False,
            "scoring_executed": False,
            "winner_selected": False,
        },
    }


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
