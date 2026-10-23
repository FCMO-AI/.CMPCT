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


@pytest.mark.parametrize("alias_kind", ["same", "hardlink", "symlink"])
def test_independent_writers_snapshot_serialized_through_footer(tmp_path, alias_kind):
    """Second writer cannot snapshot the same footer while first writer is paused."""
    ctx = mp.get_context("fork")
    archive = _make_archive(tmp_path)
    alias = tmp_path / "hardlink-alias.cmpct"
    if alias_kind == "hardlink":
        os.link(archive, alias)
    elif alias_kind == "symlink":
        alias.symlink_to(archive)

    q = ctx.Queue()
    release = ctx.Event()
    a = ctx.Process(
        target=_rename_worker,
        args=(str(archive), "alpha.txt", "alpha-new.txt", q, release),
    )
    b = ctx.Process(
        target=_rename_worker,
        args=(str(alias if alias_kind != "same" else archive), "beta.txt", "beta-new.txt", q),
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
    if alias_kind != "same":
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


def test_replace_archive_path_between_snapshot_and_append_cannot_mutate_replacement(tmp_path, monkeypatch):
    """An exception alone is insufficient: outside/replacement bytes must survive."""
    import hashlib

    archive = _make_archive(tmp_path)
    replacement = tmp_path / "fresh.cmpct"
    shutil.copyfile(archive, replacement)
    expected_bytes = replacement.read_bytes()
    original_inode = replacement.stat().st_ino
    original = tx._append_generation

    def swap_after_snapshot(*args, **kwargs):
        os.replace(replacement, archive)
        return original(*args, **kwargs)

    monkeypatch.setattr(tx, "_append_generation", swap_after_snapshot)
    with pytest.raises(RuntimeError, match="archive"):
        tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    # On the first locking-only candidate this stronger assertion FAILS:
    # the post-commit check observes an inode swap, but only after mutating
    # the replacement's contents. The next candidate must reject pre-write.
    assert archive.stat().st_ino == original_inode
    assert archive.read_bytes() == expected_bytes
    assert hashlib.sha256(archive.read_bytes()).digest() == hashlib.sha256(expected_bytes).digest()


def _lock_then_os_exit(archive, ready):
    """Bypass Python finally deliberately: kernel must release the advisory lock."""
    with tx._cooperative_writer_lease(Path(archive)):
        ready.set()
        os._exit(17)


def test_kernel_releases_writer_lock_after_crashed_owner(tmp_path):
    ctx = mp.get_context("fork")
    archive = _make_archive(tmp_path)
    ready = ctx.Event()
    worker = ctx.Process(target=_lock_then_os_exit, args=(str(archive), ready))
    worker.start()
    try:
        assert ready.wait(timeout=15), "child never acquired the archive lease"
        worker.join(timeout=15)
        assert worker.exitcode == 17
        # A fresh public operation must not deadlock on an orphaned lease.
        tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
        with CMPCT(archive) as reader:
            assert reader.read("alpha-new.txt") == b"alpha payload\n" * 70
            assert reader.verify() >= 2
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)


def test_transient_rebind_cannot_poison_new_blob_offsets(tmp_path, monkeypatch):
    """Even a short-lived different pathname inode cannot supply blob offsets."""
    import hashlib

    archive = _make_archive(tmp_path)
    control = tmp_path / "control.cmpct"
    shutil.copyfile(archive, control)
    foreign_tree = tmp_path / "foreign-source"
    foreign_tree.mkdir()
    (foreign_tree / "other.dat").write_bytes(os.urandom(8192))
    foreign = tmp_path / "foreign.cmpct"
    Builder(foreign_tree).build(foreign)
    assert foreign.stat().st_size != archive.stat().st_size
    foreign_sha = hashlib.sha256(foreign.read_bytes()).digest()
    new_source = tmp_path / "new-data.bin"
    new_source.write_bytes(b"CHANGED CONTENT\n" * 300)

    original = tx._locked_archive_size
    parked = tmp_path / "parked-original.cmpct"
    rebinding_count = []

    def swap_just_while_sizing(path):
        os.replace(archive, parked)
        os.replace(foreign, archive)
        try:
            assert os.stat(archive).st_ino != os.stat(parked).st_ino
            rebinding_count.append(True)
            return original(path)
        finally:
            os.replace(archive, foreign)
            os.replace(parked, archive)

    control_result = tx.append_update(control, "alpha.txt", new_source)
    monkeypatch.setattr(tx, "_locked_archive_size", swap_just_while_sizing)
    candidate_result = tx.append_update(archive, "alpha.txt", new_source)
    assert rebinding_count, "adversary must have actually substituted an inode"
    assert candidate_result == control_result
    assert archive.read_bytes() == control.read_bytes()
    assert hashlib.sha256(foreign.read_bytes()).digest() == foreign_sha
    with CMPCT(archive) as reader:
        assert reader.read("alpha.txt") == new_source.read_bytes()
        assert reader.read("beta.txt") == b"beta payload\n" * 70
        assert reader.verify() >= 2


