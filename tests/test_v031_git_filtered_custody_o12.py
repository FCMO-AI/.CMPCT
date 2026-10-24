"""O12: independent adversarial controls for raw versus Git-clean-filtered custody."""
from __future__ import annotations
import subprocess
from pathlib import Path
import pytest
from tools import research_v031_git_filtered_custody_o12 as o12


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def fixture(root: Path) -> dict:
    (root / "src").mkdir()
    git(root, "init", "-q")
    (root / ".gitattributes").write_text("*.py text\n*.bin binary\n", encoding="utf-8")
    (root / "src/a.py").write_bytes(b"alpha\nbeta\n")
    (root / "src/raw.bin").write_bytes(b"\x00\x01\r\n\xff")
    git(root, "add", "--", ".gitattributes", "src/a.py", "src/raw.bin")
    return {"fingerprint_globs": ["src/**/*.py", "src/**/*.bin"],
            "required_paths": ["src/a.py", "src/raw.bin"]}


def test_text_newlines_normalized_only_by_git_rules(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    baseline = o12.compute(m, root=tmp_path)
    (tmp_path / "src/a.py").write_bytes(b"alpha\r\nbeta\r\n")
    converted = o12.compute(m, root=tmp_path)
    assert baseline["git_filtered_roster_sha256"] == converted["git_filtered_roster_sha256"]
    assert baseline["raw_worktree_sha256"] != converted["raw_worktree_sha256"]
    assert baseline["git_filtered_object_ids"]["src/a.py"] == git(tmp_path, "rev-parse", ":src/a.py")
    (tmp_path / "src/a.py").write_bytes(b"alpha\r\nCHANGED\r\n")
    dirty = o12.compute(m, root=tmp_path)
    assert dirty["git_filtered_roster_sha256"] != baseline["git_filtered_roster_sha256"]


def test_binary_crlf_is_never_implicitly_normalized(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    baseline = o12.compute(m, root=tmp_path)
    (tmp_path / "src/raw.bin").write_bytes(b"\x00\x01\n\xff")
    changed = o12.compute(m, root=tmp_path)
    assert changed["git_filtered_roster_sha256"] != baseline["git_filtered_roster_sha256"]
    assert changed["git_filtered_object_ids"]["src/raw.bin"] != baseline["git_filtered_object_ids"]["src/raw.bin"]


def test_untracked_outputs_ignored_and_staged_real_source_counts(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    baseline = o12.compute(m, root=tmp_path)
    (tmp_path / "src/generated.py").write_text("generated = 1\n")
    unchanged = o12.compute(m, root=tmp_path)
    assert unchanged["git_filtered_roster_sha256"] == baseline["git_filtered_roster_sha256"]
    git(tmp_path, "add", "--", "src/generated.py")
    added = o12.compute(m, root=tmp_path)
    assert added["source_count"] == 3
    assert added["git_filtered_roster_sha256"] != baseline["git_filtered_roster_sha256"]


def test_missing_required_and_tracked_symlink_fail_closed(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    (tmp_path / "src/a.py").unlink()
    with pytest.raises(ValueError, match="missing mandatory"):
        o12.compute(m, root=tmp_path)
    (tmp_path / "src/a.py").write_bytes(b"alive\n")
    link = tmp_path / "src/link.py"
    try:
        link.symlink_to(tmp_path / "src/a.py")
    except (OSError, NotImplementedError):
        pytest.skip("symlink not permitted by host")
    git(tmp_path, "add", "--", "src/link.py")
    with pytest.raises(ValueError, match="symlink"):
        o12.compute(m, root=tmp_path)


def test_unbound_batch_size_rejected(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    with pytest.raises(ValueError, match="batch size"):
        o12.compute(m, root=tmp_path, batch_size=10**9)


def test_custom_git_clean_filter_is_rejected_before_hashed_content(tmp_path: Path) -> None:
    # O12b preregistered the malicious-config negative before this test.
    # Different Git-local clean commands would change a Git object ID even
    # though the source bytes and Git HEAD are identical.
    m = fixture(tmp_path)
    (tmp_path / ".gitattributes").write_text("*.py filter=flaky\n*.bin binary\n")
    git(tmp_path, "config", "filter.flaky.clean", "cat")
    with pytest.raises(ValueError, match="unsupported Git source filter"):
        o12.compute(m, root=tmp_path)


def test_working_tree_encoding_transform_is_explicitly_excluded(tmp_path: Path) -> None:
    m = fixture(tmp_path)
    (tmp_path / ".gitattributes").write_text("*.py working-tree-encoding=UTF-16\n*.bin binary\n")
    with pytest.raises(ValueError, match="unsupported Git source filter"):
        o12.compute(m, root=tmp_path)
