from __future__ import annotations

import binascii
import hashlib
import struct
import threading

import pytest

from cmpct.reader import CMPCT, BHDR, BMAGIC, K_FILE, S_PACK


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _reader(member: bytes, whole_pack: bytes, *, claimed_member_sha: bytes | None = None,
            claimed_physical_sha: bytes | None = None, include_member: bool = True) -> CMPCT:
    """Method-contract witness. Independent wire/preflight and platform tests are separate gates."""
    reader = object.__new__(CMPCT)
    reader.files = (
        [["a.bin", K_FILE, 0o600, 0, len(member),
          claimed_member_sha or _sha(member), [S_PACK, 0, 0, len(member)]]]
        if include_member else []
    )
    reader.cache = {"old": b"cached"}
    reader.vcache = {"old": b"cached"}
    reader._cache_lock = threading.Lock()
    reader.record_base = 0
    header = BHDR.pack(
        BMAGIC, 0, 0, 0, len(whole_pack), len(whole_pack), 0,
        binascii.crc32(whole_pack) & 0xFFFFFFFF,
        claimed_physical_sha or _sha(whole_pack),
    )
    reader.mm = header + whole_pack
    reader.blobs = [(0, len(whole_pack), len(whole_pack), 0, 0)]
    reader._blob = lambda idx: whole_pack
    reader.read = lambda name: whole_pack[:len(member)]
    reader.file_sha256 = lambda name: _sha(reader.read(name))
    return reader


def test_strong_verify_accepts_independent_logical_and_physical_identity() -> None:
    member = b"same bytes"
    reader = _reader(member, member + b"unreferenced")
    assert reader.verify() == 1
    assert reader.cache == {} and reader.vcache == {}


def test_strong_verify_rejects_wrong_equal_size_packed_member() -> None:
    actual = b"wrong"
    reader = _reader(actual, actual, claimed_member_sha=_sha(b"right"))
    with pytest.raises(OSError, match="SHA-256 verification failure"):
        reader.verify()


def test_strong_verify_rejects_corrupted_unreferenced_pack_tail() -> None:
    member = b"member"
    raw = member + b"changed suffix"
    reader = _reader(
        member, raw, claimed_physical_sha=_sha(member + b"original suffix")
    )
    with pytest.raises(OSError, match="physical SHA-256"):
        reader.verify()


def test_strong_verify_checks_orphan_physical_record() -> None:
    reader = _reader(b"", b"orphan", claimed_physical_sha=_sha(b"different"),
                     include_member=False)
    with pytest.raises(OSError, match="physical SHA-256"):
        reader.verify()
