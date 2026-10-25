"""O87: falsify nonregular destination availability on genuine installed O84 Builder.

Never invoke Builder on an unwritten FIFO in the test process. Children have a
hard deadline and are terminated by subprocess.run() on timeout. A matched
regular-output child proves the time bound is not just ordinary build latency.
This suite proves/narrows a source-bound defect; it is not a product repair.
"""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

from cmpct.core import Builder, CMPCT


EXPECTED_BUILDER_BLOB = "64b0cd21ad54ce7c8e8c6f5847b3c613fff6511c"
MAX_CHILD_SECONDS = 8


def _source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    raw = hashlib.shake_256(b"O87-genuine-output-admission").digest(512)
    (root / "payload.bin").write_bytes(raw)
    return root, raw


def _child(root, output):
    # Child cwd outside the repository; product is pip-installed by the court.
    program = (
        "import sys\n"
        "from pathlib import Path\n"
        "from cmpct.core import Builder\n"
        "Builder(Path(sys.argv[1]), workers=1).build(Path(sys.argv[2]))\n"
        "print('O87_BUILD_RETURNED', flush=True)\n"
    )
    return subprocess.run(
        [sys.executable, "-c", program, str(root), str(output)],
        cwd=str(root.parent),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=MAX_CHILD_SECONDS,
        check=False,
    )


def _matching_regular_control(root, raw, output):
    output.write_bytes(b"prior independent output contents")
    result = _child(root, output)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "O87_BUILD_RETURNED" in result.stdout, (result.stdout, result.stderr)
    with CMPCT(output) as ar:
        ar.verify()
        assert ar.read("payload.bin") == raw
    assert (root / "payload.bin").read_bytes() == raw


def test_existing_regular_destination_completes_and_verifies(tmp_path):
    root, raw = _source(tmp_path)
    _matching_regular_control(root, raw, tmp_path / "regular.cmpct")


def test_unconnected_fifo_destination_blocks_real_builder(tmp_path):
    root, raw = _source(tmp_path)
    _matching_regular_control(root, raw, tmp_path / "control.cmpct")
    out = tmp_path / "unconnected-fifo.cmpct"
    assert hasattr(os, "mkfifo"), "POSIX FIFO API needed for this court"
    os.mkfifo(out)
    assert stat.S_ISFIFO(os.stat(out).st_mode)
    try:
        result = _child(root, out)
    except subprocess.TimeoutExpired:
        print("O87_REAL_PRODUCT_FIFO_TIMEOUT=CONFIRMED", flush=True)
    else:
        raise AssertionError(
            "genuine Builder did not block at an unconnected FIFO: "
            f"rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    assert stat.S_ISFIFO(os.stat(out).st_mode)
    assert (root / "payload.bin").read_bytes() == raw


def test_symlink_to_unconnected_fifo_blocks_real_builder(tmp_path):
    root, raw = _source(tmp_path)
    _matching_regular_control(root, raw, tmp_path / "control.cmpct")
    fifo = tmp_path / "fifo-target"
    os.mkfifo(fifo)
    out = tmp_path / "outside-symlink.cmpct"
    out.symlink_to(fifo)
    assert out.is_symlink() and stat.S_ISFIFO(os.stat(out).st_mode)
    try:
        result = _child(root, out)
    except subprocess.TimeoutExpired:
        print("O87_REAL_PRODUCT_SYMLINK_FIFO_TIMEOUT=CONFIRMED", flush=True)
    else:
        raise AssertionError(
            "genuine Builder did not block at a symlink-to-FIFO: "
            f"rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    assert out.is_symlink() and stat.S_ISFIFO(os.stat(out).st_mode)
    assert (root / "payload.bin").read_bytes() == raw
