"""ONE-G0.2 hostile false-pattern transfer for the shift-coverage gate.

Frozen before the coverage gate has produced a result-bearing CI artifact.

A one-byte grid can be cheap and phase-robust yet still confuse sparse resemblance with exact reusable
structure. This transfer constructs a +1-looking second half but injects one mismatch every 32 bytes at
positions that do not coincide with the 64-byte probe grid. Exact matching spans are therefore shorter
than ONE's 64-byte reuse minimum even though the probe sees coherent +1 support.

Disproof: if the minimizer has zero positive marginal opportunity over fixed observation and the coverage
gate enables, retire one-byte coverage as a sufficient admission signal. Do not move the mismatch phase,
change stride/majority, or reinterpret probe matches as stored-byte savings after execution.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_shift_coverage_gate_ab import CoverageResult, MIN_HITS, MAJORITY_DEN, MAJORITY_NUM
from experiments.one.observe import observe


def _fragmented_shift(seed: int, n: int, spacing: int) -> bytes:
    a = random.Random(seed).randbytes(n)
    b = bytearray(b"X" + a[:-1])
    # Deliberately offset from probe positions (probe q for +1 is 3 mod 64).
    # spacing=32 caps exact spans below MIN_RUN=64; spacing=96 is a transfer control
    # where useful exact spans can still survive.
    for j in range(16, n, spacing):
        b[j] ^= 0xA7
    return a + bytes(b)


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-coverage-false-pattern-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_shift_coverage_gate_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cdll = ctypes.CDLL(str(lib))
    fn = cdll.one_g02_shift_coverage_gate
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(CoverageResult)]
    fn.restype = ctypes.c_int
    return fn, td


def run():
    fn, td = _build()
    rows = []
    try:
        for name, data in {
            "fragmented_shift_every32": _fragmented_shift(8101, 64 * 1024, 32),
            "fragmented_shift_every96_control": _fragmented_shift(8102, 64 * 1024, 96),
        }.items():
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW,
                            max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            minimizer = _minimizer_observe(data)
            marginal = minimizer.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            out = CoverageResult()
            rc = fn(arr, len(data), ctypes.byref(out))
            if rc != 0:
                raise RuntimeError(f"coverage gate returned {rc}")
            required = max(MIN_HITS, (int(out.samples) * MAJORITY_NUM + MAJORITY_DEN - 1) // MAJORITY_DEN)
            enabled = fixed.stats.reuse_opportunity_bytes == 0 and int(out.best_hits) >= required
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "minimizer_opportunity_bytes": minimizer.reuse_opportunity_bytes,
                "marginal_opportunity_bytes": marginal,
                "positive_marginal": marginal > 0,
                "samples": int(out.samples),
                "best_hits": int(out.best_hits),
                "required_hits": required,
                "best_shift": int(out.best_shift),
                "gate_enable": enabled,
                "classification_correct": enabled == (marginal > 0),
            })
        passed = all(r["classification_correct"] for r in rows)
        return {
            "schema": "cmpct-one-g02-shift-coverage-false-pattern-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "decision": "advance_coverage_false_pattern_transfer" if passed else "retire_one_byte_coverage_admission",
            "claim_boundary": "hostile writer-discovery falsification only; no product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_coverage_false_pattern_transfer" else 1)
