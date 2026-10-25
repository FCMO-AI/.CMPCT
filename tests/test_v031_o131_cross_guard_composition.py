"""O131: exact installed Reader source-inode admission under host name resolution.

The physical alias is discovered from the real destination filesystem rather than
assuming Linux, Windows or macOS case behavior. The same source/archive fixture is
also tested with an ordinary independent destination. Nothing in this test changes
the frozen source-exact owner assertions of #336 or #472.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


_PAYLOAD = hashlib.shake_256(b"O131-physical-namespace-union").digest(32768)
_OTHER = b"O131-keep-all-sources-and-no-partial-output\n"


def _fixture(tmp_path: Path) -> tuple[Path, bytes, bytes]:
    source = tmp_path / "input"
    source.mkdir()
    (source / "payload.bin").write_bytes(_PAYLOAD)
    (source / "other.txt").write_bytes(_OTHER)
    archive = tmp_path / "PAYLOAD.BIN"
    Builder(source, workers=1, reproducible=True).build(archive)
    archived = archive.read_bytes()
    with CMPCT(archive) as reader:
        assert reader.read("payload.bin") == _PAYLOAD
        assert reader.read("other.txt") == _OTHER
        assert reader.verify()
    return archive, archived, _PAYLOAD


def test_independent_destination_preserves_exact_tree(tmp_path: Path) -> None:
    archive, immutable_bytes, payload = _fixture(tmp_path)
    dest = tmp_path / "independent"
    with CMPCT(archive) as reader:
        reader.extractall(dest, metadata=False)
    assert (dest / "payload.bin").read_bytes() == payload
    assert (dest / "other.txt").read_bytes() == _OTHER
    assert archive.read_bytes() == immutable_bytes


def test_host_resolved_source_alias_is_refused_before_any_member(tmp_path: Path) -> None:
    archive, immutable_bytes, payload = _fixture(tmp_path)
    # Archive path differs lexically from its member. Its *physical* resolution
    # is host/filesystem-specific and must be measured, not guessed from os.name.
    leaf = tmp_path / "payload.bin"
    aliases_source = leaf.exists() and os.path.samefile(archive, leaf)
    before_files = {p.name for p in tmp_path.iterdir() if p.is_file()}
    with CMPCT(archive) as reader:
        if aliases_source:
            with pytest.raises(IOError, match="extraction destination aliases open source archive"):
                reader.extractall(tmp_path, metadata=False)
        else:
            reader.extractall(tmp_path, metadata=False)
    assert archive.read_bytes() == immutable_bytes
    if aliases_source:
        assert {p.name for p in tmp_path.iterdir() if p.is_file()} == before_files
        assert not (tmp_path / "other.txt").exists()
    else:
        assert leaf.read_bytes() == payload
        assert (tmp_path / "other.txt").read_bytes() == _OTHER
