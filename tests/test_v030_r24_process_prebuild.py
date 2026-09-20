from __future__ import annotations
from pathlib import Path
import hashlib
import pytest

from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r24_process_prebuild_is_byte_identical(tmp_path: Path):
    from experiments import entropygraph_v030_release_product_base as product

    root = tmp_path / "src"
    root.mkdir()
    (root / "a.txt").write_text("alpha beta gamma\n" * 200)
    (root / "b.bin").write_bytes(bytes(range(256)) * 32)
    direct = tmp_path / "direct.cmpct"
    child = tmp_path / "child.cmpct"
    direct_stats = product._locality_bounded_r24_build(root, direct)
    with R24PrebuildProcess(root, child, timeout_s=30) as proc:
        child_stats = proc.result()
    assert child_stats == direct_stats
    assert child.stat().st_size == direct.stat().st_size
    assert _sha(child) == _sha(direct)


def test_r24_process_prebuild_failure_does_not_publish_candidate(tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    out = tmp_path / "candidate.cmpct"
    with R24PrebuildProcess(missing, out, timeout_s=30) as proc:
        with pytest.raises(RuntimeError, match="r24 prebuild child failed"):
            proc.result()
    assert not out.exists()


def test_r24_process_prebuild_rejects_double_start(tmp_path: Path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "x").write_bytes(b"x")
    proc = R24PrebuildProcess(root, tmp_path / "out.cmpct", timeout_s=30).start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            proc.start()
    finally:
        proc.close()
