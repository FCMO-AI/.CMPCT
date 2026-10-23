"""Authentic revision-24 sparse NAME_MAX composition and failure-atomicity court.

This test composes independent Reader #268 with sparse proof #255 and short-name
staging #256; it must run on the *same installed package*, never a mock archive.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_SPARSE
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name != "posix", reason="POSIX sparse/NAME_MAX semantics")
def test_sparse_full_length_filename_verified_and_failure_atomic(tmp_path):
    name = "n" * 251 + ".bin"  # 255 encoded bytes under POSIX NAME_MAX.
    assert len(os.fsencode(name)) == 255
    assert os.pathconf(tmp_path, "PC_NAME_MAX") >= 255
    source = tmp_path / "source"
    source.mkdir()
    logical_size = 8 * 1024 * 1024
    chunk_a = b"A" * 8192
    chunk_b = b"B" * 8192
    original = source / name
    with original.open("wb") as stream:
        stream.seek(4096)
        stream.write(chunk_a)
        stream.seek(logical_size - len(chunk_b))
        stream.write(chunk_b)
    assert original.stat().st_size == logical_size
    archive = tmp_path / "content.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        row = reader.by[name]
        assert row[6][0] == S_SPARSE, "must exercise genuine sparse archive representation"
        assert reader.verify() >= 1
        destination = tmp_path / "dest"
        reader.extractall(destination, metadata=False)
        restored = destination / name
        assert restored.stat().st_size == logical_size
        with restored.open("rb") as stream:
            assert stream.read(4096) == b"\x00" * 4096
            assert stream.read(len(chunk_a)) == chunk_a
            stream.seek(logical_size // 2)
            assert stream.read(8192) == b"\x00" * 8192
            stream.seek(logical_size - len(chunk_b))
            assert stream.read(len(chunk_b)) == chunk_b
        with restored.open("rb") as stream:
            restored_hash = hashlib.file_digest(stream, "sha256").digest()
        assert restored_hash == row[5]
        inode = restored.stat().st_ino
        # Mutate only in-memory logical commitment: failure cannot truncate/replace
        # prior correctly reconstructed output, even at the exact NAME_MAX boundary.
        row[5] = hashlib.sha256(b"forged logical sparse commitment").digest()
        with pytest.raises(OSError, match="sparse logical integrity failure"):
            reader.extractall(destination, metadata=False)
        assert restored.stat().st_ino == inode
        with restored.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").digest() == restored_hash
        assert not list(destination.glob(".cmpct-part-*"))
