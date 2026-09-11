"""ONE-G0.2 hostile transfer for exclusive non-zero-shift gating.

Frozen before result-bearing execution.

The first exclusive-shift gate passed its inherited opportunity matrix and fixed the two causal failures
of the preceding sparse FNV probe.  This transfer asks whether the signal survives cases that were not
used to build it: both displacement signs, two-byte displacement, periodic/low-entropy controls, and an
adversarial phase case where a genuine global shifted relation is damaged only at the eight deterministic
sample locations.

Hypothesis
----------
With the already-frozen 4/8 threshold, the gate will enable every case where the full minimizer has
positive marginal reuse opportunity over fixed observation and disable every zero-marginal case.
No sample locations, displacement set, or threshold may change after this run.

Disproof
--------
Any false negative or false positive retires this deterministic eight-sample gate as a general discovery
gate.  In particular, failure on the phase-damaged shifted case is evidence that point sampling cannot be
the sole admission signal, not permission to add more hand-picked points.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile

from benchmarks.one.one_g02_exclusive_shift_gate_ab import GateResult, MATCH_THRESHOLD
from benchmarks.one.one_g02_gear_replacement_ab import FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from experiments.one.observe import observe


def _shifted_pair(seed: int, n: int, shift: int) -> bytes:
    assert shift in (-2, -1, 1, 2)
    a = random.Random(seed).randbytes(n)
    if shift > 0:
        b = bytes([0xA5]) * shift + a[:-shift]
    else:
        k = -shift
        b = a[k:] + bytes([0x5A]) * k
    return a + b


def _sample_positions(half: int) -> list[int]:
    return [96 + ((half - 192 - 64) * (s + 1)) // 9 for s in range(8)]


def _phase_damaged_shift(seed: int, n: int) -> bytes:
    a = bytearray(random.Random(seed).randbytes(n))
    b = bytearray(b"X" + bytes(a[:-1]))
    # Break only the exact deterministic sample neighborhoods used by the gate.
    # The rest of the ~n-byte +1 relation remains intact and should still be visible
    # to full minimizer observation if the opportunity is genuine.
    for idx, p in enumerate(_sample_positions(n)):
        lo = max(0, p - 2)
        hi = min(n, p + 66)
        for j in range(lo, hi):
            b[j] ^= (0x31 + idx * 17 + j) & 0xFF
    return bytes(a + b)


def _cases() -> dict[str, bytes]:
    n = 64 * 1024
    return {
        "shift_plus1_64k": _shifted_pair(7001, n, 1),
        "shift_minus1_64k": _shifted_pair(7002, n, -1),
        "shift_plus2_64k": _shifted_pair(7003, n, 2),
        "shift_minus2_64k": _shifted_pair(7004, n, -2),
        "phase_damaged_plus1_64k": _phase_damaged_shift(7005, n),
        "periodic_ab_128k": (b"AB" * (n // 2)) * 2,
        "periodic_abc_128k": ((b"ABC" * ((n + 2) // 3))[:n]) * 2,
        "independent_random_128k": random.Random(7006).randbytes(2 * n),
        "zeros_128k": b"\x00" * (2 * n),
    }


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-exclusive-transfer-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_exclusive_shift_gate_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cdll = ctypes.CDLL(str(lib))
    fn = cdll.one_g02_exclusive_shift_gate
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(GateResult)]
    fn.restype = ctypes.c_int
    return fn, td


def run():
    fn, td = _build()
    rows = []
    try:
        for name, data in _cases().items():
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW,
                            max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            minimizer = _minimizer_observe(data)
            marginal = minimizer.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            positive = marginal > 0
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            out = GateResult()
            rc = fn(arr, len(data), ctypes.byref(out))
            if rc != 0:
                raise RuntimeError(f"gate returned {rc} for {name}")
            enabled = (
                fixed.stats.reuse_opportunity_bytes == 0
                and int(out.exclusive_shift_matches) >= MATCH_THRESHOLD
            )
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "minimizer_opportunity_bytes": minimizer.reuse_opportunity_bytes,
                "marginal_opportunity_bytes": marginal,
                "positive_marginal": positive,
                "gate_enable": enabled,
                "exclusive_shift_matches": int(out.exclusive_shift_matches),
                "zero_shift_matches": int(out.zero_shift_matches),
                "best_shift": int(out.best_shift),
                "compared_bytes": int(out.compared_bytes),
                "classification_correct": enabled == positive,
            })
        passed = all(r["classification_correct"] for r in rows)
        return {
            "schema": "cmpct-one-g02-exclusive-shift-gate-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_threshold": MATCH_THRESHOLD,
            "decision": "advance_exclusive_shift_transfer" if passed else "retire_deterministic_point_sample_gate",
            "claim_boundary": "hostile writer-discovery transfer only; no product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_exclusive_shift_transfer" else 1)
