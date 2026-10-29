#!/usr/bin/env python3
"""J24I36 detached physical byte referee; deliberately imports NO cmpct module.

The source of truth is the immutable direct-codec golden JSON and standardized
zstd/zlib decompression. The verifier does not trust generator observations.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import zlib
from pathlib import Path
import zstandard

H = struct.Struct("<8sHHQQQ32s")
B = struct.Struct("<4sBBHQQII32s")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--case-dir", type=Path, required=True)
    args = ap.parse_args()
    vectors = json.loads(args.vectors.read_text())
    assert vectors["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    observed = []
    for record in vectors["vectors"]:
        original = base64.b64decode(record["archive_base64"], validate=True)
        stem = record["name"].split(".")[0]
        observed_original = (args.case_dir / (stem + "-original.cmpct")).read_bytes()
        altered = (args.case_dir / (stem + "-crc-wrong.cmpct")).read_bytes()
        assert original == observed_original
        assert sha256(original) == record["archive_sha256"]
        assert len(original) == len(altered) == record["archive_bytes"]
        magic, version, flags, index_csize, index_usize, span, index_hash = H.unpack_from(original)
        assert magic == b"CMPCT24" + bytes([0]) and version == 24 and flags == 0
        assert 0 < index_csize < 1_000_000 and 0 < index_usize < 1_000_000
        index_frame = original[H.size:H.size + index_csize]
        index = zstandard.ZstdDecompressor().decompress(index_frame, max_output_size=index_usize)
        assert len(index) == index_usize
        assert hashlib.sha256(index).digest() == index_hash
        start = H.size + index_csize
        fields = B.unpack_from(original, start)
        assert fields[0] == b"CMA4" and fields[1] == record["codec"]
        assert fields[6] < 1_000_000
        payload_start = start + B.size + fields[6]
        payload_end = payload_start + fields[5]
        assert payload_end <= len(original) and span == B.size + fields[6] + fields[5]
        compressed = original[payload_start:payload_end]
        if record["codec"] == 0:
            decoded = compressed
        elif record["codec"] == 1:
            decoded = zstandard.ZstdDecompressor().decompress(compressed, max_output_size=fields[4])
        elif record["codec"] == 4:
            decoded = zlib.decompress(compressed, -15)
        else:
            raise AssertionError("unknown frozen codec")
        assert len(decoded) == fields[4] == record["logical_size"]
        assert sha256(decoded) == record["logical_sha256"]
        assert hashlib.sha256(decoded).digest() == fields[8]
        computed_crc = zlib.crc32(decoded) & 0xffffffff
        assert computed_crc == fields[7]
        crc_offset = start + 28
        differences = [i for i, (x, y) in enumerate(zip(original, altered)) if x != y]
        assert differences == [crc_offset]
        assert (original[crc_offset] ^ altered[crc_offset]) == 1
        after_fields = B.unpack_from(altered, start)
        assert after_fields[:7] == fields[:7]
        assert after_fields[8] == fields[8]
        assert after_fields[7] != computed_crc
        assert altered[payload_start:payload_end] == compressed
        assert original[:crc_offset] == altered[:crc_offset]
        assert original[crc_offset + 1:] == altered[crc_offset + 1:]
        observed.append({
            "name": record["name"],
            "codec": record["codec"],
            "source_sha256": sha256(original),
            "crc_wrong_sha256": sha256(altered),
            "crc_position": crc_offset,
            "sha256_decoded_unchanged": sha256(decoded),
            "real_crc": computed_crc,
            "mutant_crc": after_fields[7],
            "both_index_copies_and_footer_unchanged": True,
        })
    outcome = {"schema": "j24i36-independent-fixed-codec-referee-v1", "result": "PASS", "vectors": observed}
    (args.case_dir / "detached-audit.json").write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()
