#!/usr/bin/env python3
"""Detached exact physical r24 WAV/FLAC auditor. Never imports CMPCT."""
import argparse
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path

import msgpack
import numpy as np
import soundfile as sf
import zstandard

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOT = struct.Struct("<8sBBBBQQQ32s")


def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def audit(root: Path):
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["schema"] == "j24i44-small-builder-direct-wav-v1"
    checks = {}
    for kib in manifest["pcm_kib"]:
        case = manifest["records"][str(kib)]
        original = (root / f"source-{kib}k" / "capture.wav").read_bytes()
        encoded = (root / f"builder-wav-{kib}k.cmpct").read_bytes()
        assert sha(original).hex() == case["logical_sha256"]
        assert sha(encoded).hex() == case["archive_sha256"]
        magic, revision, flags, cs, us, span, ihash = HEADER.unpack_from(encoded)
        assert (magic, revision, flags) == (b"CMPCT24\0", 24, 0)
        index_raw = zstandard.ZstdDecompressor().decompress(
            encoded[HEADER.size:HEADER.size+cs], max_output_size=us
        )
        assert len(index_raw) == us and sha(index_raw) == ihash
        index = msgpack.unpackb(index_raw, raw=False)
        assert len(index["files"]) == 1
        row = index["files"][0]
        assert row[0] == "capture.wav" and row[4] == len(original)
        # Regardless of selection, verify the duplicate index and footer.
        tail = HEADER.size + cs + span
        assert encoded[tail:tail+cs] == encoded[HEADER.size:HEADER.size+cs]
        assert len(encoded) == tail + cs + FOOT.size
        assert FOOT.unpack_from(encoded, tail+cs) == (
            b"CMPTF24\0", 0, 1, 0, 0, cs, us, 0, ihash
        )
        if not case["selected_flac"]:
            checks[str(kib)] = {
                "selected_flac": False,
                "archive_sha256": sha(encoded).hex(),
                "index_duplicate_identical": True,
            }
            continue
        assert len(index["blobs"]) == 1 and row[6] == [0, 0]
        off, usize, csize, codec, meta_len = index["blobs"][0]
        assert (off, usize, codec) == (0, len(original), 2)
        rec_pos = HEADER.size + cs
        bm, bc, bf, reserved, bu, bcsize, bm_len, crc, digest = BLOB.unpack_from(
            encoded, rec_pos
        )
        assert (bm, bc, bf, reserved) == (b"CMA4", 2, 0, 0)
        assert (bu, bcsize, bm_len) == (usize, csize, meta_len)
        assert span == BLOB.size + meta_len + csize
        start = rec_pos + BLOB.size
        prefix, suffix, channels, rate, bits = msgpack.unpackb(
            encoded[start:start+meta_len], raw=False
        )
        assert (channels, rate, bits) == (1, 44100, 16)
        flac = encoded[start+meta_len:start+meta_len+csize]
        assert len(flac) == csize and flac[:4] == b"fLaC"
        samples, sample_rate = sf.read(io.BytesIO(flac), dtype="int16", always_2d=False)
        assert sample_rate == rate
        reconstructed = bytes(prefix) + np.asarray(samples, dtype="<i2").tobytes() + bytes(suffix)
        assert reconstructed == original, "independent FLAC reconstruction differs"
        assert digest == sha(original) and crc == zlib.crc32(original) & 0xFFFFFFFF
        checks[str(kib)] = {
            "selected_flac": True,
            "logical_sha256": sha(reconstructed).hex(),
            "archive_sha256": sha(encoded).hex(),
            "logical_bytes": len(reconstructed),
            "encoded_bytes": csize,
            "logical_crc32": crc,
            "index_duplicate_identical": True,
        }
    result = {
        "schema": "j24i44-detached-physical-audit-v1",
        "result": "PASS",
        "independent_of_cmpct_import": True,
        "cases": checks,
    }
    (root / "detached-audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("J24I44_DETACHED_PASS", sum(v["selected_flac"] for v in checks.values()), "/", len(checks))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, required=True)
    args = parser.parse_args()
    audit(args.case_dir)
