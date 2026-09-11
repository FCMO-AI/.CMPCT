"""ONE-G0.2 integrated reference discovery A/B.

Referee freeze before result-bearing execution
==============================================
The scalar epoch-min candidate survived generator-distinct hard-rescue transfer and the
fully charged native-signal MIY gate. The strongest surviving criticism is that native
signal timing can hide index lookup/update and proof bookkeeping performed around that
signal. Before building a fused native observer, this experiment times the *complete
reference discovery paths* symmetrically: fixed observation + mature minimizer versus
fixed observation + epoch-min sparse/rescue candidate, including exact verification and
extension work already implemented by each observer.

This is intentionally a pre-fusion reference experiment. Both arms perform the same
already-required fixed observation plus one augmentation scan, so neither arm receives a
source-pass gift. Python timings are algorithm/integration evidence only; they are not
product-speed authority.

Frozen advancement gate on every mature-positive marginal row:
- candidate total exact opportunity >= mature full-minimizer opportunity;
- candidate complete reference elapsed <= 0.80x mature complete reference elapsed;
- candidate modeled discovery state <= 0.60x mature modeled discovery state;
- candidate proof reads <= mature proof reads.
On random and zlib-random zero-opportunity controls, candidate complete elapsed must be
<=0.90x mature and must not invent exact opportunity. Any row failure blocks the claim
that epoch-min integration debt is already small enough to justify native fusion.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import time

from benchmarks.one.one_g02_epoch_min_charged_miy import _candidate, INDEX_BYTES_PER_ENTRY
from benchmarks.one.one_g02_gear_replacement_ab import (
    _cases,
    FIXED_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from experiments.one.observe import observe

ROUNDS = 7


def _fixed(data: bytes):
    return observe(
        data,
        min_run=MIN_RUN,
        chunk_size=WINDOW,
        max_index_entries=FIXED_MAX_INDEX_ENTRIES,
    )


def _mature_path(data: bytes):
    fixed = _fixed(data)
    mature = _minimizer_observe(data)
    return fixed, mature


def _candidate_path(data: bytes):
    fixed = _fixed(data)
    candidate = _candidate(data)
    return fixed, candidate


def _time(fn):
    t0 = time.perf_counter_ns()
    value = fn()
    return time.perf_counter_ns() - t0, value


def _abba(base_fn, cand_fn):
    # Warm both code/data paths before the paired measurements.
    base_fn()
    cand_fn()
    base_samples = []
    cand_samples = []
    ratios = []
    base_last = cand_last = None
    for _ in range(ROUNDS):
        b1, base_last = _time(base_fn)
        c1, cand_last = _time(cand_fn)
        c2, cand_last = _time(cand_fn)
        b2, base_last = _time(base_fn)
        b = (b1 + b2) * 0.5
        c = (c1 + c2) * 0.5
        base_samples.append(b)
        cand_samples.append(c)
        ratios.append(c / b)
    return (
        float(statistics.median(base_samples)),
        float(statistics.median(cand_samples)),
        float(statistics.median(ratios)),
        base_last,
        cand_last,
    )


def run():
    cases = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    rows = []
    failures = []
    positive = []
    for name, data in cases.items():
        mature_ns, candidate_ns, ratio, mature_pair, candidate_pair = _abba(
            lambda d=data: _mature_path(d),
            lambda d=data: _candidate_path(d),
        )
        fixed_m, mature = mature_pair
        fixed_c, candidate = candidate_pair
        if fixed_m.stats.reuse_opportunity_bytes != fixed_c.stats.reuse_opportunity_bytes:
            raise AssertionError((name, "fixed observer drift"))

        fixed_bytes = fixed_m.stats.reuse_opportunity_bytes
        mature_bytes = mature.reuse_opportunity_bytes
        candidate_bytes = max(fixed_bytes, candidate.reuse)
        mature_marginal = max(0, mature_bytes - fixed_bytes)

        mature_index_bytes = (
            mature.global_entries + mature.local_entries
        ) * INDEX_BYTES_PER_ENTRY
        # Reference mature state accounts the retained indexes here; the native
        # signal-state component is charged by the separate exact-head MIY gate.
        candidate_index_bytes = (
            candidate.sparse_entries + candidate.rescue_entries
        ) * INDEX_BYTES_PER_ENTRY
        # Use the exact native signal-state charges established by the paired MIY
        # experiment so this integration test does not pretend Python object size
        # is a portable systems metric.
        mature_signal_state = 41056
        candidate_signal_state = 2088
        mature_state = mature_signal_state + mature_index_bytes
        candidate_state = candidate_signal_state + candidate_index_bytes

        mature_proof = mature.verification_read_bytes + mature.extension_read_bytes
        candidate_proof = candidate.verify + candidate.extension
        row = {
            "case": name,
            "input_bytes": len(data),
            "fixed_opportunity_bytes": fixed_bytes,
            "mature_opportunity_bytes": mature_bytes,
            "candidate_total_opportunity_bytes": candidate_bytes,
            "mature_marginal_opportunity_bytes": mature_marginal,
            "mature_complete_reference_ns": mature_ns,
            "candidate_complete_reference_ns": candidate_ns,
            "candidate_over_mature_elapsed_ratio": ratio,
            "mature_modeled_state_bytes": mature_state,
            "candidate_modeled_state_bytes": candidate_state,
            "candidate_over_mature_state_ratio": (
                candidate_state / mature_state if mature_state else 0.0
            ),
            "mature_proof_read_bytes": mature_proof,
            "candidate_proof_read_bytes": candidate_proof,
            "candidate_over_mature_proof_ratio": (
                candidate_proof / mature_proof if mature_proof else 0.0
            ),
            "candidate_sparse_entries": candidate.sparse_entries,
            "candidate_rescue_entries": candidate.rescue_entries,
            "candidate_pulses": candidate.pulses,
            "source_scans_mature": 2,
            "source_scans_candidate": 2,
        }
        reasons = []
        if mature_marginal:
            positive.append(name)
            if candidate_bytes < mature_bytes:
                reasons.append("opportunity")
            if ratio > 0.80:
                reasons.append("complete_reference_elapsed")
            if row["candidate_over_mature_state_ratio"] > 0.60:
                reasons.append("state")
            if candidate_proof > mature_proof:
                reasons.append("proof")
        if name in {"random_1mib", "zlib_random_payload"}:
            if candidate_bytes != 0 or mature_bytes != 0:
                reasons.append("zero_opportunity_control_not_zero")
            if ratio > 0.90:
                reasons.append("negative_control_elapsed")
        if reasons:
            failures.append({"case": name, "reasons": reasons})
        rows.append(row)

    decision = (
        "advance_epoch_min_to_native_fused_integration"
        if positive and not failures
        else "block_native_fusion_on_integrated_reference_debt"
    )
    return {
        "schema": "cmpct-one-g02-epoch-min-integrated-reference-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD")
        or os.environ.get("GITHUB_SHA")
        or "local-unbound",
        "rounds": ROUNDS,
        "mature_positive_marginal_cases": positive,
        "gate_failures": failures,
        "decision": decision,
        "claim_boundary": (
            "complete Python reference discovery-path integration evidence only; "
            "two scans on both arms; no native/product/stored-byte/comparator/release authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
