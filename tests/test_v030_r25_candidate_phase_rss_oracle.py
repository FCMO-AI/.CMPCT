from pathlib import Path
from types import SimpleNamespace

from benchmarks import v030_r25_candidate_phase_rss_oracle as oracle


def test_worker_failure_preserves_stdout_stderr_and_fails_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        oracle.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=17,
            stdout="partial worker context\n",
            stderr="causal traceback\n",
        ),
    )
    receipt = oracle._run_worker("shipping", tmp_path / "source", tmp_path / "archive.cmpct")
    assert receipt["eligible"] is False
    assert receipt["worker_failed"] is True
    assert receipt["returncode"] == 17
    assert receipt["stdout"] == "partial worker context\n"
    assert receipt["stderr"] == "causal traceback\n"
    assert receipt["archive_exists"] is False


def test_successful_worker_receipt_is_not_reclassified_as_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        oracle.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout='noise before receipt\n{"eligible": true, "tree_sha256": "abc"}\n',
            stderr="",
        ),
    )
    receipt = oracle._run_worker("g04", tmp_path / "source", tmp_path / "archive.cmpct")
    assert receipt["eligible"] is True
    assert receipt["worker_failed"] is False
    assert receipt["returncode"] == 0
    assert receipt["tree_sha256"] == "abc"
