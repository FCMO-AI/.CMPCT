from __future__ import annotations

from pathlib import Path
import os

import pytest

from experiments import entropygraph_v030_logs_fused_extract as FUSED
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT


def _source(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    plain = root / "service.log"
    raw = (b"2026-08-29 INFO request=ok worker=7\n" * 5000)
    plain.write_bytes(raw)
    import gzip
    (root / "service.log.gz").write_bytes(gzip.compress(raw, mtime=0))
    second = root / "audit.log"
    second_raw = (b"audit accepted actor=unit-test\n" * 4000)
    second.write_bytes(second_raw)
    (root / "audit.log.gz").write_bytes(gzip.compress(second_raw, mtime=0))
    (root / "nested").mkdir()
    (root / "nested" / "plain.txt").write_text("semantic payload\n" * 100)


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_fused_extract_matches_canonical_product(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _source(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    assert PRODUCT.strong_verify(archive)["ok"] is True
    current = tmp_path / "current"
    fused = tmp_path / "fused"
    PRODUCT.extract(archive, current)
    FUSED.extract(archive, fused)
    assert _files(fused) == _files(current) == _files(src)


def test_fused_extract_budget_fails_before_publication(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _source(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    dst = tmp_path / "existing"
    dst.mkdir()
    sentinel = dst / "sentinel.txt"
    sentinel.write_text("keep")
    with pytest.raises(RuntimeError, match="output budget"):
        FUSED.extract(archive, dst, max_output_bytes=1024)
    assert sentinel.read_text() == "keep"
    assert list(dst.iterdir()) == [sentinel]


def test_fused_extract_corruption_fails_closed(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _source(src)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(src, archive)
    raw = bytearray(archive.read_bytes())
    # Damage payload rather than one recoverable control copy.
    raw[len(raw) // 2] ^= 0x5A
    bad = tmp_path / "bad.cmpct"
    bad.write_bytes(raw)
    dst = tmp_path / "bad-out"
    with pytest.raises(Exception):
        FUSED.extract(bad, dst)
    assert not dst.exists()
