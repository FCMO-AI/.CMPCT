"""ONE-G0.2 fused-observation microbenchmark.

Discovery-only evidence: no compression ratio or product-speed claim. The instrument
measures one forward source scan, exact-verification rereads, candidate opportunity mass,
bounded index payload and Python reference throughput on deterministic regimes.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time
import zlib

from experiments.one.observe import observe

REPETITIONS = 7
SIZE = 1024 * 1024


def _cases() -> dict[str, bytes]:
    random_bytes = random.Random(11).randbytes(SIZE)
    source = random.Random(12).randbytes(64 * 1024)
    repeated = source * (SIZE // len(source))
    version_basis = random.Random(13).randbytes(512 * 1024)
    # A one-byte insertion between otherwise identical versions deliberately changes
    # the alignment of the second copy. Fixed chunks should expose this as a negative
    # result rather than being mistaken for a general resemblance detector.
    shifted_version_pair = version_basis + b"X" + version_basis
    already_compressed = zlib.compress(random.Random(14).randbytes(SIZE), level=9)
    return {
        "random_1mib": random_bytes,
        "zeros_1mib": b"\0" * SIZE,
        "repeated_64k_1mib": repeated,
        "shifted_version_pair_1byte_insert": shifted_version_pair,
        "zlib_random_payload": already_compressed,
        "tiny_random_4k": random.Random(15).randbytes(4096),
    }


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for name, data in _cases().items():
        samples: list[int] = []
        result = None
        for _ in range(REPETITIONS):
            start = time.perf_counter_ns()
            result = observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14)
            samples.append(time.perf_counter_ns() - start)
        assert result is not None
        median_ns = int(statistics.median(samples))
        assert result.stats.source_scan_bytes == len(data)
        rows.append(
            {
                "case": name,
                "input_bytes": len(data),
                "median_ns": median_ns,
                "reference_mib_s": (len(data) / (1024 * 1024)) / (median_ns / 1_000_000_000),
                "source_scan_bytes": result.stats.source_scan_bytes,
                "verification_read_bytes": result.stats.verification_read_bytes,
                "total_source_read_bytes": result.stats.total_source_read_bytes,
                "source_read_amplification": result.stats.total_source_read_bytes / len(data),
                "chunk_fingerprints": result.stats.chunk_fingerprints,
                "hash_lookups": result.stats.hash_lookups,
                "collision_verifications": result.stats.collision_verifications,
                "run_candidates": result.stats.run_candidates,
                "run_opportunity_bytes": result.stats.run_opportunity_bytes,
                "run_opportunity_fraction": result.stats.run_opportunity_bytes / len(data),
                "reuse_candidates": result.stats.reuse_candidates,
                "reuse_opportunity_bytes": result.stats.reuse_opportunity_bytes,
                "reuse_opportunity_fraction": result.stats.reuse_opportunity_bytes / len(data),
                "peak_index_entries": result.stats.peak_index_entries,
                "retained_index_payload_bytes": result.stats.retained_index_payload_bytes,
            }
        )
    return {
        "schema": "cmpct-one-g02-observer-v2",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "claim_boundary": "Python fused-observation discovery evidence only; opportunity bytes are candidates, not saved bytes",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
