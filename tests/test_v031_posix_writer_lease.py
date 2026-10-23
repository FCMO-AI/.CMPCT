"""Exact public-API POSIX cooperative writer lease court.

Research result #289 reproduces stale-footer lost updates even when complete
physical writes serialize. This product candidate must acquire one inode lock
*before* the Reader snapshot. It does not claim protection from uncooperative
writers or malicious concurrent pathname changes.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path
from queue import Empty
import shutil
import time

import pytest

from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX inode-lease candidate")


def _make_archive(tmp_path: Path) -> Path:
    inp = tmp_path / "input"
    inp.mkdir()
    (inp / "alpha.txt").write_bytes(b"alpha payload\n" * 70)
    (inp / "beta.txt").write_bytes(b"beta payload\n" * 70)
    p = tmp_path / "source.cmpct"
    Builder(inp).build(p)
    return p


def _rename_worker(archive, old, new, output, release=None):
    original = tx._append_generation

    def traced_append(*args, **kwargs):
        output.put(("at_append", old, args[2]))
        if release is not None and not release.wait(timeout=20):
            raise TimeoutError("first writer was not released")
        result = original(*args, **kwargs)
        output.put(("appended", old, result[0]))
        return result

    tx._append_generation = traced_append
    try:
        output.put(("entered", old, None))
        tx.append_rename(Path(archive), old, new)
        output.put(("completed", old, None))
    except BaseException as exc:
        output.put(("error", old, repr(exc)))
        raise
    finally:
        tx._append_generation = original


def _wait_event(q, kind, member, seconds=25):
    end = time.monotonic() + seconds
    held = []
    while time.monotonic() < end:
        try:
            e = q.get(timeout=min(0.2, max(0.01, end - time.monotonic())))
        except Empty:
            continue
        if e[0] == "error":
            raise AssertionError(f"writer failed: {e!r}; earlier={held!r}")
        if e[0] == kind and e[1] == member:
            return e, held
        held.append(e)
    raise AssertionError(f"missing {(kind, member)!r}; earlier={held!r}")


@pytest.mark.parametrize("via_hardlink", [False, True])
def test_independent_writers_snapshot_serialized_through_footer(tmp_path, via_hardlink):
    """Second writer cannot snapshot the same footer while first writer is paused."""
    ctx = mp.get_context("fork")
    archive = _make_archive(tmp_path)
    alias = tmp_path / "hardlink-alias.cmpct"
    if via_hardlink:
        os.link(archive, alias)

    q = ctx.Queue()
    release = ctx.Event()
    a = ctx.Process(
        target=_rename_worker,
        args=(str(archive), "alpha.txt", "alpha-new.txt", q, release),
    )
    b = ctx.Process(
        target=_rename_worker,
        args=(str(alias if via_hardlink else archive), "beta.txt", "beta-new.txt", q),
    )
    a.start()
    try:
        first, old = _wait_event(q, "at_append", "alpha.txt")
        assert first[2] >= 0
        b.start()
        _wait_event(q, "entered", "beta.txt")
        # If the lock protected only append(), B would reach its own
        # _append_generation while A is blocked (the original lost-update bug).
        observed = []
        until = time.monotonic() + 0.45
        while time.monotonic() < until:
            try:
                event = q.get(timeout=0.05)
            except Empty:
                continue
            if event[0] == "error":
                raise AssertionError(event)
            observed.append(event)
        assert not any(e[:2] == ("at_append", "beta.txt") for e in observed), observed
    finally:
        release.set()
        a.join(timeout=30)
        if b.pid is not None:
            b.join(timeout=30)
        for p in (a, b):
            if p.pid is not None and p.is_alive():
                p.terminate()
                p.join(timeout=5)
    assert (a.exitcode, b.exitcode) == (0, 0)
    remaining = old + observed
    while True:
        try:
            remaining.append(q.get_nowait())
        except Empty:
            break
    assert not [e for e in remaining if e[0] == "error"], remaining
    assert {x[1] for x in remaining if x[0] == "completed"} == {"alpha.txt", "beta.txt"}
    appended = {x[1]: x[2] for x in remaining if x[0] == "appended"}
    assert set(appended) == {"alpha.txt", "beta.txt"}
    b_at_append = [x for x in remaining if x[:2] == ("at_append", "beta.txt")]
    assert len(b_at_append) == 1
    assert b_at_append[0][2] == appended["alpha.txt"], remaining
    with CMPCT(archive) as reader:
        assert "alpha-new.txt" in reader.by
        assert "beta-new.txt" in reader.by
        assert "alpha.txt" not in reader.by
        assert "beta.txt" not in reader.by
        assert reader.read("alpha-new.txt") == b"alpha payload\n" * 70
        assert reader.read("beta-new.txt") == b"beta payload\n" * 70
        assert reader.verify() >= 2
    if via_hardlink:
        assert os.stat(alias).st_ino == os.stat(archive).st_ino


def test_lease_released_on_failed_mutation(tmp_path):
    archive = _make_archive(tmp_path)
    with pytest.raises(KeyError):
        tx.append_rename(archive, "missing.txt", "not-here.txt")
    tx.append_delete(archive, "alpha.txt")
    with CMPCT(archive) as reader:
        assert "alpha.txt" not in reader.by
        assert reader.read("beta.txt") == b"beta payload\n" * 70


def test_path_replacement_detection_releases_lock(tmp_path):
    archive = _make_archive(tmp_path)
    replacement = tmp_path / "replacement.cmpct"
    shutil.copyfile(archive, replacement)
    with pytest.raises(RuntimeError, match="pathname changed"):
        with tx._cooperative_writer_lease(archive):
            os.replace(replacement, archive)
    tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    with CMPCT(archive) as reader:
        assert "alpha-new.txt" in reader.by


def test_unsupported_lock_does_not_fall_back_to_unsafe_writes(tmp_path, monkeypatch):
    archive = _make_archive(tmp_path)
    monkeypatch.setattr(tx, "fcntl", None)
    with pytest.raises(NotImplementedError, match="POSIX inode lock"):
        tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    with CMPCT(archive) as reader:
        assert "alpha.txt" in reader.by
        assert "alpha-new.txt" not in reader.by


def test_update_then_rename_then_delete_under_leases(tmp_path):
    archive = _make_archive(tmp_path)
    new_source = tmp_path / "replacement.txt"
    new_source.write_bytes(b"independent new bytes" * 100)
    receipt = tx.append_update(archive, "alpha.txt", new_source)
    assert receipt["member"] == "alpha.txt"
    tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    tx.append_delete(archive, "beta.txt")
    with CMPCT(archive) as reader:
        assert reader.read("alpha-new.txt") == new_source.read_bytes()
        assert "beta.txt" not in reader.by
        assert reader.verify() >= 1
