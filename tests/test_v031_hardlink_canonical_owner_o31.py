"""O29: exact signed-r24 lexical hardlink target normalization falsifier.

Source-original O29 signed fixture, with separate positive product assertions.
Original O29 scientific negative remains durable in PR #383; no rewrite.
"""
from __future__ import annotations

import binascii
import hashlib
from pathlib import Path

import msgpack
import pytest

from cmpct.codec import (
    BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, K_FILE, K_HARDLINK,
    MAGIC, S_BLOB, VERSION, sha, zc,
)
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PAYLOAD = b"exact-r24-owner-separator-normalization\x00\xfe"


def _signed_archive(path: Path, target: str) -> Path:
    # Construct real format-r24 framing and SHA-committed logical index.
    # Only the alias spelling differs; physical owner and bytes are identical.
    files = sorted([
        ["sub/owner.bin", K_FILE, 0o644, 0, len(PAYLOAD), sha(PAYLOAD), [S_BLOB, 0]],
        ["alias.bin", K_HARDLINK, 0o644, 0, len(PAYLOAD), sha(PAYLOAD), [target]],
    ], key=lambda row: row[0])
    index = {
        "v": VERSION,
        "files": files,
        "blobs": [[0, len(PAYLOAD), len(PAYLOAD), CODEC_RAW, 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }
    raw_index = msgpack.packb(index, use_bin_type=True)
    zipped_index = zc(raw_index, 3)
    blob = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(PAYLOAD), len(PAYLOAD), 0,
        binascii.crc32(PAYLOAD) & 0xFFFFFFFF, sha(PAYLOAD),
    ) + PAYLOAD
    header = HDR.pack(MAGIC, VERSION, 0, len(zipped_index), len(raw_index),
                      len(blob), sha(raw_index))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(zipped_index), len(raw_index),
                      0, sha(raw_index))
    path.write_bytes(header + zipped_index + blob + zipped_index + footer)
    return path


def test_o31_signed_hardlink_targets_use_the_same_canonical_owner_for_reader_and_extract(tmp_path):
    forward = _signed_archive(tmp_path / "forward.cmpct", "sub/owner.bin")
    backslash = _signed_archive(tmp_path / "backslash.cmpct", "sub\\\\owner.bin")
    # The index hashes differ while one owner and reconstructed contents agree.
    assert hashlib.sha256(forward.read_bytes()).digest() != hashlib.sha256(
        backslash.read_bytes()).digest()
    for path in (forward, backslash):
        assert preflight_archive(path)["files"] == 2
        with CMPCT(path) as reader:
            assert reader.read("alias.bin") == PAYLOAD
            assert reader.read_range("alias.bin", 2, 7) == PAYLOAD[2:9]
            assert reader.read_raw_range_verified("alias.bin", 1, 9) == PAYLOAD[1:10]
            assert reader.file_sha256("alias.bin") == sha(PAYLOAD)
            assert reader._hardlink_owners["alias.bin"] == "sub/owner.bin"
            assert reader.verify() == 2
            dest = tmp_path / ("extract-forward" if path == forward else "extract-backslash")
            reader.extractall(dest, metadata=False)
        assert (dest / "sub" / "owner.bin").read_bytes() == PAYLOAD
        assert (dest / "alias.bin").read_bytes() == PAYLOAD


@pytest.mark.parametrize("unsafe_target", [
    "../escape.bin", "sub/../owner.bin", "sub\\\\..\\\\escape.bin",
])
def test_o31_signed_unsafe_hardlink_target_still_rejected_before_extract(tmp_path, unsafe_target):
    path = _signed_archive(tmp_path / "unsafe.cmpct", unsafe_target)
    with pytest.raises((ValidationError, ValueError)):
        preflight_archive(path)
    with pytest.raises(OSError, match="unsafe hardlink"):
        with CMPCT(path):
            pass
    assert not (tmp_path / "extracted").exists()
