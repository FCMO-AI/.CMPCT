"""ONE-G0.2 structural validation for direct Gear-difference witness ranking."""
from __future__ import annotations

import heapq
import json
import os

from benchmarks.one.one_g02_gear_difference_phase_certificate_validation import (
    MODELED_STATE_BYTES,
    _difference_local_gear8,
    _direct_local_gear8,
    _prefix_states,
)
from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import (
    PER_PHASE_K,
    SOURCE_PHASES,
    STRIDE,
    TARGET_PHASE,
    WORD,
    SIZES,
    SEEDS,
    _build_safe,
    _cases,
    _safe_result,
)


def _source_certificate(source: bytes):
    states = _prefix_states(source)
    cert = []
    sampled = 0
    identity_mismatches = []
    for phase in SOURCE_PHASES:
        heap = []
        for pos in range(phase, len(source) - WORD + 1, STRIDE):
            sampled += 1
            local = _difference_local_gear8(states, pos)
            if local != _direct_local_gear8(source, pos):
                identity_mismatches.append(pos)
            item = (-local, -pos, local)
            if len(heap) < PER_PHASE_K:
                heapq.heappush(heap, item)
            elif local < heap[0][2]:
                heapq.heapreplace(heap, item)
        cert.extend((entry[2], -entry[1], phase) for entry in heap)
    return cert, sampled, identity_mismatches


def _nominate(source: bytes, target: bytes):
    cert, source_samples, source_identity = _source_certificate(source)
    by_token = {}
    for token, pos, phase in cert:
        by_token.setdefault(token, []).append((pos, phase))
    target_states = _prefix_states(target)
    target_samples = 0
    compares = 0
    target_identity = []
    for pos in range(TARGET_PHASE, len(target) - WORD + 1, STRIDE):
        target_samples += 1
        local = _difference_local_gear8(target_states, pos)
        if local != _direct_local_gear8(target, pos):
            target_identity.append(pos)
        for source_pos, phase in by_token.get(local, ()):
            compares += 1
            if target[pos : pos + WORD] == source[source_pos : source_pos + WORD]:
                return True, source_samples, target_samples, compares, phase, source_identity, target_identity
    return False, source_samples, target_samples, compares, None, source_identity, target_identity


def run():
    safe, td = _build_safe()
    rows = []
    misses = []
    random_false = []
    identity_failures = []
    max_fraction = 0.0
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    enabled, best_shift, proofs = _safe_result(safe, source, target)
                    nominated, ss, ts, compares, phase, src_id, tgt_id = _nominate(source, target)
                    if src_id or tgt_id:
                        identity_failures.append((size, seed, name, len(src_id), len(tgt_id)))
                    frac = (ss + ts) / len(source)
                    max_fraction = max(max_fraction, frac)
                    if enabled and not nominated:
                        misses.append((size, seed, name))
                    if name == "independent_random" and nominated:
                        random_false.append((size, seed, name))
                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "exact_relation_enabled": enabled,
                        "best_shift": best_shift,
                        "exact_proofs": proofs,
                        "unmixed_gear_difference_nominated": nominated,
                        "matching_source_phase": phase,
                        "source_word_samples": ss,
                        "target_word_samples_until_decision": ts,
                        "sampled_position_fraction": frac,
                        "exact_word_compares": compares,
                        "identity_mismatches_source": len(src_id),
                        "identity_mismatches_target": len(tgt_id),
                    })
        passed = (
            not identity_failures
            and not misses
            and not random_false
            and max_fraction <= 0.19
            and MODELED_STATE_BYTES <= 280
        )
        return {
            "schema": "cmpct-one-g02-unmixed-gear-difference-certificate-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_seeds": list(SEEDS),
            "stride": STRIDE,
            "word_bytes": WORD,
            "source_phases": list(SOURCE_PHASES),
            "per_phase_witnesses": PER_PHASE_K,
            "modeled_state_bytes": MODELED_STATE_BYTES,
            "gear_difference_identity_failures": identity_failures,
            "required_positive_misses": misses,
            "independent_random_false_nominations": random_false,
            "max_sampled_position_fraction": max_fraction,
            "decision": "advance_unmixed_gear_difference_to_native_cost" if passed else "retire_unmixed_gear_difference",
            "claim_boundary": "structural discovery ranking only; no timing/density/reader/format/comparator claim",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_unmixed_gear_difference_to_native_cost" else 2)
