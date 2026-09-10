from __future__ import annotations

from copy import deepcopy

from benchmarks.one.one_genesis_gate_result_validator import (
    V029_SHA,
    V030_SHA,
    validate_gate_result,
)


def _measurement(stored: int):
    return {
        "stored_bytes": stored,
        "creation": {"measured": True, "cpu_s": 1.0, "wall_s": 1.0, "peak_rss_bytes": 1},
        "whole_read": {"measured": True, "cpu_s": 1.0, "wall_s": 1.0},
        "selective_access": {
            "measured": True,
            "requested_bytes": 4096,
            "touched_bytes": 4096,
            "decoded_bytes": 4096,
            "authentication_bytes": 64,
            "reconstruction_work": 4096,
            "temporary_bytes": 4096,
        },
        "semantics": {"exact": True, "integrity": True, "recovery": True, "portable": True},
        "reader_burden": {"reader_discovery": False, "hidden_codec": False},
    }


def _payload():
    rows = []
    for suite, count in (("neutral_hostile_v1", 10), ("resemblance_hostile_v1", 5)):
        for i in range(count):
            name = f"w{i:02d}"
            rows.append(
                {
                    "suite": suite,
                    "name": name,
                    "files": i + 1,
                    "logical_bytes": 8192 + i,
                    "tree_sha256": f"{i + 1:064x}",
                    "measurements": {
                        "cmpct1": _measurement(1000),
                        "v0.29": _measurement(1100),
                        "v0.30": _measurement(1050),
                    },
                    "comparisons": {
                        "v0.29": {
                            "size_status": "SIZE_WIN",
                            "creation_status": "WIN",
                            "read_status": "WIN",
                            "selective_resource_status": "WIN",
                            "semantic_status": "PASS",
                            "verdict": "WIN",
                        },
                        "v0.30": {
                            "size_status": "SIZE_WIN",
                            "creation_status": "WIN",
                            "read_status": "WIN",
                            "selective_resource_status": "WIN",
                            "semantic_status": "PASS",
                            "verdict": "WIN",
                        },
                    },
                }
            )
    return {
        "schema": "cmpct-one-genesis-gate-result-v1",
        "cmpct1_candidate_sha": "a" * 40,
        "frozen_comparators": {"v0.29": V029_SHA, "v0.30": V030_SHA},
        "readiness_authority": {
            "source_sha": "b" * 40,
            "artifact_digest": "sha256:" + "c" * 64,
            "all_15_identities_exact": True,
        },
        "environment": {
            "os": "test",
            "cpu": "test",
            "python": "test",
            "toolchain": "test",
            "codec_versions": {},
            "runner_identity": "test",
        },
        "measurement_protocol": {
            "repetitions": 3,
            "statistic": "median",
            "process_boundaries": ["library"],
            "cache_semantics": "declared",
            "integrity_semantics": "same for contenders",
        },
        "workloads": rows,
        "aggregates": {"v0.29": {}, "v0.30": {}},
        "v030_frontier_ledger": {
            "ledger_path": "docs/one/evidence/ONE_GENESIS_FROZEN_COMPARATOR_LEDGER_2026-09-09.md",
            "ledger_commit": "d" * 40,
            "evidence_refs": ["record"],
            "strongest_admissible_result": "record",
        },
        "strongest_one_negative": {
            "evidence_ref": "record",
            "summary": "negative",
            "unresolved_debt": True,
        },
        "final_adjudication": {
            "decision": "KEEP_CMPCT1_PRIMARY",
            "rationale": "test",
            "hostile_review": "test",
            "gate_run_source_sha": "a" * 40,
            "artifact_digest": "sha256:" + "e" * 64,
        },
    }


def test_complete_gate_result_shape_passes():
    result = validate_gate_result(_payload())
    assert result.ok, result.errors


def test_missing_workload_fails_closed():
    payload = _payload()
    payload["workloads"].pop()
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("exactly 15 workload" in error for error in result.errors)


def test_wrong_frozen_comparator_fails_closed():
    payload = _payload()
    payload["frozen_comparators"]["v0.30"] = "f" * 40
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("v0.30 comparator SHA" in error for error in result.errors)


def test_missing_selective_measurement_family_fails_closed():
    payload = _payload()
    del payload["workloads"][0]["measurements"]["cmpct1"]["selective_access"]
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("missing measurement family selective_access" in error for error in result.errors)


def test_unavailable_is_explicitly_accepted_but_synthetic_zero_is_not():
    payload = _payload()
    payload["workloads"][0]["measurements"]["cmpct1"]["selective_access"] = "unavailable"
    assert validate_gate_result(payload).ok

    invalid = deepcopy(payload)
    invalid["workloads"][0]["measurements"]["cmpct1"]["selective_access"] = {
        "requested_bytes": 0,
        "touched_bytes": 0,
    }
    result = validate_gate_result(invalid)
    assert not result.ok
    assert any("zero without measured=true" in error for error in result.errors)


def test_duplicate_identity_fails_closed():
    payload = _payload()
    payload["workloads"][1]["name"] = payload["workloads"][0]["name"]
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("duplicate workload identity" in error for error in result.errors)
