from __future__ import annotations

"""Fail-closed validator for the preregistered ONE-G0.2 creation profile V2 receipt."""

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "cmpct-one-g02-general-law-archive-creation-profile-v2"
DECISIONS = {
    "ADVANCE_CREATION_PROFILE_V2",
    "HOLD_CREATION_COMPUTE_V2",
    "RETIRE_OR_REPAIR_V2",
}
EXPECTED_CASES = {"unrelated-1m", "exact-copy-1m", "add8-1m", "mixed-8x512k"}


def _fail(message: str) -> None:
    raise ValueError(message)


def validate(payload: dict[str, Any]) -> None:
    if payload.get("schema") != SCHEMA:
        _fail("wrong schema")
    if payload.get("experimental_version") != "ONE-G0.2":
        _fail("wrong experimental version")
    if payload.get("decision") not in DECISIONS:
        _fail("unknown decision")
    for flag in (
        "genesis_inputs_executed",
        "genesis_comparison_executed",
        "genesis_scoring_executed",
        "genesis_winner_selected",
    ):
        if payload.get(flag) is not False:
            _fail(f"Genesis-dark flag violated: {flag}")

    if payload.get("rounds") != 9:
        _fail("round count drifted")
    rows = payload.get("rows")
    if not isinstance(rows, list) or {row.get("case") for row in rows} != EXPECTED_CASES or len(rows) != 4:
        _fail("case identity drifted")

    all_semantic = True
    all_structure = True
    all_single_pass = True
    all_no_auth_reread = True
    for row in rows:
        candidate = row.get("candidate")
        baseline = row.get("baseline")
        if not isinstance(candidate, list) or not isinstance(baseline, list):
            _fail(f"missing samples for {row.get('case')}")
        if len(candidate) != 9 or len(baseline) != 9:
            _fail(f"sample count drifted for {row.get('case')}")
        if row.get("candidate_wire_deterministic") is not True or row.get("baseline_wire_deterministic") is not True:
            all_semantic = False
        if row.get("candidate_structure_consistent") is not True:
            all_structure = False
        evidence = row.get("candidate_structure_evidence")
        if not isinstance(evidence, dict) or evidence.get("ok") is not True:
            all_structure = False

        for sample in candidate:
            if sample.get("roundtrip_exact") is not True:
                all_semantic = False
            stats = sample.get("stats")
            if not isinstance(stats, dict):
                _fail(f"missing candidate stats for {row.get('case')}")
            logical = stats.get("logical_file_bytes")
            source_read = stats.get("source_read_bytes")
            auth_reread = stats.get("authentication_source_reread_bytes")
            if not isinstance(logical, int) or not isinstance(source_read, int) or logical < 0 or source_read < 0:
                _fail(f"invalid source accounting for {row.get('case')}")
            if source_read != logical:
                all_single_pass = False
            if auth_reread != 0:
                all_no_auth_reread = False
        for sample in baseline:
            if sample.get("roundtrip_exact") is not True:
                all_semantic = False
            stats = sample.get("stats")
            if not isinstance(stats, dict) or "authentication_source_reread_bytes" not in stats:
                _fail(f"baseline reread accounting not retained for {row.get('case')}")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        _fail("missing gates")
    if gates.get("semantic_exact") is not all_semantic:
        _fail("semantic gate contradicts raw samples")
    if gates.get("reader_structure_exact") is not all_structure:
        _fail("reader-structure gate contradicts raw samples")
    if gates.get("candidate_auth_source_reread_zero") is not all_no_auth_reread:
        _fail("auth-reread gate contradicts raw samples")
    if not all_single_pass:
        _fail("candidate did not preserve one logical source pass in every measured sample")

    # The preregistered decision priority is fail-closed. Semantic/structure failures
    # cannot be downgraded to a mere performance HOLD or promoted to ADVANCE.
    if (not all_semantic or not all_structure) and payload["decision"] != "RETIRE_OR_REPAIR_V2":
        _fail("semantic/structure failure was not retired/repaired")
    if payload["decision"] == "ADVANCE_CREATION_PROFILE_V2":
        required_bool = (
            "semantic_exact",
            "reader_structure_exact",
            "unrelated_wire_byte_identical",
            "every_productive_stored_smaller",
            "candidate_auth_source_reread_zero",
        )
        if not all(gates.get(key) is True for key in required_bool):
            _fail("ADVANCE contradicts boolean gates")
        required_numeric = {
            "unrelated_cpu_ratio": 1.15,
            "unrelated_wall_ratio": 1.15,
            "unrelated_worst_paired_cpu_ratio": 1.30,
            "unrelated_rss_ratio": 1.10,
            "productive_median_stored_ratio": 0.70,
            "productive_median_cpu_ratio": 2.00,
            "productive_worst_cpu_ratio": 2.50,
            "productive_median_rss_ratio": 1.20,
        }
        for key, ceiling in required_numeric.items():
            value = gates.get(key)
            if not isinstance(value, (int, float)) or value > ceiling:
                _fail(f"ADVANCE exceeds frozen {key} ceiling")
        if gates.get("unrelated_exact_proof_bytes") != 0:
            _fail("ADVANCE paid exact proof bytes on unrelated control")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=Path("one-g02-general-law-archive-creation-profile-v2.json"))
    args = parser.parse_args()
    payload = json.loads(args.path.read_text(encoding="utf-8"))
    validate(payload)
    print(f"VALID {payload['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
