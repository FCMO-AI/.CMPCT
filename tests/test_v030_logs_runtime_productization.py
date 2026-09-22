from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME


def _logs_source(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for stem, line, count in (
        ("service.log", b"2026-08-29 INFO request=ok worker=7\n", 5000),
        ("audit.log", b"audit accepted actor=product-ratchet\n", 4000),
    ):
        raw = line * count
        (root / stem).write_bytes(raw)
        (root / f"{stem}.gz").write_bytes(gzip.compress(raw, mtime=0))
    (root / "nested").mkdir()
    (root / "nested" / "plain.txt").write_text("semantic payload\n" * 100)


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_runtime_logs_extract_is_exact_and_product_bytes_unchanged(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _logs_source(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    before = archive.read_bytes()
    dst = tmp_path / "out"
    RUNTIME.extract(archive, dst)
    assert archive.read_bytes() == before
    assert _files(dst) == _files(src)
    assert RUNTIME.strong_verify(archive)["ok"] is True
    assert RUNTIME.PROMOTED_LOGS_ONE_SESSION_EXTRACTION is True


def test_runtime_logs_budget_and_corruption_fail_before_publication(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _logs_source(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)

    dst = tmp_path / "existing"
    dst.mkdir()
    sentinel = dst / "sentinel.txt"
    sentinel.write_text("keep")
    with pytest.raises(RuntimeError, match="output budget"):
        RUNTIME.extract(archive, dst, max_output_bytes=1024)
    assert sentinel.read_text() == "keep"
    assert list(dst.iterdir()) == [sentinel]

    raw = bytearray(archive.read_bytes())
    raw[len(raw) // 2] ^= 0x5A
    bad = tmp_path / "bad.cmpct"
    bad.write_bytes(raw)
    bad_dst = tmp_path / "bad-out"
    with pytest.raises(Exception):
        RUNTIME.extract(bad, bad_dst)
    assert not bad_dst.exists()


def test_runtime_non_logs_delegates_to_promoted_product(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "nonlogs.cmpct"
    archive.write_bytes(b"not-a-logs-archive")
    dst = tmp_path / "out"
    called = {}

    def fake_extract(path, target, *, max_output_bytes, safe_symlinks):
        called.update(
            path=Path(path),
            target=Path(target),
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )

    monkeypatch.setattr(PRODUCT, "extract", fake_extract)
    RUNTIME.extract(archive, dst, max_output_bytes=12345, safe_symlinks=False)
    assert called == {
        "path": archive,
        "target": dst,
        "max_output_bytes": 12345,
        "safe_symlinks": False,
    }
