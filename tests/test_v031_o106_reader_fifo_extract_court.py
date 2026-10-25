"""O106 genuine installed-product Reader FIFO output-leaf availability court.

This is a *negative scientific test*: a passing FIFO test means a bounded
availability failure was reproduced, not that the Reader is safe. Never open an
unconnected FIFO in the pytest host process. Every extraction runs in an
independent killable child with a matched regular/fresh control.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.codec import S_BLOB

CHILD_DEADLINE_S = 8
EXPECTED_READER_GIT_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"


@pytest.fixture(scope="module")
def genuine_archive(tmp_path_factory):
    # One physical archive for all three A/B/C cases on the same runner. This
    # prevents source timestamps/paths from changing archive SHA between arms.
    tmp_path = tmp_path_factory.mktemp("o106-fixed-archive")
    source = tmp_path / "source"
    source.mkdir()
    payload = hashlib.shake_256(b"O106-existing-extract-output-FIFO").digest(4096)
    (source / "payload.bin").write_bytes(payload)
    archive = tmp_path / "original.cmpct"
    Builder(source, workers=1).build(archive)
    with CMPCT(archive) as reader:
        assert len(reader.files) == 1
        assert reader.files[0][0] == "payload.bin"
        assert reader.files[0][6][0] == S_BLOB, reader.files[0][6]
        assert reader.verify() == 1
        assert reader.read("payload.bin") == payload
    yield archive, payload, tmp_path


def _extract_child(archive: Path, dest: Path):
    program = (
        "from pathlib import Path\n"
        "from cmpct.core import CMPCT\n"
        "import hashlib,sys\n"
        "archive=Path(sys.argv[1]);dest=Path(sys.argv[2])\n"
        "with CMPCT(archive) as r:\n"
        "    print('O106_CHILD_INDEX_OPENED',flush=True)\n"
        "    r.extractall(dest,metadata=False)\n"
        "print('O106_EXTRACT_RETURNED',flush=True)\n"
        "print('O106_EXTRACT_SHA='+hashlib.sha256((dest/'payload.bin').read_bytes()).hexdigest(),flush=True)\n"
    )
    return subprocess.run(
        [sys.executable, "-c", program, str(archive), str(dest)],
        cwd=str(dest.parent),
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=CHILD_DEADLINE_S, check=False,
    )


def _check_success(result, expected):
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert "O106_CHILD_INDEX_OPENED" in result.stdout, result.stdout
    assert "O106_EXTRACT_RETURNED" in result.stdout, result.stdout
    assert "O106_EXTRACT_SHA=" + hashlib.sha256(expected).hexdigest() in result.stdout, result.stdout


def _evidence(case, archive, dest, payload, state):
    result = {
        "case": case,
        "outcome": state,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "leaf_kind": "fifo" if dest.joinpath("payload.bin").exists() and stat.S_ISFIFO(os.lstat(dest / "payload.bin").st_mode) else ("regular" if (dest / "payload.bin").is_file() else "unknown"),
        "parent_pid": os.getpid(),
        "child_timeout_seconds": CHILD_DEADLINE_S,
    }
    print("O106_CASE=" + json.dumps(result, sort_keys=True), flush=True)


def test_o106_fresh_destination_exact(genuine_archive):
    archive, payload, root = genuine_archive
    dest = root / "fresh"
    dest.mkdir()
    result = _extract_child(archive, dest)
    _check_success(result, payload)
    assert (dest / "payload.bin").read_bytes() == payload
    _evidence("fresh", archive, dest, payload, "reconstructed_exact")


def test_o106_existing_regular_destination_exact(genuine_archive):
    archive, payload, root = genuine_archive
    dest = root / "regular"
    dest.mkdir()
    old = b"pre-existing regular-file bytes"
    (dest / "payload.bin").write_bytes(old)
    assert (dest / "payload.bin").read_bytes() == old
    result = _extract_child(archive, dest)
    _check_success(result, payload)
    assert (dest / "payload.bin").read_bytes() == payload
    _evidence("regular", archive, dest, payload, "reconstructed_exact")


def test_o106_unconnected_fifo_blocks_reader(genuine_archive):
    archive, payload, root = genuine_archive
    dest = root / "fifo"
    dest.mkdir()
    leaf = dest / "payload.bin"
    assert hasattr(os, "mkfifo"), "POSIX FIFO creation is a prerequisite"
    os.mkfifo(leaf)
    assert stat.S_ISFIFO(os.lstat(leaf).st_mode)
    try:
        result = _extract_child(archive, dest)
    except subprocess.TimeoutExpired as exc:
        assert stat.S_ISFIFO(os.lstat(leaf).st_mode), "Reader mutated FIFO before timeout"
        assert (root / "source" / "payload.bin").read_bytes() == payload
        print("O106_REAL_READER_FIFO_TIMEOUT=CONFIRMED", flush=True)
        _evidence("unconnected_fifo", archive, dest, payload, "timeout_expected_hypothesis")
    else:
        raise AssertionError(
            "Authentic Reader did not block on unconnected FIFO; hypothesis falsified: "
            f"rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}"
        )
