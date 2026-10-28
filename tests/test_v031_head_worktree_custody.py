"""Prospective HEAD/worktree binding for candidate source receipts (J24G03).

These tests do not relax the existing filesystem-mutation fingerprint properties.
A candidate receipt must be rejected if its named Git HEAD does not own the
actual source rows that the fingerprint just measured.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools import check_v031_candidate_fingerprint as C


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _fixture_repo(root: Path) -> tuple[dict, str]:
    (root / "src").mkdir()
    (root / "research").mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "cmpct-tests@example.invalid")
    _git(root, "config", "user.name", "CMPCT custody test")
    (root / "src/first.py").write_text("VALUE = 1\n")
    (root / "src/second.py").write_text("SECOND = 2\n")
    _git(root, "add", "src/first.py", "src/second.py")
    _git(root, "commit", "-qm", "clean baseline")
    return {
        "fingerprint_globs": ["src/**/*.py", "research/**/*.py", "setup.py", "native/**/*.c"],
        "required_paths": ["src/first.py", "src/second.py"],
    }, _git(root, "rev-parse", "HEAD")


def _check(root: Path, manifest: dict, expected_head: str) -> tuple[str, list[str]]:
    digest, rows = C.fingerprint(manifest, root=root)
    C.assert_git_head_custody(rows, root=root, expected_head=expected_head)
    return digest, rows


def test_clean_git_checkout_and_uncovered_untracked_file_are_accepted(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    digest, rows = _check(tmp_path, manifest, head)
    assert len(digest) == 64 and rows == ["src/first.py", "src/second.py"]
    (tmp_path / "uncovered.tmp").write_text("ordinary generated non-source\n")
    assert _check(tmp_path, manifest, head) == (digest, rows)


def test_untracked_matching_research_source_fails_closed(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    baseline, _ = _check(tmp_path, manifest, head)
    (tmp_path / "research/ephemeral.py").write_text("UNTRACKED = True\n")
    changed, rows = C.fingerprint(manifest, root=tmp_path)
    assert changed != baseline
    assert _git(tmp_path, "rev-parse", "HEAD") == head
    with pytest.raises(ValueError, match="untracked|Git HEAD"):
        C.assert_git_head_custody(rows, root=tmp_path, expected_head=head)


def test_unstaged_staged_and_deleted_tracked_sources_fail_closed(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    source = tmp_path / "src/first.py"
    source.write_text("VALUE = 42\n")
    with pytest.raises(ValueError, match="dirty|Git HEAD"):
        _check(tmp_path, manifest, head)
    _git(tmp_path, "add", "src/first.py")
    with pytest.raises(ValueError, match="dirty|Git HEAD"):
        _check(tmp_path, manifest, head)
    source.unlink()
    with pytest.raises(ValueError, match="dirty|Git HEAD"):
        _check(tmp_path, manifest, head)


def test_head_mismatch_fails_even_for_clean_checkout(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    digest, rows = _check(tmp_path, manifest, head)
    assert digest
    with pytest.raises(ValueError, match="HEAD|changed"):
        C.assert_git_head_custody(rows, root=tmp_path, expected_head="0" * 40)


def test_cargo_target_generated_sources_do_not_enter_git_custody(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    baseline = _check(tmp_path, manifest, head)
    cargo = tmp_path / "native/crate/target/release/build/generated"
    cargo.mkdir(parents=True)
    (cargo / "flag_check.c").write_text("int generated = 1;\n")
    assert _check(tmp_path, manifest, head) == baseline


def test_optional_root_setup_py_binds_committed_build_semantics(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    baseline, _ = _check(tmp_path, manifest, head)
    setup = tmp_path / "setup.py"
    setup.write_text("from setuptools import setup\nsetup(name='cmpct')\n")
    # Adding an untracked source is not permission to emit a HEAD-bound receipt.
    digest, rows = C.fingerprint(manifest, root=tmp_path)
    assert digest != baseline and "setup.py" in rows
    with pytest.raises(ValueError, match="untracked|Git HEAD"):
        C.assert_git_head_custody(rows, root=tmp_path, expected_head=head)
    _git(tmp_path, "add", "setup.py")
    _git(tmp_path, "commit", "-qm", "add optional root build source")
    committed = _git(tmp_path, "rev-parse", "HEAD")
    accepted, rows = _check(tmp_path, manifest, committed)
    assert accepted == digest and "setup.py" in rows
    setup.write_text("from setuptools import setup\nsetup(name='cmpct2')\n")
    with pytest.raises(ValueError, match="dirty|Git HEAD"):
        _check(tmp_path, manifest, committed)
    _git(tmp_path, "add", "setup.py")
    _git(tmp_path, "commit", "-qm", "change root build semantics")
    revised, _ = _check(tmp_path, manifest, _git(tmp_path, "rev-parse", "HEAD"))
    assert revised != accepted


def test_missing_repository_does_not_emulate_authority(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src/first.py").write_text("valid = True\n")
    with pytest.raises(ValueError, match="Git HEAD|repository"):
        C.assert_git_head_custody(["src/first.py"], root=tmp_path, expected_head="a" * 40)


def test_assume_unchanged_index_flag_cannot_hide_dirty_source(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    source = tmp_path / "src/first.py"
    _git(tmp_path, "update-index", "--assume-unchanged", "src/first.py")
    source.write_text("VALUE = 999999999\n")
    # Independently reproduce the misleading negative from ordinary git diff:
    # the index flag suppresses a genuinely changed tracked source.
    assert _git(tmp_path, "diff", "--name-only", "HEAD", "--") == ""
    assert "h src/first.py" in _git(tmp_path, "ls-files", "-v")
    with pytest.raises(ValueError, match="index|flag|HEAD"):
        _check(tmp_path, manifest, head)
    _git(tmp_path, "update-index", "--no-assume-unchanged", "src/first.py")
    with pytest.raises(ValueError, match="dirty|HEAD"):
        _check(tmp_path, manifest, head)


def test_skip_worktree_index_flag_is_not_accepted_as_full_source(tmp_path: Path) -> None:
    manifest, head = _fixture_repo(tmp_path)
    _git(tmp_path, "update-index", "--skip-worktree", "src/second.py")
    assert "S src/second.py" in _git(tmp_path, "ls-files", "-v")
    with pytest.raises(ValueError, match="index|flag|HEAD"):
        _check(tmp_path, manifest, head)
    _git(tmp_path, "update-index", "--no-skip-worktree", "src/second.py")
    assert len(_check(tmp_path, manifest, head)[0]) == 64
