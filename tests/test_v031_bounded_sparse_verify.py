"""Builder-independent r24 verification regressions for physical plus sparse logical identity.

The default-sized fixture stays cheap in ordinary CI. The separate 4-GiB court records
resource-bounded full hashing under an address-space cap; this test catches the
allocation mechanism even when CI cannot afford a 4-GiB SHA traversal.
"""
from __future__ import annotations

import binascii
import hashlib
from pathlib import Path

import msgpack
import pytest

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, HDR, K_FILE, K_HARDLINK, MAGIC, S_SPARSE, zc,
)
from cmpct.reader import CMPCT


def _archive(path: Path, *, logical_bytes: int = 16 << 20,
             hardlink: bool = False, bad_physical: bool = False,
             wrong_owner_length: bool = False, missing_logical_sha: bool = False) -> Path:
    """Independent wire framing; no Builder/encoder imports or golden regeneration."""
    chunk = b"span:" + bytes(range(64))
    h = hashlib.sha256()
    h.update(chunk)
    zero = bytes(1 << 20)
    gap = logical_bytes - len(chunk)
    while gap:
        count = min(len(zero), gap)
        h.update(memoryview(zero)[:count])
        gap -= count
    physical_sha = hashlib.sha256(chunk).digest()
    if bad_physical:
        physical_sha = bytes([physical_sha[0] ^ 1]) + physical_sha[1:]
    record = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(chunk), len(chunk), 0,
        binascii.crc32(chunk) & 0xffffffff, physical_sha,
    ) + chunk
    files = [["large.sparse", K_FILE, 0o644, 0, logical_bytes,
              None if missing_logical_sha else h.digest(),
              [S_SPARSE, [[0, len(chunk), [0]]]]]]
    if hardlink:
        files.append(["large.link", K_HARDLINK, 0o644, 0,
                      logical_bytes + int(wrong_owner_length), None, ["large.sparse"]])
    files.sort(key=lambda row: row[0])
    index = {
        "v": 24,
        "blobs": [[0, len(chunk), len(chunk), CODEC_RAW, 0]],
        "files": files,
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {},
        "features": [],
    }
    unpacked = msgpack.packb(index, use_bin_type=True)
    compressed = zc(unpacked, 3)
    path.write_bytes(
        HDR.pack(MAGIC, 24, 0, len(compressed), len(unpacked), len(record),
                 hashlib.sha256(unpacked).digest()) + compressed + record
    )
    return path


def test_sparse_verification_never_calls_full_read(tmp_path: Path):
    path = _archive(tmp_path / "sparse.cmpct")
    with CMPCT(path) as archive:
        def no_full_read(_name):
            raise AssertionError("verify() may not materialize an entire sparse logical file")
        archive.read = no_full_read
        assert archive.verify() == 1


def test_hardlinked_sparse_verification_never_calls_full_read(tmp_path: Path):
    path = _archive(tmp_path / "hardlink.cmpct", hardlink=True)
    with CMPCT(path) as archive:
        archive.read = lambda name: (_ for _ in ()).throw(
            AssertionError("hardlink owner materialized")
        )
        assert archive.verify() == 2


def test_hardlink_owner_length_mismatch_is_refused_before_hash(tmp_path: Path):
    path = _archive(tmp_path / "badlink.cmpct", hardlink=True, wrong_owner_length=True)
    with CMPCT(path) as archive:
        with pytest.raises(OSError, match="hardlink logical length mismatch"):
            archive.verify()


def test_physical_blob_sha_mismatch_is_refused(tmp_path: Path):
    path = _archive(tmp_path / "badblob.cmpct", bad_physical=True)
    with CMPCT(path) as archive:
        with pytest.raises(OSError, match="physical SHA-256"):
            archive.verify()


def test_missing_sparse_logical_commitment_is_not_self_verification(tmp_path: Path):
    path = _archive(tmp_path / "no-commitment.cmpct", missing_logical_sha=True)
    with CMPCT(path) as archive:
        archive.read = lambda name: (_ for _ in ()).throw(
            AssertionError("missing digest must not trigger full logical read")
        )
        with pytest.raises(OSError, match="missing sparse logical SHA-256"):
            archive.verify()
