#!/usr/bin/env python3
"""Deterministic charged-traffic falsifier for ONE-G0.2 fused observation caching.

The cache only matters if it removes enough observation work to pay for everything it
adds.  This benchmark therefore refuses to score `feature_recompute_bytes` alone.  It
charges, for each creation path:

* current-content SHA validation reads;
* changed-block fused-feature recomputation reads;
* cache integrity SHA input bytes (verify + build, from the independent ledger);
* cached feature payload reads;
* exact current-byte reuse-proof reads.

The result is a deterministic byte-traffic lower-bound, not a CPU-time equivalence model:
SHA work, Python object traffic and the fused byte loop do not cost one cycle per byte.
The purpose is to kill cache shapes whose claimed savings disappear even before wall-time
measurement.  Exact observation equivalence against a from-scratch oracle is mandatory.

Reader-visible ONE bytes and semantics are unaffected; this is writer-side ONE-07
research instrumentation only.
"""
from __future__ import annotations

import hashlib
import json
import random
import zlib

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.fused_cache_cost_ledger import audit_integrity_cost

BLOCK_SIZE = 4096
CHUNK_SIZE = 64
MIN_RUN = 8
SIZES = (4 * 1024, 256 * 1024, 1024 * 1024)


def _structured(size: int) -> bytes:
    pattern = (
        b"A" * 96
        + bytes((index * 73 + 19) & 0xFF for index in range(2048))
        + b"B" * 128
        + bytes((index * 151 + 11) & 0xFF for index in range(1792))
        + b"C" * 32
    )
    repeats, remainder = divmod(size, len(pattern))
    return pattern * repeats + pattern[:remainder]


def _incompressible(size: int) -> bytes:
    rng = random.Random(0xC0DEC7 + size)
    return bytes(rng.randrange(256) for _ in range(size))


def _compressed_like(size: int) -> bytes:
    # Deterministic high-entropy-ish bytes produced by a mature entropy-coded format,
    # repeated only as needed to keep the requested root size exact.
    seed = _structured(max(size, 64 * 1024))
    blob = zlib.compress(seed, level=9)
    material = hashlib.sha256(blob).digest() + blob
    repeats, remainder = divmod(size, len(material))
    return material * repeats + material[:remainder]


FAMILIES = {
    "structured": _structured,
    "incompressible": _incompressible,
    "compressed_like": _compressed_like,
}


def _charged_traffic(result, *, previous=None) -> dict[str, int]:
    ledger = audit_integrity_cost(result, previous=previous)
    stats = result.stats
    total = (
        stats.validation_read_bytes
        + stats.feature_recompute_bytes
        + ledger.charged_hash_bytes
        + stats.cache_feature_payload_read_bytes
        + stats.verification_read_bytes
    )
    return {
        "validation_read_bytes": stats.validation_read_bytes,
        "feature_recompute_bytes": stats.feature_recompute_bytes,
        "integrity_hash_input_bytes": ledger.charged_hash_bytes,
        "cache_feature_payload_read_bytes": stats.cache_feature_payload_read_bytes,
        "exact_verification_read_bytes": stats.verification_read_bytes,
        "charged_traffic_bytes": total,
        "recomputed_blocks": stats.recomputed_blocks,
        "reused_blocks": stats.reused_blocks,
        "persistent_payload_bytes": stats.persistent_payload_bytes,
    }


def _equivalent(candidate, oracle) -> bool:
    return candidate.observation == oracle.observation


