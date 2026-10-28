from __future__ import annotations

import gzip
import hashlib
import io
import os
from pathlib import Path
import zipfile

import pytest

from experiments import entropygraph_v030_federated_candidate as CAND
from experiments import entropygraph_v030_federated_public as PUBLIC


def _noise(size: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < size:
        out.extend(hashlib.sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:size])


def _gzip(raw: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as stream:
        stream.write(raw)
    return buf.getvalue()


def _zip(path: Path, shared: bytes, unique: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("shared.bin", shared)
        archive.writestr("unique.bin", unique)


def _source(root: Path) -> dict[str, bytes | None]:
    root.mkdir()
    (root / "nested").mkdir()

    shared = _noise(96 * 1024, b"shared")
    for index in range(3):
        _zip(root / f"bundle-{index}.zip", shared, _noise(12 * 1024, f"u{index}".encode()))

    loose = (b"federated inverse relation\n" * 8192) + b"end"
    (root / "telemetry.log").write_bytes(loose)
    (root / "telemetry.log.gz").write_bytes(_gzip(loose))

    child = _noise(192 * 1024, b"child")
    parent = _noise(48 * 1024, b"prefix") + child + _noise(48 * 1024, b"suffix")
    owner = root / "nested" / "child.bin"
    owner.write_bytes(child)
    (root / "parent.bin").write_bytes(parent)

    hardlink = root / "nested" / "child-hardlink.bin"
    try:
        os.link(owner, hardlink)
    except OSError:
        pytest.skip("filesystem does not support hardlinks")
    symlink = root / "child-link"
    try:
        symlink.symlink_to("nested/child.bin")
    except (OSError, NotImplementedError):
        pytest.skip("filesystem does not support symlinks")

    expected: dict[str, bytes | None] = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            expected[rel] = os.readlink(path).encode()
        elif path.is_dir():
            expected[rel] = None
        elif path.is_file():
            expected[rel] = path.read_bytes()
    return expected


def test_federated_public_reader_matches_filesystem_semantics(tmp_path: Path) -> None:
    source = tmp_path / "source"
    expected = _source(source)
    archive = tmp_path / "candidate.cmpct"
    built = CAND.build(source, archive)
    assert built["locality"]["within_release_bounds"] is True

    listed = {row["path"]: row for row in PUBLIC.list_members(archive)}
    assert set(listed) == set(expected)

    for rel, value in expected.items():
        if value is None:
            with pytest.raises(IsADirectoryError):
                PUBLIC.read_member(archive, rel)
            continue
        got, stats = PUBLIC.read_member_with_stats(archive, rel)
        assert got == value
        assert stats["amplification"] <= CAND.MAX_MEMBER_AMPLIFICATION
        assert stats["decoded_context_bytes"] <= CAND.MAX_DECODE_UNIT * max(1, stats["pack_count"])

    verified = PUBLIC.strong_verify(archive)
    assert verified["ok"] is True

    restored = tmp_path / "restored"
    PUBLIC.extract(archive, restored)
    assert CAND._treehash(restored) == CAND._treehash(source)
