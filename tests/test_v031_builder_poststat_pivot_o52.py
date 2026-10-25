"""O52 source-exact Builder post-lstat pathname pivot research.

The hook changes a genuine filesystem pathname only at the builtin open boundary.
It never substitutes an encoder, decoder or synthetic archive.
"""
from __future__ import annotations

import builtins
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_SYMLINK
from cmpct.reader import CMPCT


def _create(root: Path, out: Path) -> None:
    Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(out)


def _interleave_before_regular_open(victim: Path, operation, monkeypatch) -> dict:
    """Deterministically model a separate local actor switching a path after lstat.

    A correct descriptor-bound Builder would reject the replacement independently
    of our scheduling hook. Static type admission alone cannot do so.
    """
    original = builtins.open
    status = {"fired": False}

    def hooked(file, mode="r", *args, **kwargs):
        if mode == "rb" and os.fspath(file) == os.fspath(victim):
            assert not status["fired"], "unexpected duplicate victim read"
            status["fired"] = True
            operation()
        return original(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", hooked)
    return status


def test_stable_control_exact_and_preexisting_symlink_type(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    payload = b"ordinary-trusted-source"
    (src / "victim.bin").write_bytes(payload)
    if os.name != "nt":
        os.symlink("victim.bin", src / "preexisting-link")
    archive = tmp_path / "normal.cmpct"
    _create(src, archive)
    with CMPCT(archive) as ar:
        ar.verify()
        assert ar.read("victim.bin") == payload
        rows = {row[0]: row for row in ar.index["files"]}
        assert rows["victim.bin"][1] == K_FILE
        if os.name != "nt":
            assert rows["preexisting-link"][1] == K_SYMLINK
    print("O52_STABLE_CONTROL=PASS archive_sha256=" +
          hashlib.sha256(archive.read_bytes()).hexdigest())


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="original POSIX special-file admission boundary")
def test_static_fifo_is_rejected_before_any_archive_output(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    os.mkfifo(src / "victim.bin")
    archive = tmp_path / "sentinel.cmpct"
    sentinel = b"PRIOR_OUTPUT_NOT_TO_BE_REPLACED"
    archive.write_bytes(sentinel)
    with pytest.raises(OSError, match="unsupported filesystem entry"):
        _create(src, archive)
    assert archive.read_bytes() == sentinel
    print("O52_STATIC_FIFO_REJECTION=PASS")


@pytest.mark.skipif(os.name == "nt",
                    reason="POSIX symlink switch tested only on unix-like hosts")
def test_poststat_regular_to_external_symlink_captures_outside_bytes(
        tmp_path: Path, monkeypatch):
    src = tmp_path / "source"
    src.mkdir()
    victim = src / "victim.bin"
    trusted = b"TRUSTED_INSIDE_BYTES"
    outside = tmp_path / "outside-secret.bin"
    external = b"OUTSIDE_SOURCE_ROOT_DECISIVE_BYTES"
    victim.write_bytes(trusted)
    outside.write_bytes(external)

    def pivot():
        victim.unlink()
        os.symlink(outside, victim)

    state = _interleave_before_regular_open(victim, pivot, monkeypatch)
    archive = tmp_path / "pivot.cmpct"
    _create(src, archive)
    assert state["fired"], "the genuine Builder did not reach original open()"
    assert victim.is_symlink()
    with CMPCT(archive) as ar:
        assert ar.verify() >= 1
        row = next(row for row in ar.index["files"] if row[0] == "victim.bin")
        assert row[1] == K_FILE, row
        assert ar.read("victim.bin") == external
        assert ar.read("victim.bin") != trusted
    print("O52_EXTERNAL_SOURCE_CAPTURE=CONFIRMED")
    print("O52_EXTERNAL_SHA256=" + hashlib.sha256(external).hexdigest())
    print("O52_ARCHIVE_SHA256=" +
          hashlib.sha256(archive.read_bytes()).hexdigest())


def _fifo_child(root: Path):
    # Execute actual O50 Builder in an independently killable Python process.
    # No reader/codec/Builder source code is replaced.
    from unittest.mock import patch
    src = root / "source"
    src.mkdir()
    victim = src / "victim.bin"
    victim.write_bytes(b"REGULAR_BEFORE_LSTAT")
    original = builtins.open
    fired = False

    def hooked(file, mode="r", *args, **kwargs):
        nonlocal fired
        if mode == "rb" and os.fspath(file) == os.fspath(victim):
            assert not fired
            fired = True
            victim.unlink()
            os.mkfifo(victim)
            print("O52_PIVOT_TRIGGERED=TRUE", flush=True)
        return original(file, mode, *args, **kwargs)

    with patch.object(builtins, "open", hooked):
        _create(src, root / "hung-output.cmpct")
    print("O52_CHILD_RETURNED_WITHOUT_BLOCK=TRUE", flush=True)


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="FIFO no-writer open is a POSIX-specific falsifier")
def test_poststat_regular_to_fifo_blocks_until_killed(tmp_path: Path):
    child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                              "--o52-fifo-child", str(tmp_path)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True)
    try:
        try:
            out, err = child.communicate(timeout=3.0)
        except subprocess.TimeoutExpired:
            child.kill()
            out, err = child.communicate(timeout=4.0)
            assert "O52_PIVOT_TRIGGERED=TRUE" in out, (out, err)
            assert not (tmp_path / "hung-output.cmpct").exists()
            print("O52_FIFO_POSTSTAT_BLOCK=CONFIRMED timeout=3.0s")
            return
        pytest.fail("Builder unexpectedly returned within timeout; "
                    f"returncode={child.returncode} stdout={out!r} stderr={err!r}")
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=4.0)


if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "--o52-fifo-child":
    _fifo_child(Path(sys.argv[2]))
