"""Custody helpers for the CMPCT1 / ONE Genesis week gate.

This module deliberately does *not* run the September 11 decision early. It freezes the exact
15-workload identity set and rejects accidental comparison of historical aggregates from different
repair substrates. The result-bearing gate must bind one regenerated input manifest and execute all
credited engines against those same trees.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

FROZEN_V029_SHA = "02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d"
FROZEN_V030_SHA = "f4b158a55a08b9b18b50e4e4abe4b9251048c772"
FROZEN_V029_HISTORY = Path("benchmarks/history/2026-08-17-mosaic-v029-generalization-v2.json")
FROZEN_V029_RECORDED_BYTES = 137_507_932
DEFERRED_V030_REPAIRED_V029_BYTES = 137_499_525


@dataclass(frozen=True, slots=True)
class WorkloadIdentity:
    suite: str
    name: str
    tree_sha256: str

    @property
    def key(self) -> str:
        return f"{self.suite}/{self.name}"


WORKLOADS = (
    WorkloadIdentity("neutral_hostile_v1", "01_developer_repository", "ddcdf1ae1b61042634aae40b1b12da629feb98cb45db23c56d1da15334b74645"),
    WorkloadIdentity("neutral_hostile_v1", "02_office_workspace", "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"),
    WorkloadIdentity("neutral_hostile_v1", "03_media_library", "1966d025d334e4bf6ea38656188708d400f26b6ca53bb581b497357dcdbf869a"),
    WorkloadIdentity("neutral_hostile_v1", "04_analytics_and_database", "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d"),
    WorkloadIdentity("neutral_hostile_v1", "05_logs_and_telemetry", "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931"),
    WorkloadIdentity("neutral_hostile_v1", "06_incremental_backups", "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"),
    WorkloadIdentity("neutral_hostile_v1", "07_incompressible_and_encrypted_like", "da4f37ac1d7a6751c4adcaabb50cc2cd6f2ffbed7bd2100d34b9ef597f7d1d80"),
    WorkloadIdentity("neutral_hostile_v1", "08_many_tiny_files", "a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f"),
    WorkloadIdentity("neutral_hostile_v1", "09_ml_artifacts", "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d"),
    WorkloadIdentity("neutral_hostile_v1", "10_large_mixed_binary", "9373f96626c7f463b4112bf138ac5db766e7e71def9b209c7ba28fe44f0878d3"),
    WorkloadIdentity("resemblance_hostile_v1", "01_shifted_versions", "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd"),
    WorkloadIdentity("resemblance_hostile_v1", "02_false_neighbors", "3427fd306a10a7c293d4303323d64948ee74d4065353bf99310cfed34dc73d0e"),
    WorkloadIdentity("resemblance_hostile_v1", "03_boundary_churn", "3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d"),
    WorkloadIdentity("resemblance_hostile_v1", "04_deflate_family", "527a9e356e923e5bcc26566a8f677a7f7277af1577493e09c2bdca1b6d17154a"),
    WorkloadIdentity("resemblance_hostile_v1", "05_incompressible", "1efe49fb1adb16ef911f64f44d41629db599dbeef264d72fd8f26e40515130e4"),
)


def expected_tree_map() -> dict[str, str]:
    return {row.key: row.tree_sha256 for row in WORKLOADS}


def verify_frozen_v029_history(path: Path = FROZEN_V029_HISTORY) -> dict:
    """Fail closed if the local historical ledger no longer matches frozen custody."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "cmpct-v029-generalization-v2":
        raise AssertionError("unexpected frozen v0.29 history schema")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != len(WORKLOADS):
        raise AssertionError("frozen v0.29 history must contain exactly 15 rows")
    actual = {f"{row['suite']}/{row['name']}": row["tree_sha256"] for row in rows}
    if actual != expected_tree_map():
        missing = sorted(set(expected_tree_map()) - set(actual))
        extra = sorted(set(actual) - set(expected_tree_map()))
        drift = sorted(key for key in set(actual) & set(expected_tree_map()) if actual[key] != expected_tree_map()[key])
        raise AssertionError(f"frozen 15-tree identity drift: missing={missing} extra={extra} changed={drift}")
    totals = payload.get("totals", {})
    if totals.get("workloads") != 15:
        raise AssertionError("frozen v0.29 workload count drift")
    if totals.get("candidate_bytes") != FROZEN_V029_RECORDED_BYTES:
        raise AssertionError("frozen v0.29 aggregate identity drift")
    return payload


def assert_historical_aggregates_not_interchangeable() -> None:
    """Encode the known custody mismatch so future gate code cannot silently equate it."""
    if FROZEN_V029_RECORDED_BYTES == DEFERRED_V030_REPAIRED_V029_BYTES:
        raise AssertionError("historical substrate distinction unexpectedly disappeared")


def gate_manifest() -> dict:
    verify_frozen_v029_history()
    assert_historical_aggregates_not_interchangeable()
    return {
        "schema": "cmpct-one-genesis-gate-custody-v1",
        "frozen_v029_sha": FROZEN_V029_SHA,
        "frozen_v030_sha": FROZEN_V030_SHA,
        "historical_aggregate_warning": {
            "frozen_v029_recorded_bytes": FROZEN_V029_RECORDED_BYTES,
            "deferred_v030_repaired_v029_bytes": DEFERRED_V030_REPAIRED_V029_BYTES,
            "directly_comparable": False,
        },
        "workloads": [
            {"suite": row.suite, "name": row.name, "tree_sha256": row.tree_sha256}
            for row in WORKLOADS
        ],
    }


if __name__ == "__main__":
    print(json.dumps(gate_manifest(), sort_keys=True))
