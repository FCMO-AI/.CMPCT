"""ONE-G0.2 sparse opportunity gate integrated before exact relation proof.

Frozen before result-bearing execution.

Mission Lock
------------
The overlap-safe generalized relation writer now transfers from 4 KiB through
256 KiB, but that isolated result still pays full proof/search work for every
already-nominated relation pair. This experiment asks whether a very cheap,
content-only falsifier can reject obvious non-relations before the exact proof
without losing any productive Law opportunity.

The gate samples 16 evenly spaced positions and only the four bounded shifts
already owned by the downstream proof kernel (-2,-1,+1,+2). Two supporting
samples are enough to admit full proof. This deliberately permissive threshold
is derived from the random null (16/256 expected hits per shift), not tuned to a
workload. The downstream exact proof remains authoritative.

Frozen corpus: the unchanged five relation-transfer cases at 4, 8, 16, 32, 64,
128 and 256 KiB. Each size is measured as one mixed batch containing all five
cases, so negative-control savings must pay for gate overhead on productive
cases. Candidate pair identity is supplied by the frozen adjacent-relation
batch; arbitrary pair discovery remains explicit debt for the later fused
observer experiment.

Advance requires, at every size:
- identical enabled/disabled classification versus the ungated safe dispatcher;
- identical best shift for every enabled relation;
- 100% retention of baseline productive relations;
- at least one cheaply rejected pair in the five-case batch;
- gate compared bytes <= 1.0% of logical relation bytes in the batch;
- gated/baseline elapsed <= 1.03x (no material local regression).

Across the seven sizes, median gated/baseline must be <= 0.95x. No aggregate may
hide a correctness loss. A timing miss retires this exact sparse gate shape; it
does not weaken the already-proven generalized relation representation.
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
MAX_ROW_RATIO = 1.03
MAX_MEDIAN_RATIO = 0.95
MAX_GATE_READ_FRACTION = 0.01


class Measurement(ctypes.Structure):
    _fields_ = [
        ("gated_ns_per_batch", ctypes.c_double),
        ("baseline_ns_per_batch", ctypes.c_double),
        ("gate_compared_bytes", ctypes.c_uint64),
        ("gate_fires", ctypes.c_uint64),
        ("gate_rejects", ctypes.c_uint64),
        ("baseline_enabled", ctypes.c_uint64),
        ("gated_enabled", ctypes.c_uint64),
        ("productive_retained", ctypes.c_uint64),
        ("false_controls", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-sparse-relation-gate-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
            str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
            str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"),
            str(here / "one_g02_shift_relation_sparse_gate_kernel.c"),
            "-o", str(lib),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    measure = c.one_g02_shift_relation_sparse_gate_measure
    measure.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(Measurement)]
    measure.restype = ctypes.c_int
    baseline = c.one_g02_shift_relation_safe_dispatch
    baseline.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                         ctypes.c_size_t, ctypes.POINTER(Result)]
    baseline.restype = ctypes.c_int
    gated = c.one_g02_shift_relation_sparse_gate
    gated.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                      ctypes.c_size_t, ctypes.POINTER(Result), ctypes.POINTER(ctypes.c_uint64)]
    gated.restype = ctypes.c_int
    return measure, baseline, gated, td


def _ptr(arr, offset: int):
    return ctypes.cast(ctypes.byref(arr, offset), ctypes.POINTER(ctypes.c_uint8))


def run():
    measure, baseline, gated, td = _build()
    rows = []
    case_rows = []
    try:
        all_exact = True
        all_row_cost = True
        all_gate_reads = True
        all_reject = True
        ratios = []
        for size in SIZES:
            cases = _relation_cases(size)
            packed = b"".join(src + dst for src, dst, _expected, _shift in cases.values())
            arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)

            gated_samples = []
            baseline_samples = []
            last = Measurement()
            for _ in range(ROUNDS):
                m = Measurement()
                rc = measure(arr, size, len(cases), BATCH_CALLS, ctypes.byref(m))
                if rc:
                    raise RuntimeError(f"measure failed at {size}: {rc}")
                gated_samples.append(float(m.gated_ns_per_batch))
                baseline_samples.append(float(m.baseline_ns_per_batch))
                last = m
            gated_ns = float(statistics.median(gated_samples))
            baseline_ns = float(statistics.median(baseline_samples))
            ratio = gated_ns / baseline_ns
            ratios.append(ratio)
            logical_batch_bytes = len(cases) * size
            gate_read_fraction = int(last.gate_compared_bytes) / logical_batch_bytes

            classification_exact = True
            productive = 0
            retained = 0
            offset = 0
            for case, (_src, _dst, expected_enable, expected_shift) in cases.items():
                b = Result()
                g = Result()
                reads = ctypes.c_uint64()
                srcp = _ptr(arr, offset)
                dstp = _ptr(arr, offset + size)
                brc = baseline(srcp, dstp, size, ctypes.byref(b))
                grc = gated(srcp, dstp, size, ctypes.byref(g), ctypes.byref(reads))
                if brc < 0 or grc < 0:
                    raise RuntimeError(f"classification call failed at {size}/{case}: {brc}/{grc}")
                ben = int(b.exact_proofs) >= 4
                gen = int(g.exact_proofs) >= 4
                if ben:
                    productive += 1
                    retained += int(gen and int(g.best_shift) == int(b.best_shift))
                exact = (ben == gen) and (not ben or int(g.best_shift) == int(b.best_shift))
                classification_exact &= exact
                case_rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "expected_enable_from_frozen_case": bool(expected_enable),
                    "expected_shift_from_frozen_case": expected_shift,
                    "baseline_enable": ben,
                    "gated_enable": gen,
                    "baseline_best_shift": int(b.best_shift),
                    "gated_best_shift": int(g.best_shift),
                    "gate_fired": bool(grc),
                    "gate_compared_bytes": int(reads.value),
                    "classification_exact": exact,
                })
                offset += 2 * size

            row_exact = (
                classification_exact
                and int(last.baseline_enabled) == int(last.gated_enabled)
                and int(last.productive_retained) == int(last.baseline_enabled)
                and retained == productive
            )
            row_cost = ratio <= MAX_ROW_RATIO
            read_ok = gate_read_fraction <= MAX_GATE_READ_FRACTION
            reject_ok = int(last.gate_rejects) >= 1
            all_exact &= row_exact
            all_row_cost &= row_cost
            all_gate_reads &= read_ok
            all_reject &= reject_ok
            rows.append({
                "relation_bytes": size,
                "pair_count": len(cases),
                "gated_median_ns_per_batch": gated_ns,
                "baseline_median_ns_per_batch": baseline_ns,
                "gated_over_baseline": ratio,
                "gate_compared_bytes": int(last.gate_compared_bytes),
                "gate_read_fraction_of_relation_bytes": gate_read_fraction,
                "gate_fires": int(last.gate_fires),
                "gate_rejects": int(last.gate_rejects),
                "baseline_enabled": int(last.baseline_enabled),
                "gated_enabled": int(last.gated_enabled),
                "productive_retained": int(last.productive_retained),
                "false_controls": int(last.false_controls),
                "classification_exact": row_exact,
                "row_cost_pass": row_cost,
                "gate_read_pass": read_ok,
                "cheap_reject_pass": reject_ok,
            })

        median_ratio = float(statistics.median(ratios))
        passed = (
            all_exact and all_row_cost and all_gate_reads and all_reject
            and median_ratio <= MAX_MEDIAN_RATIO
        )
        return {
            "schema": "cmpct-one-g02-shift-relation-sparse-gate-integration-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_rounds": ROUNDS,
            "frozen_batch_calls": BATCH_CALLS,
            "frozen_max_row_ratio": MAX_ROW_RATIO,
            "frozen_max_median_ratio": MAX_MEDIAN_RATIO,
            "frozen_max_gate_read_fraction": MAX_GATE_READ_FRACTION,
            "median_gated_over_baseline": median_ratio,
            "decision": "advance_sparse_relation_gate" if passed else "retire_sparse_relation_gate_shape",
            "claim_boundary": (
                "writer-side relation opportunity gating only; adjacent relation-pair identity is supplied "
                "by the frozen batch and arbitrary-pair discovery, stored bytes, reader speed/access, "
                "v0.29/v0.30 comparison and release authority remain outside this result"
            ),
            "rows": rows,
            "case_rows": case_rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_sparse_relation_gate" else 1)
