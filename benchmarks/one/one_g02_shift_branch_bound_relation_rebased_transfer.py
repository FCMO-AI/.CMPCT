"""ONE-G0.2 pointer-rebased arbitrary relation structural transfer.

Frozen before result-bearing execution.

The first arbitrary-offset kernel transferred every classification/proof signature correctly but exceeded
the frozen <=1.10x 32/64 KiB cost ceiling (roughly 1.16-1.28x). This superseding Builder changes only
address formation: source/target bounds are validated once and pointers are rebased once, leaving hot-loop
coordinates relation-local. Corpus, relation placements, admission semantics, proof budget, <=25% read
ceiling and <=1.10x cost ceiling are unchanged.

Hypothesis: the semantic transfer was sound and the prior loss was address/code-shape debt. Rebased arbitrary
relations must reproduce the same placement-invariant proof signatures and classifications while meeting
<=1.10x the equivalent half-to-half proof-led median on every 32/64 KiB row. 8 KiB rows remain semantic/read
controls; their relative-cost ratios are diagnostic as in the frozen predecessor.

Disproof retires pointer rebasing as sufficient rehabilitation. Do not loosen the 1.10x bound or change the
corpus after result; if it fails, inspect generated code / loop bounds before touching admission semantics.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import (
    CARRIER_BYTES,
    MAX_READ_FRACTION,
    MAX_RELATIVE_COST,
    PLACEMENTS,
    RELATION_SIZES,
    Result,
    _relation_cases,
)


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-rebased-transfer-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_shift_branch_bound_relation_rebased_kernel.c"),
         str(here / "one_g02_shift_branch_bound_proof_led_kernel.c"),
         "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    relation = cdll.one_g02_shift_branch_bound_relation_rebased
    relation.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
                         ctypes.POINTER(Result)]
    relation.restype = ctypes.c_int
    half = cdll.one_g02_shift_branch_bound_proof_led
    half.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
    half.restype = ctypes.c_int
    return relation, half, td


def _median_relation(fn, arr, n, aoff, boff, rlen):
    out = Result()
    if fn(arr, n, aoff, boff, rlen, ctypes.byref(out)) != 0:
        raise RuntimeError("rebased relation kernel failed")
    samples = []
    for _ in range(101):
        t0 = time.perf_counter_ns()
        fn(arr, n, aoff, boff, rlen, ctypes.byref(out))
        samples.append(time.perf_counter_ns() - t0)
    return float(statistics.median(samples)), out


def _median_half(fn, packed: bytes):
    arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
    out = Result()
    fn(arr, len(packed), ctypes.byref(out))
    samples = []
    for _ in range(101):
        t0 = time.perf_counter_ns()
        fn(arr, len(packed), ctypes.byref(out))
        samples.append(time.perf_counter_ns() - t0)
    return float(statistics.median(samples)), out


def run():
    import random
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
                half_signature = (int(half_out.best_shift), int(half_out.best_hits),
                                  int(half_out.proof_attempts), int(half_out.exact_proofs),
                                  int(half_out.strata_with_support))
                for placement_id, (aoff, boff) in enumerate(PLACEMENTS):
                    carrier = bytearray(random.Random(33000 + size + placement_id).randbytes(CARRIER_BYTES))
                    carrier[aoff:aoff + size] = source
                    carrier[boff:boff + size] = target
                    arr = (ctypes.c_uint8 * len(carrier)).from_buffer_copy(carrier)
                    ns, out = _median_relation(relation, arr, len(carrier), aoff, boff, size)
                    enabled = int(out.exact_proofs) >= 4
                    correct = enabled == expected_enable and (
                        not enabled or expected_shift is None or int(out.best_shift) == expected_shift
                    )
                    signature = (int(out.best_shift), int(out.best_hits), int(out.proof_attempts),
                                 int(out.exact_proofs), int(out.strata_with_support))
                    all_ok &= correct and signature == half_signature
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
                        "gate_enable": enabled,
                        "best_shift": int(out.best_shift),
                        "best_hits": int(out.best_hits),
                        "proof_attempts": int(out.proof_attempts),
                        "exact_proofs": int(out.exact_proofs),
                        "strata_with_support": int(out.strata_with_support),
                        "modeled_read_fraction": read_fraction,
                        "rebased_median_ns": ns,
                        "equivalent_half_median_ns": half_ns,
                        "rebased_over_half": ratio,
                        "signature_matches_half": signature == half_signature,
                        "classification_correct": correct,
                    })
        passed = all_ok and cost_ok and placement_ok
        return {
            "schema": "cmpct-one-g02-shift-branch-bound-rebased-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_relation_sizes": list(RELATION_SIZES),
            "frozen_placements": [list(x) for x in PLACEMENTS],
            "frozen_max_relative_cost_32k_plus": MAX_RELATIVE_COST,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "decision": "advance_rebased_arbitrary_relation_transfer" if passed else "retire_rebased_arbitrary_relation_transfer",
            "claim_boundary": "writer-side structural transfer only; automatic candidate discovery remains external and no reader/product/comparator authority is granted",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_rebased_arbitrary_relation_transfer" else 1)
