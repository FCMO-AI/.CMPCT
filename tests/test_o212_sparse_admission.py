"""O212: same-effective-index S_SPARSE admission parity, independent of the O198/O202 courts.

This is a product regression test, not a frozen benchmark. Only genuine revision-24 wire
objects with valid SHA/CRC and authenticated indexes are used; malformed *geometry* is
the sole perturbation. The stored format and evaluator contract are unchanged.
"""
import binascii
import hashlib
from pathlib import Path

import msgpack
import pytest

from cmpct.codec import (
    MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
    CODEC_RAW, K_FILE, S_SPARSE, S_BLOB, zc, sha,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PAYLOAD = b"ABCD"
PATH = "sparse.bin"


def _archive_bytes(extents, logical_bytes, *, storage_kind=S_SPARSE, latest_index=None):
    """Produce authenticated primary/physical/last-generation revision-24 bytes."""
    record = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xffffffff, sha(PAYLOAD),
    ) + PAYLOAD
    storage = [storage_kind, extents] if storage_kind == S_SPARSE else [S_BLOB, 0]
    idx = {
        "v": VERSION,
        "files": [[PATH, K_FILE, 0o644, 946684800000000000,
                   len(logical_bytes), sha(logical_bytes), storage]],
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None, "fsmeta": {},
    }

    def encode(index):
        raw = msgpack.packb(index, use_bin_type=True)
        return zc(raw, 12), raw, sha(raw)

    compressed, raw, digest = encode(idx)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, digest)
    archive = (
        HDR.pack(MAGIC, VERSION, 0, len(compressed), len(raw), len(record), digest)
        + compressed + record + compressed + footer
    )
    if latest_index is not None:
        compressed, raw, digest = encode(latest_index)
        archive += compressed + FTR.pack(
            FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, digest
        )
    return archive


def _write(tmp_path, raw, label):
    path = tmp_path / (label + ".cmpct")
    path.write_bytes(raw)
    return path


def test_valid_sparse_full_range_verify_extract_and_holes(tmp_path):
    expected = PAYLOAD + b"\0" * 4 + PAYLOAD
    path = _write(tmp_path, _archive_bytes([[0, 4, [0]], [8, 4, [0]]], expected), "valid-holes")
    assert preflight_archive(path, verify_blob_headers=True)["files"] == 1
    with CMPCT(path) as archive:
        assert archive.verify() == 1
        assert archive.read(PATH) == expected
        assert archive.read_range(PATH, 3, 6) == b"D" + b"\0" * 4 + b"A"
        assert archive.read_range(PATH, 4, 4) == b"\0" * 4
        destination = tmp_path / "extracted"
        archive.extractall(destination, metadata=False)
    assert (destination / PATH).read_bytes() == expected


@pytest.mark.parametrize("declared", [1, 2, 5])
def test_root_versioned_corrupt_sparse_length_fails_at_open_without_write(tmp_path, declared):
    raw = _archive_bytes([[0, declared, [0]]], PAYLOAD)
    path = _write(tmp_path, raw, "bad-%d" % declared)
    before = hashlib.sha256(path.read_bytes()).digest()
    with pytest.raises(ValidationError):
        preflight_archive(path)
    with pytest.raises(ValidationError):
        CMPCT(path)
    assert hashlib.sha256(path.read_bytes()).digest() == before


def test_latest_authenticated_index_not_just_primary_is_admitted(tmp_path):
    primary_idx = {
        "v": VERSION,
        "files": [[PATH, K_FILE, 0o644, 946684800000000000,
                   4, sha(PAYLOAD), [S_SPARSE, [[0, 1, [0]]]]]],
        "blobs": [[0, 4, 4, CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None, "fsmeta": {},
    }
    # The PRIMARY index is valid. The later authenticated generation is contradictory.
    path = _write(tmp_path, _archive_bytes([[0, 4, [0]]], PAYLOAD,
                                         latest_index=primary_idx), "bad-latest")
    with pytest.raises(ValidationError):
        preflight_archive(path)
    with pytest.raises(ValidationError):
        CMPCT(path)


def test_non_sparse_blob_behavior_remains_unchanged(tmp_path):
    path = _write(tmp_path, _archive_bytes(None, PAYLOAD, storage_kind=S_BLOB), "regular")
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as archive:
        assert archive.verify() == 1
        assert archive.read(PATH) == PAYLOAD
        assert archive.read_range(PATH, 2, 2) == b"CD"


def test_many_valid_sparse_extents_are_admitted_once(tmp_path):
    # An intermediate-scale, structurally different control; repeats a physical blob
    # without inventing a second physical frame, and checks early + late random access.
    count, stride = 64, 1 << 20
    expected = bytearray((count - 1) * stride + 4)
    extents = []
    for i in range(count):
        expected[i * stride : i * stride + 4] = PAYLOAD
        extents.append([i * stride, 4, [0]])
    path = _write(tmp_path, _archive_bytes(extents, expected), "many")
    assert preflight_archive(path)["files"] == 1
    with CMPCT(path) as archive:
        assert archive.read_range(PATH, 0, 4) == PAYLOAD
        assert archive.read_range(PATH, (count - 1) * stride, 4) == PAYLOAD
        assert archive.read_range(PATH, 5, 4) == b"\0" * 4
