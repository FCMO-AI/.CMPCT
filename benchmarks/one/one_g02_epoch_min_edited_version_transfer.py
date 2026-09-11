"""ONE-G0.2 epoch-min structural transfer on internally edited versions.

Referee freeze before result-bearing execution
==============================================
The existing unfiltered structural-transfer cohort uses `basis + insertion + basis`: it
proves shift invariance across inserted gaps, but the second version remains byte-identical
once alignment is recovered. Real temporal/versioned data also contains edits *inside* the
later version. This generator-distinct cohort asks whether replacing the mature rolling
minimizer with sparse Gear + scalar starvation-epoch minima loses exact reusable regions
when a repeated version is locally damaged.

Corpus is fixed independent of candidate outcome:
- master seed 0xE017ED17;
- base sizes 65,536 and 262,144 bytes;
- 8 independent random bases per size;
- mutation counts 1, 4, 16, 64 bytes in the second version;
- mutation positions are sampled without replacement from the interior [WINDOW, n-WINDOW)
  and sorted; replacement bytes are forced to differ from the source byte;
- input is `basis + edited_basis` (no insertion shift is gifted here).

Every nominated relation is still exact-byte verified by the inherited observers.

Frozen structural-replacement gate:
- there must be mature-positive rows beyond the fixed observer;
- on every mature-positive row, candidate total exact opportunity must be >= mature total;
- candidate may not invent nonzero exact opportunity on a row where fixed and mature are 0;
- proof/extension read traffic is recorded but does not rescue an opportunity loss.

Any per-row loss blocks the claim that epoch-min can replace the mature selector across
internally edited temporal/versioned data. Aggregate extra opportunity cannot compensate.
This is encoder-discovery transfer evidence only, never stored-byte or product-speed proof.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_epoch_min_charged_miy import _candidate
from benchmarks.one.one_g02_gear_replacement_ab import (
    FIXED_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from experiments.one.observe import observe

MASTER_SEED = 0xE017ED17
BASE_SIZES = (65_536, 262_144)
BASES_PER_SIZE = 8
MUTATION_COUNTS = (1, 4, 16, 64)


def _edited(base: bytes, rng: random.Random, count: int) -> bytes:
    if len(base) <= 2 * WINDOW:
        raise ValueError("base too small for frozen interior mutation contract")
    positions = sorted(rng.sample(range(WINDOW, len(base) - WINDOW), count))
    out = bytearray(base)
    for pos in positions:
        old = out[pos]
        delta = rng.randrange(1, 256)
        out[pos] = (old + delta) & 0xFF
    return bytes(out)


def run() -> dict[str, object]:
    master = random.Random(MASTER_SEED)
    rows = []
    losses = []
    false_rows = []
    mature_positive = 0
    total_mature_marginal = 0
    total_captured = 0

    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutation_count in MUTATION_COUNTS:
                edit_rng = random.Random(seed ^ (mutation_count << 32) ^ 0xA11CE5EED)
                edited = _edited(base, edit_rng, mutation_count)
                data = base + edited

                fixed = observe(
                    data,
                    min_run=MIN_RUN,
                    chunk_size=WINDOW,
                    max_index_entries=FIXED_MAX_INDEX_ENTRIES,
                ).stats
                mature = _minimizer_observe(data)
                candidate = _candidate(data)

                f = fixed.reuse_opportunity_bytes
                m = mature.reuse_opportunity_bytes
                c = max(f, candidate.reuse)
                marginal = max(0, m - f)
                captured = min(max(0, c - f), marginal)
                mature_proof = mature.verification_read_bytes + mature.extension_read_bytes
                candidate_proof = candidate.verify + candidate.extension

                if marginal:
                    mature_positive += 1
                    total_mature_marginal += marginal
                    total_captured += captured
                    if c < m:
                        losses.append(
                            {
                                "base_bytes": size,
                                "base_index": base_index,
                                "mutation_count": mutation_count,
                                "mature_total": m,
                                "candidate_total": c,
                                "lost_bytes": m - c,
                            }
                        )
                if f == 0 and m == 0 and c != 0:
                    false_rows.append(
                        {
                            "base_bytes": size,
                            "base_index": base_index,
                            "mutation_count": mutation_count,
                            "candidate_total": c,
                        }
                    )

                rows.append(
                    {
                        "base_bytes": size,
                        "base_index": base_index,
                        "mutation_count": mutation_count,
                        "input_bytes": len(data),
                        "fixed_opportunity_bytes": f,
                        "mature_opportunity_bytes": m,
                        "candidate_total_opportunity_bytes": c,
                        "mature_marginal_opportunity_bytes": marginal,
                        "captured_mature_marginal_bytes": captured,
                        "candidate_minus_mature_total_bytes": c - m,
                        "mature_proof_read_bytes": mature_proof,
                        "candidate_proof_read_bytes": candidate_proof,
                        "candidate_sparse_entries": candidate.sparse_entries,
                        "candidate_rescue_entries": candidate.rescue_entries,
                        "candidate_pulses": candidate.pulses,
                    }
                )

    decision = (
        "advance_epoch_min_edited_version_transfer"
        if mature_positive and not losses and not false_rows
        else "block_epoch_min_replacement_on_edited_version_transfer"
    )
    return {
        "schema": "cmpct-one-g02-epoch-min-edited-version-transfer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD")
        or os.environ.get("GITHUB_SHA")
        or "local-unbound",
        "corpus": {
            "master_seed": MASTER_SEED,
            "base_sizes": list(BASE_SIZES),
            "bases_per_size": BASES_PER_SIZE,
            "mutation_counts": list(MUTATION_COUNTS),
            "rows": len(rows),
        },
        "mature_positive_rows": mature_positive,
        "mature_marginal_opportunity_bytes": total_mature_marginal,
        "captured_mature_marginal_bytes": total_captured,
        "capture_fraction": (
            total_captured / total_mature_marginal if total_mature_marginal else 0.0
        ),
        "positive_loss_cases": losses,
        "false_exact_opportunity_rows": false_rows,
        "decision": decision,
        "claim_boundary": (
            "internally edited temporal/versioned encoder-discovery structural transfer only; "
            "no stored-byte/product/comparator/release authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
