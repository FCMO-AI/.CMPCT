"""O57: fail-closed NTFS named streams, unchanged supported r24 source semantics."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT


_PAYLOAD = bytes((i * 23 + (i >> 6) * 17 + 5) & 255 for i in range(8192))
_ADS = b"o57-named-fork-proves-losslessness-boundary\x00" * 11


def _source_with_named_stream(tmp_path: Path, hardlink: bool) -> tuple[Path, Path]:
    root = tmp_path / "input"
    root.mkdir()
    owner = root / "owner.bin"
    owner.write_bytes(_PAYLOAD)
    if hardlink:
        alias = root / "alias.bin"
        os.link(owner, alias)
        assert os.path.samefile(owner, alias)
    named = str(owner) + ":cmpct_o57"
    with open(named, "wb") as writer:
        writer.write(_ADS)
    with open(named, "rb") as reader:
        assert reader.read() == _ADS
    assert owner.stat().st_size == len(_PAYLOAD)
    if hardlink:
        with open(str(root / "alias.bin") + ":cmpct_o57", "rb") as reader:
            assert reader.read() == _ADS
    return root, owner


@pytest.mark.skipif(os.name != "nt", reason="Win32 NTFS source stream scenario")
def test_ntfs_regular_named_stream_rejected_before_output(tmp_path: Path) -> None:
    root, owner = _source_with_named_stream(tmp_path, hardlink=False)
    fresh = tmp_path / "new.cmpct"
    with pytest.raises(OSError, match="unsupported NTFS named stream"):
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(fresh)
    assert not fresh.exists()
    assert owner.read_bytes() == _PAYLOAD
    with open(str(owner) + ":cmpct_o57", "rb") as reader:
        assert reader.read() == _ADS


@pytest.mark.skipif(os.name != "nt", reason="Win32 NTFS hardlinked source stream scenario")
def test_ntfs_hardlinked_named_stream_rejects_without_clobber(tmp_path: Path) -> None:
    root, owner = _source_with_named_stream(tmp_path, hardlink=True)
    old = tmp_path / "preserved.cmpct"
    old.write_bytes(b"PREEXISTING-BYTES-MUST-REMAIN")
    with pytest.raises(OSError, match="unsupported NTFS named stream"):
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(old)
    assert old.read_bytes() == b"PREEXISTING-BYTES-MUST-REMAIN"
    assert os.path.samefile(owner, root / "alias.bin")
    with open(str(root / "alias.bin") + ":cmpct_o57", "rb") as reader:
        assert reader.read() == _ADS


def test_supported_stable_tree_remains_exact_and_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "ordinary"
    root.mkdir()
    owner = root / "owner.bin"
    owner.write_bytes(_PAYLOAD)
    alias = root / "alias.bin"
    os.link(owner, alias)
    independent = root / "independent.bin"
    independent.write_bytes(_PAYLOAD)
    assert os.path.samefile(owner, alias)
    assert not os.path.samefile(owner, independent)
    if os.name == "nt":
        from cmpct.ntfs_streams import refuse_unsupported_named_streams
        for x in (owner, alias, independent):
            refuse_unsupported_named_streams(x)
    digests = []
    for n in range(2):
        archive = tmp_path / f"good-{n}.cmpct"
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
        digests.append(hashlib.sha256(archive.read_bytes()).hexdigest())
        restored = tmp_path / f"restored-{n}"
        with CMPCT(archive) as reader:
            assert reader.verify() >= 1
            rows = reader.index["files"]
            assert sum(row[1] == K_HARDLINK for row in rows) == 1
            for name in ("owner.bin", "alias.bin", "independent.bin"):
                assert reader.read(name) == _PAYLOAD
            reader.extractall(restored, metadata=False)
        assert os.path.samefile(restored / "owner.bin", restored / "alias.bin")
        assert not os.path.samefile(restored / "owner.bin", restored / "independent.bin")
        for name in ("owner.bin", "alias.bin", "independent.bin"):
            assert (restored / name).read_bytes() == _PAYLOAD
    assert digests[0] == digests[1]
