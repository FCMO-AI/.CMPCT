"""Verify that CMPCT chooses one package-native binary *before* ctypes loads it.

The real native_codec.py is executed from an isolated package directory; only
ctypes.CDLL is replaced, allowing the test to observe attempts to load code.
"""
from __future__ import annotations

import ctypes
from pathlib import Path
import runpy
import shutil

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "src" / "cmpct" / "native_codec.py"


class FakeLibrary:
    def __getattr__(self, name):
        return type("Symbol", (), {})()


def execute(tmp_path, monkeypatch, entries):
    package = tmp_path / "cmpct"
    package.mkdir()
    shutil.copyfile(SOURCE, package / "native_codec.py")
    for name, kind in entries.items():
        path = package / name
        if kind == "file":
            path.write_bytes(b"synthetic dummy; not loaded")
        elif kind == "directory":
            path.mkdir()
        elif kind in ("symlink", "dangling"):
            destination = tmp_path / "outside.dat"
            if kind == "symlink":
                destination.write_bytes(b"synthetic dummy")
            path.symlink_to(destination)
        else:
            raise AssertionError(kind)
    calls = []

    def spy(path):
        calls.append(Path(path))
        return FakeLibrary()

    monkeypatch.setattr(ctypes, "CDLL", spy)
    return package, calls, lambda: runpy.run_path(str(package / "native_codec.py"))


@pytest.mark.parametrize("extension", ["so", "pyd", "dll", "dylib"])
def test_one_regular_file_keeps_original_load_path(tmp_path, monkeypatch, extension):
    package, calls, load = execute(tmp_path, monkeypatch, {f"cmpct_core.{extension}": "file", "other.so": "file"})
    result = load()
    assert calls == [package / f"cmpct_core.{extension}"]
    assert result["_library_path"]() == calls[0]


def test_no_matching_file_fails_before_load(tmp_path, monkeypatch):
    _, calls, load = execute(tmp_path, monkeypatch, {"other.so": "file"})
    with pytest.raises(RuntimeError, match="missing"):
        load()
    assert calls == []


@pytest.mark.parametrize("additional", ["cmpct_core-legacy.so", "cmpct_core.abi3.so", "cmpct_core.cpython-310.so"])
def test_two_matching_regular_files_fail_before_load(tmp_path, monkeypatch, additional):
    _, calls, load = execute(tmp_path, monkeypatch, {"cmpct_core.so": "file", additional: "file"})
    with pytest.raises(RuntimeError, match="ambiguous"):
        load()
    assert calls == []


@pytest.mark.parametrize("kind", ["symlink", "dangling", "directory"])
def test_single_nonregular_matching_file_fails_before_load(tmp_path, monkeypatch, kind):
    _, calls, load = execute(tmp_path, monkeypatch, {"cmpct_core.so": kind})
    with pytest.raises(RuntimeError, match="not a regular file"):
        load()
    assert calls == []


@pytest.mark.parametrize("kind", ["symlink", "dangling", "directory"])
def test_nonregular_second_match_is_not_ignored(tmp_path, monkeypatch, kind):
    _, calls, load = execute(tmp_path, monkeypatch, {"cmpct_core.so": "file", "cmpct_core-legacy.so": kind})
    with pytest.raises(RuntimeError, match="ambiguous"):
        load()
    assert calls == []
