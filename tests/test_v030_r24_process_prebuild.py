from __future__ import annotations
from pathlib import Path
import ctypes
import hashlib
import os
import pytest

# Issue #176 is product loader debt, not a subprocess-boundary result. The workflow supplies the original
# runner DLL path so its adjacent dependencies remain discoverable while this focused oracle stays isolated.
if os.name == "nt":
    _ci_zstd = os.environ.get("CMPCT_CI_ZSTD_DLL")
    if _ci_zstd:
        ctypes.CDLL(str(Path(_ci_zstd).resolve()))

from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _stable_stats(stats: dict) -> dict: return {k: v for k, v in stats.items() if "wall" not in k and "cpu" not in k and not k.endswith("_s")}


def test_r24_process_prebuild_is_byte_identical(tmp_path: Path):
    from experiments import entropygraph_v030_release_product as product
    root = tmp_path / "src"; root.mkdir()
    (root / "a.txt").write_text("alpha beta gamma\n" * 200); (root / "b.bin").write_bytes(bytes(range(256)) * 32)
    direct = tmp_path / "direct.cmpct"; child = tmp_path / "child.cmpct"
    direct_stats = product._locality_bounded_r24_build(root, direct)
    with R24PrebuildProcess(root, child, timeout_s=30) as proc: child_stats = proc.result()
    assert _stable_stats(child_stats) == _stable_stats(direct_stats)
    assert child.stat().st_size == direct.stat().st_size; assert _sha(child) == _sha(direct)


def test_r24_process_prebuild_is_independent_of_caller_cwd(tmp_path: Path, monkeypatch):
    root = tmp_path / "src"; root.mkdir(); (root / "x.txt").write_text("cwd-independent child\n" * 200)
    out = tmp_path / "child.cmpct"; elsewhere = tmp_path / "elsewhere"; elsewhere.mkdir(); monkeypatch.chdir(elsewhere)
    with R24PrebuildProcess(root, out, timeout_s=30) as proc: stats = proc.result()
    assert out.is_file(); assert stats["format_revision"] == 24


def test_r24_process_prebuild_failure_does_not_publish_candidate(tmp_path: Path):
    missing = tmp_path / "does-not-exist"; out = tmp_path / "candidate.cmpct"
    with R24PrebuildProcess(missing, out, timeout_s=30) as proc:
        with pytest.raises(RuntimeError, match="r24 prebuild child failed"): proc.result()
    assert not out.exists()


def test_r24_process_prebuild_rejects_double_start(tmp_path: Path):
    root = tmp_path / "src"; root.mkdir(); (root / "x").write_bytes(b"x")
    proc = R24PrebuildProcess(root, tmp_path / "out.cmpct", timeout_s=30).start()
    try:
        with pytest.raises(RuntimeError, match="already started"): proc.start()
    finally: proc.close()


def test_r24_process_prebuild_abandonment_removes_candidate(tmp_path: Path):
    root = tmp_path / "src"; root.mkdir(); (root / "x.txt").write_text("repeatable child output\n" * 500)
    out = tmp_path / "abandoned.cmpct"; proc = R24PrebuildProcess(root, out, timeout_s=30).start()
    proc._proc.communicate(timeout=30); assert proc._proc.returncode == 0; assert out.is_file(); proc.close(); assert not out.exists()


def test_r24_process_prebuild_refuses_to_clobber_existing_output(tmp_path: Path):
    root = tmp_path / "src"; root.mkdir(); (root / "x").write_bytes(b"x")
    out = tmp_path / "owned-by-someone-else.cmpct"; out.write_bytes(b"preserve-me")
    with pytest.raises(FileExistsError, match="output already exists"): R24PrebuildProcess(root, out, timeout_s=30).start()
    assert out.read_bytes() == b"preserve-me"
