"""O96: science-only installed O93 output *ancestor* rebind, not final-leaf pivot.

Passing hostile test proves a product limitation, not an accepted safety fix.
Only the original builder.scan entrypoint is wrapped for a deterministic barrier.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import threading

import pytest
from cmpct.core import Builder, CMPCT


pytestmark = pytest.mark.skipif(os.name == "nt", reason="atomic POSIX symlink ancestor replacement")


def _source(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    data = hashlib.shake_256(b"o96-public-source-fixture").digest(4096)
    leaf = root / "leaf.bin"
    leaf.write_bytes(data)
    assert leaf.stat().st_nlink == 1
    return root, leaf, data


def _assert_archive(path: Path, leaf_data: bytes):
    with CMPCT(path) as archive:
        archive.verify()
        assert archive.read("leaf.bin") == leaf_data


def test_o96_static_source_containment_denies_output_before_scan(tmp_path):
    root, leaf, data = _source(tmp_path)
    destination = root / "archive.cmpct"
    with pytest.raises(ValueError, match="outside the source root"):
        Builder(root, workers=1).build(destination)
    assert not destination.exists()
    assert leaf.read_bytes() == data
    print("O96_STATIC_INROOT_REFUSAL=PASS", flush=True)


def test_o96_stable_symlink_ancestor_creates_external_archive(tmp_path):
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    alias = tmp_path / "active-parent"
    alias.symlink_to(external, target_is_directory=True)
    destination = alias / "archive.cmpct"
    assert not destination.exists()
    assert os.path.realpath(destination).startswith(str(external) + os.sep)
    result = Builder(root, workers=1, reproducible=True).build(destination)
    assert result["bytes"] == destination.stat().st_size > 0
    assert result["logical_files"] == 1
    assert (external / "archive.cmpct").is_file()
    assert not (root / "archive.cmpct").exists()
    assert leaf.read_bytes() == data
    _assert_archive(destination, data)
    print("O96_STABLE_EXTERNAL_ANCESTOR=PASS", flush=True)


def test_o96_postscan_atomic_parent_symlink_swap_creates_inside_source(tmp_path):
    """The original scan is used; only the mutable parent-name boundary changes."""
    root, leaf, data = _source(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    alias = tmp_path / "active-parent"
    alias.symlink_to(external, target_is_directory=True)
    destination = alias / "archive.cmpct"
    assert not destination.exists()
    before = os.path.realpath(destination)
    assert os.path.commonpath((os.path.realpath(root), before)) != os.path.realpath(root)
    assert os.path.realpath(alias) == os.path.realpath(external)

    pending = tmp_path / "pending-parent-symlink"
    pending.symlink_to(root, target_is_directory=True)
    scan_done = threading.Event()
    actor_done = threading.Event()
    problems = []
    original_scan = None
    builder = Builder(root, workers=1, reproducible=True)
    original_scan = builder.scan

    def actor():
        try:
            assert scan_done.wait(8), "genuine scan never reached actor"
            os.replace(pending, alias)
            assert os.path.realpath(alias) == os.path.realpath(root)
        except BaseException as exc:
            problems.append(exc)
        finally:
            actor_done.set()

    def synchronized_scan():
        original_scan()
        scan_done.set()
        assert actor_done.wait(8), "actor did not complete atomically"
        assert not problems, repr(problems)

    builder.scan = synchronized_scan
    worker = threading.Thread(target=actor, daemon=True)
    worker.start()
    try:
        result = builder.build(destination)
    finally:
        worker.join(timeout=8)
    assert not worker.is_alive() and not problems, repr(problems)
    assert result["bytes"] == destination.stat().st_size > 0
    assert result["logical_files"] == 1  # original single-file tree; output now in that tree
    planted = root / "archive.cmpct"
    assert planted.is_file() and (root / "leaf.bin").is_file()
    assert os.stat(destination).st_ino == os.stat(planted).st_ino
    assert not (external / "archive.cmpct").exists()
    assert leaf.read_bytes() == data
    assert len(list(root.iterdir())) == 2
    _assert_archive(destination, data)
    print("O96_POSTSCAN_ANCESTOR_PIVOT_SOURCE_MUTATION=CONFIRMED", flush=True)
    print("O96_DESCRIPTOR_LEAF_IDENTITY_DOES_NOT_BIND_PARENT_NAMESPACE=CONFIRMED", flush=True)
