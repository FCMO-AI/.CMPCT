from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from benchmarks.one.one_genesis_gate_result_validator import (
    IDENTITY_MANIFEST,
    V029_SHA,
    V030_SHA,
    validate_gate_result,
)

READINESS_SOURCE = "070d4f803c7b4441f517fc5c0b90f19214f5b05f"
READINESS_DIGEST = "sha256:a1b009dfed8deeed3a9d46ab0cc4cdaf224141c903b2c8bdcdeae32434074abd"


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
    frozen = json.loads(Path(IDENTITY_MANIFEST).read_text(encoding="utf-8"))
    rows = []
    for identity in frozen["workloads"]:
        rows.append(
            {
                **identity,
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
            "source_sha": READINESS_SOURCE,
            "artifact_digest": READINESS_DIGEST,
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


def test_substituted_workload_identity_fails_closed():
    payload = _payload()
    payload["workloads"][0]["name"] = "01_plausible_but_not_frozen"
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("unexpected gate workload identity" in error for error in result.errors)
    assert any("missing frozen gate workload identity" in error for error in result.errors)


def test_identity_hash_drift_fails_closed():
    payload = _payload()
    payload["workloads"][0]["tree_sha256"] = "f" * 64
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("tree_sha256 differs from frozen readiness authority" in error for error in result.errors)


def test_wrong_readiness_authority_fails_closed():
    payload = _payload()
    payload["readiness_authority"]["artifact_digest"] = "sha256:" + "0" * 64
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("readiness artifact digest differs" in error for error in result.errors)


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


def test_size_status_must_match_retained_stored_bytes():
    payload = _payload()
    payload["workloads"][0]["comparisons"]["v0.29"]["size_status"] = "SIZE_LOSS"
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("contradicts stored bytes" in error for error in result.errors)

    payload = _payload()
    payload["workloads"][0]["measurements"]["cmpct1"]["stored_bytes"] = 1100
    payload["workloads"][0]["comparisons"]["v0.29"]["size_status"] = "SIZE_EQUAL"
    assert validate_gate_result(payload).ok


def test_unavailable_stored_bytes_require_unavailable_size_status():
    payload = _payload()
    payload["workloads"][0]["measurements"]["cmpct1"]["stored_bytes"] = "unavailable"
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("size_status must be unavailable" in error for error in result.errors)

    payload["workloads"][0]["comparisons"]["v0.29"]["size_status"] = "unavailable"
    payload["workloads"][0]["comparisons"]["v0.30"]["size_status"] = "unavailable"
    assert validate_gate_result(payload).ok


def test_duplicate_identity_fails_closed():
    payload = _payload()
    payload["workloads"][1]["name"] = payload["workloads"][0]["name"]
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("duplicate workload identity" in error for error in result.errors)


def test_candidate_and_gate_source_must_be_same_hex_commit():
    payload = _payload()
    payload["cmpct1_candidate_sha"] = "not-a-commit-but-forty-characters-long----"
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("40-hex commit identity" in error for error in result.errors)

    payload = _payload()
    payload["final_adjudication"]["gate_run_source_sha"] = "b" * 40
    result = validate_gate_result(payload)
    assert not result.ok
    assert any("must equal frozen cmpct1_candidate_sha" in error for error in result.errors)
