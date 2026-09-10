from __future__ import annotations

from copy import deepcopy

import pytest

from benchmarks.one.one_g02_general_law_archive_creation_profile_v2_validate import validate


def _sample() -> dict:
    return {
        "roundtrip_exact": True,
        "stats": {
            "logical_file_bytes": 100,
            "source_read_bytes": 100,
            "authentication_source_reread_bytes": 0,
        },
    }


def _payload() -> dict:
    rows = []
    for case in ("unrelated-1m", "exact-copy-1m", "add8-1m", "mixed-8x512k"):
        rows.append(
            {
                "case": case,
                "candidate": [_sample() for _ in range(9)],
                "baseline": [_sample() for _ in range(9)],
                "candidate_wire_deterministic": True,
                "baseline_wire_deterministic": True,
                "candidate_structure_consistent": True,
                "candidate_structure_evidence": {"ok": True},
            }
        )
    return {
        "schema": "cmpct-one-g02-general-law-archive-creation-profile-v2",
        "experimental_version": "ONE-G0.2",
        "decision": "ADVANCE_CREATION_PROFILE_V2",
        "rounds": 9,
        "rows": rows,
        "gates": {
            "semantic_exact": True,
            "reader_structure_exact": True,
            "unrelated_cpu_ratio": 1.0,
            "unrelated_wall_ratio": 1.0,
            "unrelated_worst_paired_cpu_ratio": 1.0,
            "unrelated_rss_ratio": 1.0,
            "unrelated_wire_byte_identical": True,
            "unrelated_exact_proof_bytes": 0,
            "productive_median_stored_ratio": 0.5,
            "productive_median_cpu_ratio": 1.0,
            "productive_worst_cpu_ratio": 1.0,
            "productive_median_rss_ratio": 1.0,
            "every_productive_stored_smaller": True,
            "candidate_auth_source_reread_zero": True,
        },
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }


def test_validator_accepts_complete_advance_receipt():
    validate(_payload())


@pytest.mark.parametrize(
    "mutator",
    [
        lambda p: p.update(genesis_inputs_executed=True),
        lambda p: p["rows"].pop(),
        lambda p: p["rows"][0]["candidate"].pop(),
        lambda p: p["rows"][0]["candidate"][0]["stats"].update(source_read_bytes=99),
        lambda p: p["rows"][0]["candidate"][0]["stats"].update(authentication_source_reread_bytes=1),
        lambda p: p["rows"][0].update(candidate_structure_evidence={"ok": False}),
        lambda p: p["gates"].update(productive_median_cpu_ratio=2.01),
        lambda p: p["gates"].update(unrelated_exact_proof_bytes=1),
    ],
)
def test_validator_rejects_corrupt_or_overclaimed_receipts(mutator):
    payload = deepcopy(_payload())
    mutator(payload)
    with pytest.raises(ValueError):
        validate(payload)
