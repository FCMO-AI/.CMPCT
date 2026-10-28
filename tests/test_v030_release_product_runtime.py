from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_runtime as RUNTIME


def _logs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for stem, line, count in (
        ("service.log", b"INFO promoted one-session release bridge\n", 4500),
        ("audit.log", b"audit promoted bridge accepted\n", 3500),
    ):
        raw = line * count
        (root / stem).write_bytes(raw)
        (root / f"{stem}.gz").write_bytes(gzip.compress(raw, mtime=0))


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_release_runtime_bridge_preserves_logs_bytes_and_semantics(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _logs(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    before = archive.read_bytes()
    out = tmp_path / "out"
    RUNTIME.extract(archive, out)
    assert archive.read_bytes() == before
    assert _tree(out) == _tree(src)
    assert RUNTIME.strong_verify(archive)["ok"] is True


def test_release_runtime_bridge_delegates_non_logs_unchanged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "ordinary.cmpct"
    archive.write_bytes(b"ordinary-placeholder")
    dst = tmp_path / "out"
    called = {}

    monkeypatch.setattr(PRODUCT._LOGS_PROMOTED, "_is_logs_archive", lambda _: False)

    def fake_extract(path, target, *, max_output_bytes, safe_symlinks):
        called.update(path=Path(path), target=Path(target), max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)

    monkeypatch.setattr(PRODUCT, "extract", fake_extract)
    RUNTIME.extract(archive, dst, max_output_bytes=777, safe_symlinks=False)
    assert called == {
        "path": archive,
        "target": dst,
        "max_output_bytes": 777,
        "safe_symlinks": False,
    }


def test_release_runtime_bridge_propagates_budget_fail_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _logs(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    dst = tmp_path / "existing"
    dst.mkdir()
    sentinel = dst / "keep.txt"
    sentinel.write_text("keep")
    with pytest.raises(RuntimeError, match="output budget"):
        RUNTIME.extract(archive, dst, max_output_bytes=1024)
    assert sentinel.read_text() == "keep"
    assert list(dst.iterdir()) == [sentinel]
