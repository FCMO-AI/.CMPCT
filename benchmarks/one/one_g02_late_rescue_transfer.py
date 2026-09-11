"""ONE-G0.2 structural-transfer falsifier for starvation-gated minimizer rescue.

Inputs are selected only by a pre-existing causal property: a 4 KiB pseudorandom basis has
zero qualifying sparse Gear anchors.  Selection does not inspect minimizer or late-rescue
outcomes.  Each selected basis is then duplicated with an insertion between versions.
This asks whether the fixed 4,096-position starvation gate preserves full-minimizer marginal
opportunity across generator-distinct hostile seeds rather than one constructed example.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import (
    FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW, _gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_late_minimizer_rescue import _late_rescue_observe
from benchmarks.one.one_g02_starvation_gate_map import _gate_stats
from experiments.one.observe import observe

BASIS_BYTES = 4096
TARGET_STARVED_BASES = 12
MAX_SEED = 4095
INSERTIONS = (b"X", b"seven777", bytes(range(31)))


def _starved_bases() -> list[tuple[int, bytes]]:
    out: list[tuple[int, bytes]] = []
    for seed in range(MAX_SEED + 1):
        basis = random.Random(seed).randbytes(BASIS_BYTES)
        if _gate_stats(basis)["sparse_anchors"] == 0:
            out.append((seed, basis))
            if len(out) == TARGET_STARVED_BASES:
                break
    return out


def run() -> dict[str, object]:
    selected = _starved_bases()
    if len(selected) < TARGET_STARVED_BASES:
        raise AssertionError(f"only {len(selected)} starved bases found before frozen MAX_SEED={MAX_SEED}")

    rows = []
    hard_rows = 0
    hard_losses: list[str] = []
    for seed, basis in selected:
        for insertion in INSERTIONS:
            data = basis + insertion + basis
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            sparse = _gear_observe(data)
            full = _minimizer_observe(data)
            late = _late_rescue_observe(data)
            cheap = max(fixed.stats.reuse_opportunity_bytes, sparse.reuse_opportunity_bytes)
            hard = full.reuse_opportunity_bytes > cheap
            if hard:
                hard_rows += 1
                if late.reuse_opportunity_bytes < full.reuse_opportunity_bytes:
                    hard_losses.append(f"seed={seed}/insert={len(insertion)}")
            rows.append({
                "seed": seed,
                "basis_bytes": BASIS_BYTES,
                "insertion_bytes": len(insertion),
                "input_bytes": len(data),
                "fixed_reuse_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "sparse_reuse_opportunity_bytes": sparse.reuse_opportunity_bytes,
                "full_minimizer_reuse_opportunity_bytes": full.reuse_opportunity_bytes,
                "late_rescue_reuse_opportunity_bytes": late.reuse_opportunity_bytes,
                "hard_rescue_needed": hard,
                "late_minus_full_opportunity_bytes": late.reuse_opportunity_bytes - full.reuse_opportunity_bytes,
                "rescue_active_fraction": late.rescue_active_positions / len(data),
                "emitted_rescue_minimizers": late.emitted_minimizers,
                "verification_read_bytes": late.verification_read_bytes,
                "extension_read_bytes": late.extension_read_bytes,
            })

    return {
        "schema": "cmpct-one-g02-late-rescue-transfer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "selection_rule": f"first {TARGET_STARVED_BASES} seeds in [0,{MAX_SEED}] whose {BASIS_BYTES}-byte basis has zero qualifying sparse Gear anchors",
        "selected_seeds": [seed for seed, _ in selected],
        "insertion_lengths": [len(x) for x in INSERTIONS],
        "frozen_gate_gap_positions": 4096,
        "hypothesis": "fixed starvation-gated cold minimizer rescue preserves full-minimizer marginal opportunity across independently generated sparse-anchor-starved shifted pairs",
        "disproof": "any hard-rescue transfer row loses full-minimizer opportunity; zero hard-rescue transfer rows makes the experiment inconclusive rather than a win",
        "hard_rescue_rows": hard_rows,
        "hard_rescue_loss_cases": hard_losses,
        "decision": (
            "transfer_survives"
            if hard_rows > 0 and not hard_losses
            else "transfer_inconclusive_no_hard_rows"
            if hard_rows == 0
            else "reject_late_rescue_transfer"
        ),
        "claim_boundary": "generator-distinct encoder-discovery transfer only; selection uses starvation property, not algorithm outcome; no native/product or release authority",
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