def _row(family: str, size: int) -> dict[str, object]:
    source = FAMILIES[family](size)
    fresh = observe_incremental(
        source, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE, min_run=MIN_RUN
    )
    fresh_cost = _charged_traffic(fresh)

    repeat = observe_incremental(
        source,
        previous=fresh.cache,
        block_size=BLOCK_SIZE,
        chunk_size=CHUNK_SIZE,
        min_run=MIN_RUN,
    )
    repeat_oracle = observe_incremental(
        source, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE, min_run=MIN_RUN
    )
    repeat_cost = _charged_traffic(repeat, previous=fresh.cache)

    sparse_bytes = bytearray(source)
    sparse_bytes[len(sparse_bytes) // 2] ^= 0xA5
    sparse_source = bytes(sparse_bytes)
    sparse = observe_incremental(
        sparse_source,
        previous=fresh.cache,
        block_size=BLOCK_SIZE,
        chunk_size=CHUNK_SIZE,
        min_run=MIN_RUN,
    )
    sparse_oracle = observe_incremental(
        sparse_source, block_size=BLOCK_SIZE, chunk_size=CHUNK_SIZE, min_run=MIN_RUN
    )
    sparse_cost = _charged_traffic(sparse, previous=fresh.cache)
    sparse_fresh_cost = _charged_traffic(sparse_oracle)

    repeat_ratio = repeat_cost["charged_traffic_bytes"] / fresh_cost["charged_traffic_bytes"]
    sparse_ratio = (
        sparse_cost["charged_traffic_bytes"] / sparse_fresh_cost["charged_traffic_bytes"]
    )
    return {
        "family": family,
        "input_bytes": size,
        "input_sha256": hashlib.sha256(source).hexdigest(),
        "blocks": len(fresh.cache.blocks),
        "fresh": fresh_cost,
        "exact_repeat": repeat_cost,
        "one_byte_sparse_edit": sparse_cost,
        "one_byte_sparse_fresh_oracle": sparse_fresh_cost,
        "exact_repeat_oracle_equal": _equivalent(repeat, repeat_oracle),
        "sparse_edit_oracle_equal": _equivalent(sparse, sparse_oracle),
        "exact_repeat_charged_ratio": repeat_ratio,
        "sparse_edit_charged_ratio": sparse_ratio,
    }


def main() -> int:
    rows = [_row(family, size) for family in FAMILIES for size in SIZES]
    failures: list[str] = []

    for row in rows:
        label = f"{row['family']}:{row['input_bytes']}"
        if not row["exact_repeat_oracle_equal"]:
            failures.append(f"{label}: exact-repeat observation diverged from fresh oracle")
        if not row["sparse_edit_oracle_equal"]:
            failures.append(f"{label}: sparse-edit observation diverged from fresh oracle")

        # This is deliberately a strong pre-wall-time gate. If an exact repeat cannot
        # remove at least 20% of this charged byte-traffic lower-bound, the cache is too
        # weak to justify more expensive timing promotion work in this shape.
        if row["exact_repeat_charged_ratio"] > 0.80:
            failures.append(
                f"{label}: exact-repeat charged traffic {row['exact_repeat_charged_ratio']:.6f}x > 0.80x"
            )

        # A one-byte edit should still localize feature recomputation strongly enough to
        # buy at least 15% charged-traffic reduction versus from-scratch observation.
        if row["sparse_edit_charged_ratio"] > 0.85:
            failures.append(
                f"{label}: sparse-edit charged traffic {row['sparse_edit_charged_ratio']:.6f}x > 0.85x"
            )

        sparse = row["one_byte_sparse_edit"]
        if sparse["recomputed_blocks"] != 1:
            failures.append(
                f"{label}: one-byte edit recomputed {sparse['recomputed_blocks']} blocks, expected 1"
            )

    payload = {
        "experiment": "ONE-G0.2 fused observation cache charged-traffic economics",
        "interpretation": (
            "deterministic byte-traffic lower-bound only; passing does not prove CPU/wall-time benefit"
        ),
        "block_size": BLOCK_SIZE,
        "chunk_size": CHUNK_SIZE,
        "min_run": MIN_RUN,
        "gates": {
            "exact_repeat_charged_ratio_max": 0.80,
            "one_byte_sparse_edit_charged_ratio_max": 0.85,
            "sparse_recomputed_blocks": 1,
            "fresh_oracle_equivalence_required": True,
        },
        "rows": rows,
        "failures": failures,
        "passed": not failures,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
