"""O11: source-custody negative/positive court for Git-tracked worktree bytes.

A generated Rust build file must not change source identity. Dirty or newly
tracked source must; untracked source is not a canonical Git source member.
"""
from __future__ import annotations

import glob
import subprocess
from pathlib import Path

import pytest

from tools import check_v031_candidate_fingerprint as candidate


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _fixture(root: Path) -> dict:
    (root / "native/cmpct-core/src").mkdir(parents=True)
    (root / "src/cmpct").mkdir(parents=True)
    (root / "native/cmpct-core/src/lib.rs").write_text("fn stable() {}\n")
    (root / "src/cmpct/core.py").write_text("STABLE = 1\n")
    _run_git(root, "init", "-q")
    _run_git(root, "add", "--", "native/cmpct-core/src/lib.rs", "src/cmpct/core.py")
    return {
        "fingerprint_globs": ["native/**/*.rs", "native/**/*.c", "native/**/*.h", "src/**/*.py"],
        "required_paths": ["native/cmpct-core/src/lib.rs", "src/cmpct/core.py"],
    }


def test_generated_native_build_products_do_not_contaminate_source_identity(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    before, rows = candidate.fingerprint(manifest, root=tmp_path)
    assert rows == ["native/cmpct-core/src/lib.rs", "src/cmpct/core.py"]

    generated = tmp_path / "native/cmpct-core/target/release/build/serde/out/private.rs"
    generated.parent.mkdir(parents=True)
    generated.write_text("// untracked generated Rust\n")
    (generated.parent / "flag_check.c").write_text("/* generated */\n")
    (generated.parent / "zstd.h").write_text("/* generated */\n")
    # A glob-only historical roster would have treated this untracked source
    # as product identity; verify that the falsifier actually matches the glob.
    assert str(generated) in glob.glob(str(tmp_path / "native/**/*.rs"), recursive=True)
    after, actual_rows = candidate.fingerprint(manifest, root=tmp_path)
    assert (after, actual_rows) == (before, rows)


def test_unstaged_mutation_and_newly_staged_addition_change_source_identity(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    baseline, rows = candidate.fingerprint(manifest, root=tmp_path)
    tracked = tmp_path / "src/cmpct/core.py"
    tracked.write_text("STABLE = 2\n")  # dirty tracked bytes; no git add
    changed, _ = candidate.fingerprint(manifest, root=tmp_path)
    assert changed != baseline

    added = tmp_path / "src/cmpct/new.py"
    added.write_text("ADDED = True\n")
    still_untracked, before_add_rows = candidate.fingerprint(manifest, root=tmp_path)
    assert still_untracked == changed and before_add_rows == rows
    _run_git(tmp_path, "add", "--", "src/cmpct/new.py")
    newly_tracked, after_add_rows = candidate.fingerprint(manifest, root=tmp_path)
    assert newly_tracked != changed and "src/cmpct/new.py" in after_add_rows

    added.rename(tmp_path / "src/cmpct/renamed.py")
    _run_git(tmp_path, "add", "-A", "--", "src/cmpct")
    renamed, rename_rows = candidate.fingerprint(manifest, root=tmp_path)
    assert renamed != newly_tracked and "src/cmpct/renamed.py" in rename_rows
    assert "src/cmpct/new.py" not in rename_rows

    (tmp_path / "src/cmpct/renamed.py").unlink()
    deleted, delete_rows = candidate.fingerprint(manifest, root=tmp_path)
    assert deleted != renamed and "src/cmpct/renamed.py" not in delete_rows


def test_tracked_required_source_and_git_root_are_mandatory(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    (tmp_path / "src/cmpct/core.py").unlink()
    with pytest.raises(ValueError, match="missing mandatory"):
        candidate.fingerprint(manifest, root=tmp_path)

    orphan = tmp_path / "unversioned"
    orphan.mkdir()
    (orphan / "a.py").write_text("x = 1\n")
    with pytest.raises(ValueError, match="Git repository root"):
        candidate.fingerprint({"fingerprint_globs": ["*.py"], "required_paths": []}, root=orphan)


def test_untracked_symlink_not_source_but_tracked_symlink_fails_closed(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    baseline, _ = candidate.fingerprint(manifest, root=tmp_path)
    path = tmp_path / "src/cmpct/shortcut.py"
    try:
        path.symlink_to(tmp_path / "src/cmpct/core.py")
    except (OSError, NotImplementedError):
        pytest.skip("this runner does not permit symlink creation")
    untracked, _ = candidate.fingerprint(manifest, root=tmp_path)
    assert untracked == baseline
    _run_git(tmp_path, "add", "--", "src/cmpct/shortcut.py")
    with pytest.raises(ValueError, match="symlink"):
        candidate.fingerprint(manifest, root=tmp_path)
