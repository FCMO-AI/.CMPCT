from __future__ import annotations

"""Regression tests for external structural-competitor path identity.

The structural sweep intentionally changes `cwd` to the corpus root so tools archive `.`. Output paths
must therefore be absolute or the tool and Python can refer to different filesystem objects even when
the compressor itself succeeds.
"""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "benchmarks" / "entropygraph_v028_bench.py"


def _helper():
    spec = importlib.util.spec_from_file_location("cmpct_structural_competitor_path_test", HELPER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_optional_tool_renders_absolute_output_when_cwd_changes(tmp_path: Path, monkeypatch) -> None:
    helper = _helper()
    monkeypatch.chdir(tmp_path)
    root = Path("corpus")
    root.mkdir()
    output = Path("evidence/out.7z")
    monkeypatch.setattr(helper.shutil, "which", lambda name: f"/fake/{name}")

    def fake_run(cmd, cwd, stdout, stderr, timeout):
        assert cwd == root.resolve()
        rendered = Path(cmd[-2])
        assert rendered.is_absolute()
        assert rendered == output.resolve()
        rendered.parent.mkdir(parents=True, exist_ok=True)
        rendered.write_bytes(b"measured-archive")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"")

    monkeypatch.setattr(helper.subprocess, "run", fake_run)
    row = helper._optional_tool(
        "7z", root, output,
        ["{exe}", "a", "-mx=9", "{output}", "."],
        "synthetic structural archive",
    )
    assert row["available"] is True
    assert row["bytes"] == len(b"measured-archive")


def test_borg_uses_same_absolute_repository_for_tool_and_measurement(tmp_path: Path, monkeypatch) -> None:
    helper = _helper()
    monkeypatch.chdir(tmp_path)
    root = Path("corpus")
    root.mkdir()
    repo = Path("evidence/borg-repo")
    monkeypatch.setattr(helper.shutil, "which", lambda name: f"/fake/{name}")
    calls = []

    def fake_run(cmd, cwd, env, stdout, stderr, timeout):
        assert cwd == root.resolve()
        calls.append(cmd)
        if "init" in cmd:
            rendered = Path(cmd[-1])
            assert rendered.is_absolute()
            assert rendered == repo.resolve()
            (rendered / "data").mkdir(parents=True, exist_ok=True)
            (rendered / "config").write_bytes(b"config")
        else:
            location = cmd[-2].split("::", 1)[0]
            rendered = Path(location)
            assert rendered == repo.resolve()
            (rendered / "data" / "segment").write_bytes(b"segment-bytes")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"")

    monkeypatch.setattr(helper.subprocess, "run", fake_run)
    row = helper._borg(root, repo)
    assert len(calls) == 2
    assert row["available"] is True
    assert row["bytes"] == len(b"config") + len(b"segment-bytes")
