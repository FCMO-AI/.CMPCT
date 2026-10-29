"""J24G50: physically compose J24G44 Zstd-empty verification and J24G47 fsmeta rekey.

The input archive is a genuine Builder r24 empty member, then independently signed
with a valid Zstd frame and a synthetic xattr record. This deliberately tests the
Reader/Writer integration rather than claiming Builder captured that synthetic xattr.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib

import msgpack
import pytest
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, FMAGIC, FTR, HDR, MAGIC, S_BLOB, VERSION
from cmpct.reader import CMPCT
from cmpct.transactions import append_update


KEY = "com.fcmo.cmpct.j24g50" if sys.platform == "darwin" else "user.cmpct_j24g50"
VALUE = b"cmpct-integrated-identity\x00\xff"


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _replace_empty_raw_with_signed_zstd_and_xattr(source: bytes) -> tuple[bytes, int]:
    magic, revision, flags, old_cs, old_us, old_span, old_sha = HDR.unpack_from(source)
    assert magic == MAGIC and revision == VERSION and flags == 0
    payload = zstd.ZstdDecompressor().decompress(
        source[HDR.size:HDR.size + old_cs], max_output_size=old_us + 1
    )
    assert len(payload) == old_us and _sha(payload) == old_sha
    idx = msgpack.unpackb(payload, raw=False)
    assert len(idx["files"]) == len(idx["blobs"]) == 1
    row, blob = idx["files"][0], idx["blobs"][0]
    assert row[0] == "empty.bin" and row[4] == 0 and row[6][0] == S_BLOB
    assert blob[1] == blob[2] == 0 and blob[3] == CODEC_RAW
    assert old_span == BHDR.size
    assert BHDR.unpack_from(source, HDR.size + old_cs)[-1] == _sha(b"")

    frame = zstd.ZstdCompressor(level=3).compress(b"")
    idx["blobs"][0][2] = len(frame)
    idx["blobs"][0][3] = CODEC_ZSTD
    # Self-checksummed physical index bytes, not a cryptographic authenticity signature.
    idx["fsmeta"] = {
        "owner": [0, 0],
        "owner_overrides": [],
        "xattrs": [[0, [[KEY, VALUE]]]],
    }
    raw_index = msgpack.packb(idx, use_bin_type=True)
    compressed_index = zstd.ZstdCompressor(level=3).compress(raw_index)
    record = (
        BHDR.pack(BMAGIC, CODEC_ZSTD, 0, 0, 0, len(frame), 0,
                  zlib.crc32(b"") & 0xffffffff, _sha(b"")) + frame
    )
    head = HDR.pack(MAGIC, VERSION, 0, len(compressed_index),
                    len(raw_index), len(record), _sha(raw_index))
    tail = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed_index),
                    len(raw_index), 0, _sha(raw_index))
    archive = head + compressed_index + record + compressed_index + tail
    return archive, len(head) + len(compressed_index) + BHDR.size


def _host_xattr(path: Path) -> bytes | None:
    if sys.platform == "darwin":
        p = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                           text=True, capture_output=True)
        return bytes.fromhex("".join(p.stdout.split())) if p.returncode == 0 else None
    if sys.platform == "linux":
        try:
            return os.getxattr(path, KEY, follow_symlinks=False)
        except OSError:
            return None
    return None


def test_signed_zero_zstd_and_shifted_xattr_identity_share_one_real_archive(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "empty.bin").write_bytes(b"")
    origin = tmp_path / "origin.cmpct"
    Builder(source, workers=1, reproducible=True).build(origin)
    signed, physical_pos = _replace_empty_raw_with_signed_zstd_and_xattr(origin.read_bytes())
    archive_path = tmp_path / "composed.cmpct"
    archive_path.write_bytes(signed)

    with CMPCT(archive_path) as initial:
        assert initial.verify() == 1
        assert initial.read("empty.bin") == b""
        assert initial.fsmeta["xattrs"] == [[0, [[KEY, VALUE]]]]

    insertion = tmp_path / "insertion.txt"
    insertion.write_bytes(b"independent-new-content" * 7)
    append_update(archive_path, "a-new.bin", insertion)

    with CMPCT(archive_path) as ar:
        assert [row[0] for row in ar.files] == ["a-new.bin", "empty.bin"]
        assert ar.verify() == 2
        assert ar.read("empty.bin") == b""
        assert ar.read("a-new.bin") == insertion.read_bytes()
        assert ar.fsmeta["xattrs"] == [[1, [[KEY, VALUE]]]]
        output = tmp_path / "restored"
        ar.extractall(output, metadata=True,
                      require_xattrs=sys.platform in ("darwin", "linux"))
    assert (output / "empty.bin").read_bytes() == b""
    assert (output / "a-new.bin").read_bytes() == insertion.read_bytes()
    if sys.platform in ("darwin", "linux"):
        assert _host_xattr(output / "empty.bin") == VALUE
        assert _host_xattr(output / "a-new.bin") is None

    # The journal and checksum-bearing logical index remain unchanged; only the
    # original encoded Zstd frame magic is corrupted after its signed-index binding.
    invalid = bytearray(archive_path.read_bytes())
    assert invalid[physical_pos:physical_pos + 4] == bytes.fromhex("28b52ffd")
    invalid[physical_pos] ^= 1
    bad = tmp_path / "one-byte-corrupt.cmpct"
    bad.write_bytes(invalid)
    with CMPCT(bad) as damaged:
        assert damaged.fsmeta["xattrs"] == [[1, [[KEY, VALUE]]]]
        with pytest.raises((RuntimeError, IOError, ValueError)):
            damaged.verify()
    with pytest.raises(zstd.ZstdError):
        zstd.ZstdDecompressor().decompress(
            invalid[physical_pos:physical_pos + len(zstd.ZstdCompressor(level=3).compress(b""))],
            max_output_size=1,
        )

    evidence_dir = os.environ.get("J24G50_EVIDENCE_DIR")
    if evidence_dir:
        target = Path(evidence_dir)
        target.mkdir(parents=True, exist_ok=True)
        (target / "valid-with-journal.cmpct").write_bytes(archive_path.read_bytes())
        (target / "corrupt-with-journal.cmpct").write_bytes(invalid)
        receipt = {
            "case": "signed zero-output Zstd direct member with index-positional fsmeta shifted by journal insertion",
            "source_sha256": _sha(origin.read_bytes()).hex(),
            "signed_prejournal_sha256": _sha(signed).hex(),
            "valid_sha256": _sha(archive_path.read_bytes()).hex(),
            "invalid_sha256": _sha(invalid).hex(),
            "physical_corrupt_offset": physical_pos,
            "modified_bytes": 1,
            "semantic": "valid verifies both members; malformed Zstd rejects; original empty member retains synthetic xattr across insertion",
            "native_xattr_evidence": sys.platform in ("darwin", "linux"),
            "platform": sys.platform,
        }
        (target / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
