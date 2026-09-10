from __future__ import annotations

from pathlib import Path

from benchmarks.one.one_genesis_selective_access_plan import PLAN_VERSION, select_primary_request


def test_selects_largest_regular_file(tmp_path: Path):
    (tmp_path / "a.bin").write_bytes(b"a" * 10)
    (tmp_path / "b.bin").write_bytes(b"b" * 20)
    row = select_primary_request(tmp_path).to_dict()
    assert row == {
        "status": "selected",
        "selection_rule": PLAN_VERSION,
        "relative_path": "b.bin",
        "requested_bytes": 20,
    }


def test_equal_size_tie_is_lexically_stable(tmp_path: Path):
    (tmp_path / "z.bin").write_bytes(b"z" * 20)
    nested = tmp_path / "a"
    nested.mkdir()
    (nested / "x.bin").write_bytes(b"x" * 20)
    row = select_primary_request(tmp_path)
    assert row.relative_path == "a/x.bin"
    assert row.requested_bytes == 20


def test_single_regular_file_is_not_mislabeled_selective(tmp_path: Path):
    (tmp_path / "only.bin").write_bytes(b"x" * 4096)
    row = select_primary_request(tmp_path).to_dict()
    assert row["status"] == "unavailable"
    assert row["relative_path"] == "only.bin"
    assert "whole-object" in row["reason"]


def test_empty_tree_is_explicitly_unavailable(tmp_path: Path):
    row = select_primary_request(tmp_path).to_dict()
    assert row["status"] == "unavailable"
    assert "no regular file" in row["reason"]


def test_symlink_is_not_counted_as_a_regular_member(tmp_path: Path):
    target = tmp_path / "target.bin"
    target.write_bytes(b"t" * 10)
    other = tmp_path / "other.bin"
    other.write_bytes(b"o" * 5)
    link = tmp_path / "huge-looking-link.bin"
    link.symlink_to(target)
    row = select_primary_request(tmp_path)
    assert row.status == "selected"
    assert row.relative_path == "target.bin"
    assert row.requested_bytes == 10
