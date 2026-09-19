"""Hostile research gate for ML verification folding; never release authority by itself."""
from pathlib import Path

from benchmarks import v030_ml_semantic_fold_hostile as hostile


def test_ml_semantic_fold_hostile_matrix(tmp_path: Path) -> None:
    result = hostile.run(tmp_path / "hostile")
    assert result["release_credit"] is False
    checks = {row["label"]: row for row in result["checks"]}
    assert set(checks) == {
        "payload-sha",
        "physical-usize-bound",
        "physical-csize-bound",
        "record-crc",
        "transactional-corrupt-payload",
        "strong-verify-corrupt-payload",
    }
    assert all(row["failed_closed"] for row in checks.values())
    assert checks["transactional-corrupt-payload"]["destination_tree_preserved"] is True
    assert isinstance(result["scope_probe"]["strong_verify_accepted_under_global_oracle"], bool)
