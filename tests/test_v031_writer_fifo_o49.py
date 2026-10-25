"""O49: source-exact bounded real Writer CLI FIFO admission probe; research only."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _archive(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "initial.txt").write_bytes(b"original-payload")
    archive = tmp_path / "authentic-r24.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.read("initial.txt") == b"original-payload"
        assert reader.verify() >= 1
    return archive


def test_ordinary_cli_update_control(tmp_path):
    archive = _archive(tmp_path)
    payload = tmp_path / "new-file.bin"
    payload.write_bytes(bytes((i * 11 + 9) % 256 for i in range(2048)))
    cp = subprocess.run(
        [sys.executable, "-m", "cmpct", "update",
         str(archive), "initial.txt", str(payload)],
        check=False, capture_output=True, text=True, timeout=40)
    assert cp.returncode == 0, (cp.stdout, cp.stderr)
    with CMPCT(archive) as reader:
        assert reader.read("initial.txt") == payload.read_bytes()
        assert reader.verify() >= 1


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="real no-writer named pipe requires POSIX")
def test_real_cli_update_fifo_source_blocks_without_writer(tmp_path):
    archive = _archive(tmp_path)
    prior_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    fifo = tmp_path / "input.fifo"
    os.mkfifo(fifo, 0o600)
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [sys.executable, "-m", "cmpct", "update",
             str(archive), "initial.txt", str(fifo)],
            check=False, capture_output=True, text=True, timeout=3.0)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == prior_digest
    with CMPCT(archive) as reader:
        assert reader.read("initial.txt") == b"original-payload"
        assert reader.verify() >= 1
