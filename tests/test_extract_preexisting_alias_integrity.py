"""Regression: extracting over preexisting destination links must never mutate external files.

These tests deliberately fail against the unmodified v0.31 Reader. They use isolated
temporary directories, retain full archive integrity assertions, and allow fail-closed
output rejection. Static-link correctness is not a promise against same-UID concurrent
namespace relocation.
"""
import hashlib
import os

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


@pytest.mark.parametrize(
    "link_type,member",
    [
        ("symlink_parent", "nested/data.bin"),
        ("symlink_leaf", "top.bin"),
        ("hardlink_leaf", "top.bin"),
        ("symlink_leaf", "sparse.bin"),
        ("hardlink_leaf", "sparse.bin"),
    ],
)
def test_extractall_preserves_external_inode_through_preexisting_alias(
    tmp_path, link_type, member
):
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "nested/data.bin").write_bytes(b"INSIDE NESTED")
    (source / "top.bin").write_bytes(b"INSIDE ROOT")
    with (source / "sparse.bin").open("wb") as stream:
        stream.seek(4 * 1024 * 1024)
        stream.write(b"END")

    archive = tmp_path / "input.cmpct"
    Builder(source, workers=1).build(archive)
    output = tmp_path / "output"
    output.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / (
        "data.bin" if link_type == "symlink_parent" else "victim.bin"
    )
    sentinel = b"OUTSIDE-SENTINEL-IMMUTABLE"
    victim.write_bytes(sentinel)

    if link_type == "symlink_parent":
        (output / "nested").symlink_to(outside, target_is_directory=True)
    else:
        leaf = output / member
        if link_type == "symlink_leaf":
            leaf.symlink_to(victim)
        else:
            os.link(victim, leaf)

    with CMPCT(archive) as reader:
        assert reader.verify() == 3
        try:
            reader.extractall(output, safe_symlinks=True)
        except (OSError, IOError):
            pass
        assert reader.verify() == 3

    assert hashlib.sha256(victim.read_bytes()).digest() == hashlib.sha256(
        sentinel
    ).digest(), f"extraction touched an external inode through {link_type} for {member}"
