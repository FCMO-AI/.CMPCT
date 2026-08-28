from pathlib import Path
from types import SimpleNamespace

from benchmarks import v030_r25_candidate_phase_rss_oracle as oracle
from benchmarks import v030_r25_candidate_phase_rss_worker as worker


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


def test_shipping_verification_uses_product_dispatcher_for_portfolio_fallbacks(tmp_path: Path) -> None:
    calls: list[str] = []

    class Product:
        @staticmethod
        def strong_verify(path):
            calls.append("product")
            return {"ok": True, "tree_sha256": "tree", "representation": "accepted-v029"}

    class PrefixGraph:
        @staticmethod
        def strong_verify(path):
            calls.append("prefixgraph")
            raise AssertionError("shipping fallback must not be forced through the PrefixGraph research reader")

    class CandidateReader:
        @staticmethod
        def strong_verify(path):
            calls.append("candidate")
            raise AssertionError("shipping fallback must not be forced through the canonical-r25 reader")

    candidate = SimpleNamespace(READER=CandidateReader())
    verified, owner = worker._strong_verify_for_mode(
        "shipping", PrefixGraph(), candidate, Product(), tmp_path / "shipping.cmpct"
    )
    assert verified["ok"] is True
    assert verified["representation"] == "accepted-v029"
    assert owner == "release-product-dispatcher"
    assert calls == ["product"]


def test_isolated_candidates_use_their_own_semantic_owners(tmp_path: Path) -> None:
    calls: list[str] = []

    class Product:
        @staticmethod
        def strong_verify(path):
            calls.append("product")
            raise AssertionError("isolated candidate should not use the shipping portfolio dispatcher")

    class PrefixGraph:
        @staticmethod
        def strong_verify(path):
            calls.append("prefixgraph")
            return {"ok": True, "tree_sha256": "tree"}

    class CandidateReader:
        @staticmethod
        def strong_verify(path):
            calls.append("candidate")
            return {"ok": True, "tree_sha256": "tree"}

    candidate = SimpleNamespace(READER=CandidateReader())

    verified, owner = worker._strong_verify_for_mode(
        "g04", PrefixGraph(), candidate, Product(), tmp_path / "g04.cmpct"
    )
    assert verified["ok"] is True
    assert owner == "canonical-r25-candidate-reader"

    verified, owner = worker._strong_verify_for_mode(
        "prefixgraph", PrefixGraph(), candidate, Product(), tmp_path / "prefixgraph.cmpct"
    )
    assert verified["ok"] is True
    assert owner == "prefixgraph-grammar-owner"

    assert calls == ["candidate", "prefixgraph"]
