from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks import v030_federated_candidate_productization as P


LABEL = "02_office_workspace"
KEY = ("neutral_hostile_v1", LABEL)


def _install_fake_builders(monkeypatch: pytest.MonkeyPatch, *, candidate_bytes: int, r24_bytes: int) -> None:
    monkeypatch.setattr(P.GENERAL, "_historical_treehash", lambda source: "accepted-tree")
    monkeypatch.setattr(P.CAND, "_treehash", lambda source: "user-tree")

    def candidate_build(source: Path, archive: Path) -> dict:
        archive.write_bytes(b"candidate")
        return {
            "archive_bytes": candidate_bytes,
            "locality": {
                "within_release_bounds": True,
                "max_member_read_amplification": 1.0,
                "max_decode_unit_bytes": 4096,
            },
        }

    monkeypatch.setattr(P.CAND, "build", candidate_build)
    monkeypatch.setattr(
        P.CAND,
        "strong_verify",
        lambda archive: {"ok": True, "canonical_user_tree_sha256": "user-tree"},
    )
    monkeypatch.setattr(
        P,
        "_recovery",
        lambda archive, work: {
            "primary_recovers_from_tail": True,
            "tail_recovers_from_primary": True,
            "both_fail_closed": True,
        },
    )

    def r24_build(source: Path, archive: Path) -> dict:
        archive.write_bytes(b"r24")
        return {"archive_bytes": r24_bytes}

    monkeypatch.setattr(P.CANON, "_r24_build", r24_build)
    monkeypatch.setattr(P.CANON, "strong_verify", lambda archive: {"ok": True, "format_revision": 24})


def test_product_floor_requires_candidate_to_beat_accepted_v029_and_genuine_r24(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    accepted = {KEY: {"tree_sha256": "accepted-tree", "accepted_v029_bytes": 100}}
    _install_fake_builders(monkeypatch, candidate_bytes=90, r24_bytes=110)

    result = P._product_floor(LABEL, source, tmp_path, accepted)

    assert result["candidate_bytes"] == 90
    assert result["saving_vs_accepted_v029_bytes"] == 10
    assert result["saving_vs_genuine_r24_bytes"] == 20
    assert result["strictly_smaller_than_accepted_v029"] is True
    assert result["strictly_smaller_than_genuine_r24"] is True


def test_product_floor_does_not_confuse_r24_win_with_accepted_v029_win(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    accepted = {KEY: {"tree_sha256": "accepted-tree", "accepted_v029_bytes": 100}}
    _install_fake_builders(monkeypatch, candidate_bytes=105, r24_bytes=110)

    result = P._product_floor(LABEL, source, tmp_path, accepted)

    assert result["strictly_smaller_than_accepted_v029"] is False
    assert result["strictly_smaller_than_genuine_r24"] is True
    assert result["saving_vs_accepted_v029_bytes"] == -5
    assert result["saving_vs_genuine_r24_bytes"] == 5


def test_product_floor_rejects_wrong_repaired_source_before_building(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    accepted = {KEY: {"tree_sha256": "accepted-tree", "accepted_v029_bytes": 100}}
    monkeypatch.setattr(P.GENERAL, "_historical_treehash", lambda source: "wrong-tree")

    called = False

    def forbidden_build(source: Path, archive: Path) -> dict:
        nonlocal called
        called = True
        raise AssertionError("candidate must not build on the wrong source identity")

    monkeypatch.setattr(P.CAND, "build", forbidden_build)

    with pytest.raises(RuntimeError, match="product-floor source identity drift"):
        P._product_floor(LABEL, source, tmp_path, accepted)

    assert called is False
