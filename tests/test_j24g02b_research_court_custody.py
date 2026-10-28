"""Prospective v0.31 source identity includes live research evidence instruments.

An exact Git commit SHA is a separate source witness; the candidate fingerprint must
also change when science programs/episodes change, or fingerprint-only evidence
reuse can silently cross source boundaries. These are generic corpus-free controls.
"""
from __future__ import annotations

from pathlib import Path

from tools import check_v031_candidate_fingerprint as candidate

ROOT = Path(__file__).resolve().parents[1]


def test_existing_research_courts_and_episodes_are_charged() -> None:
    manifest = candidate.load_manifest()
    assert "research/**/*.py" in manifest["fingerprint_globs"]
    assert "research/**/*.jsonl" in manifest["fingerprint_globs"]
    _digest, source_paths = candidate.fingerprint(manifest)
    expected = {
        path.relative_to(ROOT).as_posix()
        for suffix in ("*.py", "*.jsonl")
        for path in (ROOT / "research").rglob(suffix)
        if path.is_file()
    }
    # Vacuous success is not enough on a branch with source-exact research courts.
    assert expected, "no research provenance controls found"
    assert expected.issubset(set(source_paths)), sorted(expected - set(source_paths))


def test_research_court_and_episode_byte_changes_invalidate_fingerprint(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "main.py").write_text("x = 1\n", encoding="utf-8")
    manifest = {
        "fingerprint_globs": ["src/**/*.py", "research/**/*.py", "research/**/*.jsonl"],
        "required_paths": [],
    }
    baseline, _ = candidate.fingerprint(manifest, root=tmp_path)
    research = tmp_path / "research"
    research.mkdir()
    test = research / "nested"
    test.mkdir()
    court = test / "original.py"
    court.write_text("assert True\n", encoding="utf-8")
    added, rows = candidate.fingerprint(manifest, root=tmp_path)
    assert added != baseline and "research/nested/original.py" in rows

    court.write_text("assert False\n", encoding="utf-8")
    mutated, _ = candidate.fingerprint(manifest, root=tmp_path)
    assert mutated != added

    court.rename(test / "renamed.py")
    renamed, rows = candidate.fingerprint(manifest, root=tmp_path)
    assert renamed != mutated and "research/nested/renamed.py" in rows

    episode = research / "discovery_episodes.jsonl"
    episode.write_text('{"prediction":"A"}\n', encoding="utf-8")
    with_episode, rows = candidate.fingerprint(manifest, root=tmp_path)
    assert with_episode != renamed and "research/discovery_episodes.jsonl" in rows

    episode.write_text('{"prediction":"B"}\n', encoding="utf-8")
    episode_changed, _ = candidate.fingerprint(manifest, root=tmp_path)
    assert episode_changed != with_episode
