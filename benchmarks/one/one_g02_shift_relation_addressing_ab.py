"""ONE-G0.2 direct addressing-shape A/B for arbitrary proof-led relations.

Frozen before result-bearing execution.

The first arbitrary-offset relation kernel transferred semantics but cost 1.16-1.28x the compact
half-layout baseline at 32/64 KiB. The superseding Builder rebases source/target pointers once and keeps
hot coordinates relation-local. This direct A/B runs both arbitrary kernels over identical carrier bytes,
so any elapsed delta is attributable to address/bounds code shape rather than corpus or admission changes.

Hypothesis: pointer rebasing preserves exact result structs and reduces median elapsed by at least 8% on
every frozen 32/64 KiB relation row. This deliberately asks for a large causal effect, not a marginal win.
Disproof retires pointer rebasing as the main cost owner even if another absolute transfer gate happens to
pass through noise. Do not lower the 8% threshold after result.
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

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import (
    CARRIER_BYTES,
    PLACEMENTS,
    Result,
    _relation_cases,
)

SIZES = (32 * 1024, 64 * 1024)
MIN_SPEEDUP = 0.08


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-addressing-ab-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_shift_branch_bound_relation_kernel.c"),
         str(here / "one_g02_shift_branch_bound_relation_rebased_kernel.c"),
         "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    old = cdll.one_g02_shift_branch_bound_relation
    new = cdll.one_g02_shift_branch_bound_relation_rebased
    args = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
            ctypes.POINTER(Result)]
    old.argtypes = args; old.restype = ctypes.c_int
    new.argtypes = args; new.restype = ctypes.c_int
    return old, new, td


def _once(fn, arr, n, aoff, boff, rlen, out):
    rc = fn(arr, n, aoff, boff, rlen, ctypes.byref(out))
    if rc:
        raise RuntimeError(f"kernel returned {rc}")


def _paired(old, new, arr, n, aoff, boff, rlen):
    oo = Result(); no = Result()
    _once(old, arr, n, aoff, boff, rlen, oo)
    _once(new, arr, n, aoff, boff, rlen, no)
    old_samples = []
    new_samples = []
    # O-N-N-O pairing suppresses first-order runner drift.
    for _ in range(101):
        t = time.perf_counter_ns(); _once(old, arr, n, aoff, boff, rlen, oo); o1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); _once(new, arr, n, aoff, boff, rlen, no); n1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); _once(new, arr, n, aoff, boff, rlen, no); n2 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); _once(old, arr, n, aoff, boff, rlen, oo); o2 = time.perf_counter_ns() - t
        old_samples.append((o1 + o2) * 0.5)
        new_samples.append((n1 + n2) * 0.5)
    return float(statistics.median(old_samples)), float(statistics.median(new_samples)), oo, no


def _sig(x: Result):
    return tuple(int(getattr(x, name)) for name, _ in Result._fields_)


def run():
    old, new, td = _build()
    rows = []
    try:
        passed = True
        for size in SIZES:
            for case, (source, target, _, _) in _relation_cases(size).items():
                for placement, (aoff, boff) in enumerate(PLACEMENTS):
                    carrier = bytearray(random.Random(41000 + size + placement).randbytes(CARRIER_BYTES))
                    carrier[aoff:aoff + size] = source
                    carrier[boff:boff + size] = target
                    arr = (ctypes.c_uint8 * len(carrier)).from_buffer_copy(carrier)
                    old_ns, new_ns, oo, no = _paired(old, new, arr, len(carrier), aoff, boff, size)
                    exact = _sig(oo) == _sig(no)
                    speedup = 1.0 - new_ns / old_ns
                    passed &= exact and speedup >= MIN_SPEEDUP
                    rows.append({
                        "relation_bytes": size,
                        "case": case,
                        "placement": placement,
                        "old_median_ns": old_ns,
                        "rebased_median_ns": new_ns,
                        "rebased_over_old": new_ns / old_ns,
                        "rebasing_speedup_fraction": speedup,
                        "result_struct_exact": exact,
                    })
        return {
            "schema": "cmpct-one-g02-shift-relation-addressing-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_min_speedup": MIN_SPEEDUP,
            "decision": "address_rebasing_is_material_cost_owner" if passed else "address_rebasing_not_sufficient_cost_owner",
            "claim_boundary": "writer-side causal compute attribution only; no representation/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "address_rebasing_is_material_cost_owner" else 1)
