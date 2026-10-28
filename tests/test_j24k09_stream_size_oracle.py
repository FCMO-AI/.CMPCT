"""J24K09: small independent stream-coordinate oracle; no archive fixtures."""
from __future__ import annotations

import zipfile
import pytest

from cmpct.codec import range_vzip


def _recipe(method=zipfile.ZIP_STORED, mode=0):
    # Logical layout is ABC + pq + WXYZ. The skeleton owns ABCWXYZ.
    return [0, [3, 4], [[1, method, mode, 2, 2, -1]],
            b"", 9, 0]


@pytest.mark.parametrize("method,mode", [
    (zipfile.ZIP_STORED, 0),
    (zipfile.ZIP_DEFLATED, 0),
    (zipfile.ZIP_DEFLATED, 1),
])
def test_skipped_physical_stream_uses_size_only(method, mode):
    calls = []
    def content(idx):
        calls.append(("content", idx))
        if idx == 0:
            return b"ABCWXYZ"
        raise AssertionError("skipped content must not be decoded")
    def stream(*args):
        raise AssertionError("skipped compressed stream must not be decoded")
    def physical_size(m, sm, rawref, streamref):
        calls.append(("size", m, sm, rawref, streamref))
        assert (m, sm, rawref, streamref) == (method, mode, 1, 2)
        return 2
    assert range_vzip(_recipe(method, mode), content, stream, 6, 2, physical_size) == b"XY"
    assert calls == [("content", 0), ("size", method, mode, 1, 2)]


@pytest.mark.parametrize("wrong_size", [0, 1, 3, 1024])
def test_skipped_physical_stream_size_mismatch_fails_closed(wrong_size):
    def content(idx):
        if idx == 0:
            return b"ABCWXYZ"
        raise AssertionError("should not need skipped content")
    with pytest.raises(IOError, match="selective reconstruction length mismatch"):
        range_vzip(_recipe(), content, lambda *args: b"pq", 6, 1,
                   lambda *args: wrong_size)


def test_no_work_after_early_or_empty_ranges():
    def content(idx):
        assert idx == 0
        return b"ABCWXYZ"
    def fail(*args):
        raise AssertionError("a prior stream witness must not run")
    assert range_vzip(_recipe(), content, fail, 0, 1, fail) == b"A"
    assert range_vzip(_recipe(), fail, fail, 2, 0, fail) == b""


def test_no_callback_uses_expensive_but_safe_standalone_control():
    calls = []
    def content(idx):
        calls.append(idx)
        return b"ABCWXYZ" if idx == 0 else b"pq"
    assert range_vzip(_recipe(), content, lambda *args: b"pq", 6, 2) == b"XY"
    assert calls == [0, 1]


# A separately constructed physical BHDR is a different-rooted oracle from
# the signed archive vectors: neither the original Builder nor Reader _blob
# is involved.  It catches a tempting but invalid index-only size shortcut.
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE
from cmpct.reader import CMPCT


def _reader_with_physical_record(codec, decoded, stored, flags=0, reserved=0, claimed=None):
    obj = CMPCT.__new__(CMPCT)
    obj.record_base = 0
    obj.blobs = [claimed if claimed is not None else (0, decoded, stored, codec, 0)]
    obj.mm = (BHDR.pack(BMAGIC, codec, flags, reserved, decoded, stored, 0,
                       0, b"\\0" * 32) + b"x" * stored)
    return obj


@pytest.mark.parametrize("method,mode,codec,decoded,stored,expected", [
    (zipfile.ZIP_STORED, 0, CODEC_RAW, 5, 5, 5),
    (zipfile.ZIP_DEFLATED, 1, CODEC_ZSTD, 5, 3, 5),
    (zipfile.ZIP_DEFLATED, 0, CODEC_DEFLATE, 25, 5, 5),
])
def test_bhdr_oracle_selects_correct_physical_length(
    method, mode, codec, decoded, stored, expected
):
    reader = _reader_with_physical_record(codec, decoded, stored)
    assert reader._vzip_physical_stream_size(method, mode, 0, 0) == expected


@pytest.mark.parametrize("claim", [
    (-1, 5, 5, CODEC_RAW, 0),
    (0, 6, 5, CODEC_RAW, 0),
    (0, 5, 6, CODEC_RAW, 0),
    (0, 5, 5, CODEC_ZSTD, 0),
    (0, 5, 5, CODEC_RAW, 1),
])
def test_blob_descriptor_not_accepted_without_matching_bhdr(claim):
    reader = _reader_with_physical_record(CODEC_RAW, 5, 5, claimed=claim)
    with pytest.raises(IOError):
        reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, 0, 0)


@pytest.mark.parametrize("idx", [-1, 1, True, "0"])
def test_physical_owner_reference_must_be_exact_bounded_integer(idx):
    reader = _reader_with_physical_record(CODEC_RAW, 5, 5)
    with pytest.raises(IOError):
        reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, idx, 0)


@pytest.mark.parametrize("flags,reserved", [(1, 0), (0, 1)])
def test_nondefault_physical_record_flags_rejected(flags, reserved):
    reader = _reader_with_physical_record(CODEC_RAW, 5, 5, flags, reserved)
    with pytest.raises(IOError):
        reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, 0, 0)


def test_incomplete_physical_record_rejected():
    reader = _reader_with_physical_record(CODEC_RAW, 5, 5)
    reader.mm = reader.mm[:-1]
    with pytest.raises(IOError):
        reader._vzip_physical_stream_size(zipfile.ZIP_STORED, 0, 0, 0)


def test_canonical_mode_requires_deflate_owner_not_just_equal_size():
    reader = _reader_with_physical_record(CODEC_RAW, 5, 5)
    with pytest.raises(IOError, match="Deflate"):
        reader._vzip_physical_stream_size(zipfile.ZIP_DEFLATED, 0, 0, 0)
