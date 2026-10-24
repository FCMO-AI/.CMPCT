"""Windows installed-product O3 court for the cooperative transaction-wide lease.

Windows O0/O1/O2 proved primitives only. These tests exercise real revision-24
Builder, Reader and Writer behavior under independently spawned processes.
A green run is local NTFS/Python compatibility evidence, not general network or
uncooperative-writer immunity.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path
from queue import Empty
import time

import pytest

from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows writer lease product court")


def _archive(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    (root / "alpha.txt").write_bytes(b"first value\n" * 90)
    (root / "beta.txt").write_bytes(b"second value\n" * 80)
    archive = tmp_path / "archive.cmpct"
    Builder(root).build(archive)
    return archive


def _writer(archive, old, new, output, release=None):
    """Signal AFTER Reader snapshot but BEFORE footer append."""
    original = tx._append_generation

    def watched(*args, **kwargs):
        output.put(("snapshot", old, args[2]))
        if release is not None and not release.wait(25):
            raise TimeoutError("first writer was not released")
        result = original(*args, **kwargs)
        output.put(("append", old, result[0]))
        return result

    tx._append_generation = watched
    try:
        output.put(("entered", old, None))
        tx.append_rename(Path(archive), old, new)
        output.put(("success", old, None))
    except BaseException as e:
        output.put(("error", old, repr(e)))
        raise
    finally:
        tx._append_generation = original


def _wait(queue, kind, member, seconds=40):
    end = time.monotonic() + seconds
    collected = []
    while time.monotonic() < end:
        try:
            event = queue.get(timeout=0.15)
        except Empty:
            continue
        if event[0] == "error":
            raise AssertionError(("child writer failed", event, collected))
        if event[:2] == (kind, member):
            return event, collected
        collected.append(event)
    raise AssertionError(("missing event", kind, member, collected))


@pytest.mark.parametrize("alias_kind", ["same", "hardlink"])
def test_two_spawned_writers_keep_both_successful_renames(tmp_path, alias_kind):
    archive = _archive(tmp_path)
    alias = tmp_path / "linked.cmpct"
    if alias_kind == "hardlink":
        os.link(archive, alias)

    ctx = mp.get_context("spawn")
    output = ctx.Queue()
    release = ctx.Event()
    first = ctx.Process(target=_writer, args=(str(archive), "alpha.txt", "alpha-new.txt", output, release))
    second = ctx.Process(target=_writer, args=(str(alias if alias_kind == "hardlink" else archive), "beta.txt", "beta-new.txt", output))
    first.start()
    retained = []
    try:
        snapshot, prior = _wait(output, "snapshot", "alpha.txt")
        assert isinstance(snapshot[2], int)
        second.start()
        _, entered = _wait(output, "entered", "beta.txt")
        # The second process must not reach its snapshot while the first owns
        # the far-range lock. A footer-only lock fails this same assertion.
        observed = prior + entered
        until = time.monotonic() + 0.60
        while time.monotonic() < until:
            try:
                event = output.get(timeout=0.05)
            except Empty:
                continue
            observed.append(event)
            assert event[0] != "error", observed
        assert not any(x[:2] == ("snapshot", "beta.txt") for x in observed), observed
        # Readers remain able to inspect the old committed generation while a
        # Writer owns the sentinel (byte-zero lock would break this).
        with CMPCT(archive) as ar:
            assert ar.read("alpha.txt") == b"first value\n" * 90
            assert ar.read("beta.txt") == b"second value\n" * 80
            assert ar.verify() >= 2
        retained = observed
    finally:
        release.set()
        first.join(timeout=45)
        if second.pid is not None:
            second.join(timeout=45)
        for child in (first, second):
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)

    assert (first.exitcode, second.exitcode) == (0, 0)
    while True:
        try:
            retained.append(output.get_nowait())
        except Empty:
            break
    assert {x[1] for x in retained if x[0] == "success"} == {"alpha.txt", "beta.txt"}, retained
    appends = {x[1]: x[2] for x in retained if x[0] == "append"}
    assert appends.keys() == {"alpha.txt", "beta.txt"}, retained
    b_snapshots = [x for x in retained if x[:2] == ("snapshot", "beta.txt")]
    assert len(b_snapshots) == 1
    assert b_snapshots[0][2] == appends["alpha.txt"], retained
    with CMPCT(archive) as ar:
        assert sorted(ar.by.keys()) == ["alpha-new.txt", "beta-new.txt"]
        assert ar.read("alpha-new.txt") == b"first value\n" * 90
        assert ar.read("beta-new.txt") == b"second value\n" * 80
        assert ar.verify() >= 2
    if alias_kind == "hardlink":
        assert os.stat(alias).st_ino == os.stat(archive).st_ino


def test_sequential_real_blob_append_rename_delete_and_offsets(tmp_path):
    archive = _archive(tmp_path)
    before = archive.stat().st_size
    new_source = tmp_path / "replacement.bin"
    replacement = b"windows-lease-integrity\x00" * 10000
    new_source.write_bytes(replacement)
    report = tx.append_update(archive, "alpha.txt", new_source)
    assert report["new_size"] > before
    tx.append_rename(archive, "beta.txt", "beta-new.txt")
    tx.append_delete(archive, "beta-new.txt")
    with CMPCT(archive) as ar:
        assert list(ar.by) == ["alpha.txt"]
        assert ar.read("alpha.txt") == replacement
        assert ar.verify() >= 1
    assert archive.stat().st_size < tx._WINDOWS_LEASE_OFFSET


def test_failure_releases_windows_lease_and_preserves_preexisting_bytes(tmp_path):
    archive = _archive(tmp_path)
    untouched = archive.read_bytes()
    with pytest.raises(KeyError):
        tx.append_rename(archive, "nonexistent.txt", "never.txt")
    assert archive.read_bytes() == untouched
    # A second call must acquire the lock even after an exception.
    tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    with CMPCT(archive) as ar:
        assert ar.read("alpha-new.txt") == b"first value\n" * 90
        assert ar.verify() >= 2


def test_lock_acquisition_error_is_not_overwritten_by_unlock(tmp_path, monkeypatch):
    archive = _archive(tmp_path)
    actual = tx.msvcrt.locking
    calls = []

    def deny(fd, mode, length):
        calls.append(mode)
        if mode == tx.msvcrt.LK_LOCK:
            raise PermissionError("synthetic acquisition denied")
        return actual(fd, mode, length)

    original = archive.read_bytes()
    with monkeypatch.context() as scope:
        scope.setattr(tx.msvcrt, "locking", deny)
        with pytest.raises(PermissionError, match="synthetic acquisition denied"):
            tx.append_delete(archive, "alpha.txt")
    assert calls == [tx.msvcrt.LK_LOCK]  # no second masking LK_UNLCK
    assert archive.read_bytes() == original
    tx.append_delete(archive, "alpha.txt")
    with CMPCT(archive) as ar:
        assert "alpha.txt" not in ar.by
        assert ar.verify() >= 1
