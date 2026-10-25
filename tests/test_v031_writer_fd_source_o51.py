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
    # Darwin limits AF_UNIX sun_path to roughly 104 bytes. pytest's generated temp
    # path can exceed it before the product even opens the socket; use a short private
    # socket directory without relaxing the actual bound-socket source adversary.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="o51-", dir="/tmp") as sd:
        source = Path(sd) / "sock"
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


@pytest.mark.skipif(os.name != "posix", reason="descriptor/path replacement metadata custody POSIX")
def test_source_path_switched_after_open_uses_opened_inode_metadata(tmp_path):
    archive = _archive(tmp_path)
    source = tmp_path / "replace-me.bin"
    other = tmp_path / "attacker-new-path.bin"
    original_bytes = b"fd-original-contents" * 43
    other_bytes = b"wrong-replacement-contents" * 41
    source.write_bytes(original_bytes)
    other.write_bytes(other_bytes)
    os.chmod(source, 0o640)
    os.chmod(other, 0o600)
    before = source.stat()
    child = r"""
import os, sys
from pathlib import Path
import cmpct.transactions as transactions
archive=Path(sys.argv[1]); source=Path(sys.argv[2]); other=Path(sys.argv[3])
moved=source.with_suffix(".original")
actual_open=transactions.os.open
switched=[False]
def after_open(path,flags,*args,**kwargs):
    fd=actual_open(path,flags,*args,**kwargs)
    if os.fspath(path)==os.fspath(source) and not switched[0]:
        switched[0]=True
        os.replace(source,moved)
        os.replace(other,source)
    return fd
transactions.os.open=after_open
transactions.append_update(archive,"initial.bin",source)
assert switched[0], "test did not pivot after descriptor acquisition"
"""
    cp = subprocess.run([sys.executable, "-c", child,
                         str(archive), str(source), str(other)],
                        check=False, capture_output=True, text=True, timeout=5)
    assert cp.returncode == 0, (cp.stdout, cp.stderr)
    assert source.read_bytes() == other_bytes
    with CMPCT(archive) as reader:
        assert reader.read("initial.bin") == original_bytes
        row = reader.by["initial.bin"]
        assert row[2] == (before.st_mode & 0o7777)
        assert row[3] == before.st_mtime_ns
        assert reader.verify() >= 1


def test_directory_source_fails_without_mutating_signed_archive(tmp_path):
    archive = _archive(tmp_path)
    original_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    directory = tmp_path / "input-directory"
    directory.mkdir()
    (directory / "payload.bin").write_bytes(b"contents-do-not-turn-directory-into-file")
    cp = _cli(archive, directory, timeout=5)
    assert cp.returncode != 0, cp.stdout
    _assert_unchanged(archive, original_sha)


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"),
                    reason="POSIX symlink to FIFO admission")
def test_symlink_target_fifo_cannot_block_open_or_publish(tmp_path):
    archive = _archive(tmp_path)
    original_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    fifo = tmp_path / "symlink-target.fifo"
    os.mkfifo(fifo, 0o600)
    link = tmp_path / "source-link.bin"
    link.symlink_to(fifo)
    cp = _cli(archive, link, timeout=3)
    assert cp.returncode != 0
    _assert_unchanged(archive, original_sha)


def test_stable_regular_update_matches_original_source_read_stat_archive_bytes(tmp_path):
    """Same exact r24 source tree; compare only old vs new source-admission primitives."""
    from cmpct import transactions

    initial = _archive(tmp_path)
    baseline = tmp_path / "old-primitive.cmpct"
    candidate = tmp_path / "opened-fd.cmpct"
    baseline.write_bytes(initial.read_bytes())
    candidate.write_bytes(initial.read_bytes())
    update = tmp_path / "payload.bin"
    update.write_bytes(bytes((i * 41 + 19) & 255 for i in range(10_001)))

    # Faithfully retain historical expression semantics without depending on CI having
    # fetched the unrelated, old commit into a shallow checkout. The complete Writer,
    # codec, target/source trees and update API are otherwise identical in this A/B.
    original_source_primitive = transactions._read_regular_update_source
    def historical_read_stat(src):
        return Path(src).read_bytes(), Path(src).stat()
    try:
        transactions._read_regular_update_source = historical_read_stat
        transactions.append_update(baseline, "initial.bin", update)
    finally:
        transactions._read_regular_update_source = original_source_primitive
    transactions.append_update(candidate, "initial.bin", update)
    assert baseline.read_bytes() == candidate.read_bytes(), "stable-source archive bytes changed"
    with CMPCT(candidate) as reader:
        assert reader.read("initial.bin") == update.read_bytes()
        assert reader.verify() >= 1
