from __future__ import annotations

from contextlib import nullcontext
import hashlib
from pathlib import Path

from experiments import entropygraph_v030_canonical_final as canonical


def test_canonical_r25_verification_uses_one_policy_content_pass(monkeypatch, tmp_path: Path) -> None:
    archive = tmp_path / "candidate.cmpct"
    archive.write_bytes(canonical.G04_MAGIC + b"fixture")
    policy_calls: list[Path] = []

    monkeypatch.setattr(canonical, "_profile_for_archive", lambda path: (canonical.REVISION, "geometry-g04"))
    monkeypatch.setattr(canonical, "_revision25_profile_context", lambda: nullcontext())

    def fake_policy(path: Path) -> dict:
        policy_calls.append(Path(path))
        return {"ok": True, "tree_sha256": "content-graph", "max_member_read_amplification": 1.0}

    digest = hashlib.sha256(b"payload").digest()
    manifest = {
        "raw": b"authenticated-manifest",
        "manifest": {"entries": [["payload.bin", "f", 0o644, 0, 0, 0, [], [7, digest]]]},
        "regular": {"payload.bin": (7, digest)},
        "hardlinks": {},
    }
    monkeypatch.setattr(canonical.POLICY, "strong_verify", fake_policy)
    monkeypatch.setattr(canonical, "_validated_manifest", lambda path: manifest)
    monkeypatch.setattr(canonical, "_semantic_tree_sha", lambda decoded: "user-tree")

    # Footnote: if canonical verification ever regresses to re-decoding regular members after the policy stream,
    # this sentinel turns the redundant second pass into a hard test failure rather than a quiet runtime tax.
    monkeypatch.setattr(
        canonical,
        "_read_profile_member",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("redundant regular-member decode")),
    )

    result = canonical.strong_verify(archive)
    assert result["ok"] is True
    assert result["tree_sha256"] == "user-tree"
    assert result["content_graph_tree_sha256"] == "content-graph"
    assert result["verification_strategy"] == "single-content-pass-plus-authenticated-manifest-binding"
    assert result["regular_members_verified_by_policy_stream"] == 1
    assert policy_calls == [archive]


def test_canonical_r25_builder_defers_only_inner_final_reopen(monkeypatch, tmp_path: Path) -> None:
    staged = tmp_path / "staged"
    staged.mkdir()
    out = tmp_path / "candidate.cmpct"
    observed: dict[str, object] = {}

    monkeypatch.setattr(canonical, "_revision25_profile_context", lambda: nullcontext())

    def fake_build(
        root: Path,
        archive: Path,
        *,
        post_publish_verify: bool = True,
        defer_preselection_verify: bool = False,
    ) -> dict:
        observed["root"] = Path(root)
        observed["archive"] = Path(archive)
        observed["post_publish_verify"] = post_publish_verify
        observed["defer_preselection_verify"] = defer_preselection_verify
        archive.write_bytes(canonical.G04_MAGIC + b"candidate")
        return {"archive_bytes": archive.stat().st_size, "selected": "geometry-g04"}

    monkeypatch.setattr(canonical.RC, "build", fake_build)
    result = canonical._r25_build(staged, out)

    assert observed == {
        "root": staged,
        "archive": out,
        "post_publish_verify": False,
        "defer_preselection_verify": True,
    }
    assert result["selected"] == "geometry-g04"
    assert result["create_s"] >= 0

    # Footnote: both deferrals belong only to this canonical composition seam. ``RC.build`` itself keeps
    # verification enabled by default for standalone tournament callers, while the canonical parent verifies the
    # one artifact that can actually publish after the exact r24/r25 byte decision.
