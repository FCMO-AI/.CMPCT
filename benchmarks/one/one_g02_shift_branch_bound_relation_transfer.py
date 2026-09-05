"""ONE-G0.2 structural transfer of proof-led admission to arbitrary relation slices.

Frozen before result-bearing execution.

The proof-led gate advanced on half-to-half testbeds after exact distributed proof made a global coverage
majority unnecessary. This transfer asks whether that admission principle depends on the artificial half
layout. A new kernel receives arbitrary source/target offsets and relation length but preserves the exact
coverage stride, shifts, four-hit nomination floor, sixteen strata, four 64-byte exact proofs and sixteen-
attempt ceiling.

Hypothesis: moving the same relation to independent carrier offsets does not change admission, nominated
shift or proof outcome; random and every-32-byte fragmented negatives remain rejected; positive shifted,
locally damaged and every-96-byte relations remain admitted. For 32/64 KiB relations, arbitrary-offset
execution must be <=1.10x the equivalent half-to-half proof-led kernel median, and modeled relation reads
must remain <=25%.

Disproof retires arbitrary-offset structural transfer, not the already-proven half-to-half admission law.
Do not change placements, relation sizes, proof budget or cost bounds after result.
"""
from __future__ import annotations

import ctypes
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

MAX_RELATIVE_COST = 1.10
MAX_READ_FRACTION = 0.25
RELATION_SIZES = (8 * 1024, 32 * 1024, 64 * 1024)
PLACEMENTS = (
    (4 * 1024, 160 * 1024),
    (80 * 1024, 300 * 1024),
    (200 * 1024, 400 * 1024),
)
CARRIER_BYTES = 512 * 1024


class Result(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64),
        ("zero_shift_matches", ctypes.c_uint64),
        ("coverage_compared_bytes", ctypes.c_uint64),
        ("best_hits", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64),
        ("proof_attempts", ctypes.c_uint64),
        ("exact_proofs", ctypes.c_uint64),
        ("proof_compared_bytes", ctypes.c_uint64),
        ("strata_with_support", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-relation-transfer-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_shift_branch_bound_relation_kernel.c"),
         str(here / "one_g02_shift_branch_bound_proof_led_kernel.c"),
         "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    relation = cdll.one_g02_shift_branch_bound_relation
    relation.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
                         ctypes.POINTER(Result)]
    relation.restype = ctypes.c_int
    half = cdll.one_g02_shift_branch_bound_proof_led
    half.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
    half.restype = ctypes.c_int
    return relation, half, td


def _shifted(source: bytes, spacing: int | None = None, damage_quarter: bool = False) -> bytes:
    target = bytearray(b"X" + source[:-1])
    if spacing:
        for j in range(16, len(target), spacing):
            target[j] ^= 0xA7
    if damage_quarter:
        lo = len(target) // 3
        hi = min(len(target), lo + len(target) // 4)
        for j in range(lo, hi):
            target[j] ^= (0x6B + j * 13) & 0xFF
    return bytes(target)


def _relation_cases(size: int):
    source = random.Random(21000 + size).randbytes(size)
    return {
        "shift_plus1": (source, _shifted(source), True, 1),
        "shift_plus1_damage_quarter": (source, _shifted(source, damage_quarter=True), True, 1),
        "fragmented_every96": (source, _shifted(source, spacing=96), True, 1),
        "fragmented_every32": (source, _shifted(source, spacing=32), False, 1),
        "independent_random": (source, random.Random(22000 + size).randbytes(size), False, None),
    }


def _median_relation(fn, arr, n, aoff, boff, rlen):
    out = Result()
    fn(arr, n, aoff, boff, rlen, ctypes.byref(out))
    samples = []
    for _ in range(51):
        t0 = time.perf_counter_ns()
        fn(arr, n, aoff, boff, rlen, ctypes.byref(out))
        samples.append(time.perf_counter_ns() - t0)
    return float(statistics.median(samples)), out


def _median_half(fn, packed: bytes):
    arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
    out = Result()
    fn(arr, len(packed), ctypes.byref(out))
    samples = []
    for _ in range(51):
        t0 = time.perf_counter_ns()
        fn(arr, len(packed), ctypes.byref(out))
        samples.append(time.perf_counter_ns() - t0)
    return float(statistics.median(samples)), out


def run():
    relation, half, td = _build()
    rows = []
    try:
        all_ok = True
        cost_ok = True
        placement_ok = True
        for size in RELATION_SIZES:
            for case, (source, target, expected_enable, expected_shift) in _relation_cases(size).items():
                half_ns, half_out = _median_half(half, source + target)
                reference_signature = None
                for placement_id, (aoff, boff) in enumerate(PLACEMENTS):
                    if aoff + size > CARRIER_BYTES or boff + size > CARRIER_BYTES:
                        raise AssertionError("frozen placement exceeds carrier")
                    if not (aoff + size <= boff or boff + size <= aoff):
                        raise AssertionError("frozen source/target regions overlap")
                    carrier = bytearray(random.Random(23000 + size + placement_id).randbytes(CARRIER_BYTES))
                    carrier[aoff:aoff + size] = source
                    carrier[boff:boff + size] = target
                    arr = (ctypes.c_uint8 * len(carrier)).from_buffer_copy(carrier)
                    ns, out = _median_relation(relation, arr, len(carrier), aoff, boff, size)
                    enabled = int(out.exact_proofs) >= 4
                    correct = enabled == expected_enable and (
                        not enabled or expected_shift is None or int(out.best_shift) == expected_shift
                    )
                    all_ok &= correct
                    signature = (int(out.best_shift), int(out.best_hits), int(out.proof_attempts),
                                 int(out.exact_proofs), int(out.strata_with_support))
                    if reference_signature is None:
                        reference_signature = signature
                    else:
                        placement_ok &= signature == reference_signature
                    ratio = ns / half_ns
                    if size >= 32 * 1024:
                        cost_ok &= ratio <= MAX_RELATIVE_COST
                    read_fraction = (int(out.coverage_compared_bytes) + int(out.proof_compared_bytes)) / size
                    all_ok &= read_fraction <= MAX_READ_FRACTION
                    rows.append({
                        "relation_bytes": size,
                        "case": case,
                        "placement": placement_id,
                        "source_offset": aoff,
                        "target_offset": boff,
                        "expected_enable": expected_enable,
                        "gate_enable": enabled,
                        "best_shift": int(out.best_shift),
                        "best_hits": int(out.best_hits),
                        "proof_attempts": int(out.proof_attempts),
                        "exact_proofs": int(out.exact_proofs),
                        "strata_with_support": int(out.strata_with_support),
                        "modeled_read_fraction": read_fraction,
                        "relation_median_ns": ns,
                        "equivalent_half_median_ns": half_ns,
                        "relation_over_half": ratio,
                        "classification_correct": correct,
                    })
        passed = all_ok and cost_ok and placement_ok
        return {
            "schema": "cmpct-one-g02-shift-branch-bound-relation-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_relation_sizes": list(RELATION_SIZES),
            "frozen_placements": [list(x) for x in PLACEMENTS],
            "frozen_max_relative_cost_32k_plus": MAX_RELATIVE_COST,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "decision": "advance_arbitrary_relation_transfer" if passed else "retire_arbitrary_relation_transfer",
            "claim_boundary": "writer-side structural transfer only; candidate relation discovery remains external and no reader/product/comparator authority is granted",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_arbitrary_relation_transfer" else 1)
