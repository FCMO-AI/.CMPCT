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


def test_oracle_accepts_shipping_canonical_identity_bound_to_same_research_tree(tmp_path: Path) -> None:
    archive = tmp_path / "shipping.cmpct"
    archive.write_bytes(b"archive")
    receipt = {
        "mode": "shipping",
        "eligible": True,
        "worker_failed": False,
        "research_tree_sha256": "research-tree",
        "expected_verification_tree_sha256": "canonical-tree",
        "verified_tree_sha256": "canonical-tree",
        "tree_sha256": "canonical-tree",
        "verification_identity_domain": "canonical-filesystem-user-tree-v1",
    }
    assert oracle._receipt_identity_valid("shipping", receipt, "research-tree", archive) is True
    receipt["tree_sha256"] = "research-tree"
    assert oracle._receipt_identity_valid("shipping", receipt, "research-tree", archive) is False


def test_oracle_accepts_structural_prefixgraph_ineligibility_without_archive(tmp_path: Path) -> None:
    archive = tmp_path / "prefixgraph.cmpct"
    receipt = {
        "mode": "prefixgraph",
        "eligible": False,
        "worker_failed": False,
        "research_tree_sha256": "research-tree",
        "expected_verification_tree_sha256": "research-tree",
        "verification_identity_domain": "research-content-tree-v1",
        "reject_reason": "structural-contract-ineligible",
    }
    assert oracle._receipt_identity_valid("prefixgraph", receipt, "research-tree", archive) is True
    assert oracle._receipt_identity_valid("g04", receipt, "research-tree", archive) is False


def test_oracle_rejects_identity_mismatch_or_ineligible_archive_publication(tmp_path: Path) -> None:
    archive = tmp_path / "candidate.cmpct"
    archive.write_bytes(b"unexpected")
    ineligible = {
        "mode": "prefixgraph",
        "eligible": False,
        "worker_failed": False,
        "research_tree_sha256": "research-tree",
        "reject_reason": "structural-contract-ineligible",
    }
    assert oracle._receipt_identity_valid("prefixgraph", ineligible, "research-tree", archive) is False

    eligible = {
        "mode": "g04",
        "eligible": True,
        "worker_failed": False,
        "research_tree_sha256": "research-tree",
        "expected_verification_tree_sha256": "research-tree",
        "verified_tree_sha256": "wrong-tree",
        "tree_sha256": "wrong-tree",
    }
    assert oracle._receipt_identity_valid("g04", eligible, "research-tree", archive) is False
