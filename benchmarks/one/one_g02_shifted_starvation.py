"""ONE-G0.2 hostile falsifier: coordinate gap fallback is not shift invariant."""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_bounded_gear_ab import _bounded_observe
from experiments.one.observe import observe

BASIS_BYTES = 8 * 1024
SEED = 4876


def run() -> dict[str, object]:
    basis = random.Random(SEED).randbytes(BASIS_BYTES)
    data = basis + b"X" + basis
    fixed = observe(data, min_run=8, chunk_size=64, max_index_entries=1 << 14).stats
    bounded = _bounded_observe(data)
    return {
        "schema": "cmpct-one-g02-shifted-starvation-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "basis_bytes": BASIS_BYTES,
        "inserted_bytes": 1,
        "seed": SEED,
        "fixed_reuse_opportunity_bytes": fixed.reuse_opportunity_bytes,
        "bounded_reuse_opportunity_bytes": bounded.reuse_opportunity_bytes,
        "bounded_masked_anchors": bounded.masked_anchors,
        "bounded_fallback_anchors": bounded.fallback_anchors,
        "decision": "reject_coordinate_gap_fallback_as_shift_robust_replacement" if bounded.reuse_opportunity_bytes == 0 else "survives_current_shifted_falsifier",
        "causal_interpretation": "absolute-position fallback bounds nomination gaps but changes phase after insertion; an anchor-starved repeated region therefore receives different fallback phases and no shared content key",
        "reopening_predicate": "a content-derived selector with a worst-case spacing guarantee preserves a common anchor under insertion shifts",
        "claim_boundary": "encoder discovery negative evidence only; byte-exact reconstruction is unaffected",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
