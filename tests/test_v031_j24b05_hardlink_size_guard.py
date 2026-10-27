"""J24B05: signed r24 alias-size geometry, independent of Builder alias output.

Original immutable physical member payloads are preserved. All modified logical
indexes, both copies, footer, and SHA-256 commitments are recomputed honestly.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import (
    FMAGIC, FTR, HDR, K_FILE, K_HARDLINK, MAGIC, sha, zc, zd,
)
from cmpct.validation import ValidationError, preflight_archive


def _source(tmp_path: Path, kind: str) -> tuple[Path, bytes]:
    root = tmp_path / "source"
    root.mkdir()
    if kind == "compressible":
        payload = b"Q" * 128
    else:
        # Fixed, high-entropy synthetic bytes: no fixture identity in product code.
        payload = b"".join(hashlib.sha256(str(i).encode()).digest() for i in range(4))
        assert len(payload) == 128
    (root / "owner.bin").write_bytes(payload)
    archive = tmp_path / "source.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    return archive, payload


def _resign(source: Path, target: Path, rows_factory) -> None:
    wire = source.read_bytes()
    magic, version, flags, csize, usize, data_size, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and version == 24
    plain = zd(wire[HDR.size:HDR.size + csize], usize)
    assert sha(plain) == digest
    index = msgpack.unpackb(plain, raw=False)
    assert len(index["files"]) == 1
    owner = index["files"][0]
    assert owner[0] == "owner.bin" and owner[1] == K_FILE and owner[4] == 128
    new_files = rows_factory(list(owner))
    index["files"] = new_files
    new_plain = msgpack.packb(index, use_bin_type=True)
    new_compressed = zc(new_plain, 12)
    new_digest = sha(new_plain)
    physical = wire[HDR.size + csize:HDR.size + csize + data_size]
    assert len(physical) == data_size
    target.write_bytes(
        HDR.pack(MAGIC, version, flags, len(new_compressed), len(new_plain), data_size, new_digest)
        + new_compressed + physical + new_compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_compressed), len(new_plain), 0, new_digest)
    )
    rewritten = target.read_bytes()
    assert rewritten[HDR.size + len(new_compressed):HDR.size + len(new_compressed) + data_size] == physical
    assert rewritten[HDR.size:HDR.size + len(new_compressed)] == rewritten[-FTR.size-len(new_compressed):-FTR.size]
    assert hashlib.sha256(physical).digest() == hashlib.sha256(
        wire[HDR.size + csize:HDR.size + csize + data_size]
    ).digest()


def _alias(owner, name: str, target: str, size: int) -> list:
    return [name, K_HARDLINK, owner[2], owner[3], size, None, [target]]


@pytest.mark.parametrize("kind", ["compressible", "incompressible"])
@pytest.mark.parametrize("declared", [128, 136, 120, 0])
@pytest.mark.parametrize("reverse", [False, True])
def test_signed_alias_size_matches_terminal_owner(tmp_path: Path, kind: str, declared: int, reverse: bool) -> None:
    source, _ = _source(tmp_path, kind)
    archive = tmp_path / "alias.cmpct"

    def rows(owner):
        values = [owner, _alias(owner, "alias.bin", "owner.bin", declared)]
        return values[::-1] if reverse else values

    _resign(source, archive, rows)
    if declared == 128:
        assert preflight_archive(archive)["files"] == 2
    else:
        with pytest.raises(ValidationError, match="hardlink.*size disagrees"):
            preflight_archive(archive)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("bad_position", ["middle", "outer"])
def test_signed_chain_checks_every_alias_not_just_outer(tmp_path: Path, reverse: bool, bad_position: str) -> None:
    source, _ = _source(tmp_path, "compressible")
    archive = tmp_path / "chain.cmpct"

    def rows(owner):
        middle = _alias(owner, "middle.bin", "owner.bin", 120 if bad_position == "middle" else 128)
        outer = _alias(owner, "outer.bin", "middle.bin", 136 if bad_position == "outer" else 128)
        values = [owner, middle, outer]
        return values[::-1] if reverse else values

    _resign(source, archive, rows)
    with pytest.raises(ValidationError, match="hardlink.*size disagrees"):
        preflight_archive(archive)


@pytest.mark.parametrize("reverse", [False, True])
def test_valid_memoized_chain_retains_strict_acceptance(tmp_path: Path, reverse: bool) -> None:
    source, _ = _source(tmp_path, "incompressible")
    archive = tmp_path / "valid-chain.cmpct"
    count = 2048

    def rows(owner):
        records = [owner]
        previous = "owner.bin"
        for i in range(count):
            name = f"alias-{i:05d}.bin"
            records.append(_alias(owner, name, previous, 128))
            previous = name
        return records[::-1] if reverse else records

    _resign(source, archive, rows)
    assert preflight_archive(archive)["files"] == count + 1
