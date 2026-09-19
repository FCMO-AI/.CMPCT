from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments import entropygraph_v029_parallel_portfolio_handoff as HOFF


def test_explicit_handoff_rejects_cross_filesystem_without_copy(monkeypatch, tmp_path: Path) -> None:
    """The research seam must never hide an archive-sized copy behind a portability fallback."""
    root = tmp_path / "source"
    root.mkdir()
    out_parent = tmp_path / "out"
    retained_parent = tmp_path / "retained"
    out_parent.mkdir()
    retained_parent.mkdir()
    out = out_parent / "archive.cmpct"
    retained = retained_parent / "attempt5.cmpct"

    monkeypatch.setattr(HOFF.S.accepted, "_logical_file_count", lambda _root: 2)
    real_stat = HOFF.os.stat

    def fake_stat(path):
        path = Path(path)
        if path == out_parent:
            return SimpleNamespace(st_dev=101)
        if path == retained_parent:
            return SimpleNamespace(st_dev=202)
        return real_stat(path)

    monkeypatch.setattr(HOFF.os, "stat", fake_stat)
    with pytest.raises(RuntimeError, match="same filesystem"):
        HOFF.build_parallel_with_attempt5(root, out, retained)

    assert not out.exists()
    assert not retained.exists()


def test_explicit_handoff_refuses_to_overwrite_retained_artifact(monkeypatch, tmp_path: Path) -> None:
    """Custody is explicit: an existing retained path is never silently replaced."""
    root = tmp_path / "source"
    root.mkdir()
    out = tmp_path / "archive.cmpct"
    retained = tmp_path / "attempt5.cmpct"
    retained.write_bytes(b"sentinel")

    monkeypatch.setattr(HOFF.S.accepted, "_logical_file_count", lambda _root: 2)
    with pytest.raises(FileExistsError):
        HOFF.build_parallel_with_attempt5(root, out, retained)

    assert retained.read_bytes() == b"sentinel"
    assert not out.exists()


def test_explicit_handoff_preserves_single_file_fast_reject(monkeypatch, tmp_path: Path) -> None:
    """Requesting custody must not resurrect the expensive graph on single-file trees."""
    root = tmp_path / "source"
    root.mkdir()
    out = tmp_path / "archive.cmpct"
    retained = tmp_path / "attempt5.cmpct"

    monkeypatch.setattr(HOFF.S.accepted, "_logical_file_count", lambda _root: 1)
    with pytest.raises(RuntimeError, match="multi-file only"):
        HOFF.build_parallel_with_attempt5(root, out, retained)

    assert not out.exists()
    assert not retained.exists()
