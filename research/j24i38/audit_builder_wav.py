#!/usr/bin/env python3
"""J24I38: detached WAV-FLAC physical audit. NEVER import cmpct."""
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


def sha(b):
    return hashlib.sha256(b).digest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    a = p.parse_args()
    m = json.loads((a.case_dir / "manifest.json").read_text())
    assert m["schema"] == "j24i38-builder-wav-flac-v1"
    results = {}
    for mib in (8, 32):
        case = m["records"][str(mib)]
        original = (a.case_dir / ("source-%dm" % mib) / "capture.wav").read_bytes()
        physical = (a.case_dir / ("builder-wav-%dm.cmpct" % mib)).read_bytes()
        assert sha(original).hex() == case["source_sha256"]
        assert sha(physical).hex() == case["archive_sha256"]
        magic, rev, flags, cs, us, span, idxsha = HEADER.unpack_from(physical)
        assert (magic, rev, flags) == (b"CMPCT24\x00", 24, 0)
        start = HEADER.size
        index_comp = physical[start:start+cs]
        index_raw = zstandard.ZstdDecompressor().decompress(
            index_comp, max_output_size=us
        )
        assert len(index_raw) == us and sha(index_raw) == idxsha
        idx = msgpack.unpackb(index_raw, raw=False)
        assert len(idx["files"]) == len(idx["blobs"]) == 1
        row = idx["files"][0]
        assert row[0] == "capture.wav" and row[1] == 0 and row[4] == len(original)
        assert row[6] == [0, 0] and row[5] is None
        off, usize, csize, codec, meta_len = idx["blobs"][0]
        assert off == 0 and usize == len(original) and codec == 2
        assert csize == case["encoded_bytes"]
        rec_start = HEADER.size + cs
        bmagic, bcodec, bflags, reserved, rus, rcs, rmeta, crc, digest = BLOB.unpack_from(
            physical, rec_start
        )
        assert (bmagic, bcodec, bflags, reserved) == (b"CMA4", 2, 0, 0)
        assert (rus, rcs, rmeta) == (usize, csize, meta_len)
        blob_meta = physical[rec_start+BLOB.size:rec_start+BLOB.size+meta_len]
        flac = physical[rec_start+BLOB.size+meta_len:rec_start+BLOB.size+meta_len+csize]
        prefix, suffix, channels, rate, bits = msgpack.unpackb(blob_meta, raw=False)
        assert channels == 1 and rate == 44100 and bits == 16
        samples, decoded_rate = sf.read(io.BytesIO(flac), dtype="int16", always_2d=False)
        assert decoded_rate == rate
        reconstructed = bytes(prefix) + np.asarray(samples, dtype="<i2").tobytes() + bytes(suffix)
        assert reconstructed == original, "independent libsndfile logical reconstruction mismatch"
        assert digest == sha(original)
        assert crc == (zlib.crc32(original) & 0xffffffff) == case["crc32"]
        assert len(reconstructed) == case["logical_bytes"]
        assert span == BLOB.size + meta_len + csize
        end = rec_start + span
        assert physical[end:end+cs] == index_comp, "tail index mismatch"
        assert end + cs + FOOT.size == len(physical)
        assert FOOT.unpack_from(physical, end+cs) == (
            b"CMPTF24\x00", 0, 1, 0, 0, cs, us, 0, idxsha
        )
        results[str(mib)] = {
            "codec": 2,
            "source_sha256": sha(original).hex(),
            "archive_sha256": sha(physical).hex(),
            "logical_bytes": len(original),
            "encoded_bytes": csize,
            "physical_crc32": crc,
            "direct_member": True,
            "dual_index_equal": True,
        }
    result = {
        "schema": "j24i38-detached-authentic-builder-wav-v1",
        "result": "PASS",
        "independent_of_cmpct_import": True,
        "results": results,
    }
    (a.case_dir / "detached-audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
