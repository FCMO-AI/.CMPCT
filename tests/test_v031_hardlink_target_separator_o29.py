"""O29: exact signed-r24 lexical hardlink target normalization falsifier.

Scientific *negative* witness, not a regression test claiming the Reader is fixed.
Expected mismatch remains visible and must be retired only by a correct product fix.
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
from cmpct.validation import preflight_archive

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


def test_o29_strict_preflight_accepts_equivalent_target_but_reader_diverges(tmp_path):
    forward = _signed_archive(tmp_path / "forward.cmpct", "sub/owner.bin")
    backslash = _signed_archive(tmp_path / "backslash.cmpct", "sub\\owner.bin")
    assert hashlib.sha256(forward.read_bytes()).digest() != hashlib.sha256(
        backslash.read_bytes()).digest()
    assert preflight_archive(forward)["files"] == 2
    assert preflight_archive(backslash)["files"] == 2
    with CMPCT(forward) as reader:
        assert reader.read("alias.bin") == PAYLOAD
        assert reader.read_range("alias.bin", 2, 7) == PAYLOAD[2:9]
        assert reader.file_sha256("alias.bin") == sha(PAYLOAD)
    # Expected *scientific negative*, never confused with a passing product
    # conformance check: strict preflight agreed, ordinary Reader refuses.
    with pytest.raises(OSError, match="hardlink targets missing owner"):
        with CMPCT(backslash):
            pass
