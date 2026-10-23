"""Real-r24 direct-Deflate export: fail closed before ZIP publication with bounded buffers.

The existing PR #280 independent court proves that the original fast writer silently
exported a corrupted Deflate member. This suite turns that negative into a product
regression test without changing the frozen scientific instrument or evaluator.
"""
from __future__ import annotations

import binascii
import hashlib
import struct
import tracemalloc
import zipfile
import zlib

import msgpack
import pytest

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_DEFLATE, FMAGIC, FTR, HDR, K_FILE,
    LFH, MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT


def _archive(path, raw, *, names=("member.txt",), altered_crc=False,
             altered_sha=False, extra_stream_bytes=b""):
    """Construct an independent authentic revision-24 direct-Deflate archive."""
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    comp = co.compress(raw) + co.flush() + extra_stream_bytes
    crc = binascii.crc32(raw) & 0xffffffff
    expected_sha = sha(raw)
    record = BHDR.pack(
        BMAGIC, CODEC_DEFLATE, 0, 0, len(raw), len(comp), 0,
        crc ^ int(altered_crc),
        bytes([expected_sha[0] ^ 1]) + expected_sha[1:] if altered_sha else expected_sha,
    ) + comp
    files = [[name, K_FILE, 0o644, 0, len(raw), None, [S_BLOB, 0]]
             for name in sorted(names)]
    index = {
        "v": VERSION, "files": files,
        "blobs": [[0, len(raw), len(comp), CODEC_DEFLATE, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    clear = msgpack.packb(index, use_bin_type=True)
    packed = zc(clear, 12)
    path.write_bytes(
        HDR.pack(MAGIC, VERSION, 0, len(packed), len(clear), len(record), sha(clear)) +
        packed + record + packed +
        FTR.pack(FMAGIC, 0, 1, 0, 0, len(packed), len(clear), 0, sha(clear))
    )
    return comp


def _exported_stream(zip_path, name):
    data = zip_path.read_bytes()
    with zipfile.ZipFile(zip_path) as reader:
        info = reader.getinfo(name)
        assert info.compress_type == zipfile.ZIP_DEFLATED
        assert reader.testzip() is None
        header = LFH.unpack_from(data, info.header_offset)
        return data[
            info.header_offset + LFH.size + header[-2] + header[-1]:
            info.header_offset + LFH.size + header[-2] + header[-1] + info.compress_size
        ]


def test_valid_exact_deflate_stream_is_retained(tmp_path):
    data = (b"Lossless means the exported bytes must decode exactly.\n" * 1200)
    source, target = tmp_path / "source.cmpct", tmp_path / "export.zip"
    comp = _archive(source, data)
    with CMPCT(source) as reader:
        assert reader.read("member.txt") == data
        reader.export_zip(target)
    assert _exported_stream(target, "member.txt") == comp
    with zipfile.ZipFile(target) as z:
        assert hashlib.sha256(z.read("member.txt")).digest() == hashlib.sha256(data).digest()


@pytest.mark.parametrize("alteration", ["crc", "sha", "payload", "trailing"])
def test_invalid_direct_deflate_fails_before_creating_zip(tmp_path, alteration):
    source, target = tmp_path / "source.cmpct", tmp_path / "export.zip"
    raw = b"Content must be verified rather than trusted.\n" * 512
    _archive(
        source, raw,
        altered_crc=alteration == "crc",
        altered_sha=alteration == "sha",
        extra_stream_bytes=b"\x00\x01" if alteration == "trailing" else b"",
    )
    if alteration == "payload":
        archive = bytearray(source.read_bytes())
        offset = archive.index(BMAGIC) + BHDR.size
        archive[offset + 2] ^= 0xFF
        source.write_bytes(archive)
    with CMPCT(source) as reader, pytest.raises((IOError, zlib.error)):
        reader.export_zip(target)
    assert not target.exists(), "invalid direct physical source must not publish a ZIP"


def test_corruption_cannot_overwrite_an_existing_zip(tmp_path):
    source, target = tmp_path / "source.cmpct", tmp_path / "export.zip"
    _archive(source, b"A" * 8192, altered_crc=True)
    target.write_bytes(b"precious existing artifact")
    with CMPCT(source) as reader, pytest.raises(IOError):
        reader.export_zip(target)
    assert target.read_bytes() == b"precious existing artifact"


def test_shared_deflate_blob_verified_only_once(tmp_path, monkeypatch):
    source, target = tmp_path / "source.cmpct", tmp_path / "export.zip"
    data = (b"shared direct source\n" * 2000)
    stream = _archive(source, data, names=("a.txt", "b.txt", "c.txt"))
    with CMPCT(source) as reader:
        calls = []
        original = reader._verify_direct_deflate_blob

        def counted(index):
            calls.append(index)
            return original(index)

        monkeypatch.setattr(reader, "_verify_direct_deflate_blob", counted)
        reader.export_zip(target)
    assert calls == [0]
    with zipfile.ZipFile(target) as zip_reader:
        assert zip_reader.namelist() == ["a.txt", "b.txt", "c.txt"]
        for name in zip_reader.namelist():
            assert zip_reader.read(name) == data
            assert _exported_stream(target, name) == stream


def test_validator_does_not_allocate_entire_inflated_member(tmp_path):
    source, target = tmp_path / "source.cmpct", tmp_path / "export.zip"
    # Materialize outside the traced region; the validator must itself remain bounded.
    raw = b"\x00" * (32 * 1024 * 1024)
    _archive(source, raw)
    del raw
    with CMPCT(source) as reader:
        tracemalloc.start()
        try:
            reader.export_zip(target)
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
    assert peak < 8 * 1024 * 1024, f"bounded validation allocated {peak} B"
    with zipfile.ZipFile(target) as zip_reader:
        assert len(zip_reader.read("member.txt")) == 32 * 1024 * 1024
