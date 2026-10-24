"""Windows O5: independent-process kernel LockFileEx versus real CMPCT CRT lease.

Primitive falsifier only. Does not replace the public Writer's locking backend.
"""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
from queue import Empty
import time

import pytest
from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows kernel32 LockFileEx only")


def _archive(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    (root / "alpha.bin").write_bytes(b"cmpct-kernel-interop\n" * 137)
    archive = tmp_path / "interop.cmpct"
    Builder(root).build(archive)
    return archive


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save(label: str, record: dict) -> None:
    root = Path(os.environ.get("CMPCT_O5_ARTIFACT_DIR", "test-artifacts"))
    root.mkdir(parents=True, exist_ok=True)
    (root / (label + ".json")).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("O5_RESULT " + json.dumps(record, sort_keys=True), flush=True)


def _kernel_lock_child(path: str, events) -> None:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ("Internal", ctypes.c_size_t),
            ("InternalHigh", ctypes.c_size_t),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LockFileEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(OVERLAPPED)
    ]
    kernel.LockFileEx.restype = wintypes.BOOL
    kernel.UnlockFileEx.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, ctypes.POINTER(OVERLAPPED)
    ]
    kernel.UnlockFileEx.restype = wintypes.BOOL

    fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_BINARY)
    handle = msvcrt.get_osfhandle(fd)
    off = tx._WINDOWS_LEASE_OFFSET
    overlap = OVERLAPPED()
    overlap.Offset = off & 0xffffffff
    overlap.OffsetHigh = (off >> 32) & 0xffffffff
    overlap.hEvent = None
    success = False
    started = time.perf_counter_ns()
    events.put(("entered", started))
    try:
        if not kernel.LockFileEx(handle, 0x00000002, 0, 1, 0, ctypes.byref(overlap)):
            raise ctypes.WinError(ctypes.get_last_error())
        success = True
        acquired_ns = time.perf_counter_ns()
        events.put(("acquired", {
            "call_duration_ms": (acquired_ns - started) / 1e6,
            "acquired_ns": acquired_ns, "api": "LockFileEx/synchronous",
            "offset": off, "handle": "independent real file descriptor",
        }))
    except BaseException as exc:
        events.put(("failed", {
            "type": type(exc).__name__, "error": str(exc),
            "call_duration_ms": (time.perf_counter_ns() - started) / 1e6,
        }))
    finally:
        try:
            if success:
                if not kernel.UnlockFileEx(handle, 0, 1, 0, ctypes.byref(overlap)):
                    events.put(("unlock_failed", ctypes.get_last_error()))
                else:
                    events.put(("unlocked", None))
        finally:
            os.close(fd)


def _event(q, timeout=35):
    try:
        return q.get(timeout=timeout)
    except Empty:
        raise AssertionError("child did not emit expected Windows LockFileEx event") from None


@pytest.mark.parametrize("hold_seconds", [0.30, 11.30])
def test_lockfileex_waits_on_existing_crt_sentinel_and_unblocks(tmp_path, hold_seconds):
    archive = _archive(tmp_path)
    before_sha = _sha(archive)
    before_size = archive.stat().st_size
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    child = ctx.Process(target=_kernel_lock_child, args=(str(archive), q))
    first = outcome = unlocked = None
    try:
        with tx._cooperative_writer_lease(archive):
            child.start()
            first = _event(q)
            assert first[0] == "entered", first
            entered_ns = first[1]
            # The Reader must remain able to open and verify ordinary bytes.
            with CMPCT(archive) as reader:
                assert reader.read("alpha.bin") == b"cmpct-kernel-interop\n" * 137
                assert reader.verify() >= 1
            deadline = time.monotonic() + hold_seconds
            while time.monotonic() < deadline:
                time.sleep(min(0.04, max(0.001, deadline - time.monotonic())))
            # A successful child acquisition before this time means two writers
            # could own the same physical archive transaction concurrently.
            release_start_ns = time.perf_counter_ns()
        released_ns = time.perf_counter_ns()
        child.join(timeout=22)
        assert child.exitcode == 0, ("child process", child.exitcode)
        outcome = _event(q, 5)
        assert outcome[0] == "acquired", ("LockFileEx failed to wait for holder", outcome)
        assert outcome[1]["acquired_ns"] >= release_start_ns, (
            "kernel lock acquired before CRT lease release", outcome
        )
        unlocked = _event(q, 5)
        assert unlocked[0] == "unlocked", ("kernel lock not released", unlocked)
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)
        q.close()
        q.join_thread()

    assert _sha(archive) == before_sha, "locking primitives mutated archive"
    assert archive.stat().st_size == before_size, "locking expanded physical EOF"
    _save("windows-lockfileex-interop-" + str(round(hold_seconds * 1000)), {
        "hold_target_ms": round(hold_seconds * 1000),
        "hold_actual_ms": (released_ns - entered_ns) / 1e6,
        "crt_holder": "actual CMPCT _cooperative_writer_lease",
        "kernel_child": outcome[1],
        "child_exitcode": child.exitcode,
        "reader_while_locked": "PASS",
        "archive_size_unchanged": True,
        "archive_sha256_before": before_sha,
        "archive_sha256_after": _sha(archive),
        "platform": platform.platform(),
        "source_protocol_compatibility": "observed primitive, not product Writer promotion",
    })
