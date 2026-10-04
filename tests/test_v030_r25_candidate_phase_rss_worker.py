from pathlib import Path

import pytest

from benchmarks import v030_r25_candidate_phase_rss_worker as worker


class _Owner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def strong_verify(self, archive):
        self.calls.append(Path(archive))
        return dict(self.result)


class _Candidate:
    def __init__(self, owner):
        self.READER = owner


def test_strong_verify_dispatches_each_archive_to_its_semantic_owner(tmp_path):
    archive = tmp_path / "candidate.cmpct"
    archive.write_bytes(b"diagnostic")
    shipping = _Owner({"ok": True, "tree_sha256": "s"})
    prefixgraph = _Owner({"ok": True, "tree_sha256": "p"})
    canonical = _Owner({"ok": True, "tree_sha256": "g"})
    candidate = _Candidate(canonical)

    result, owner = worker._strong_verify_for_mode("shipping", prefixgraph, candidate, shipping, archive)
    assert result["tree_sha256"] == "s"
    assert owner == "release-product-dispatcher"
    assert shipping.calls == [archive]
    assert prefixgraph.calls == []
    assert canonical.calls == []

    result, owner = worker._strong_verify_for_mode("prefixgraph", prefixgraph, candidate, shipping, archive)
    assert result["tree_sha256"] == "p"
    assert owner == "prefixgraph-grammar-owner"
    assert prefixgraph.calls == [archive]
    assert canonical.calls == []

    result, owner = worker._strong_verify_for_mode("g04", prefixgraph, candidate, shipping, archive)
    assert result["tree_sha256"] == "g"
    assert owner == "canonical-r25-candidate-reader"
    assert canonical.calls == [archive]


def test_require_verified_tree_remains_fail_closed():
    with pytest.raises(RuntimeError, match="failed strong verification"):
        worker._require_verified_tree("prefixgraph", {"ok": False, "tree_sha256": "x"}, "x")
    with pytest.raises(RuntimeError, match="identity mismatch"):
        worker._require_verified_tree("prefixgraph", {"ok": True, "tree_sha256": "x"}, "y")
