#!/usr/bin/env python3
"""J24I36: keep three frozen independent r24 direct-codec vectors byte-exact.

This is a test *generator*, not an oracle. The detached audit runs separately
without CMPCT imports. Source vectors cannot be regenerated or edited.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
from pathlib import Path

from cmpct.reader import CMPCT

H = struct.Struct("<8sHHQQQ32s")
B = struct.Struct("<4sBBHQQII32s")
EXPECTED = {"raw.bin": 0, "zstd.txt": 1, "deflate.txt": 4}


def observe(path: Path) -> dict:
    try:
        with CMPCT(path) as reader:
            count = reader.verify()
        return {"accepted": True, "verified": count}
    except Exception as exc:
        return {"accepted": False, "error": type(exc).__name__ + ": " + str(exc)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(args.vectors.read_text())
    assert fixture["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    assert {v["name"] for v in fixture["vectors"]} == set(EXPECTED)
    results = []
    for vector in fixture["vectors"]:
        name = vector["name"]
        codec = EXPECTED[name]
        original = base64.b64decode(vector["archive_base64"], validate=True)
        assert len(original) == vector["archive_bytes"]
        assert hashlib.sha256(original).hexdigest() == vector["archive_sha256"]
        magic, version, flags, index_csize, _, span, _ = H.unpack_from(original)
        assert (magic, version, flags) == (b"CMPCT24" + bytes([0]), 24, 0)
        record = H.size + index_csize
        blob = B.unpack_from(original, record)
        assert blob[0] == b"CMA4" and blob[1] == codec
        assert record + B.size + blob[6] + blob[5] <= len(original)
        assert span == B.size + blob[6] + blob[5]
        crc_offset = record + 28
        changed = bytearray(original)
        changed[crc_offset] ^= 1
        mutated = bytes(changed)
        assert sum(x != y for x, y in zip(original, mutated)) == 1
        stem = name.split(".")[0]
        original_path = args.output / (stem + "-original.cmpct")
        changed_path = args.output / (stem + "-crc-wrong.cmpct")
        original_path.write_bytes(original)
        changed_path.write_bytes(mutated)
        original_result = observe(original_path)
        changed_result = observe(changed_path)
        assert original_result == {"accepted": True, "verified": 1}, (name, original_result)
        assert not changed_result["accepted"], (name, changed_result)
        assert "integrity" in changed_result["error"].lower(), (name, changed_result)
        results.append({
            "source_name": name,
            "source_codec": codec,
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "crc_only_sha256": hashlib.sha256(mutated).hexdigest(),
            "crc_field_offset": crc_offset,
            "index_and_footer_unchanged": True,
            "original_python": original_result,
            "mutated_python": changed_result,
        })
    output = {"schema": "j24i36-frozen-direct-crc-generator-v1", "results": results}
    (args.output / "python-observations.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
