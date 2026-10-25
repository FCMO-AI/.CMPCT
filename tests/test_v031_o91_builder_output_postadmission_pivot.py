"""O91: installed O90 Builder post-admission destination-lifetime falsifier.

These are EXPECTED-NEGATIVE research controls, not safety guarantees or release tests.
"""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import threading

import pytest
from cmpct.core import Builder, CMPCT


pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX atomic rename, FIFO and symlink oracle")


def _source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    payload = hashlib.shake_256(b"o91-source-content").digest(4096)
    leaf = root / "data.bin"
    leaf.write_bytes(payload)
    assert os.stat(leaf).st_nlink == 1
    return root, leaf, payload


def test_o91_regular_output_control(tmp_path):
    root, leaf, payload = _source(tmp_path)
    out = tmp_path / "existing.cmpct"
    out.write_bytes(b"previous-independent-output")
    result = Builder(root, workers=1).build(out)
    assert result["bytes"] == out.stat().st_size > 0
    assert leaf.read_bytes() == payload
    with CMPCT(out) as archive:
        archive.verify()
        assert archive.read("data.bin") == payload
    print("O91_REGULAR_OUTPUT_CONTROL=PASS", flush=True)


def test_o91_postscan_symlink_pivot_clobbers_one_link_source(tmp_path):
    root, leaf, payload = _source(tmp_path)
    out = tmp_path / "external.cmpct"
    out.write_bytes(b"original-independent-regular-output")
    pending = tmp_path / "pending-target-link"
    pending.symlink_to(leaf)
    original_ino = os.stat(out).st_ino
    assert os.stat(out).st_nlink == 1
    assert original_ino != os.stat(leaf).st_ino

    scanned = threading.Event()
    swapped = threading.Event()
    actor_errors = []

    def actor():
        try:
            if not scanned.wait(5):
                raise AssertionError("Builder did not reach original scan completion")
            # POSIX rename is atomic: no transient missing pathname is needed.
            os.replace(pending, out)
        except BaseException as exc:
            actor_errors.append(exc)
        finally:
            swapped.set()

    worker = threading.Thread(target=actor, daemon=True)
    builder = Builder(root, workers=1)
    real_scan = builder.scan

    def synchronized_real_scan():
        real_scan()  # Actual O90 scanner; never substitute archive contents.
        scanned.set()
        assert swapped.wait(5), "adversary missed the post-admission boundary"
        assert not actor_errors, repr(actor_errors)
        assert out.is_symlink() and out.resolve() == leaf.resolve()

    builder.scan = synchronized_real_scan
    worker.start()
    try:
        result = builder.build(out)
    finally:
        worker.join(timeout=5)

    assert not worker.is_alive() and not actor_errors, repr(actor_errors)
    assert out.is_symlink() and out.resolve() == leaf.resolve()
    assert result["bytes"] == leaf.stat().st_size > 0
    assert leaf.read_bytes() != payload, "O90 may have learned to reject post-scan source aliases"
    # This makes the failure especially deceptive: an exact archive may now
    # physically occupy the source leaf that it was supposed to preserve.
    with CMPCT(out) as archive:
        archive.verify()
        assert archive.read("data.bin") == payload
    print("O91_SOURCE_CLOBBER_AFTER_ADMISSION=CONFIRMED", flush=True)


def test_o91_postscan_fifo_pivot_blocks_despite_initial_regular_admission(tmp_path):
    root, leaf, payload = _source(tmp_path)
    out = tmp_path / "external.cmpct"
    out.write_bytes(b"initial-regular-output")
    marker = tmp_path / "swapped.marker"
    child = r"""
import os, sys, threading
from pathlib import Path
from cmpct.core import Builder
root, out, marker = map(Path, sys.argv[1:4])
stage = out.parent / "pending-fifo"
os.mkfifo(stage)
scanned = threading.Event()
swapped = threading.Event()
errors = []
def attack():
    try:
        if not scanned.wait(5):
            raise AssertionError("scan did not complete")
        os.replace(stage, out)
        marker.write_text("FIFO_SWAPPED")
    except BaseException as exc:
        errors.append(repr(exc))
    finally:
        swapped.set()
worker = threading.Thread(target=attack, daemon=True)
builder = Builder(root, workers=1)
original_scan = builder.scan
def synchronized_real_scan():
    original_scan()
    scanned.set()
    assert swapped.wait(5), "pivot was not installed"
    assert not errors, errors
    print("O91_AT_POSTSCAN_FIFO_BOUNDARY", flush=True)
builder.scan = synchronized_real_scan
worker.start()
builder.build(out)
print("O91_BUILD_RETURNED", flush=True)
"""
    try:
        completed = subprocess.run(
            [sys.executable, "-c", child, str(root), str(out), str(marker)],
            cwd=str(tmp_path), capture_output=True, text=True, timeout=7,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        assert marker.read_text() == "FIFO_SWAPPED", "timeout without proven actor pivot"
        assert stat.S_ISFIFO(os.stat(out).st_mode)
        assert leaf.read_bytes() == payload
        assert b"O91_AT_POSTSCAN_FIFO_BOUNDARY" in (exc.stdout or b""), (
            "timeout before the writer path reached the barrier", exc.stdout, exc.stderr
        )
        print("O91_POST_ADMISSION_FIFO_TIMEOUT_GT_7S=CONFIRMED", flush=True)
    else:
        pytest.fail(
            "Installed O90 Builder did not exhibit expected FIFO-path block "
            f"(rc={completed.returncode}, stdout={completed.stdout!r}, stderr={completed.stderr!r}); "
            "falsify/narrow this research claim, do not weaken the control"
        )
