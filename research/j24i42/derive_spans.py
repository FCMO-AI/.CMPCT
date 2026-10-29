#!/usr/bin/env python3
"""J24I42 detached physical span derivation, never imports CMPCT.

Consumes the *unchanged* J24I38 Builder physical/audit fixtures plus J24I39
split artifacts. No reinterpretation of a changed archive is allowed as truth.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOT = struct.Struct("<8sBBBBQQQ32s")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", type=Path, required=True)
    opts = ap.parse_args()
    root = opts.case_dir
    m = json.loads((root / "manifest.json").read_text())
    audit = json.loads((root / "detached-audit.json").read_text())
    split = json.loads((root / "stream-manifest.json").read_text())
    assert m["schema"] == "j24i38-builder-wav-flac-v1"
    assert audit["result"] == "PASS" and audit["independent_of_cmpct_import"] is True
    assert split["schema"] == "j24i39-independent-split-v1"
    result = {"schema": "j24i42-audited-original-container-ranges-v1", "records": {}}
    for mib in (8, 32):
        old = m["records"][str(mib)]
        previous = split["records"][str(mib)]
        path = root / f"builder-wav-{mib}m.cmpct"
        raw = path.read_bytes()
        assert digest(raw) == old["archive_sha256"] == previous["archive_sha256"]
        magic, rev, flags, cs, us, span, idxsha = HEADER.unpack_from(raw, 0)
        assert (magic, rev, flags) == (b"CMPCT24\x00", 24, 0)
        offset = HEADER.size + cs
        bmag, codec, bflags, reserved, logical, encoded, metadata_size, crc, sha = BLOB.unpack_from(raw, offset)
        assert (bmag, codec, bflags, reserved) == (b"CMA4", 2, 0, 0)
        assert logical == old["logical_bytes"] and encoded == old["encoded_bytes"]
        assert sha.hex() == old["payload_sha256"] and crc == old["crc32"]
        assert span == BLOB.size + metadata_size + encoded
        meta_offset = offset + BLOB.size
        encoded_offset = meta_offset + metadata_size
        assert encoded_offset + encoded == offset + span
        # Validate the complete tail; the bounded stream must not consume it.
        assert raw[offset+span:offset+span+cs] == raw[HEADER.size:HEADER.size+cs]
        assert FOOT.unpack_from(raw, offset+span+cs) == (
            b"CMPTF24\x00", 0, 1, 0, 0, cs, us, 0, idxsha
        )
        assert offset+span+cs+FOOT.size == len(raw)
        metadata = raw[meta_offset:encoded_offset]
        payload = raw[encoded_offset:encoded_offset+encoded]
        assert payload[:4] == b"fLaC" and encoded > 64
        assert digest(metadata) == previous["meta_sha256"]
        assert digest(payload) == previous["flac_sha256"]
        assert (root / previous["meta_path"]).read_bytes() == metadata
        assert (root / previous["flac_path"]).read_bytes() == payload
        corrupted = bytearray(raw)
        corrupted[encoded_offset] ^= 0x01
        assert corrupted[encoded_offset:encoded_offset+4] != b"fLaC"
        corrupt_path = root / f"badmagic-original-container-{mib}m.cmpct"
        corrupt_path.write_bytes(corrupted)
        assert corrupted[:encoded_offset] == raw[:encoded_offset]
        assert corrupted[encoded_offset+1:] == raw[encoded_offset+1:]
        result["records"][str(mib)] = {
            "archive_path": path.name, "archive_sha256": digest(raw),
            "metadata_path": previous["meta_path"],
            "metadata_sha256": digest(metadata),
            "encoded_offset": encoded_offset, "encoded_bytes": encoded,
            "encoded_sha256": digest(payload),
            "logical_bytes": logical, "logical_sha256": sha.hex(),
            "logical_crc32": crc, "corrupt_path": corrupt_path.name,
            "corrupt_archive_sha256": digest(corrupted),
            "mutation_offset": encoded_offset, "mutation_xor": 1,
            "range_end_before_tail_index": encoded_offset + encoded == offset + span,
        }
    (root / "bounded-container-manifest.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print(json.dumps({"schema": result["schema"], "status": "PASS",
                      "records": result["records"]}, sort_keys=True))


if __name__ == "__main__":
    main()
