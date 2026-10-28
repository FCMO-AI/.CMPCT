from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks.v030_r25_candidate_phase_rss_worker import (
    _require_verified_tree,
    _verification_identity_for_mode,
)


class _Candidate:
    @staticmethod
    def treehash(_source: Path) -> str:
        return "research-tree"


class _Canonical:
    @staticmethod
    def treehash(_source: Path) -> str:
        return "canonical-filesystem-tree"


def test_shipping_uses_canonical_filesystem_verification_identity(tmp_path: Path) -> None:
    research, expected, domain = _verification_identity_for_mode("shipping", tmp_path, _Candidate, _Canonical)
    assert research == "research-tree"
    assert expected == "canonical-filesystem-tree"
    assert domain == "canonical-filesystem-user-tree-v1"
    assert _require_verified_tree("shipping", {"ok": True, "tree_sha256": expected}, expected) == expected


def test_isolated_candidates_keep_research_content_identity(tmp_path: Path) -> None:
    for mode in ("g04", "prefixgraph"):
        research, expected, domain = _verification_identity_for_mode(mode, tmp_path, _Candidate, _Canonical)
        assert research == expected == "research-tree"
        assert domain == "research-content-tree-v1"
        assert _require_verified_tree(mode, {"ok": True, "tree_sha256": expected}, expected) == expected


def test_verification_identity_mismatch_still_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="verification identity mismatch"):
        _require_verified_tree(
            "shipping",
            {"ok": True, "tree_sha256": "research-tree"},
            "canonical-filesystem-tree",
        )


def test_failed_strong_verification_still_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="failed strong verification"):
        _require_verified_tree("g04", {"ok": False, "tree_sha256": "research-tree"}, "research-tree")
