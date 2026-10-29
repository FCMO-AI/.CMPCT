"""J24G44 product regression: physically valid and malformed r24 zero-output Zstd.

The first-party Builder produces the RAW-empty control. We derive a signed Zstd-empty
record using an independently installed Zstandard codec rather than changing the Builder's
admission policy. Historical J24G43 research and malformed positive control remain frozen.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import zlib

import msgpack
import pytest
import zstandard as zstd

from cmpct import native_codec
from cmpct.builder import Builder
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, FMAGIC, FTR, HDR, MAGIC, S_BLOB, VERSION
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _empty_frame() -> bytes:
    return zstd.ZstdCompressor(level=3).compress(b"")


def _corrupt_magic(frame: bytes) -> bytes:
    assert frame.startswith(bytes.fromhex("28b52ffd"))
    return bytes((frame[0] ^ 1,)) + frame[1:]


def test_zero_output_codec_api_validates_real_encoded_frame() -> None:
    frame = _empty_frame()
    broken = _corrupt_magic(frame)
    # The second hostile specimen is a *valid* frame with contradictory decoded
    # length, not just invalid Zstd magic; no SHA(empty) should rescue it.
    wrong_logical_size = zstd.ZstdCompressor(level=3).compress(b"x")
    dictionary = b"codec-zero-output-dictionary" * 16

    # This historical sentinel has no physical encoded payload to authenticate.
    assert native_codec.decompress(b"", 0) == b""
    assert native_codec.decompress_using_dict(b"", 0, dictionary) == b""

    assert native_codec.decompress(frame, 0) == b""
    assert native_codec.decompress_using_dict(frame, 0, dictionary) == b""
    decoder = native_codec.DictDecoder(dictionary)
    try:
        assert decoder.decompress(b"", 0) == b""
        assert decoder.decompress(frame, 0) == b""
        with pytest.raises((RuntimeError, IOError, ValueError)):
            decoder.decompress(broken, 0)
        with pytest.raises((RuntimeError, IOError, ValueError)):
            decoder.decompress(wrong_logical_size, 0)
    finally:
        decoder.close()

    with pytest.raises((RuntimeError, IOError, ValueError)):
        native_codec.decompress(broken, 0)
    with pytest.raises((RuntimeError, IOError, ValueError)):
        native_codec.decompress_using_dict(broken, 0, dictionary)
    with pytest.raises((RuntimeError, IOError, ValueError)):
        native_codec.decompress(wrong_logical_size, 0)
    with pytest.raises((RuntimeError, IOError, ValueError)):
        native_codec.decompress_using_dict(wrong_logical_size, 0, dictionary)

    assert zstd.ZstdDecompressor().decompress(wrong_logical_size, max_output_size=2) == b"x"
    assert zstd.ZstdDecompressor().decompress(frame, max_output_size=1) == b""
    with pytest.raises(zstd.ZstdError):
        zstd.ZstdDecompressor().decompress(broken, max_output_size=1)


def _signed_empty_zstd_archive(raw_archive: bytes, frame: bytes) -> bytes:
    magic, rev, flags, old_cs, old_us, old_span, old_sha = HDR.unpack_from(raw_archive)
    assert (magic, rev, flags) == (MAGIC, VERSION, 0)
    old_index_c = raw_archive[HDR.size:HDR.size + old_cs]
    old_index = zstd.ZstdDecompressor().decompress(old_index_c, max_output_size=old_us + 1)
    assert len(old_index) == old_us and _hash(old_index) == old_sha
    index = msgpack.unpackb(old_index, raw=False)
    assert len(index["files"]) == len(index["blobs"]) == 1
    file, blob = index["files"][0], index["blobs"][0]
    assert file[0] == "empty.bin" and file[1] == 0 and file[4] == 0
    assert file[6][0] == S_BLOB
    assert blob[1] == blob[2] == 0 and blob[3] == CODEC_RAW
    assert old_span == BHDR.size
    original_bhdr = raw_archive[HDR.size + old_cs:HDR.size + old_cs + old_span]
    assert BHDR.unpack(original_bhdr)[-1] == _hash(b"")
    assert raw_archive[HDR.size + old_cs + old_span:-FTR.size] == old_index_c
    fmagic, kind, fcodec, fflags, fres, tail_cs, tail_us, parent, tail_sha = FTR.unpack_from(raw_archive, len(raw_archive) - FTR.size)
    assert (fmagic, kind, fcodec, fflags, fres, parent) == (FMAGIC, 0, 1, 0, 0, 0)
    assert (tail_cs, tail_us, tail_sha) == (old_cs, old_us, old_sha)

    blob[2] = len(frame)
    blob[3] = CODEC_ZSTD
    signed_index = msgpack.packb(index, use_bin_type=True)
    signed_index_c = zstd.ZstdCompressor(level=3).compress(signed_index)
    record = BHDR.pack(BMAGIC, CODEC_ZSTD, 0, 0, 0, len(frame), 0, zlib.crc32(b""), _hash(b"")) + frame
    signed_header = HDR.pack(MAGIC, VERSION, 0, len(signed_index_c), len(signed_index), len(record), _hash(signed_index))
    signed_footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(signed_index_c), len(signed_index), 0, _hash(signed_index))
    return signed_header + signed_index_c + record + signed_index_c + signed_footer


def test_signed_r24_zero_output_strong_verify_rejects_only_malformed_frame(tmp_path: Path) -> None:
    source_dir = tmp_path / "input"
    source_dir.mkdir()
    (source_dir / "empty.bin").write_bytes(b"")
    original = tmp_path / "original.cmpct"
    Builder(source_dir, workers=1, reproducible=True).build(original)

    frame = _empty_frame()
    valid = _signed_empty_zstd_archive(original.read_bytes(), frame)
    valid_head = HDR.unpack_from(valid)
    payload_offset = HDR.size + valid_head[3] + BHDR.size
    corrupt = bytearray(valid)
    corrupt[payload_offset] ^= 1
    invalid = bytes(corrupt)
    assert [i for i, (a, b) in enumerate(zip(valid, invalid)) if a != b] == [payload_offset]
    assert len(valid) == len(invalid)

    good_path = tmp_path / "valid-zstd-empty.cmpct"
    bad_path = tmp_path / "corrupt-zstd-empty.cmpct"
    good_path.write_bytes(valid)
    bad_path.write_bytes(invalid)

    assert preflight_archive(good_path)["files"] == 1
    assert preflight_archive(bad_path)["files"] == 1
    with CMPCT(original) as archive:
        assert archive.verify() == 1
    with CMPCT(good_path) as archive:
        assert archive.verify() == 1
    with CMPCT(bad_path) as archive:
        with pytest.raises((RuntimeError, IOError, ValueError)):
            archive.verify()

    # Independent actual coded-stream decoder must agree with the new *physical*
    # rejection while primary/tail indexes, physical SHA(empty), CRC(empty) stay identical.
    assert valid[:payload_offset] == invalid[:payload_offset]
    assert valid[payload_offset + 1:] == invalid[payload_offset + 1:]
    assert zstd.ZstdDecompressor().decompress(valid[payload_offset:payload_offset + len(frame)], max_output_size=1) == b""
    with pytest.raises(zstd.ZstdError):
        zstd.ZstdDecompressor().decompress(invalid[payload_offset:payload_offset + len(frame)], max_output_size=1)

    out = os.environ.get("J24G44_EVIDENCE_DIR")
    if out:
        target = Path(out)
        target.mkdir(parents=True, exist_ok=True)
        for name, data in (("original", original.read_bytes()), ("valid", valid), ("invalid", invalid)):
            (target / (name + ".cmpct")).write_bytes(data)
        receipt = {
            "schema": "cmpct-j24g44-python-zero-encoded-physical-regression-v1",
            "source_builder": "Builder(reproducible=True)",
            "changed_physical_offset": payload_offset,
            "logical_size": 0,
            "frame_size": len(frame),
            "sha256": {
                "original": _hash(original.read_bytes()).hex(),
                "valid": _hash(valid).hex(),
                "invalid": _hash(invalid).hex(),
            },
            "expected": "source and signed-valid accepted; magic-corrupt encoded stream rejected by installed Python verifier and independent zstandard decoder",
        }
        (target / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
