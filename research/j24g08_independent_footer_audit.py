#!/usr/bin/env python3
"""Independent J24G08 physical archive footer/ancestry/receipt audit.

No cmpct package imports. Parses r24 framing from standard struct plus libzstd C ABI.
This checks signed metadata/physical bytes; it does not reimplement logical Reader.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPCT24\x00"
FMAGIC = b"CMPTF24\x00"


def h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


LIB = ctypes.CDLL(ctypes.util.find_library("zstd"))
LIB.ZSTD_decompress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t
]
LIB.ZSTD_decompress.restype = ctypes.c_size_t
LIB.ZSTD_isError.argtypes = [ctypes.c_size_t]
LIB.ZSTD_isError.restype = ctypes.c_uint


def decompress(raw: bytes, expected: int) -> bytes:
    src = ctypes.create_string_buffer(raw)
    out = ctypes.create_string_buffer(expected)
    n = LIB.ZSTD_decompress(out, expected, src, len(raw))
    assert not LIB.ZSTD_isError(n) and n == expected, ("invalid zstd", n)
    return out.raw[:n]


def examine(zip_path: Path) -> dict:
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None, "artifact CRC failed"
        man_raw = z.read("manifest.json")
        man = json.loads(man_raw)
        cache = json.loads(z.read("cache.json"))
        guard = json.loads(z.read("o10r.json"))
        decision = json.loads(z.read("decision.json"))
        assert cache["physical_manifest_sha256"] == guard["physical_manifest_sha256"] == h(man_raw)
        assert man["format"] == "r24" and man["physical_archive_generated_once"] is True
        specs = man["cases"]
        assert len(specs) == 7
        seen = {}
        auth = 0
        for spec in specs:
            path = "specimens/" + spec["path"]
            raw = z.read(path)
            assert h(raw) == spec["physical_sha256"] and len(raw) == spec["physical_bytes"]
            assert HDR.unpack_from(raw)[0] == MAGIC
            positions = []
            scan = 0
            while True:
                pos = raw.find(FMAGIC, scan)
                if pos < 0:
                    break
                assert pos + FTR.size <= len(raw)
                magic, kind, codec, flags, res, cs, us, prev, digest = FTR.unpack_from(raw, pos)
                assert (magic, flags, res) == (FMAGIC, 0, 0)
                assert kind in (0, 1) and codec in (0, 1) and cs <= pos
                encoded = raw[pos-cs:pos]
                payload = encoded if codec == 0 else decompress(encoded, us)
                assert len(payload) == us and hashlib.sha256(payload).digest() == digest
                assert prev == 0 or prev < pos
                positions.append((pos, kind, prev, cs))
                scan = pos + len(FMAGIC)
            assert positions and man["first_committed_footer"] in {p[0] for p in positions}
            assert all(prev == 0 or prev in {p[0] for p in positions} for _, _, prev, _ in positions)
            if spec["family"] == "committed":
                assert len(positions) == spec["depth"] + 1
                assert positions[0][1] == 0 and all(p[1] == 1 for p in positions[1:])
                assert all(b[2] == a[0] for a, b in zip(positions, positions[1:]))
            else:
                count = 4 if "4" == spec["name"].replace("orphan", "") else 140
                assert len(positions) == count + 2
                assert raw.startswith(z.read("specimens/valid1.cmpct"))
                if spec["family"] == "chained-orphan":
                    assert positions[-count][2] == 0
                    assert all(b[2] == a[0] for a, b in zip(positions[-count:-1], positions[-count+1:]))
                    assert all(p[3] == 13 for p in positions[-count:])
                else:
                    assert all(p[2] == 0 for p in positions[-count:])
            if path not in seen:
                auth += len(positions)
            seen[path] = {"sha256": h(raw), "bytes": len(raw), "sha_authenticated_footers": len(positions)}
        assert len(seen) == 6 and auth == 299
        a = {row["case"]: row for row in cache["cases"]}
        b = {row["case"]: row for row in guard["cases"]}
        assert a.keys() == b.keys() == {row["name"] for row in specs}
        for row in specs:
            n = row["name"]
            assert a[n]["physical_sha256"] == b[n]["physical_sha256"] == row["physical_sha256"]
            if a[n]["result"] == "RECOVERED":
                assert a[n]["logical_sha256"] == man["logical_sha256"]
        for n in ("orphan4", "orphan140"):
            assert a[n]["result"] == "RECOVERED" and a[n]["selected_footer"] == man["first_committed_footer"]
            assert b[n]["result"] == "RAISED" and b[n]["exception_type"] == "ResourceLimitError"
        assert a["orphan140_loose"]["decode_calls"] == 142
        assert b["orphan140_loose"]["decode_calls"] == 9872
        assert decision["decision"] == "O10R_DEPTH_LIMIT_KILLS_OLDER_COMMITTED_FALLBACK_ON_ORPHAN_TAIL"
        assert cache["release_credit"] == guard["release_credit"] == 0
        return {
            "status": "INDEPENDENT_PHYSICAL_FOOTER_AUDIT_PASS",
            "artifact_zip_sha256": h(zip_path.read_bytes()),
            "unique_physical_archives": len(seen),
            "sha_authenticated_footer_records": auth,
            "specimens": seen,
            "scope": "physical r24 SHA, ancestry, exact-file receipts; independent logical reconstruction unmeasured",
            "product_source_mutated": False, "release_credit": 0,
        }


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    result = examine(input_path)
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
