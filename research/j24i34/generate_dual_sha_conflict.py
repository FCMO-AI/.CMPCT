#!/usr/bin/env python3
"""J24I34b: physically corrupted RAW symlink with correctly re-signed row SHA.

This negative proves why both authenticated-index and independent CMA4 identity
must agree during strong verification. No product or frozen conformance edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import msgpack
from cmpct.codec import BHDR, HDR, FTR, MAGIC, VERSION, FMAGIC, sha, zc
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "j24i27"))
from test_present_row_sha import source_parts  # noqa: E402

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", type=Path, required=True)
    args = ap.parse_args()
    dest = args.case_dir
    source = (dest / "original.cmpct").read_bytes()
    index, original_physical, raw = source_parts(source)
    assert index["files"][0][1] == 2 and index["files"][0][5] is None
    off, usize, csize, codec, metalen = index["blobs"][0]
    assert codec == 0 and usize == csize == len(raw)
    payload_offset = off + BHDR.size + metalen
    assert original_physical[payload_offset:payload_offset+len(raw)] == raw
    mutated = bytearray(raw)
    mutated[0] ^= 1
    mutated_bytes = bytes(mutated)
    modified_physical = bytearray(original_physical)
    modified_physical[payload_offset] ^= 1
    assert sum(a != b for a, b in zip(original_physical, modified_physical)) == 1
    assert modified_physical[:BHDR.size] == original_physical[:BHDR.size]
    indexed_digest = hashlib.sha256(mutated_bytes).digest()
    assert indexed_digest != hashlib.sha256(raw).digest()
    index["files"][0][5] = indexed_digest
    index_wire = msgpack.packb(index, use_bin_type=True)
    encoded = zc(index_wire, 12)
    index_hash = sha(index_wire)
    header = HDR.pack(MAGIC, VERSION, 0, len(encoded), len(index_wire),
                      len(modified_physical), index_hash)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(index_wire),
                      0, index_hash)
    wire = header + encoded + bytes(modified_physical) + encoded + footer
    path = dest / "dual-commit-corrupt.cmpct"
    path.write_bytes(wire)
    try:
        with CMPCT(path) as archive:
            archive.verify()
    except IOError as ex:
        python_rejected = True
        python_reason = str(ex)
    else:
        python_rejected = False
        python_reason = "incorrectly accepted"
    assert python_rejected, "Python strong verify must reject physical corruption"
    result = {
        "schema": "cmpct-j24i34b-dual-direct-sha-conflict-v1",
        "science_only": True,
        "original_archive_sha256": hashlib.sha256(source).hexdigest(),
        "archive_sha256": hashlib.sha256(wire).hexdigest(),
        "original_physical_sha256": hashlib.sha256(original_physical).hexdigest(),
        "corrupt_physical_sha256": hashlib.sha256(modified_physical).hexdigest(),
        "original_payload_sha256": hashlib.sha256(raw).hexdigest(),
        "new_payload_sha256": hashlib.sha256(mutated_bytes).hexdigest(),
        "indexed_present_digest_matches_mutated": indexed_digest == sha(mutated_bytes),
        "physical_header_unchanged": modified_physical[:BHDR.size] == original_physical[:BHDR.size],
        "python_strong_verify_rejected": python_rejected,
        "python_error": python_reason,
    }
    (dest / "dual-commit-conflict.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
