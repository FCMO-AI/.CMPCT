from __future__ import annotations

import hashlib
import zlib

import pytest

from benchmarks import v030_c25cc01_self_describing_blobtable_oracle as O
from cmpct import codec as R24


def _record(codec: int, raw: bytes, meta: bytes = b"") -> bytes:
    # The structural oracle does not decode payloads; the record only needs to obey canonical
    # physical framing. Keep the checksum/digest correct anyway so this fixture remains useful
    # if the proof is later tightened to authenticate records during reconstruction.
    comp = raw
    return R24.BHDR.pack(
        R24.BMAGIC,
        codec,
        0,
        0,
        len(raw),
        len(comp),
        len(meta),
        zlib.crc32(raw) & 0xFFFFFFFF,
        hashlib.sha256(raw).digest(),
    ) + meta + comp


def test_blob_table_is_exactly_derivable_from_physical_records():
    first = _record(R24.CODEC_RAW, b"abc")
    second = _record(R24.CODEC_RAW, b"payload", b"m")
    data = first + second
    assert O._scan_blob_table(data) == [
        [0, 3, 3, R24.CODEC_RAW, 0],
        [len(first), 7, 7, R24.CODEC_RAW, 1],
    ]


def test_blob_table_scan_fails_closed_on_truncation():
    record = _record(R24.CODEC_RAW, b"abcdef")
    with pytest.raises(RuntimeError, match="exceeds authenticated data span"):
        O._scan_blob_table(record[:-1])


def test_blob_table_scan_fails_closed_on_bad_record_magic():
    record = bytearray(_record(R24.CODEC_RAW, b"abcdef"))
    record[:4] = b"NOPE"
    with pytest.raises(RuntimeError, match="invalid r24 blob magic"):
        O._scan_blob_table(bytes(record))
