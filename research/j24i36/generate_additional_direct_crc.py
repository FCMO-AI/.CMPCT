#!/usr/bin/env python3
"""J24I36c: source-exact held-out direct codecs 2/3 with one-bit CRC falsifiers.

Consumes immutable, Builder-independent WAV/FLAC and Zstd-dictionary r24 vectors.
This fixture generator is NOT its own independent verifier: installed CMPCT and
compiled Rust are adjudicated separately, and original-byte SHA is frozen.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct

from cmpct.reader import CMPCT

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
VECTORS = (
    ("wav", "v24-wavflac.json", "wav16.wav", 2),
    ("dict", "v24-zstd-dictionary.json", "dict.txt", 3),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(path: Path) -> dict:
    try:
        with CMPCT(path) as reader:
            count = reader.verify()
        return {"accepted": True, "verified": count}
    except Exception as exc:
        return {"accepted": False, "error": type(exc).__name__ + ": " + str(exc)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixed_dir = Path(__file__).resolve().parents[2] / "tests" / "conformance"
    records = []
    for stem, filename, expected_name, codec in VECTORS:
        original_fixture = json.loads((fixed_dir / filename).read_text())
        vector = original_fixture["vector"]
        assert vector["name"] == expected_name
        assert vector["codec"] == codec
        original = base64.b64decode(vector["archive_base64"], validate=True)
        assert len(original) == vector["archive_bytes"]
        assert sha(original) == vector["archive_sha256"]
        assert len(original) < 4 * 1024 * 1024
        magic, revision, flags, cs, us, span, _ = HEADER.unpack_from(original)
        assert (magic, revision, flags) == (b"CMPCT24" + bytes([0]), 24, 0)
        assert 0 < cs < 1024 * 1024 and 0 < us < 1024 * 1024
        offset = HEADER.size + cs
        end = offset + span
        assert 0 <= offset < end < len(original)
        physical = []
        while offset < end:
            assert offset + BLOB.size <= end
            bhdr = BLOB.unpack_from(original, offset)
            bmagic, bcodec, bflags, reserved, bus, bcs, meta_len, crc, digest = bhdr
            assert (bmagic, bflags, reserved) == (b"CMA4", 0, 0)
            assert 0 <= bus < 8 * 1024 * 1024
            assert 0 <= bcs < 8 * 1024 * 1024
            assert meta_len < 1024 * 1024
            nxt = offset + BLOB.size + meta_len + bcs
            assert offset < nxt <= end
            physical.append((offset, bcodec, crc, bus, digest.hex()))
            offset = nxt
        assert offset == end
        matching = [entry for entry in physical if entry[1] == codec]
        assert len(matching) == 1, (stem, physical)
        target_pos, _, original_crc, usize, digest = matching[0]
        assert usize == vector["logical_size"]
        assert digest == vector["logical_sha256"]
        crc_offset = target_pos + 28
        assert crc_offset + 4 <= len(original)
        mutant = bytearray(original)
        mutant[crc_offset] ^= 1
        assert sum(a != b for a, b in zip(original, mutant)) == 1
        assert (original[crc_offset] ^ mutant[crc_offset]) == 1
        assert BLOB.unpack_from(mutant, target_pos)[-2] == (original_crc ^ 1)
        assert BLOB.unpack_from(mutant, target_pos)[-1].hex() == digest
        original_path = args.output / f"{stem}-original.cmpct"
        mutant_path = args.output / f"{stem}-crc-wrong.cmpct"
        original_path.write_bytes(original)
        mutant_path.write_bytes(mutant)
        genuine_py = verify(original_path)
        mutant_py = verify(mutant_path)
        assert genuine_py == {"accepted": True, "verified": 1}, (stem, genuine_py)
        assert mutant_py["accepted"] is False, (stem, mutant_py)
        assert "integrity" in mutant_py["error"].lower(), (stem, mutant_py)
        records.append({
            "name": expected_name,
            "codec": codec,
            "archive_bytes": len(original),
            "source_sha256": sha(original),
            "crc_mutant_sha256": sha(mutant),
            "physical_blobs": len(physical),
            "crc_record_offset": crc_offset,
            "original_crc": original_crc,
            "mutant_crc": original_crc ^ 1,
            "logical_sha256_unchanged": digest,
            "both_index_copies_and_footer_unchanged": True,
            "original_python": genuine_py,
            "crc_mutant_python": mutant_py,
        })
    report = {
        "schema": "j24i36-heldout-direct-codec-court-v1",
        "result": "PASS - first-party Python only; native adjudicated separately",
        "unchanged_fixed_vectors": [p[1] for p in VECTORS],
        "records": records,
    }
    (args.output / "heldout-python-observations.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
