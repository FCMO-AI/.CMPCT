#!/usr/bin/env python3
"""Real CMPCT verifier differential on synthetic r24 physical Deflate records.

This court calls the *installed* CMPCT._verify_direct_deflate_blob implementation.
The independent control uses stdlib zlib.decompress and raw-content CRC/SHA,
never the method under test. It does not claim full Reader/archive product semantics.
"""
from __future__ import annotations

import binascii
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time
import tracemalloc
import zlib

from cmpct.codec import BHDR, BMAGIC, CODEC_DEFLATE
from cmpct.reader import CMPCT


def _physical_candidate(raw, comp, crc=None, digest=None):
    crc = (binascii.crc32(raw) & 0xffffffff) if crc is None else crc
    digest = hashlib.sha256(raw).digest() if digest is None else digest
    header = BHDR.pack(BMAGIC, CODEC_DEFLATE, 0, 0, len(raw), len(comp), 0, crc, digest)
    obj = object.__new__(CMPCT)
    obj.mm = memoryview(header + comp)
    obj.record_base = 0
    obj.blobs = [[0, len(raw), len(comp), CODEC_DEFLATE, 0]]
    return obj


def _must_fail(candidate):
    try:
        candidate._verify_direct_deflate_blob(0)
    except (IOError, zlib.error):
        return
    raise AssertionError("malformed physical direct-Deflate stream accepted")


def run():
    rng = random.Random(2026102302)
    strategies = [
        zlib.Z_DEFAULT_STRATEGY, zlib.Z_FILTERED, zlib.Z_HUFFMAN_ONLY,
        zlib.Z_RLE, zlib.Z_FIXED,
    ]
    accepted = rejected = 0
    start = time.perf_counter()
    for i in range(768):
        length = rng.randrange(0, 90_000)
        kind = i % 6
        if kind == 0:
            raw = rng.randbytes(length)
        elif kind == 1:
            raw = b"\0" * length
        elif kind == 2:
            raw = (b"record/geometry/" * ((length + 15) // 16))[:length]
        elif kind == 3:
            raw = (bytes(range(256)) * ((length + 255) // 256))[:length]
        elif kind == 4:
            raw = bytes([rng.randrange(256)]) * length
        else:
            raw = (rng.randbytes(8) * ((length + 7) // 8))[:length]
        level = rng.randrange(0, 10)
        codec = zlib.compressobj(level, zlib.DEFLATED, -15, 8, strategies[i % len(strategies)])
        comp = codec.compress(raw) + codec.flush()
        assert zlib.decompress(comp, -15) == raw, "independent decoded content"
        _physical_candidate(raw, comp)._verify_direct_deflate_blob(0)
        accepted += 1
        _must_fail(_physical_candidate(raw, comp + b"\x00"))
        _must_fail(_physical_candidate(raw, comp + comp))
        _must_fail(_physical_candidate(raw, comp[:-1]))
        _must_fail(_physical_candidate(raw, comp, crc=(binascii.crc32(raw) ^ 1) & 0xffffffff))
        bad_sha = hashlib.sha256(raw).digest()
        _must_fail(_physical_candidate(raw, comp, digest=bytes([bad_sha[0] ^ 1]) + bad_sha[1:]))
        rejected += 5

    raw = b"\0" * (64 * 1024 * 1024)
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    comp = co.compress(raw) + co.flush()
    candidate = _physical_candidate(raw, comp)
    del raw
    tracemalloc.start()
    try:
        candidate._verify_direct_deflate_blob(0)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 8 * 1024 * 1024, f"expanded 64MiB member requires {peak} B"
    result = {
        "schema": "cmpct-v031-physical-deflate-differential-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_reader_blob": subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip(),
        "independent_zlib_valid_cases": accepted,
        "physical_invalid_cases_rejected": rejected,
        "expanded_logical_case": 64 * 1024 * 1024,
        "expanded_deflate_bytes": len(comp),
        "peak_tracemalloc_bytes": peak,
        "wall_seconds_including_case_generation": round(time.perf_counter() - start, 3),
        "scope": "source-exact physical method micro/differential; not complete product benchmark",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    out = Path("deflate-evidence")
    out.mkdir(exist_ok=True)
    (out / "physical-differential.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    run()
