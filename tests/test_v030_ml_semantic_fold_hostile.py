"""Hostile research gate for ML verification folding; never release authority by itself."""
from pathlib import Path

from benchmarks import v030_ml_semantic_fold_hostile as hostile


def test_ml_semantic_fold_hostile_matrix(tmp_path: Path) -> None:
    # The historical research oracle intentionally installs process-global reader replacements because its
    # standalone worker exits immediately afterwards.  Pytest does not: restore those globals so this research
    # probe cannot weaken strict-reader tests that happen to execute later in the same interpreter.
    reader = hostile.FOLD.VR.C.POLICY.R
    original_session = reader._G04Session
    original_consume_file = reader._consume_g04_file
    try:
        result = hostile.run(tmp_path / "hostile")
    finally:
        reader._G04Session = original_session
        reader._consume_g04_file = original_consume_file

    assert result["release_credit"] is False
    checks = {row["label"]: row for row in result["checks"]}
    assert set(checks) == {
        "payload-sha",
        "physical-usize-bound",
        "physical-csize-bound",
        "record-crc",
        "post-crc-in-memory-record-fault",
        "transactional-corrupt-payload",
        "strong-verify-corrupt-payload",
    }
    assert all(row["failed_closed"] for row in checks.values())
    assert checks["post-crc-in-memory-record-fault"]["fault_injected"] is True
    assert checks["transactional-corrupt-payload"]["destination_tree_preserved"] is True
    scope = result["scope_probe"]
    assert isinstance(scope["strong_verify_accepted_under_global_oracle"], bool)
    assert isinstance(scope["selective_read_accepted_under_global_oracle"], bool)
    assert isinstance(scope["selective_read_bytes_exact"], bool)
