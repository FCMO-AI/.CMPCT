"""O60: real deferred ZIP/WHL product-source-coherence regression and historical r24 parity.

Scientific parent: O54/O55 research PR #410. Product base: O50 PR #405.
Run pytest from an isolated directory using an actually installed CMPCT wheel.
Use --emit with the historical parent and candidate to compare real archive bytes
on identical physical inputs; never substitute a synthetic historical comparator.
"""
from __future__ import annotations

import hashlib
import io
import os
import struct
import zlib
from pathlib import Path
import sys
import zipfile

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP, S_BLOB, S_PACK


def zip_bytes(kind: str, marker: bytes = b"A") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as writer:
        for i in range(3):
            method = (zipfile.ZIP_STORED if kind == "stored" or
                      (kind == "mixed" and i == 0) else zipfile.ZIP_DEFLATED)
            info = zipfile.ZipInfo(f"payload_{i:02d}.txt", (2020, 1, 1, 0, 0, 0))
            info.compress_type = method
            writer.writestr(info, marker * 4096 + bytes([65 + i]) * 273,
                            compress_type=method, compresslevel=9)
    result = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        assert len(z.infolist()) == 3
    return result


def build(root: Path, archive: Path):
    builder = Builder(root, workers=1, reproducible=True)
    builder.build(archive)
    return builder


def read_archive(archive: Path, rel: str) -> bytes:
    with CMPCT(archive) as reader:
        got = reader.read(rel)
        assert reader.verify() >= 1
    return got


@pytest.mark.parametrize("kind", ["stored", "deflated", "mixed"])
@pytest.mark.parametrize("extension", ["zip", "whl"])
def test_stable_virtual_source_captured_once(tmp_path, monkeypatch, kind, extension):
    payload = zip_bytes(kind)
    tree = tmp_path / "root"
    tree.mkdir()
    source = tree / ("nested." + extension)
    source.write_bytes(payload)
    real_read = Path.read_bytes
    seen = []

    def spy(path):
        if path == source:
            seen.append(path)
        return real_read(path)

    archive = tmp_path / "out.cmpct"
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", spy)
        builder = build(tree, archive)
    assert len(seen) == 1, ("deferred path independently re-read", seen)
    row = next(r for r in builder.files if r[0] == source.name)
    assert row[6][0] == S_VZIP, ("no virtual representation", row)
    assert read_archive(archive, source.name) == payload


@pytest.mark.parametrize("kind", ["stored", "deflated", "mixed"])
def test_same_inode_after_capture_mutation_preserves_original_archive(tmp_path, monkeypatch, kind):
    original = zip_bytes(kind, b"A")
    substitute = zip_bytes(kind, b"B")
    if kind == "mixed":
        # DEFLATE stream length can legitimately differ for equally long A/B
        # input, so fabricate a *valid same-length ZIP B* by mutating exactly
        # one STORED byte and replacing its CRC in both directory and local
        # records. Preserve all original other compressed streams unchanged.
        modified = bytearray(original)
        with zipfile.ZipFile(io.BytesIO(original)) as reference:
            stored = next(i for i in reference.infolist()
                          if i.compress_type == zipfile.ZIP_STORED)
            assert reference.infolist()[0] is stored
            assert not (stored.flag_bits & 0x08), "unexpected data descriptor"
            directory = reference.start_dir
            header = stored.header_offset
            assert original[header:header + 4] == b"PK\x03\x04"
            assert original[directory:directory + 4] == b"PK\x01\x02"
            name_len, extra_len = struct.unpack_from("<HH", original, header + 26)
            payload_offset = header + 30 + name_len + extra_len
            assert modified[payload_offset] == ord("A")
            modified[payload_offset] = ord("B")
            new_crc = zlib.crc32(
                modified[payload_offset:payload_offset + stored.file_size])
            struct.pack_into("<I", modified, header + 14, new_crc)
            struct.pack_into("<I", modified, directory + 16, new_crc)
        substitute = bytes(modified)
    assert original != substitute and len(original) == len(substitute), (
        kind, len(original), len(substitute))
    with zipfile.ZipFile(io.BytesIO(substitute)) as valid_changed_zip:
        assert valid_changed_zip.testzip() is None
    tree = tmp_path / "stable"
    tree.mkdir()
    (tree / "nested.zip").write_bytes(original)
    expected = tmp_path / "expected.cmpct"
    baseline = build(tree, expected)
    assert next(r for r in baseline.files if r[0] == "nested.zip")[6][0] == S_VZIP

    pivot_tree = tmp_path / "pivot"
    pivot_tree.mkdir()
    source = pivot_tree / "nested.zip"
    source.write_bytes(original)
    before = os.stat(source)
    real_read = Path.read_bytes
    capture_count = 0

    def capture_then_replace(path):
        nonlocal capture_count
        snapshot = real_read(path)
        if path == source:
            capture_count += 1
            assert capture_count == 1
            assert snapshot == original
            # Mutate same regular inode, preserving path, identity and byte length.
            source.write_bytes(substitute)
        return snapshot

    archive = tmp_path / "captured.cmpct"
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", capture_then_replace)
        actual = build(pivot_tree, archive)

    after = os.stat(source)
    assert capture_count == 1
    assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    assert before.st_size == after.st_size
    assert real_read(source) == substitute
    assert next(r for r in actual.files if r[0] == "nested.zip")[6][0] == S_VZIP
    assert read_archive(archive, "nested.zip") == original
    # Same input bytes and normalized metadata must produce *identical full r24*.
    assert archive.read_bytes() == expected.read_bytes()


