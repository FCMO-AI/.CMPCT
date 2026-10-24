"""Source-exact Windows O4: quantify real independent Writer contention.

A green research court means timing and outcomes were classified truthfully,
NOT that a product latency/performance release gate has passed.
"""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
from queue import Empty
import statistics
import time

import pytest
from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows CRT Writer lease only")


def _archive(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "alpha.txt").write_bytes(b"alpha-unchanged\n" * 73)
    (source / "beta.txt").write_bytes(b"beta-unchanged\n" * 71)
    target = tmp_path / "held.cmpct"
    Builder(source).build(target)
    return target


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(label, evidence):
    root = Path(os.environ.get("CMPCT_O4_ARTIFACT_DIR", "test-artifacts"))
    root.mkdir(parents=True, exist_ok=True)
    (root / (label + ".json")).write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("O4_RESULT " + json.dumps(evidence, sort_keys=True), flush=True)


def _writer(archive, events):
    """Instrument the real CRT entry without replacing the lock operation."""
    actual = tx.msvcrt.locking
    seen = False

    def timed_lock(fd, mode, size):
        nonlocal seen
        if mode != tx.msvcrt.LK_LOCK:
            return actual(fd, mode, size)
        assert not seen, "public writer unexpectedly reacquired lease"
        seen = True
        started = time.perf_counter_ns()
        events.put(("lock_enter", started))
        try:
            value = actual(fd, mode, size)
        except BaseException as exc:
            events.put(("lock_exit", {
                "status": "error", "type": type(exc).__name__,
                "message": str(exc),
                "duration_ms": (time.perf_counter_ns() - started) / 1e6,
            }))
            raise
        completed_ns = time.perf_counter_ns()
        events.put(("lock_exit", {
            "status": "acquired",
            "duration_ms": (completed_ns - started) / 1e6,
            "completed_ns": completed_ns,
        }))
        return value

    tx.msvcrt.locking = timed_lock
    try:
        tx.append_rename(Path(archive), "alpha.txt", "alpha-renamed.txt")
    except BaseException as exc:
        events.put(("writer_result", {
            "status": "error", "type": type(exc).__name__, "message": str(exc)
        }))
    else:
        events.put(("writer_result", {"status": "success"}))
    finally:
        tx.msvcrt.locking = actual


def _next(events, expected, timeout):
    try:
        item = events.get(timeout=timeout)
    except Empty:
        raise AssertionError(("missing event", expected)) from None
    assert item[0] == expected, ("unexpected event order", item, expected)
    return item[1]


@pytest.mark.parametrize("hold_seconds", [0.30, 2.20, 11.30])
def test_contended_real_windows_transaction(tmp_path, hold_seconds):
    archive = _archive(tmp_path)
    before = _sha(archive)
    ctx = mp.get_context("spawn")
    events = ctx.Queue()
    child = ctx.Process(target=_writer, args=(str(archive), events))
    entered_ns = release_begin_ns = released_ns = None
    try:
        with tx._cooperative_writer_lease(archive):
            child.start()
            entered_ns = _next(events, "lock_enter", 35)
            deadline = time.monotonic() + hold_seconds
            while time.monotonic() < deadline:
                time.sleep(min(0.04, max(0.001, deadline - time.monotonic())))
            # Still inside the held lease: a successful child lock before this
            # instant would be a lock-exclusion violation, even if bytes later verify.
            release_begin_ns = time.perf_counter_ns()
        released_ns = time.perf_counter_ns()
        child.join(timeout=45)
        assert child.exitcode == 0, ("child exit", child.exitcode)
        lock = _next(events, "lock_exit", 5)
        outcome = _next(events, "writer_result", 5)
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)
        events.close()
        events.join_thread()

    assert (lock["status"] == "acquired") == (outcome["status"] == "success")
    if outcome["status"] == "success":
        assert lock["completed_ns"] >= release_begin_ns, (
            "child acquired CRT lease while parent still held it", lock
        )
        with CMPCT(archive) as reader:
            assert sorted(reader.by) == ["alpha-renamed.txt", "beta.txt"]
            assert reader.read("alpha-renamed.txt") == b"alpha-unchanged\n" * 73
            assert reader.read("beta.txt") == b"beta-unchanged\n" * 71
            assert reader.verify() >= 2
    else:
        # A bounded retry failure is acceptable only when explicit and
        # byte-preserving. A successful retry after lease release is required.
        assert outcome["type"] in {"OSError", "PermissionError", "BlockingIOError"}
        assert _sha(archive) == before, "denied writer modified the archive"
        with CMPCT(archive) as reader:
            assert sorted(reader.by) == ["alpha.txt", "beta.txt"]
            assert reader.verify() >= 2
        tx.append_rename(archive, "alpha.txt", "alpha-renamed.txt")
        with CMPCT(archive) as reader:
            assert sorted(reader.by) == ["alpha-renamed.txt", "beta.txt"]
            assert reader.read("alpha-renamed.txt") == b"alpha-unchanged\n" * 73
            assert reader.verify() >= 2

    _save("windows-contention-" + str(round(hold_seconds * 1000)), {
        "hold_target_ms": round(hold_seconds * 1000, 2),
        "hold_actual_ms": round((released_ns - entered_ns) / 1e6, 3),
        "release_begin_ns": release_begin_ns,
        "lock": lock, "writer": outcome, "child_exitcode": child.exitcode,
        "archive_sha256_before": before, "archive_sha256_final": _sha(archive),
        "platform": platform.platform(), "python": platform.python_version(),
        "sentinel_offset": tx._WINDOWS_LEASE_OFFSET, "final_state_verified": True,
    })


def test_uncontended_full_lease_control(tmp_path):
    archive = _archive(tmp_path)
    before = _sha(archive)
    samples = []
    for _ in range(15):
        started = time.perf_counter_ns()
        with tx._cooperative_writer_lease(archive):
            pass
        samples.append((time.perf_counter_ns() - started) / 1e6)
    assert _sha(archive) == before
    _save("windows-uncontended-lease-control", {
        "trials_ms": samples, "median_ms": statistics.median(samples),
        "measurement": "full uncontended lease boundary, not bare CRT syscall",
        "archive_unchanged": True, "platform": platform.platform(),
    })
