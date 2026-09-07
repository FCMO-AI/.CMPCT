#!/usr/bin/env python3
"""Deterministic resource audit for ONE-G0.2 fused observation-cache integrity work.

This is not a wall-time benchmark.  It measures SHA-256 input bytes that must be charged
for cached-state verification *and* for creation of fresh/recomputed cache seals, using an
independent ledger.  It is intentionally deterministic so hosted CI can expose accounting
regressions without scheduler noise.
"""
from __future__ import annotations

import json

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.fused_cache_cost_ledger import audit_integrity_cost

BLOCK_SIZE = 4096
CHUNK_SIZE = 64
MIN_RUN = 8
SIZES = (256 * 1024, 1024 * 1024)


def _source(size: int) -> bytes:
    # Mix structured runs and deterministic high-entropy-ish regions so the fused cached
    # payload contains real fingerprints/run metadata rather than one trivial shape.
    pattern = (
        b"A" * 96
        + bytes((index * 73 + 19) & 0xFF for index in range(2048))
        + b"B" * 128
        + bytes((index * 151 + 11) & 0xFF for index in range(1792))
        + b"C" * 32
    )
    repeats, remainder = divmod(size, len(pattern))
    return pattern * repeats + pattern[:remainder]


def _row(size: int) -> dict[str, object]:
    source = _source(size)
    fresh = observe_incremental(
        source, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE, min_run=MIN_RUN
    )
    fresh_ledger = audit_integrity_cost(fresh)

    repeat = observe_incremental(
        source,
        previous=fresh.cache,
        block_size=BLOCK_SIZE,
        chunk_size=CHUNK_SIZE,
        min_run=MIN_RUN,
    )
    repeat_ledger = audit_integrity_cost(repeat, previous=fresh.cache)

    sparse_bytes = bytearray(source)
    sparse_bytes[len(sparse_bytes) // 2] ^= 0xA5
    sparse = observe_incremental(
        bytes(sparse_bytes),
        previous=fresh.cache,
        block_size=BLOCK_SIZE,
        chunk_size=CHUNK_SIZE,
        min_run=MIN_RUN,
    )
    sparse_ledger = audit_integrity_cost(sparse, previous=fresh.cache)

    return {
        "input_bytes": size,
        "blocks": len(fresh.cache.blocks),
        "fresh": fresh_ledger.__dict__,
        "exact_repeat": repeat_ledger.__dict__,
        "one_byte_sparse_edit": sparse_ledger.__dict__,
    }


def main() -> int:
    rows = [_row(size) for size in SIZES]
    # Scientific gate: the independent charge must never be below reconstructed work;
    # exact repeat must perform no seal-build work; sparse edit must expose both kinds.
    failures: list[str] = []
    for row in rows:
        fresh = row["fresh"]
        repeat = row["exact_repeat"]
        sparse = row["one_byte_sparse_edit"]
        assert isinstance(fresh, dict) and isinstance(repeat, dict) and isinstance(sparse, dict)
        if fresh["charged_hash_bytes"] < fresh["expected_total_hash_bytes"]:
            failures.append(f"{row['input_bytes']}: fresh undercharge")
        if repeat["expected_build_hash_bytes"] != 0:
            failures.append(f"{row['input_bytes']}: repeat unexpectedly builds seals")
        if sparse["expected_build_hash_bytes"] <= 0 or sparse["expected_verify_hash_bytes"] <= 0:
            failures.append(f"{row['input_bytes']}: sparse edit missing build/verify split")
        if sparse["charged_hash_bytes"] < sparse["expected_total_hash_bytes"]:
            failures.append(f"{row['input_bytes']}: sparse undercharge")

    payload = {
        "experiment": "ONE-G0.2 fused observation cache integrity ledger",
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "min_run": MIN_RUN,
        "rows": rows,
        "failures": failures,
        "passed": not failures,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
