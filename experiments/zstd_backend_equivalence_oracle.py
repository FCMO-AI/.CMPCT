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
    payloads = _payloads()
    for level in (1, 3, 9, 19):
        py = zstd.ZstdCompressor(level=level)
        for payload in payloads:
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

    dictionary = (b"alpha beta gamma delta structured-record\0" * 128)[:4096]
    py_dict = zstd.ZstdCompressionDict(dictionary, dict_type=zstd.DICT_TYPE_RAWCONTENT)
    for level in (1, 3, 9, 19):
        py = zstd.ZstdCompressor(level=level, dict_data=py_dict)
        decoder = zstd.ZstdDecompressor(dict_data=py_dict)
        for payload in payloads[1:]:
            system = codec.zcd(payload, dictionary, level)
            packaged = py.compress(payload)
            rows.append({
                "kind": "raw-dictionary",
                "level": level,
                "input_bytes": len(payload),
                "dictionary_bytes": len(dictionary),
                "system_bytes": len(system),
                "python_bytes": len(packaged),
                "byte_identical": system == packaged,
                "system_sha256": hashlib.sha256(system).hexdigest(),
                "python_sha256": hashlib.sha256(packaged).hexdigest(),
                "cross_decode_ok": decoder.decompress(system) == payload,
            })

    plain = [row for row in rows if row["kind"] == "plain"]
    dictionaries = [row for row in rows if row["kind"] == "raw-dictionary"]
    return {
        "schema": "cmpct-zstd-backend-equivalence-v2",
        "system_zstd_version": int(codec._z.ZSTD_versionNumber()) if hasattr(codec._z, "ZSTD_versionNumber") else None,
        "python_zstd_version": zstd.ZSTD_VERSION,
        "rows": rows,
        "all_plain_byte_identical": all(row["byte_identical"] for row in plain),
        "all_dictionary_byte_identical": all(row["byte_identical"] for row in dictionaries),
        "all_cross_decode_ok": all(row["cross_decode_ok"] for row in rows),
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["all_cross_decode_ok"]:
        raise SystemExit("cross-decode failed")
    if not result["all_plain_byte_identical"]:
        raise SystemExit("transparent Python-zstandard plain encoder substitution is not byte-identical")
    if not result["all_dictionary_byte_identical"]:
        raise SystemExit("transparent Python-zstandard dictionary encoder substitution is not byte-identical")
