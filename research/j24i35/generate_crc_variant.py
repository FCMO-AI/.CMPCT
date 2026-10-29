#!/usr/bin/env python3
"""J24I35: exact authentic r24 CMA4 CRC-only contradiction, Python observation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from cmpct.codec import HDR, BHDR
from cmpct.reader import CMPCT

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def python_verify(path: Path) -> dict:
    try:
        with CMPCT(path) as archive:
            count = archive.verify()
        return {"accepted": True, "verified": count, "error": None}
    except Exception as exc:
        return {"accepted": False, "verified": None, "error": type(exc).__name__ + ": " + str(exc)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, required=True)
    case_dir = parser.parse_args().case_dir
    original_path = case_dir / "original.cmpct"
    original = original_path.read_bytes()
    magic, revision, flags, index_csize, index_usize, span, index_hash = HDR.unpack_from(original)
    assert (magic, revision, flags) == (b"CMPCT24\0", 24, 0)
    assert index_csize < 2**26 and span < 2**30
    record_start = HDR.size + index_csize
    blob_magic, codec, blob_flags, reserved, usize, csize, meta_len, prior_crc, physical_sha = BHDR.unpack_from(original, record_start)
    assert (blob_magic, codec, blob_flags, reserved, meta_len) == (b"CMA4", 0, 0, 0, 0)
    assert usize == csize == len(b"relative-symlink-target.txt")
    assert span == BHDR.size + csize
    payload_start = record_start + BHDR.size
    payload = original[payload_start:payload_start + csize]
    assert payload == b"relative-symlink-target.txt"
    assert zlib.crc32(payload) & 0xffffffff == prior_crc
    assert hashlib.sha256(payload).digest() == physical_sha

    crc_offset = record_start + 28  # CMA4 little-endian crc32 field, byte 0
    changed = bytearray(original)
    changed[crc_offset] ^= 1
    mutated = bytes(changed)
    assert len(original) == len(mutated)
    assert [i for i, (a, b) in enumerate(zip(original, mutated)) if a != b] == [crc_offset]
    assert original[:crc_offset] == mutated[:crc_offset]
    assert original[crc_offset+1:] == mutated[crc_offset+1:]
    assert hashlib.sha256(original[payload_start:payload_start+csize]).digest() == physical_sha
    assert BHDR.unpack_from(mutated, record_start)[-1] == physical_sha

    case_path = case_dir / "crc-wrong.cmpct"
    case_path.write_bytes(mutated)
    original_result = python_verify(original_path)
    mutated_result = python_verify(case_path)
    assert original_result == {"accepted": True, "verified": 1, "error": None}
    assert not mutated_result["accepted"], "predicted Python CRC rejection falsified"
    assert "integrity" in (mutated_result["error"] or "").lower(), mutated_result

    record = {
        "schema": "cmpct-j24i35-crc-only-physical-contradiction-v1",
        "scientific_status": "negative candidate, NOT product repair",
        "source_archive_sha256": digest(original),
        "crc_mutated_archive_sha256": digest(mutated),
        "payload_sha256": digest(payload),
        "physical_index_and_footer_unchanged": True,
        "mutated_offset": crc_offset,
        "original_crc32": prior_crc,
        "mutated_crc32": BHDR.unpack_from(mutated, record_start)[-2],
        "original_python": original_result,
        "crc_mutated_python": mutated_result,
    }
    (case_dir / "j24i35-python-observations.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