def test_pre_footer_flush_failure_releases_lease_and_preserves_last_commit(tmp_path, monkeypatch):
    """A failed first fsync leaves a noncommitted tail, not a visible rename."""
    archive = _make_archive(tmp_path)
    original_fsync = tx.os.fsync

    def fail_first_fsync(fd):
        raise OSError("injected pre-footer flush failure")

    monkeypatch.setattr(tx.os, "fsync", fail_first_fsync)
    try:
        with pytest.raises(OSError, match="pre-footer"):
            tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    finally:
        monkeypatch.setattr(tx.os, "fsync", original_fsync)

    # The payload was physically appended but no new footer is committed.
    # Reader must recover previous generation and after lock release a new
    # transaction may succeed without discarding or fabricating old content.
    with CMPCT(archive) as reader:
        assert "alpha.txt" in reader.by
        assert "alpha-new.txt" not in reader.by
        assert reader.read("alpha.txt") == b"alpha payload\n" * 70
        assert reader.verify() >= 2

    tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    with CMPCT(archive) as reader:
        assert reader.read("alpha-new.txt") == b"alpha payload\n" * 70
        assert reader.read("beta.txt") == b"beta payload\n" * 70
        assert reader.verify() >= 2


def test_generation_append_uses_locked_description_not_archive_path(tmp_path, monkeypatch):
    """No second pathname open is allowed after the transaction snapshot."""
    archive = _make_archive(tmp_path)
    old_generation = tx._append_generation
    called = []

    def disallow_archive_path_reopen(*args, **kwargs):
        called.append(True)
        original_open = tx.os.open

        def refuse_archive_open(path, flags, *a, **kw):
            if os.fspath(path) == os.fspath(archive):
                raise AssertionError("generation tried to reopen mutable archive pathname")
            return original_open(path, flags, *a, **kw)

        with monkeypatch.context() as local:
            local.setattr(tx.os, "open", refuse_archive_open)
            return old_generation(*args, **kwargs)

    monkeypatch.setattr(tx, "_append_generation", disallow_archive_path_reopen)
    tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    assert called, "must reach real physical generation writer"
    with CMPCT(archive) as reader:
        assert reader.read("alpha-new.txt") == b"alpha payload\n" * 70
        assert reader.read("beta.txt") == b"beta payload\n" * 70
        assert reader.verify() >= 2


def test_reader_snapshot_cannot_be_redirected_after_lock(tmp_path, monkeypatch):
    """A replacement Reader inode is rejected before any generation is appended."""
    archive = _make_archive(tmp_path)
    new_archive = tmp_path / "replacement.cmpct"
    shutil.copyfile(archive, new_archive)
    expected = new_archive.read_bytes()
    previous = tmp_path / "previous-original.cmpct"
    real_checked_reader = tx._checked_writer_reader

    def switched_reader(path):
        os.replace(archive, previous)
        os.replace(new_archive, archive)
        return real_checked_reader(path)

    monkeypatch.setattr(tx, "_checked_writer_reader", switched_reader)
    with pytest.raises(RuntimeError, match="Reader descriptor changed"):
        tx.append_rename(archive, "alpha.txt", "alpha-new.txt")
    assert archive.read_bytes() == expected
    assert previous.exists()
    with CMPCT(archive) as reader:
        assert "alpha.txt" in reader.by
        assert "alpha-new.txt" not in reader.by


def _update_worker(archive, member, source, release, results):
    try:
        if not release.wait(timeout=15):
            raise TimeoutError("did not receive update barrier")
        result = tx.append_update(Path(archive), member, Path(source))
        results.put(("ok", member, result["new_chunks"]))
    except BaseException as exc:
        results.put(("error", member, repr(exc)))
        raise


def test_two_process_disjoint_public_update_preserves_both_blobs(tmp_path):
    """Reader, physical blob offsets and commit ancestry survive multiwriter updates."""
    ctx = mp.get_context("fork")
    archive = _make_archive(tmp_path)
    payloads = {
        "alpha.txt": b"ALPHA REVISION " * 32000,
        "beta.txt": b"BETA REVISION " * 32000,
    }
    sources = {}
    for member, raw in payloads.items():
        source = tmp_path / (member + ".source")
        source.write_bytes(raw)
        sources[member] = source
    release = ctx.Event()
    results = ctx.Queue()
    children = [
        ctx.Process(target=_update_worker, args=(str(archive), member, str(source), release, results))
        for member, source in sources.items()
    ]
    for child in children:
        child.start()
    try:
        release.set()
        for child in children:
            child.join(timeout=50)
        for child in children:
            assert child.exitcode == 0, f"worker exit={child.exitcode}"
        events = [results.get(timeout=10) for _ in children]
        assert all(e[0] == "ok" for e in events), events
        assert {e[1] for e in events} == set(payloads)
        with CMPCT(archive) as reader:
            for member, raw in payloads.items():
                assert reader.read(member) == raw
            assert reader.verify() >= 2
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
