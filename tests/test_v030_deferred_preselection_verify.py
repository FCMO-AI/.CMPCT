from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_canonical_final as canonical


def test_canonical_parent_can_defer_temporary_r25_candidate_verification(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "candidate.cmpct"
    calls: list[str] = []

    monkeypatch.setattr(canonical.RC, "treehash", lambda _root: "tree")
    monkeypatch.setattr(
        canonical.RC,
        "_prefixgraph_eligibility",
        lambda _root, _tree: (False, "not-needed"),
    )

    class FakeG04:
        @staticmethod
        def build(_root: Path, target: Path) -> dict:
            target.write_bytes(b"candidate-bytes")
            return {
                "selected": "v029-fallback",
                "v029_bytes": len(b"candidate-bytes"),
                "max_selected_member_read_amplification": 1.0,
            }

    monkeypatch.setattr(canonical.RC, "G04", FakeG04)

    def forbidden_verify(*_args, **_kwargs):
        calls.append("verify")
        raise AssertionError("temporary r25 candidate must not be logically decoded in canonical composition")

    monkeypatch.setattr(canonical.RC, "_verify_component", forbidden_verify)

    result = canonical._overlapped_release_candidate_build(
        root,
        out,
        post_publish_verify=False,
        defer_preselection_verify=True,
    )

    assert calls == []
    assert out.read_bytes() == b"candidate-bytes"
    assert result["preselection_logical_verification"] == "deferred-to-canonical-parent"
    assert result["selected_strong_verify"] is None
    assert result["final_strong_verify"]["verification_state"] == "deferred-to-canonical-parent"
    assert result["final_strong_verify"]["publication_logical_verification_deferred"] is True


def test_standalone_candidate_still_requires_preselection_verification(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "candidate.cmpct"
    calls: list[str] = []

    monkeypatch.setattr(canonical.RC, "treehash", lambda _root: "tree")
    monkeypatch.setattr(
        canonical.RC,
        "_prefixgraph_eligibility",
        lambda _root, _tree: (False, "not-needed"),
    )

    class FakeG04:
        @staticmethod
        def build(_root: Path, target: Path) -> dict:
            target.write_bytes(b"candidate-bytes")
            return {
                "selected": "v029-fallback",
                "v029_bytes": len(b"candidate-bytes"),
                "max_selected_member_read_amplification": 1.0,
            }

    monkeypatch.setattr(canonical.RC, "G04", FakeG04)

    def fake_verify(_path: Path, expected_tree: str, label: str) -> dict:
        calls.append(label)
        return {"ok": True, "tree_sha256": expected_tree}

    monkeypatch.setattr(canonical.RC, "_verify_component", fake_verify)

    result = canonical._overlapped_release_candidate_build(
        root,
        out,
        post_publish_verify=False,
        defer_preselection_verify=False,
    )

    assert calls == ["G0-G4 candidate"]
    assert result["preselection_logical_verification"] == "performed"
    assert result["selected_strong_verify"]["ok"] is True
