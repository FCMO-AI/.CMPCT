"""O48: default r24 builder must not silently omit unsupported filesystem entries."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import socket
import tempfile

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _temp_source():
    # AF_UNIX pathname limits are tighter than runner checkout paths.
    return tempfile.TemporaryDirectory(prefix="cmpct-o48-", dir=tempfile.gettempdir())


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="POSIX FIFO fixture requires os.mkfifo")
def test_fifo_is_not_silently_omitted_from_successful_archive():
    with _temp_source() as td:
        root = Path(td) / "tree"
        root.mkdir()
        (root / "present.txt").write_bytes(b"must-not-produce-partial-archive")
        os.mkfifo(root / "named-pipe", mode=0o600)
        output = Path(td) / "incomplete.cmpct"
        with pytest.raises(OSError, match="unsupported filesystem entry"):
            Builder(root, workers=1, reproducible=True).build(output)
        assert not output.exists(), "a partial tree was published"


@pytest.mark.skipif(os.name == "nt" or not hasattr(socket, "AF_UNIX"),
                    reason="POSIX AF_UNIX pathname socket fixture")
def test_bound_unix_socket_is_not_silently_omitted():
    with _temp_source() as td:
        root = Path(td) / "tree"
        root.mkdir()
        (root / "present.txt").write_bytes(b"normal-file")
        sock_path = root / "endpoint.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.bind(os.fspath(sock_path))
            output = Path(td) / "incomplete.cmpct"
            with pytest.raises(OSError, match="unsupported filesystem entry"):
                Builder(root, workers=1, reproducible=True).build(output)
            assert not output.exists(), "a partial tree was published"


def test_ordinary_tree_remains_byte_deterministic_and_exactly_reconstructible(tmp_path):
    root = tmp_path / "source"
    (root / "nested").mkdir(parents=True)
    payload = bytes((i * 29 + (i >> 3)) & 255 for i in range(1024))
    (root / "nested" / "payload.bin").write_bytes(payload)
    (root / "empty.txt").write_bytes(b"")
    if os.name != "nt":
        os.symlink("nested/payload.bin", root / "safe-link")
    digests = []
    for n in range(2):
        archive = tmp_path / f"output-{n}.cmpct"
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
        digests.append(hashlib.sha256(archive.read_bytes()).hexdigest())
        with CMPCT(archive) as reader:
            assert reader.verify() >= 1
            assert reader.read("nested/payload.bin") == payload
            assert reader.read("empty.txt") == b""
            destination = tmp_path / f"restored-{n}"
            reader.extractall(destination, metadata=False)
        assert (destination / "nested" / "payload.bin").read_bytes() == payload
        assert (destination / "empty.txt").read_bytes() == b""
        if os.name != "nt":
            assert os.readlink(destination / "safe-link") == "nested/payload.bin"
    assert digests[0] == digests[1]


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="CLI FIFO user-surface control requires POSIX")
def test_cli_rejects_fifo_without_overwriting_existing_output(tmp_path):
    """The end-user create command must not report success or clobber an older archive."""
    import subprocess
    import sys

    root = tmp_path / "source"
    root.mkdir()
    (root / "ordinary.dat").write_bytes(b"this-file-exists")
    os.mkfifo(root / "another-pipe")
    archive = tmp_path / "previous.cmpct"
    archive.write_bytes(b"KEEP-PREVIOUS-ARCHIVE-EXACT")
    completed = subprocess.run(
        [sys.executable, "-m", "cmpct", "create", str(root), str(archive)],
        capture_output=True, text=True, timeout=90, check=False)
    assert completed.returncode != 0, completed.stdout
    assert "unsupported filesystem entry" in completed.stderr, completed.stderr
    assert archive.read_bytes() == b"KEEP-PREVIOUS-ARCHIVE-EXACT"
