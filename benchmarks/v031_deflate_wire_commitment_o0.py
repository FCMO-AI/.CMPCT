#!/usr/bin/env python3
"""O0 research: price an index-authenticated compressed-wire commitment.

NOT a revision-24 format extension. A physical-wire SHA stored in the
independently SHA-bound index could authenticate copied compressed bytes
without inflation at export, but only when the producer first authenticated
the raw Deflate stream at creation. This instrument charges two compressed
index copies and tests hostile physical mutations before any product change.
"""
from __future__ import annotations

import binascii
import hashlib
import json
import random
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import msgpack
from cmpct.codec import BHDR, BMAGIC, CODEC_DEFLATE, zc, sha
from cmpct.reader import CMPCT

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_v031_deflate_export_verified import _archive

HEADER_CRC_OFFSET = struct.calcsize("<4sBBHQQI")
HEADER_SHA_OFFSET = struct.calcsize("<4sBBHQQII")


def _project(reader: CMPCT, idx: int) -> dict:
    off, usize, csize, codec, mlen = reader.blobs[idx]
    assert codec == CODEC_DEFLATE
    offset = reader.record_base + off
    wire = reader.mm[offset:offset + BHDR.size + mlen + csize]
    assert len(wire) == BHDR.size + mlen + csize
    # Real r24 Reader must first check the logical, decompressed identity.
    # This first-time producer work is NOT removed by proposed wire commitment.
    original_name = next(row[0] for row in reader.files if row[6] and row[6][0] == 0)
    assert sha(reader.read(original_name)) == BHDR.unpack_from(wire, 0)[-1]
    wire_sha = hashlib.sha256(wire).digest()
    original_idx = dict(reader.index)
    prospective_idx = dict(original_idx)
    # A *hypothetical* new index record; the existing reader does not consume it.
    prospective_idx["physical_wire_sha256"] = [[idx, wire_sha]]
    original_packed = msgpack.packb(original_idx, use_bin_type=True)
    proposed_packed = msgpack.packb(prospective_idx, use_bin_type=True)
    original_comp = zc(original_packed, 12)
    proposed_comp = zc(proposed_packed, 12)
    physical_index_extra = 2 * (len(proposed_comp) - len(original_comp))
    assert physical_index_extra > 0, "no zero-cost magic added index"
    # Identity of all the physical bytes (header and complete encoded stream) is
    # different under each mutation, while the index-stored digest stays frozen.
    edits = {
        "crc_field": HEADER_CRC_OFFSET,
        "logical_sha_field": HEADER_SHA_OFFSET,
        "deflate_payload": BHDR.size + mlen + csize // 2,
    }
    for name, byte_off in edits.items():
        candidate = bytearray(wire)
        candidate[byte_off] ^= 1
        assert hashlib.sha256(candidate).digest() != wire_sha, name
    assert hashlib.sha256(wire + b"\x00").digest() != wire_sha
    # Null meaning: rejected on source-wire comparison, not proof of compression.
    a, b = [], []
    for order in ("ABBA" * 6):
        start = time.perf_counter_ns()
        if order == "A":
            reader._verify_direct_deflate_blob(idx)
            a.append((time.perf_counter_ns() - start) / 1e6)
        else:
            assert hashlib.sha256(wire).digest() == wire_sha
            b.append((time.perf_counter_ns() - start) / 1e6)
    return {
        "logical_bytes": usize,
        "compressed_stream_bytes": csize,
        "physical_wire_bytes": len(wire),
        "existing_index_zstd_bytes_per_copy": len(original_comp),
        "prospective_index_zstd_bytes_per_copy": len(proposed_comp),
        "complete_two_index_exported_cost_extra_bytes": physical_index_extra,
        "size_extra_over_physical_deflate_pct": round(100 * physical_index_extra / max(csize, 1), 4),
        "median_existing_stream_decompress_and_hash_ms": statistics.median(a),
        "median_prospective_wire_sha_ms": statistics.median(b),
        "observed_ratio_existing_to_wire": round(statistics.median(a) / max(statistics.median(b), 1e-9), 2),
        "raw_time_existing_ms": a,
        "raw_time_wire_ms": b,
        "hostile_physical_mutations_rejected": len(edits) + 1,
        "producer_one_time_plain_authentication": "required and performed using real CMPCT.read()",
    }


def run():
    rng = random.Random(2026102303)
    cases = [
        ("small_text", b"predictable small text line\n" * 256),
        ("shared_text", b"common reusable Deflate payload\n" * 14000),
        ("highly_sparse_zeros_32m", b"\x00" * (32 * 1024 * 1024)),
        ("entropy_4m", rng.randbytes(4 * 1024 * 1024)),
    ]
    with tempfile.TemporaryDirectory(prefix="cmpct-wire-commitment-o0-") as d:
        root = Path(d)
        results = {}
        for name, raw in cases:
            path = root / f"{name}.cmpct"
            _archive(path, raw)
            with CMPCT(path) as reader:
                results[name] = _project(reader, 0)
    artifact = {
        "schema": "cmpct-v031-direct-deflate-wire-index-oracle-o0",
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "reader_blob": subprocess.check_output(["git", "hash-object", "src/cmpct/reader.py"], text=True).strip(),
        "hypothesis": "A per-physical-blob SHA commitment in future authenticated index can verify compressed export bytes without re-inflation",
        "authority": "research only: no shipped index grammar, no current-r24 equivalence, not a release benchmark",
        "decision_boundary": "compare gain versus compressed repeated-index extra, one-time decode-at-create, generic admission and compatibility costs",
        "cases": results,
    }
    print(json.dumps(artifact, indent=2, sort_keys=True))
    folder = Path("deflate-evidence")
    folder.mkdir(exist_ok=True)
    (folder / "wire-commitment-o0.json").write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    run()
