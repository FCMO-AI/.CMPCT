"""ONE-G0.2 hostile damage-envelope transfer for stratified branch-bound proof ownership.

Frozen before result-bearing execution.

The stratified topology recovered 1 KiB front/middle/tail damage while preserving the original proof
budget. This transfer asks for a stronger causal bound rather than another friendly example: with a
64 KiB source half and a global +1 shifted target half, how much contiguous target corruption can the
sixteen-stratum / four-proof topology tolerate while useful exact reuse survives?

Hypothesis: for front, middle and tail contiguous corruption at the frozen widths below, every row with
at least 16 KiB of minimizer-positive marginal reuse remains enabled. This corresponds to four 4 KiB
proof strata worth of surviving relation support. Rows below that opportunity floor are diagnostic only;
they may expose the topology's expected recall boundary but cannot be used to tune proof count or strata.

Disproof: any tested placement with >=16 KiB positive minimizer marginal opportunity and gate disabled
retires the claimed 16 KiB contiguous-damage envelope. This does not invalidate the already-proven 1 KiB
transfer or the broader cheap-coverage -> exact-proof principle.
"""
from __future__ import annotations

import ctypes
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from experiments.one.observe import observe

MIN_SURVIVING_MARGINAL = 16 * 1024
WIDTHS_KIB = (1, 4, 8, 16, 24, 32, 40, 48, 52, 56, 60)


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
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-bb-envelope-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_shift_branch_bound_stratified_kernel.c"), "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    fn = cdll.one_g02_shift_branch_bound_stratified
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
    fn.restype = ctypes.c_int
    return fn, td


def _case(seed: int, width: int, placement: str) -> bytes:
    n = 64 * 1024
    a = random.Random(seed).randbytes(n)
    b = bytearray(b"X" + a[:-1])
    if placement == "front":
        lo = 0
    elif placement == "middle":
        lo = (n - width) // 2
    elif placement == "tail":
        lo = n - width
    else:
        raise ValueError(placement)
    lo -= lo % 64
    hi = min(n, lo + width)
    for j in range(lo, hi):
        b[j] ^= (0xA9 + j * 17 + (j - lo) * 29) & 0xFF
    return a + bytes(b)


def run():
    fn, td = _build()
    rows = []
    try:
        envelope_ok = True
        for wi, width_kib in enumerate(WIDTHS_KIB):
            width = width_kib * 1024
            for pi, placement in enumerate(("front", "middle", "tail")):
                data = _case(12000 + wi * 7 + pi, width, placement)
                fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW,
                                max_index_entries=FIXED_MAX_INDEX_ENTRIES)
                mini = _minimizer_observe(data)
                marginal = mini.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
                arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                out = Result()
                rc = fn(arr, len(data), ctypes.byref(out))
                if rc != 0:
                    raise RuntimeError(f"stratified gate returned {rc}")
                enabled = fixed.stats.reuse_opportunity_bytes == 0 and int(out.exact_proofs) >= 4
                in_claimed_envelope = marginal >= MIN_SURVIVING_MARGINAL
                if in_claimed_envelope:
                    envelope_ok &= enabled
                rows.append({
                    "placement": placement,
                    "damage_bytes": width,
                    "input_bytes": len(data),
                    "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                    "minimizer_opportunity_bytes": mini.reuse_opportunity_bytes,
                    "marginal_opportunity_bytes": marginal,
                    "in_claimed_envelope": in_claimed_envelope,
                    "best_hits": int(out.best_hits),
                    "best_shift": int(out.best_shift),
                    "strata_with_support": int(out.strata_with_support),
                    "proof_attempts": int(out.proof_attempts),
                    "exact_proofs": int(out.exact_proofs),
                    "gate_enable": enabled,
                    "modeled_read_fraction": (int(out.coverage_compared_bytes) + int(out.proof_compared_bytes)) / len(data),
                })
        return {
            "schema": "cmpct-one-g02-shift-branch-bound-damage-envelope-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_widths_kib": list(WIDTHS_KIB),
            "frozen_placements": ["front", "middle", "tail"],
            "frozen_min_surviving_marginal_bytes": MIN_SURVIVING_MARGINAL,
            "decision": "advance_16k_contiguous_damage_envelope" if envelope_ok else "retire_16k_contiguous_damage_envelope",
            "claim_boundary": "hostile writer-discovery robustness map only; not product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_16k_contiguous_damage_envelope" else 1)
