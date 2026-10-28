"""Regression: physical RAW control bits are not authenticated-index capabilities.

The strict preflight rejects nonzero BHDR flags/reserved even if all content,
index, length, CRC and SHA bytes remain valid. Reader read/read_range/verify
and mmap-backed extraction must not bypass that same unsupported-bit rule.
"""
from __future__ import annotations

import binascii
import hashlib
from pathlib import Path

import msgpack
import pytest

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FTR, FMAGIC, HDR, MAGIC,
    K_FILE, K_SYMLINK, S_BLOB, VERSION, zc,
)
from cmpct.core import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]


def _wire(kind: int):
    # Builder-independent authenticated index; physical HEADER bit mutations
    # do not alter a single index, payload, CRC or SHA byte.
    member = "direct.bin" if kind == K_FILE else "link"
    index = {
        "v": VERSION,
        "files": [[member, kind, 0o644, 0, len(PAYLOAD), None, [S_BLOB, 0]]],
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
        "features": [],
    }
    plain = msgpack.packb(index, use_bin_type=True)
    compressed = zc(plain, 3)
    h = hashlib.sha256(plain).digest()
    body = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD),
                     0, binascii.crc32(PAYLOAD) & 0xFFFFFFFF,
                     hashlib.sha256(PAYLOAD).digest()) + PAYLOAD
    first = HDR.pack(MAGIC, VERSION, 0, len(compressed), len(plain),
                     len(body), h)
    tail = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(plain), 0, h)
    return member, first + compressed + body + compressed + tail, body


@pytest.mark.parametrize("kind", [K_FILE, K_SYMLINK], ids=["regular", "symlink"])
@pytest.mark.parametrize(
    ("field", "value"),
    [(2, 1), (2, 128), (3, 1), (3, 65535)],
    ids=["flag-low", "flag-high", "reserved-low", "reserved-high"],
)
def test_raw_reader_rejects_unsupported_physical_bits(
    tmp_path: Path, kind: int, field: int, value: int
):
    member, valid, frame = _wire(kind)
    good = tmp_path / "good.cmpct"
    good.write_bytes(valid)
    assert preflight_archive(good)["files"] == 1
    with CMPCT(good) as reader:
        assert reader.read_range(member, 7, 8) == PAYLOAD[7:15]
        assert reader.read(member) == PAYLOAD
        assert reader.verify() == 1
        assert bytes(reader._raw_blob_view_for_extract(0)) == PAYLOAD

    pos = valid.find(frame)
    assert pos >= 0 and valid.count(frame) == 1
    original = list(BHDR.unpack_from(frame))
    assert original[2] == original[3] == 0
    mutated = original.copy()
    mutated[field] = value
    replacement = BHDR.pack(*mutated)
    archive = valid[:pos] + replacement + valid[pos + BHDR.size:]
    assert len(archive) == len(valid)
    assert archive[:pos] == valid[:pos]
    assert archive[pos + BHDR.size:] == valid[pos + BHDR.size:]
    assert [i for i in range(len(original)) if original[i] != mutated[i]] == [field]
    hostile = tmp_path / "unsupported-control.cmpct"
    hostile.write_bytes(archive)

    with pytest.raises(ValidationError, match="unsupported flags"):
        preflight_archive(hostile)
    with CMPCT(hostile) as reader:
        with pytest.raises(IOError, match="header mismatch"):
            reader.read_range(member, 7, 8)
        with pytest.raises(IOError, match="header mismatch"):
            reader.read(member)
        with pytest.raises(IOError, match="header mismatch"):
            reader.verify()
        with pytest.raises(IOError, match="header mismatch"):
            reader._raw_blob_view_for_extract(0)
