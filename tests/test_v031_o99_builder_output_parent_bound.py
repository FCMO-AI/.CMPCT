"""O99: installed Builder output-ancestor identity repair; inherited O93 tests remain intact."""
from __future__ import annotations

import hashlib
import os
import stat
import sys
import threading
from pathlib import Path

import pytest
from cmpct.core import Builder, CMPCT


def _source(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    data = hashlib.shake_256(b"o99-public-source-fixture").digest(4096)
    leaf = root / "leaf.bin"
    leaf.write_bytes(data)
    return root, leaf, data


def _verify_archive(path: Path, original: bytes):
    with CMPCT(path) as archive:
        archive.verify()
        assert archive.read("leaf.bin") == original


def test_o99_stable_external_parent_regular_archive(tmp_path):
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "outside"
    external.mkdir()
    destination = external / "archive.cmpct"
    result = Builder(root, workers=1, reproducible=True).build(destination)
    assert result["bytes"] == destination.stat().st_size > 0
    _verify_archive(destination, data)
    assert leaf.read_bytes() == data
    print("O99_STABLE_REGULAR=PASS", flush=True)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX directory symlink")
def test_o99_stable_symlink_parent_and_existing_inode(tmp_path):
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "outside"
    external.mkdir()
    alias = tmp_path / "active-parent"
    alias.symlink_to(external, target_is_directory=True)
    output = alias / "archive.cmpct"
    output.write_bytes(b"old")
    before = output.stat()
    result = Builder(root, workers=1, reproducible=True).build(output)
    after = output.stat()
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert result["bytes"] == after.st_size > 0
    assert not (root / "archive.cmpct").exists()
    assert leaf.read_bytes() == data
    _verify_archive(output, data)
    print("O99_STABLE_SYMLINK_PARENT_INPLACE=PASS", flush=True)


@pytest.mark.skipif(os.name == "nt", reason="requires POSIX atomic ancestor-symlink replacement")
@pytest.mark.parametrize("redirect", ["source", "other-external"])
def test_o99_postscan_parent_pivot_refused_before_output_mutation(tmp_path, redirect):
    """Same deterministic genuine-Builder scan barrier as independent O96, opposite verdict."""
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "outside"
    external.mkdir()
    other = (root if redirect == "source" else tmp_path / "alternate")
    if redirect == "other-external":
        other.mkdir()
    alias = tmp_path / "active-parent"
    alias.symlink_to(external, target_is_directory=True)
    output = alias / "archive.cmpct"
    assert not output.exists()
    pending = tmp_path / "pending-parent"
    pending.symlink_to(other, target_is_directory=True)

    scan_done = threading.Event()
    actor_done = threading.Event()
    errors = []
    builder = Builder(root, workers=1, reproducible=True)
    original_scan = builder.scan

    def actor():
        try:
            assert scan_done.wait(8), "genuine Builder scan did not finish"
            os.replace(pending, alias)
            assert os.path.realpath(alias) == os.path.realpath(other)
        except BaseException as exc:
            errors.append(exc)
        finally:
            actor_done.set()

    def gated_scan():
        original_scan()
        scan_done.set()
        assert actor_done.wait(8), "parent actor timed out"
        assert not errors, repr(errors)

    builder.scan = gated_scan
    thread = threading.Thread(target=actor, daemon=True)
    thread.start()
    try:
        with pytest.raises(ValueError, match="output parent identity changed"):
            builder.build(output)
    finally:
        thread.join(timeout=8)
    assert not thread.is_alive() and not errors, repr(errors)
    assert not (root / "archive.cmpct").exists()
    assert not (external / "archive.cmpct").exists()
    assert not (other / "archive.cmpct").exists()
    assert leaf.read_bytes() == data
    print("O99_POSTSCAN_PARENT_"+redirect.replace("-","_").upper()+"_REFUSED=PASS",flush=True)


@pytest.mark.skipif(sys.platform != "linux", reason="O_PATH execute-only parent policy specific to Linux")
def test_o99_execute_only_destination_directory_remains_admitted(tmp_path):
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "exec-only"
    external.mkdir()
    external.chmod(0o311)
    try:
        out = external / "archive.cmpct"
        result = Builder(root, workers=1, reproducible=True).build(out)
        assert result["bytes"] > 0
    finally:
        external.chmod(0o700)
    _verify_archive(external / "archive.cmpct", data)
    assert leaf.read_bytes() == data
    print("O99_LINUX_EXECUTE_ONLY_PARENT=PASS", flush=True)
