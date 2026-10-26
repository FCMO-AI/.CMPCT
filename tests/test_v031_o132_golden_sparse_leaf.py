"""O132: builder-independent revision-24 S_SPARSE Reader guard on POSIX.

This does NOT replace or waive the unchanged parent Builder-generated sparse
fixture. It is an additional positive control that removes filesystem source
allocation from the archive storage-mode selection question.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

import pytest

from cmpct.codec import S_SPARSE
from cmpct.reader import CMPCT

pytestmark = pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "link"),
    reason="POSIX hardlink alias required",
)

VECTOR = Path.cwd() / "tests" / "conformance" / "v24-sparse.json"


def _original_archive(tmp_path: Path) -> tuple[Path, dict]:
    record = json.loads(VECTOR.read_text())
    assert record["schema"] == "cmpct-v24-sparse-golden-v1"
    assert record["format_revision"] == 24
    assert record["member"]["storage_kind"] == S_SPARSE
    archive_bytes = base64.b64decode(record["archive"]["base64"], validate=True)
    assert len(archive_bytes) == record["archive"]["bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive"]["sha256"]
    archive = tmp_path / "immutable-source.cmpct"
    archive.write_bytes(archive_bytes)
    return archive, record


def _external_hardlink(tmp_path: Path, rel: str) -> tuple[Path, Path, Path]:
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "sentinel.bin"
    victim.write_bytes(b"OUTSIDE-EXACT-SENTINEL")
    dest = tmp_path / "dest"
    dest.mkdir()
    leaf = dest / rel
    os.link(victim, leaf)
    assert victim.stat().st_ino == leaf.stat().st_ino
    return victim, dest, leaf


def test_fixed_golden_sparse_mode_rejects_preexisting_external_hardlink(tmp_path: Path):
    archive, record = _original_archive(tmp_path)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    member = record["member"]
    victim, dest, alias = _external_hardlink(tmp_path, member["path"])
    expected = victim.read_bytes()
    stat_before = victim.stat()
    with CMPCT(archive) as reader:
        assert reader.by[member["path"]][6][0] == S_SPARSE
        assert reader.verify() == 1
        assert hashlib.sha256(reader.read(member["path"])).hexdigest() == member["sha256"]
        with pytest.raises(OSError, match="pre-existing destination hardlink alias"):
            reader.extractall(dest, safe_symlinks=True, metadata=False)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha
    assert victim.read_bytes() == alias.read_bytes() == expected
    assert victim.stat().st_ino == alias.stat().st_ino == stat_before.st_ino
    print("O132_GOLDEN_SPARSE_SAFE_REJECTION_PASS", flush=True)


def test_fixed_golden_sparse_explicit_unsafe_optout_is_not_silent(tmp_path: Path):
    archive, record = _original_archive(tmp_path)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    member = record["member"]
    victim, dest, alias = _external_hardlink(tmp_path, member["path"])
    original = victim.read_bytes()
    inode = victim.stat().st_ino
    with CMPCT(archive) as reader:
        assert reader.by[member["path"]][6][0] == S_SPARSE
        assert reader.verify() == 1
        expected = reader.read(member["path"])
        assert hashlib.sha256(expected).hexdigest() == member["sha256"]
        reader.extractall(dest, safe_symlinks=False, metadata=False)
    assert victim.read_bytes() == alias.read_bytes() == expected
    assert victim.read_bytes() != original
    assert victim.stat().st_ino == alias.stat().st_ino == inode
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha
    print("O132_GOLDEN_SPARSE_EXPLICIT_OPTOUT_PASS", flush=True)
