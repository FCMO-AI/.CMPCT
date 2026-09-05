"""ONE-G0.2 hostile probe for sparse Gear anchor starvation.

A 1/1024 content mask has an expected density, not a worst-case spacing guarantee. This
instrument freezes a deterministic 8 KiB basis whose exact historical cmpct-gear-v1 stream
contains zero sparse anchors, then repeats it. It tests sparse-only and the bounded 64-entry
local tier so friendly probability cannot be mistaken for architectural coverage.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import _gear_observe
from benchmarks.one.one_g02_tiered_gear_ab import _tiered_observe
from experiments.one.observe import observe

BASIS_BYTES = 8 * 1024
SEED = 4876


def run() -> dict[str, object]:
    basis = random.Random(SEED).randbytes(BASIS_BYTES)
    data = basis * 2
    fixed = observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14).stats
    sparse = _gear_observe(data)
    tiered = _tiered_observe(data)
    return {
        "schema": "cmpct-one-g02-anchor-starvation-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "basis_bytes": BASIS_BYTES,
        "seed": SEED,
        "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
        "sparse_gear_anchors": sparse.anchors,
        "sparse_reuse_opportunity_bytes": sparse.reuse_opportunity_bytes,
        "tiered_reuse_opportunity_bytes": tiered.reuse_opportunity_bytes,
        "tiered_local_entries": tiered.local_entries,
        "tiered_global_anchors": tiered.global_anchors,
        "decision": (
            "reject_current_tiered_retention_as_complete_fixed_signal_replacement"
            if tiered.reuse_opportunity_bytes < fixed.reuse_opportunity_bytes
            else "current_tiered_retention_survives_starvation_adversary"
        ),
        "causal_interpretation": "masked Gear anchors have no worst-case spacing bound; a local cache shorter than the repeat period can evict the only reusable phase before the second copy",
        "reopening_predicate": "a one-signal retention policy with an explicit worst-case nomination-gap bound recovers this relation without restoring fixed-index carrying cost",
        "claim_boundary": "discovery-opportunity negative evidence only; compression correctness is unaffected",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
