"""O101: independent installed O99 falsifier, physical inode != stable namespace ancestry.

PASS on hostile case means unsafe publication reproduced, not repaired.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import threading
from pathlib import Path

import pytest
from cmpct.core import Builder, CMPCT

pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX directory rename/openat evidence only")


def _fixture(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    original = hashlib.shake_256(b"o101-public-same-inode-parent-fixture").digest(4096)
    leaf = source / "leaf.bin"
    leaf.write_bytes(original)
    outside = tmp_path / "external-parent"
    outside.mkdir()
    alias = tmp_path / "active-parent"
    alias.symlink_to(outside, target_is_directory=True)
    output = alias / "archive.cmpct"
    assert not output.exists()
    return source, leaf, original, outside, alias, output


def _verify(output: Path, original: bytes):
    with CMPCT(output) as archive:
        archive.verify()
        assert archive.read("leaf.bin") == original


def _save(name: str, facts: dict):
    path = os.environ.get("O101_RESULTS_DIR")
    if path:
        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)
        (out / (name + ".json")).write_text(json.dumps(facts, sort_keys=True, indent=2) + "\n")
    print("O101_" + name.upper() + "=PASS", flush=True)


def _after_scan(builder: Builder, operation):
    original_scan = builder.scan
    signal = threading.Event()
    completed = threading.Event()
    errors: list[BaseException] = []

    def actor():
        try:
            if not signal.wait(8):
                raise TimeoutError("genuine Builder scan never signalled")
            operation()
        except BaseException as exc:
            errors.append(exc)
        finally:
            completed.set()

    worker = threading.Thread(target=actor, daemon=True)

    def intercepted_scan():
        original_scan()
        signal.set()
        assert completed.wait(8), "filesystem actor timed out"
        assert not errors, repr(errors)

    builder.scan = intercepted_scan
    worker.start()
    return worker, errors


def test_o101_stable_external_parent_positive_control(tmp_path):
    source, leaf, original, outside, alias, output = _fixture(tmp_path)
    initial = os.stat(alias)
    result = Builder(source, workers=1, reproducible=True).build(output)
    _verify(output, original)
    assert leaf.read_bytes() == original
    assert (initial.st_dev, initial.st_ino) == (os.stat(alias).st_dev, os.stat(alias).st_ino)
    assert not (source / "archive.cmpct").exists()
    _save("stable_external", {
        "verdict": "ACCEPTED_STABLE_EXTERNAL",
        "bytes": result["bytes"],
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    })


def test_o101_changed_parent_inode_rejected_inherited_control(tmp_path):
    source, leaf, original, outside, alias, output = _fixture(tmp_path)
    alternative = tmp_path / "different-inode-parent"
    alternative.mkdir()
    original_parent = os.stat(alias)
    candidate = tmp_path / "replacement-alias"
    candidate.symlink_to(alternative, target_is_directory=True)

    def rebind():
        os.replace(candidate, alias)
        assert (os.stat(alias).st_dev, os.stat(alias).st_ino) != (
            original_parent.st_dev, original_parent.st_ino
        )

    builder = Builder(source, workers=1, reproducible=True)
    thread, errors = _after_scan(builder, rebind)
    try:
        with pytest.raises(ValueError, match="output parent identity changed"):
            builder.build(output)
    finally:
        thread.join(timeout=8)
    assert not thread.is_alive() and not errors, repr(errors)
    assert leaf.read_bytes() == original
    assert not (source / "archive.cmpct").exists()
    assert not (outside / "archive.cmpct").exists()
    assert not (alternative / "archive.cmpct").exists()
    _save("different_inode_refused", {
        "verdict": "REFUSED_CHANGED_PARENT_INODE",
        "original_parent_inode": [original_parent.st_dev, original_parent.st_ino],
        "new_parent_inode": [os.stat(alias).st_dev, os.stat(alias).st_ino],
    })


def test_o101_same_inode_parent_relocation_into_source_is_admitted(tmp_path):
    """Attack changes ancestor *topology* while keeping O99's exact dev/ino witness."""
    source, leaf, original, outside, alias, output = _fixture(tmp_path)
    initial = os.stat(alias)
    initial_realpath = os.path.realpath(alias)
    moved = source / "relocated-parent"
    new_alias = tmp_path / "new-alias"
    new_alias.symlink_to(moved, target_is_directory=True)
    barrier_facts = {}

    def reparent():
        # Rename the original directory inode. Do not create a new parent inode.
        os.rename(outside, moved)
        os.replace(new_alias, alias)
        rebound = os.stat(alias)
        assert (rebound.st_dev, rebound.st_ino) == (initial.st_dev, initial.st_ino)
        assert os.path.commonpath([str(source.resolve()), os.path.realpath(alias)]) == str(source.resolve())
        assert not (moved / "archive.cmpct").exists()
        barrier_facts.update({
            "initial_realpath": initial_realpath,
            "postscan_realpath": os.path.realpath(alias),
            "dev_ino_before": [initial.st_dev, initial.st_ino],
            "dev_ino_after": [rebound.st_dev, rebound.st_ino],
            "same_parent_inode": True,
            "postscan_parent_inside_source": True,
        })

    builder = Builder(source, workers=1, reproducible=True)
    thread, errors = _after_scan(builder, reparent)
    try:
        result = builder.build(output)
    finally:
        thread.join(timeout=8)
    assert not thread.is_alive() and not errors, repr(errors)
    assert barrier_facts["same_parent_inode"]
    assert output.samefile(moved / "archive.cmpct")
    assert leaf.read_bytes() == original
    _verify(output, original)
    assert result["logical_files"] == 1, result
    assert {entry.name for entry in source.iterdir()} == {"leaf.bin", "relocated-parent"}
    barrier_facts.update({
        "verdict": "ACCEPTED_IN_SOURCE_DESPITE_ORIGINAL_EXTERNAL_ADMISSION",
        "source_original_sha256": hashlib.sha256(original).hexdigest(),
        "source_after_sha256": hashlib.sha256(leaf.read_bytes()).hexdigest(),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "archive_bytes": result["bytes"],
        "source_tree_after": sorted(entry.name for entry in source.iterdir()),
        "logical_files_in_archive": result["logical_files"],
        "reader_verify": "PASS",
    })
    _save("same_inode_reparent_into_source", barrier_facts)
