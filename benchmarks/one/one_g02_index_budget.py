"""ONE-G0.2 fixed-reuse index budget sweep.

The fixed-chunk observer is a cheap first-stage signal, not the whole discovery system.
This instrument measures how much reusable-byte opportunity it earns per retained index
payload as the cap changes. It is designed to expose whether a small cheap near-range
stage plus a sparse content-defined long-range stage is preferable to a large universal
fixed index.
"""
from __future__ import annotations

import json
import os
import random

from experiments.one.observe import observe

CHUNK = 64
CAPS = (256, 1024, 4096, 16384)
SIZE = 1024 * 1024


def _cases() -> dict[str, bytes]:
    return {
        "random_1mib": random.Random(21).randbytes(SIZE),
        "repeat_basis_16k": random.Random(22).randbytes(16 * 1024) * 64,
        "repeat_basis_64k": random.Random(23).randbytes(64 * 1024) * 16,
        "repeat_basis_256k": random.Random(24).randbytes(256 * 1024) * 4,
        "exact_pair_512k": (lambda b: b + b)(random.Random(25).randbytes(512 * 1024)),
    }


def run() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case, data in _cases().items():
        for cap in CAPS:
            result = observe(data, min_run=8, chunk_size=CHUNK, max_index_entries=cap)
            s = result.stats
            rows.append({
                "case": case,
                "cap_entries": cap,
                "input_bytes": len(data),
                "retained_entries": s.peak_index_entries,
                "retained_index_payload_bytes": s.retained_index_payload_bytes,
                "reuse_candidates": s.reuse_candidates,
                "reuse_opportunity_bytes": s.reuse_opportunity_bytes,
                "reuse_opportunity_fraction": s.reuse_opportunity_bytes / len(data),
                "opportunity_bytes_per_retained_payload_byte": (
                    s.reuse_opportunity_bytes / s.retained_index_payload_bytes
                    if s.retained_index_payload_bytes
                    else 0.0
                ),
                "verification_read_bytes": s.verification_read_bytes,
                "total_source_read_bytes": s.total_source_read_bytes,
            })
    return {
        "schema": "cmpct-one-g02-index-budget-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "chunk_size": CHUNK,
        "caps": CAPS,
        "claim_boundary": "discovery opportunity/memory accounting only; candidate bytes are not stored-byte savings",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