def test_unsupported_zip_method_uses_same_captured_fallback(tmp_path, monkeypatch):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        z.writestr("unsupported.txt", b"A" * 4096,
                   compress_type=zipfile.ZIP_BZIP2)
    tree = tmp_path / "src"
    tree.mkdir()
    source = tree / "unsupported.zip"
    source.write_bytes(payload.getvalue())
    real_read = Path.read_bytes
    read_count = 0

    def one_read(path):
        nonlocal read_count
        if path == source:
            read_count += 1
        return real_read(path)

    archive = tmp_path / "fallback.cmpct"
    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", one_read)
        builder = build(tree, archive)
    row = next(r for r in builder.files if r[0] == source.name)
    assert row[6][0] == S_BLOB
    assert read_count == 1
    assert read_archive(archive, source.name) == payload.getvalue()


def test_eight_zip_cohort_remains_exact(tmp_path):
    root = tmp_path / "many"
    root.mkdir()
    expected = {}
    for n in range(8):
        rel = f"nested_{n:02d}.zip"
        raw = zip_bytes("mixed", bytes([65 + n]))
        (root / rel).write_bytes(raw)
        expected[rel] = raw
    archive = tmp_path / "cohort.cmpct"
    builder = build(root, archive)
    assert all(r[6][0] == S_PACK for r in builder.files if r[0] in expected)
    with CMPCT(archive) as reader:
        for name, raw in expected.items():
            assert reader.read(name) == raw
        assert reader.verify() >= 1


def emit_historical_corpus(location: Path, output: Path):
    """Same physical input tree is shared between historical and candidate builds."""
    location.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    names = ["stored", "deflated", "mixed"]
    for kind in names:
        root = location / kind
        root.mkdir(exist_ok=True)
        source = root / "nested.zip"
        if not source.exists():
            source.write_bytes(zip_bytes(kind))
        archive = output / (kind + ".cmpct")
        builder = build(root, archive)
        assert next(r for r in builder.files if r[0] == "nested.zip")[6][0] == S_VZIP
        assert read_archive(archive, "nested.zip") == zip_bytes(kind)
    # Included because .whl and the >=8 deferred cohort are distinct branches.
    wheelroot = location / "wheel"
    wheelroot.mkdir(exist_ok=True)
    whl = wheelroot / "example.whl"
    if not whl.exists():
        whl.write_bytes(zip_bytes("deflated"))
    wheelarchive = output / "wheel.cmpct"
    build(wheelroot, wheelarchive)
    assert read_archive(wheelarchive, "example.whl") == zip_bytes("deflated")
    cohortroot = location / "cohort"
    cohortroot.mkdir(exist_ok=True)
    for n in range(8):
        source = cohortroot / f"nested_{n:02d}.zip"
        if not source.exists():
            source.write_bytes(zip_bytes("mixed", bytes([65 + n])))
    cohortarchive = output / "cohort.cmpct"
    build(cohortroot, cohortarchive)
    assert read_archive(cohortarchive, "nested_00.zip") == zip_bytes("mixed", b"A")
    for name in ["stored", "deflated", "mixed", "wheel", "cohort"]:
        data = (output / (name + ".cmpct")).read_bytes()
        print("O60_EMIT", name, len(data), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    assert len(sys.argv) == 4 and sys.argv[1] == "--emit", sys.argv
    emit_historical_corpus(Path(sys.argv[2]), Path(sys.argv[3]))
