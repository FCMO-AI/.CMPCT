from __future__ import annotations
"""Platform-neutral fingerprint for the proposed #176 Python-zstandard backend."""
import hashlib
import json
import random
import zstandard as zstd

rng = random.Random(176)
payloads = [
    b"a",
    b"abc" * 1000,
    bytes(range(256)) * 64,
    bytes(rng.randrange(256) for _ in range(65537)),
    (b"structured-record\0" * 8192) + bytes(range(64)) * 128,
]
dictionary = (b"alpha beta gamma delta structured-record\0" * 128)[:4096]
d = zstd.ZstdCompressionDict(dictionary, dict_type=zstd.DICT_TYPE_RAWCONTENT)
rows = []
for level in (1, 3, 9, 19):
    plain = zstd.ZstdCompressor(level=level)
    rawdict = zstd.ZstdCompressor(level=level, dict_data=d)
    for i, payload in enumerate(payloads):
        for kind, encoded in (("plain", plain.compress(payload)), ("raw-dictionary", rawdict.compress(payload))):
            rows.append({"kind": kind, "level": level, "payload": i, "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()})
print(json.dumps({"schema": "cmpct-python-zstd-platform-fingerprint-v1", "zstd_version": zstd.ZSTD_VERSION, "rows": rows}, sort_keys=True))
