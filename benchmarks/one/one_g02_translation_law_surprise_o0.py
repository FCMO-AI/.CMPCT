"""ONE-G0.2 O0 headroom: persist a proven translation Law across Surprise.

Referee freeze before result-bearing execution
==============================================
Causal attribution of the only internally-edited-version epoch-min loss showed that the
mature rolling minimizer does not discover a new mapping. It merely re-nominates the same
version-to-version translation delta after a substituted byte. The missed 1,331-byte exact
island lies precisely between two edits.

Hypothesis: once the existing sparse/epoch discovery path has byte-proven *one* source→target
translation relation, the ONE representation should be able to keep that Law active across
sparse prediction failures and encode those failures as Surprise, instead of paying to
rediscover each exact island with a rolling minimizer.

Oracle honesty / O0 gift
------------------------
This is intentionally O0 headroom, not product discovery. The experiment may gift only the
continuation decision and the target version extent from the frozen synthetic generator.
It may NOT gift the Law itself: every evaluated row must first contain an exact successful
candidate nomination whose source/target start difference proves the correct translation
delta. It may not gift Surprise values, positions, control bytes, or reconstruction.

Charged representation model
----------------------------
The existing first version is the base and is not counted again. The second version is
represented by:
- 32 B conservative generic Law/control payload (source start, target start, span and control);
- ULEB128 Surprise count;
- for every Surprise: ULEB128 delta from previous Surprise position + 1 literal byte.
All bytes are charged. Reconstruction copies predicted source bytes and patches every
explicit Surprise; exact equality is mandatory.

Frozen corpus is identical to the edited-version structural transfer: master seed
0xE017ED17, base sizes 65,536/262,144, 8 bases each, 1/4/16/64 internal substitutions.

Frozen advancement gate on every row:
- an existing candidate exact relation must seed the correct translation delta;
- reconstruction must be byte exact;
- charged Surprise count must equal actual mismatches (no gifted residuals);
- Law-predicted exact bytes must be >= mature minimizer exact reuse opportunity;
- charged second-version representation must be < literal second-version bytes;
- for the previously failing 262,144/base1/16-edit row, Law-predicted exact bytes must
  subsume the mature 262,128-byte opportunity and the 1,331-byte missed island by continuity.

A pass establishes representation/headroom evidence only. Automatic continuation extent,
product speed, generic false-positive control and wire encoding remain debt.
"""
from __future__ import annotations

import json
import os
import random

from benchmarks.one.one_g02_epoch_min_edited_loss_attribution import _candidate_trace
from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_gear_replacement_ab import WINDOW

LAW_CONTROL_BYTES = 32


def _uleb_bytes(value: int) -> int:
    if value < 0:
        raise ValueError(value)
    n = 1
    while value >= 0x80:
        value >>= 7
        n += 1
    return n


def _seed_delta(data: bytes, second_start: int):
    _, events, _ = _candidate_trace(data)
    for event in events:
        if event.get("gained_bytes", 0) <= 0:
            continue
        source = event.get("source")
        start = event.get("start")
        if source is None or start is None:
            continue
        if source < second_start <= start:
            return int(start - source), event
    return None, None


def _charge_surprises(base: bytes, edited: bytes):
    positions = [i for i, (a, b) in enumerate(zip(base, edited)) if a != b]
    cost = LAW_CONTROL_BYTES + _uleb_bytes(len(positions))
    previous = 0
    for pos in positions:
        cost += _uleb_bytes(pos - previous) + 1
        previous = pos
    return positions, cost


def run():
    master = random.Random(MASTER_SEED)
    rows = []
    failures = []
    seeded = 0
    total_literal = total_charged = total_predicted = total_mature = 0

    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed = master.getrandbits(64)
            base = random.Random(seed).randbytes(size)
            for mutation_count in MUTATION_COUNTS:
                edited = _edited(
                    base,
                    random.Random(seed ^ (mutation_count << 32) ^ 0xA11CE5EED),
                    mutation_count,
                )
                data = base + edited
                delta, seed_event = _seed_delta(data, size)
                mature = _minimizer_observe(data)
                surprises, charged = _charge_surprises(base, edited)
                predicted = size - len(surprises)

                exact = False
                if delta == size:
                    rebuilt = bytearray(base)
                    for pos in surprises:
                        rebuilt[pos] = edited[pos]
                    exact = bytes(rebuilt) == edited

                reasons = []
                if delta is None:
                    reasons.append("no_candidate_seed")
                elif delta != size:
                    reasons.append("wrong_seed_delta")
                else:
                    seeded += 1
                if not exact:
                    reasons.append("reconstruction")
                if len(surprises) != mutation_count:
                    reasons.append("surprise_count")
                if predicted < mature.reuse_opportunity_bytes:
                    reasons.append("mature_opportunity_not_subsumed")
                if charged >= size:
                    reasons.append("representation_not_better_than_literal")
                if size == 262_144 and base_index == 1 and mutation_count == 16:
                    if predicted < 262_128:
                        reasons.append("known_loss_not_subsumed")

                row = {
                    "base_bytes": size,
                    "base_index": base_index,
                    "mutation_count": mutation_count,
                    "input_bytes": len(data),
                    "seed_delta": delta,
                    "seed_kind": seed_event.get("kind") if seed_event else None,
                    "seed_target_start": seed_event.get("start") if seed_event else None,
                    "seed_source_start": seed_event.get("source") if seed_event else None,
                    "surprise_bytes": len(surprises),
                    "law_predicted_exact_bytes": predicted,
                    "mature_exact_reuse_opportunity_bytes": mature.reuse_opportunity_bytes,
                    "charged_second_version_bytes": charged,
                    "literal_second_version_bytes": size,
                    "charged_fraction_of_literal": charged / size,
                    "exact_reconstruction": exact,
                    "gate_failures": reasons,
                }
                if reasons:
                    failures.append({"base_bytes": size, "base_index": base_index,
                                     "mutation_count": mutation_count, "reasons": reasons})
                rows.append(row)
                total_literal += size
                total_charged += charged
                total_predicted += predicted
                total_mature += mature.reuse_opportunity_bytes

    decision = (
        "advance_translation_law_surprise_from_o0_headroom"
        if not failures
        else "block_translation_law_surprise_on_seed_or_representation_falsifier"
    )
    return {
        "schema": "cmpct-one-g02-translation-law-surprise-o0-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "oracle_tier": "O0",
        "gifted": ["continuation decision after an already byte-proven candidate Law seed", "frozen target-version extent"],
        "not_gifted": ["Law seed/delta", "Law/control bytes", "Surprise positions", "Surprise literal bytes", "exact reconstruction"],
        "law_control_bytes_per_row": LAW_CONTROL_BYTES,
        "rows": len(rows),
        "seeded_rows": seeded,
        "gate_failures": failures,
        "total_literal_second_version_bytes": total_literal,
        "total_charged_second_version_bytes": total_charged,
        "charged_fraction_of_literal": total_charged / total_literal,
        "total_law_predicted_exact_bytes": total_predicted,
        "total_mature_exact_reuse_opportunity_bytes": total_mature,
        "decision": decision,
        "claim_boundary": (
            "O0 representation/headroom and exact reconstruction only; continuation search/extent is gifted; "
            "no automatic-discovery, native-speed, generic false-positive, wire, comparator or release authority"
        ),
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
