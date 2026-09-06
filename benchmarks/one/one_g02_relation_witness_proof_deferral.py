"""ONE-G0.2 traffic falsifier for witness-first relation proof deferral."""
from __future__ import annotations

from collections import OrderedDict, deque
import ctypes
import json
import os

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, _extend_left, _extend_right,
    GEAR_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW,
)
from benchmarks.one.one_g02_relation_shared_observer_validation import (
    LOCAL_ENTRIES, MINIMIZER_SPAN, Result, _build_safe, _cases,
)

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
CASES = (
    "shift_plus1", "damage_quarter", "fragmented_every96",
    "hostile_fixed_bands", "fragmented_every32", "independent_random",
)
NEGATIVES = {"fragmented_every32", "independent_random"}


def _safe_detail(fn, source: bytes, target: bytes) -> tuple[bool, int]:
    a = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    b = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
    out = Result()
    rc = fn(a, b, len(source), ctypes.byref(out))
    if rc < 0:
        raise RuntimeError(f"safe relation dispatcher failed: {rc}")
    return int(out.exact_proofs) >= 4, int(out.proof_compared_bytes)


def _nomination_traffic(source: bytes, target: bytes, *, witness_only: bool) -> dict[str, int | bool]:
    data = source + target
    boundary = len(source)
    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    minima: deque[tuple[int, int]] = deque()
    minimizer_enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    last_emitted_position = -1
    h = 0
    run_value = data[0]
    run_length = 0
    covered_until = 0
    nominated = False
    verification_bytes = 0
    extension_bytes = 0
    cross_witnesses = 0

    def audition(start: int, prior: int | None) -> None:
        nonlocal covered_until, nominated, verification_bytes, extension_bytes, cross_witnesses
        if prior is None or start < covered_until:
            return
        is_cross = prior < boundary <= start
        verification_bytes += 2 * WINDOW
        if data[prior:prior + WINDOW] != data[start:start + WINDOW]:
            return
        if is_cross:
            cross_witnesses += 1
            if witness_only:
                nominated = True
                return
        left, left_reads = _extend_left(data, prior, start, covered_until)
        right, right_reads = _extend_right(data, prior, start)
        extension_bytes += int(left_reads) + int(right_reads)
        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end > target_start:
            if is_cross:
                nominated = True
            covered_until = target_end

    for position, value in enumerate(data):
        if not run_length:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            run_value, run_length = value, 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)

        if not run_dominated and (position + 1) % WINDOW == 0:
            prior = local_index.get(h)
            if not (witness_only and nominated):
                audition(start, prior)
            if prior is None:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)

        if not minimizer_enabled:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        if first_valid < WINDOW - 1:
            continue
        signal, anchor_position = minima[0]
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        anchor_start = anchor_position + 1 - WINDOW
        prior = global_index.get(signal)
        if not (witness_only and nominated):
            audition(anchor_start, prior)
        if prior is None and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
            global_index[signal] = anchor_start

    return {
        "nominated": nominated,
        "verification_bytes": verification_bytes,
        "extension_bytes": extension_bytes,
        "cross_witnesses": cross_witnesses,
    }


def run() -> dict[str, object]:
    safe, td = _build_safe()
    rows = []
    opportunity_losses = []
    false_laws = []
    negative_regressions = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                generated = _cases(size, seed)
                for name in CASES:
                    source, target = generated[name]
                    safe_enabled, safe_proof_bytes = _safe_detail(safe, source, target)
                    baseline = _nomination_traffic(source, target, witness_only=False)
                    candidate = _nomination_traffic(source, target, witness_only=True)

                    baseline_proof = safe_proof_bytes if baseline["nominated"] else 0
                    candidate_proof = safe_proof_bytes if candidate["nominated"] else 0
                    baseline_total = int(baseline["verification_bytes"]) + int(baseline["extension_bytes"]) + baseline_proof
                    candidate_total = int(candidate["verification_bytes"]) + candidate_proof

                    if baseline["nominated"] and safe_enabled and not candidate["nominated"]:
                        opportunity_losses.append((size, seed, name))
                    final_candidate_law = bool(candidate["nominated"] and safe_enabled)
                    if final_candidate_law and not safe_enabled:
                        false_laws.append((size, seed, name))
                    ratio = candidate_total / baseline_total if baseline_total else (1.0 if candidate_total == 0 else float("inf"))
                    if name in NEGATIVES and baseline_total and ratio > 1.10:
                        negative_regressions.append((size, seed, name, ratio))

                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "safe_relation_enabled": safe_enabled,
                        "safe_relation_proof_compared_bytes": safe_proof_bytes,
                        "baseline_nominated": bool(baseline["nominated"]),
                        "candidate_nominated": bool(candidate["nominated"]),
                        "candidate_final_law": final_candidate_law,
                        "baseline_verification_bytes": int(baseline["verification_bytes"]),
                        "baseline_extension_bytes": int(baseline["extension_bytes"]),
                        "candidate_verification_bytes": int(candidate["verification_bytes"]),
                        "baseline_total_proof_bytes": baseline_total,
                        "candidate_total_proof_bytes": candidate_total,
                        "candidate_over_baseline_proof_bytes": ratio,
                        "candidate_cross_witnesses": int(candidate["cross_witnesses"]),
                    })

        baseline_aggregate = sum(int(r["baseline_total_proof_bytes"]) for r in rows)
        candidate_aggregate = sum(int(r["candidate_total_proof_bytes"]) for r in rows)
        aggregate_ratio = candidate_aggregate / baseline_aggregate if baseline_aggregate else 1.0
        if opportunity_losses or aggregate_ratio >= 1.0:
            decision = "reject_relation_witness_proof_deferral"
        elif aggregate_ratio <= 0.70 and not negative_regressions:
            decision = "advance_relation_witness_proof_deferral"
        else:
            decision = "hold_relation_witness_proof_deferral"

        return {
            "schema": "cmpct-one-g02-relation-witness-proof-deferral-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "opportunity_losses": opportunity_losses,
            "false_laws": false_laws,
            "negative_regressions": negative_regressions,
            "aggregate_baseline_proof_bytes": baseline_aggregate,
            "aggregate_candidate_proof_bytes": candidate_aggregate,
            "aggregate_candidate_over_baseline": aggregate_ratio,
            "decision": decision,
            "rows": rows,
            "claim_boundary": (
                "modeled/reference proof-traffic evidence for relation nomination only; exact-reuse Law discovery "
                "semantics are not removed and Python elapsed is not native speed authority"
            ),
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_relation_witness_proof_deferral" else 1)
