"""O51: actual revision-24 Writer descriptor admission, including pre-open FIFO pivot."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _archive(tmp_path):
    source = tmp_path / "tree"
    source.mkdir()
    (source / "initial.bin").write_bytes(b"original-payload")
    archive = tmp_path / "authentic-r24.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.read("initial.bin") == b"original-payload"
        assert reader.verify() >= 1
    return archive


def _assert_unchanged(archive, before):
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == before
    with CMPCT(archive) as reader:
        assert reader.read("initial.bin") == b"original-payload"
        assert reader.verify() >= 1


def _cli(archive, source, timeout=5):
    return subprocess.run(
        [sys.executable, "-m", "cmpct", "update", str(archive), "initial.bin", str(source)],
        check=False, capture_output=True, text=True, timeout=timeout)


def test_real_installed_regular_source_update(tmp_path):
    archive = _archive(tmp_path)
    source = tmp_path / "replacement.bin"
    payload = bytes((i * 13 + 7) % 256 for i in range(8192))
    source.write_bytes(payload)
    cp = _cli(archive, source, timeout=40)
    assert cp.returncode == 0, (cp.stdout, cp.stderr)
    with CMPCT(archive) as reader:
        assert reader.read("initial.bin") == payload
        assert reader.verify() >= 1


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"),
                    reason="no-writer FIFO admission is POSIX-specific")
def test_fifo_source_refused_promptly_without_new_footer(tmp_path):
    archive = _archive(tmp_path)
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    fifo = tmp_path / "no-writer.fifo"
    os.mkfifo(fifo, 0o600)
    cp = _cli(archive, fifo, timeout=3)
    assert cp.returncode != 0
    assert "not a regular file" in cp.stderr
    _assert_unchanged(archive, before)


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink-following source contract")
def test_symlink_to_regular_preserves_original_source_semantics(tmp_path):
    archive = _archive(tmp_path)
    target = tmp_path / "valid-target.bin"
    data = b"symlink-to-regular-accepted" * 31
    target.write_bytes(data)
    link = tmp_path / "regular-link.bin"
    link.symlink_to(target)
    cp = _cli(archive, link, timeout=20)
    assert cp.returncode == 0, (cp.stdout, cp.stderr)
    with CMPCT(archive) as reader:
        assert reader.read("initial.bin") == data
        assert reader.verify() >= 1


@pytest.mark.skipif(os.name != "posix" or not hasattr(socket, "AF_UNIX"),
                    reason="bound AF_UNIX socket sources are POSIX-only")
def test_socket_source_refused_without_archive_mutation(tmp_path):
    archive = _archive(tmp_path)
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    source = tmp_path / "listening.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(source))
        cp = _cli(archive, source, timeout=3)
        assert cp.returncode != 0
        _assert_unchanged(archive, before)
    finally:
        server.close()


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"),
                    reason="deterministic path-replacement FIFO adversary requires POSIX")
def test_pivot_before_actual_open_is_nonblocking_and_fd_typed(tmp_path):
    archive = _archive(tmp_path)
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    original = tmp_path / "input.bin"
    original.write_bytes(b"valid-regular-before-switch")
    # A real subprocess contains the adversarial path swap and prevents a regressed blocking
    # open from hanging the test runner. The hook runs *at* the true os.open call, not at lstat.
    child = r"""
import os, sys
from pathlib import Path
import cmpct.transactions as transactions
archive=Path(sys.argv[1]); source=Path(sys.argv[2])
moved=source.with_suffix(".moved")
original_open=transactions.os.open
seen=[False]
def pivot(path,flags,*args,**kwargs):
    if os.fspath(path)==os.fspath(source) and not seen[0]:
        seen[0]=True
        os.replace(source,moved)
        os.mkfifo(source,0o600)
    return original_open(path,flags,*args,**kwargs)
transactions.os.open=pivot
try:
    transactions.append_update(archive,"initial.bin",source)
except OSError:
    assert seen[0], "adversary did not reach actual source open"
else:
    raise AssertionError("Writer accepted swapped FIFO")
"""
    cp = subprocess.run([sys.executable, "-c", child, str(archive), str(original)],
                        check=False, capture_output=True, text=True, timeout=5)
    assert cp.returncode == 0, (cp.stdout, cp.stderr)
    _assert_unchanged(archive, before)
