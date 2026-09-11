"""ONE-G0.2 amortization-safe known-pair relation gate integration.

Frozen by ONE_G02_AMORTIZATION_SAFE_RELATION_GATE_PREREG_2026-09-05.md.
The sparse detector is unchanged. Admission is derived from its fixed 160-byte
maximum comparison cost and the frozen 1% information-read budget: below 16,000
bytes use exact safe proof directly; at/above 16,000 bytes use the sparse gate
before exact proof.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
ROUNDS = 41
BATCH_CALLS = 16
BOUNDARY = 16000
MAX_ROW_RATIO = 1.03
MAX_MEDIAN_RATIO = 0.95
MAX_GATE_READ_FRACTION = 0.01


class Measurement(ctypes.Structure):
    _fields_ = [
        ("candidate_ns_per_batch", ctypes.c_double),
        ("baseline_ns_per_batch", ctypes.c_double),
        ("gate_compared_bytes", ctypes.c_uint64),
        ("gate_fires", ctypes.c_uint64),
        ("gate_rejects", ctypes.c_uint64),
        ("direct_pairs", ctypes.c_uint64),
        ("baseline_enabled", ctypes.c_uint64),
        ("candidate_enabled", ctypes.c_uint64),
        ("productive_retained", ctypes.c_uint64),
        ("false_controls", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-amort-safe-gate-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
        str(here / "one_g02_shift_relation_sparse_gate_kernel.c"),
        str(here / "one_g02_shift_relation_amortization_safe_gate_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    measure = c.one_g02_shift_relation_amortization_safe_measure
    measure.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(Measurement)]
    measure.restype = ctypes.c_int
    baseline = c.one_g02_shift_relation_safe_dispatch
    baseline.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                         ctypes.c_size_t, ctypes.POINTER(Result)]
    baseline.restype = ctypes.c_int
    candidate = c.one_g02_shift_relation_amortization_safe_gate
    candidate.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                          ctypes.c_size_t, ctypes.POINTER(Result),
                          ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int)]
    candidate.restype = ctypes.c_int
    return measure, baseline, candidate, td


def _ptr(arr, offset: int):
    return ctypes.cast(ctypes.byref(arr, offset), ctypes.POINTER(ctypes.c_uint8))


def run():
    measure, baseline, candidate, td = _build()
    rows = []
    case_rows = []
    try:
        ratios = []
        all_exact = all_cost = all_reads = all_eligible_reject = True
        for size in SIZES:
            cases = _relation_cases(size)
            packed = b"".join(src + dst for src, dst, _expected, _shift in cases.values())
            arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
            cand_samples, base_samples = [], []
            last = Measurement()
            for _ in range(ROUNDS):
                m = Measurement()
                rc = measure(arr, size, len(cases), BATCH_CALLS, ctypes.byref(m))
                if rc:
                    raise RuntimeError(f"measure failed at {size}: {rc}")
                cand_samples.append(float(m.candidate_ns_per_batch))
                base_samples.append(float(m.baseline_ns_per_batch))
                last = m
            cand_ns = float(statistics.median(cand_samples))
            base_ns = float(statistics.median(base_samples))
            ratio = cand_ns / base_ns
            ratios.append(ratio)
            logical = len(cases) * size
            read_fraction = int(last.gate_compared_bytes) / logical

            classification_exact = True
            productive = retained = 0
            offset = 0
            used_gate_count = 0
            rejects = 0
            for case, (_src, _dst, expected_enable, expected_shift) in cases.items():
                b = Result(); c = Result(); reads = ctypes.c_uint64(); used = ctypes.c_int()
                srcp = _ptr(arr, offset); dstp = _ptr(arr, offset + size)
                brc = baseline(srcp, dstp, size, ctypes.byref(b))
                crc = candidate(srcp, dstp, size, ctypes.byref(c), ctypes.byref(reads), ctypes.byref(used))
                if brc < 0 or crc < 0:
                    raise RuntimeError(f"classification call failed at {size}/{case}: {brc}/{crc}")
                ben = int(b.exact_proofs) >= 4
                cen = int(c.exact_proofs) >= 4
                if ben:
                    productive += 1
                    retained += int(cen and int(c.best_shift) == int(b.best_shift))
                exact = (ben == cen) and (not ben or int(c.best_shift) == int(b.best_shift))
                classification_exact &= exact
                used_gate_count += int(bool(used.value))
                rejects += int(bool(used.value) and not bool(crc))
                case_rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "expected_enable_from_frozen_case": bool(expected_enable),
                    "expected_shift_from_frozen_case": expected_shift,
                    "baseline_enable": ben,
                    "candidate_enable": cen,
                    "baseline_best_shift": int(b.best_shift),
                    "candidate_best_shift": int(c.best_shift),
                    "used_sparse_gate": bool(used.value),
                    "gate_fired": bool(crc) if used.value else None,
                    "gate_compared_bytes": int(reads.value),
                    "classification_exact": exact,
                })
                offset += 2 * size

            row_exact = (classification_exact and
                         int(last.baseline_enabled) == int(last.candidate_enabled) and
                         int(last.productive_retained) == int(last.baseline_enabled) and
                         retained == productive)
            row_cost = ratio <= MAX_ROW_RATIO
            read_ok = read_fraction <= MAX_GATE_READ_FRACTION
            eligible = size >= BOUNDARY
            reject_ok = (not eligible) or rejects >= 1
            all_exact &= row_exact
            all_cost &= row_cost
            all_reads &= read_ok
            all_eligible_reject &= reject_ok
            rows.append({
                "relation_bytes": size,
                "pair_count": len(cases),
                "candidate_median_ns_per_batch": cand_ns,
                "baseline_median_ns_per_batch": base_ns,
                "candidate_over_baseline": ratio,
                "gate_compared_bytes": int(last.gate_compared_bytes),
                "gate_read_fraction_of_relation_bytes": read_fraction,
                "gate_fires": int(last.gate_fires),
                "gate_rejects": int(last.gate_rejects),
                "direct_pairs": int(last.direct_pairs),
                "used_gate_count_recheck": used_gate_count,
                "baseline_enabled": int(last.baseline_enabled),
                "candidate_enabled": int(last.candidate_enabled),
                "productive_retained": int(last.productive_retained),
                "false_controls": int(last.false_controls),
                "classification_exact": row_exact,
                "row_cost_pass": row_cost,
                "gate_read_pass": read_ok,
                "eligible_reject_pass": reject_ok,
            })

        median_ratio = float(statistics.median(ratios))
        passed = all_exact and all_cost and all_reads and all_eligible_reject and median_ratio <= MAX_MEDIAN_RATIO
        return {
            "schema": "cmpct-one-g02-shift-relation-amortization-safe-gate-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "derived_boundary_bytes": BOUNDARY,
            "frozen_sizes": list(SIZES),
            "frozen_rounds": ROUNDS,
            "frozen_batch_calls": BATCH_CALLS,
            "frozen_max_row_ratio": MAX_ROW_RATIO,
            "frozen_max_median_ratio": MAX_MEDIAN_RATIO,
            "frozen_max_gate_read_fraction": MAX_GATE_READ_FRACTION,
            "median_candidate_over_baseline": median_ratio,
            "decision": "advance_known_pair_amortization_safe_gate" if passed else "retire_or_reform_amortization_safe_gate",
            "claim_boundary": "known-pair writer-side turnstile only; arbitrary pair nomination, density, reader speed/access, release authority and v0.29/v0.30 comparison remain outside this result",
            "rows": rows,
            "case_rows": case_rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_known_pair_amortization_safe_gate" else 1)
