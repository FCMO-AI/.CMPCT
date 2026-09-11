from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from benchmarks.one.one_genesis_gate_manifest import (
    DEFERRED_V030_REPAIRED_V029_BYTES,
    FROZEN_V029_RECORDED_BYTES,
    FROZEN_V029_SHA,
    FROZEN_V030_SHA,
    WORKLOADS,
    gate_manifest,
    verify_frozen_v029_history,
)


def test_genesis_gate_manifest_binds_exact_authorities_and_15_unique_trees():
    manifest = gate_manifest()
    assert manifest["frozen_v029_sha"] == FROZEN_V029_SHA
    assert manifest["frozen_v030_sha"] == FROZEN_V030_SHA
    assert len(manifest["workloads"]) == 15
    keys = {(row["suite"], row["name"]) for row in manifest["workloads"]}
    hashes = {row["tree_sha256"] for row in manifest["workloads"]}
    assert len(keys) == 15
    assert len(hashes) == 15
    assert all(len(value) == 64 for value in hashes)


def test_historical_v029_and_v030_repaired_aggregate_are_explicitly_not_same_substrate():
    manifest = gate_manifest()
    warning = manifest["historical_aggregate_warning"]
    assert FROZEN_V029_RECORDED_BYTES == 137_507_932
    assert DEFERRED_V030_REPAIRED_V029_BYTES == 137_499_525
    assert warning["directly_comparable"] is False
    assert warning["frozen_v029_recorded_bytes"] != warning["deferred_v030_repaired_v029_bytes"]


def test_frozen_v029_history_rejects_tree_identity_drift(tmp_path: Path):
    payload = verify_frozen_v029_history()
    mutant = copy.deepcopy(payload)
    mutant["rows"][0]["tree_sha256"] = "0" * 64
    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(mutant), encoding="utf-8")
    with pytest.raises(AssertionError, match="identity drift"):
        verify_frozen_v029_history(path)


def test_frozen_v029_history_rejects_aggregate_drift(tmp_path: Path):
    payload = verify_frozen_v029_history()
    mutant = copy.deepcopy(payload)
    mutant["totals"]["candidate_bytes"] += 1
    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(mutant), encoding="utf-8")
    with pytest.raises(AssertionError, match="aggregate identity drift"):
        verify_frozen_v029_history(path)


def test_workload_order_remains_10_neutral_plus_5_resemblance():
    assert [row.name for row in WORKLOADS[:10]] == [
        "01_developer_repository",
        "02_office_workspace",
        "03_media_library",
        "04_analytics_and_database",
        "05_logs_and_telemetry",
        "06_incremental_backups",
        "07_incompressible_and_encrypted_like",
        "08_many_tiny_files",
        "09_ml_artifacts",
        "10_large_mixed_binary",
    ]
    assert [row.name for row in WORKLOADS[10:]] == [
        "01_shifted_versions",
        "02_false_neighbors",
        "03_boundary_churn",
        "04_deflate_family",
        "05_incompressible",
    ]
