#!/usr/bin/env python3
"""Independent physical r24 archive and mutation witness, no cmpct import.

Usage: python tests/research/j24i21_physical_audit.py <J24I21_EVIDENCE_DIR>
Requires Python msgpack and libzstd. Science only; checks actual physical files.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOTER = struct.Struct("<8sBBBBQQQ32s")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_primary(raw, library):
    magic, version, flags, cs, us, ds, expected = HEADER.unpack_from(raw)
    assert magic == b"CMPCT24\x00" and version == 24
    buffer = ctypes.create_string_buffer(us)
    output = library.ZSTD_decompress(
        buffer, us, raw[HEADER.size:HEADER.size + cs], cs
    )
    assert not library.ZSTD_isError(output) and output == us
    assert hashlib.sha256(buffer.raw).digest() == expected
    index = msgpack.unpackb(buffer.raw, raw=False)
    physical = (HEADER.size + cs, HEADER.size + cs + ds)
    return index, physical, raw[HEADER.size:HEADER.size + cs], raw[-FOOTER.size:]


def main(directory):
    library = ctypes.CDLL("libzstd.so.1")
    library.ZSTD_decompress.argtypes = (
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t
    )
    library.ZSTD_decompress.restype = ctypes.c_size_t
    library.ZSTD_isError.argtypes = (ctypes.c_size_t,)
    library.ZSTD_isError.restype = ctypes.c_uint
    root = Path(directory)
    report = json.loads((root / "report.json").read_text())
    assert report["decision"] == "NAIVE_CACHE_MUTABLE_CUSTODY_FALSIFIED"
    assert (root / "reader-git-blob.txt").read_text().strip() == (
        "f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f"
    )
    result = {"schema": "J24I21-third-party-wire-v1", "case_sha": [],
              "mutation_checks": [], "decision": "ORIGINAL_WIRE_AUDIT_PASS"}
    for case in report["cases"]:
        raw = (root / f"source-{case['size']}-{case['aliases']}.cmpct").read_bytes()
        assert len(raw) == case["stored_bytes"] and digest(raw) == case["source_sha256"]
        index, physical, primary, footer = decode_primary(raw, library)
        owners = [row for row in index["files"] if row[1] == 0]
        aliases = [row for row in index["files"] if row[1] == 3]
        assert len(owners) == 1 and len(aliases) == case["aliases"]
        assert owners[0][4] == case["size"] and owners[0][6][0] == 3
        assert all(row[4] == case["size"] and row[6][0] == "a-owner.bin"
                   for row in aliases)
        assert [entry["streamed_sha_calls"] for entry in case["trials"]] == [
            case["aliases"] + 1, 1, 1, case["aliases"] + 1
        ]
        assert all(entry["source_sha_before"] == entry["source_sha_after"]
                   == case["source_sha256"] and entry["accepted"]
                   for entry in case["trials"])
        result["case_sha"].append({"bytes": len(raw), "sha256": digest(raw),
                                   "owner_size": case["size"],
                                   "hardlink_aliases": case["aliases"]})
    original = (root / "source-67108864-32.cmpct").read_bytes()
    index, physical, primary, footer = decode_primary(original, library)
    for record in report["mutation"]:
        data = (root / f"race-{record['mode']}-tampered.cmpct").read_bytes()
        assert len(data) == len(original)
        assert record["source_sha_before"] == digest(original)
        assert record["source_sha_after"] == digest(data)
        diffs = [i for i, (a, b) in enumerate(zip(data, original)) if a != b]
        assert len(diffs) == 1 and diffs[0] == record["tamper"][0]["offset"]
        index2, physical2, primary2, footer2 = decode_primary(data, library)
        assert index2 == index and primary2 == primary and footer2 == footer
        idx = next(row for row in index["files"] if row[1] == 0)[6][1][0][2][0]
        pos = physical[0] + index["blobs"][idx][0]
        magic, codec, flags, reserved, us, cs, ml, crc, sha = BLOB.unpack_from(
            original, pos
        )
        assert magic == b"CMA4"
        payload = pos + BLOB.size + ml
        assert payload <= diffs[0] < payload + cs
        assert data[diffs[0]] == original[diffs[0]] ^ 1
        assert (record["mode"] == "baseline" and not record["accepted"]) or (
            record["mode"] == "cache-oracle" and record["accepted"]
        )
        result["mutation_checks"].append({"mode": record["mode"],
            "changed_byte_offset": diffs[0], "physical_blob_range": [payload, payload + cs],
            "index_and_footer_unchanged": True, "accepted": record["accepted"]})
    assert len(result["mutation_checks"]) == 2
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: physical_audit.py <original-artifact-extracted-directory>")
    main(sys.argv[1])
