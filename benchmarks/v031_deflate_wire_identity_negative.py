#!/usr/bin/env python3
"""Independently distinguish logical verification from physical stream identity.

Two SAME-LENGTH raw RFC-1951 streams can decode to identical plaintext, CRC32,
SHA-256 and logical bytes. Revision-24 commits only the logical SHA in BHDR,
so a validator recomputing that plaintext identity MUST accept either wire
encoding. This is a contract-boundary falsifier, not a logical integrity bug.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

from cmpct.codec import BHDR, BMAGIC, LFH
from cmpct.reader import CMPCT

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_v031_deflate_export_verified import _archive, _exported_stream


def run():
    raw = b"a" * 512
    co9 = zlib.compressobj(9, zlib.DEFLATED, -15)
    raw9 = co9.compress(raw) + co9.flush()
    co1 = zlib.compressobj(1, zlib.DEFLATED, -15)
    raw1 = co1.compress(raw) + co1.flush()
    assert raw9 != raw1 and len(raw9) == len(raw1) == 8
    assert zlib.decompress(raw9, -15) == zlib.decompress(raw1, -15) == raw
    with tempfile.TemporaryDirectory(prefix="cmpct-wire-identity-negative-") as d:
        root = Path(d)
        original = root / "source.cmpct"
        target_original = root / "original.zip"
        target_alt = root / "alternate.zip"
        assert _archive(original, raw) == raw9
        with CMPCT(original) as r:
            assert r.verify() == 1
            r._verify_direct_deflate_blob(0)
            r.export_zip(target_original)
        data = bytearray(original.read_bytes())
        pos = data.index(BMAGIC)
        m, c, flags, res, usize, csize, msize, crc, plaintext_sha = BHDR.unpack_from(data, pos)
        assert usize == 512 and csize == 8 and msize == 0
        payload_off = pos + BHDR.size
        assert data[payload_off:payload_off + csize] == raw9
        data[payload_off:payload_off + csize] = raw1
        original.write_bytes(data)
        with CMPCT(original) as r:
            assert r.verify() == 1, "logical contents remain byte-exact"
            r._verify_direct_deflate_blob(0)
            r.export_zip(target_alt)
        copied_9 = _exported_stream(target_original, "member.txt")
        copied_1 = _exported_stream(target_alt, "member.txt")
        assert copied_9 == raw9 and copied_1 == raw1 and copied_9 != copied_1
        with zipfile.ZipFile(target_original) as a, zipfile.ZipFile(target_alt) as b:
            assert a.read("member.txt") == b.read("member.txt") == raw
        result = {
            "schema": "cmpct-v031-equal-plaintext-different-deflate-wire-v1",
            "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "reader_blob": subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip(),
            "sha256_logical": hashlib.sha256(raw).hexdigest(),
            "same_physical_encoded_length": len(raw9),
            "source_wire_level9": raw9.hex(),
            "mutated_wire_level1": raw1.hex(),
            "independent_zip_logical_identity": "PASS",
            "cmpct_verify_both": "PASS",
            "retained_physical_streams_differ": copied_9 != copied_1,
            "decision": "LOGICAL_INTEGRITY_DOES_NOT_COMMIT_RFC1951_PHYSICAL_IDENTITY",
            "scope": "expected revision-24 semantic boundary; not an archive logical corruption vulnerability",
        }
    print(json.dumps(result, sort_keys=True, indent=2))
    evidence = Path("deflate-evidence")
    evidence.mkdir(exist_ok=True)
    (evidence / "same-plaintext-wire-falsifier.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )


if __name__ == "__main__":
    run()
