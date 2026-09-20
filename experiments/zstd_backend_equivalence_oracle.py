from __future__ import annotations
"""Oracle for issue #176: can the required Python zstandard backend preserve current encoder bytes?

This is research evidence only. It compares the shipping ctypes/system-lib implementation against
`zstandard`, which is already a required project dependency. A mismatch kills transparent backend
substitution for canonical encoding; successful decoding alone is not enough for byte-identity credit.
"""
import hashlib
import json
import random

import zstandard as zstd
from cmpct import codec


def _payloads() -> list[bytes]:
    rng = random.Random(176)
    return [
        b"",
        b"a",
        b"abc" * 1000,
        bytes(range(256)) * 64,
        bytes(rng.randrange(256) for _ in range(65537)),
        (b"structured-record\0" * 8192) + bytes(range(64)) * 128,
    ]


def run() -> dict:
    rows = []
    for level in (1, 3, 9, 19):
        py = zstd.ZstdCompressor(level=level)
        for payload in _payloads():
            system = codec.zc(payload, level)
            packaged = py.compress(payload) if payload else b""
            rows.append({
                "kind": "plain",
                "level": level,
                "input_bytes": len(payload),
                "system_bytes": len(system),
                "python_bytes": len(packaged),
                "byte_identical": system == packaged,
                "system_sha256": hashlib.sha256(system).hexdigest(),
                "python_sha256": hashlib.sha256(packaged).hexdigest(),
                "cross_decode_ok": (not payload) or zstd.ZstdDecompressor().decompress(system) == payload,
            })
    return {
        "schema": "cmpct-zstd-backend-equivalence-v1",
        "system_zstd_version": int(codec._z.ZSTD_versionNumber()) if hasattr(codec._z, "ZSTD_versionNumber") else None,
        "python_zstd_version": zstd.ZSTD_VERSION,
        "rows": rows,
        "all_plain_byte_identical": all(row["byte_identical"] for row in rows),
        "all_cross_decode_ok": all(row["cross_decode_ok"] for row in rows),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["all_cross_decode_ok"]:
        raise SystemExit("cross-decode failed")
    if not result["all_plain_byte_identical"]:
        raise SystemExit("transparent Python-zstandard encoder substitution is not byte-identical")
