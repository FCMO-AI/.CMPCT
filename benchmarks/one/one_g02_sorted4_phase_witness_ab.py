"""ONE-G0.2 exact sorted-4 vs heap phase-witness selector A/B."""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_fused_phase_witness_native_cost import (
    LARGE_REPS,
    MODELED_INCREMENTAL_STATE_BYTES,
    Stats,
    _buf,
    _c_source as _control_source,
    _cases,
    _native_cert,
    _reference,
)

PAIRED_ROUNDS = 9
GATE_NAMES = {
    "random_1mib",
    "compressed_like_1mib",
    "repeated_1mib",
    "shifted_version_1mib",
    "zeros_1mib",
}

SORTED_OFFER = r'''static inline void offer(uint64_t h,uint32_t pos,uint64_t hs[K],uint32_t ps[K],unsigned *cnt,uint64_t *adm,uint64_t *rep) {
  if(*cnt<K) {
    unsigned i=*cnt;
    while(i && (h<hs[i-1u] || (h==hs[i-1u] && pos<ps[i-1u]))) {
      hs[i]=hs[i-1u]; ps[i]=ps[i-1u]; i--;
    }
    hs[i]=h; ps[i]=pos; (*cnt)++; (*adm)++; return;
  }
  /* Positions arrive monotonically.  Equal-hash newcomers are later and cannot
     improve the already-held earliest tie, so the common path is one compare. */
  if(h>=hs[K-1u]) return;
  unsigned i=K-1u;
  while(i && (h<hs[i-1u] || (h==hs[i-1u] && pos<ps[i-1u]))) {
    hs[i]=hs[i-1u]; ps[i]=ps[i-1u]; i--;
  }
  hs[i]=h; ps[i]=pos; (*adm)++; (*rep)++;
}
'''


def _candidate_source() -> str:
    src = _control_source()
    start = src.index("static inline void offer(")
    end = src.index("static inline uint64_t baseline_once", start)
    return src[:start] + SORTED_OFFER + src[end:]


def _build_source(td: str, stem: str, source: str):
    c_path = Path(td) / f"{stem}.c"
    so_path = Path(td) / f"{stem}.so"
    c_path.write_text(source)
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared", str(c_path), "-o", str(so_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lib = ctypes.CDLL(str(so_path))
    p8 = ctypes.POINTER(ctypes.c_uint8)
    lib.run_fused.argtypes = [p8, ctypes.c_size_t, ctypes.c_uint, ctypes.POINTER(Stats)]
    lib.run_fused.restype = ctypes.c_uint64
    lib.phase_exact.argtypes = [
        p8,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.phase_exact.restype = ctypes.c_int
    return lib


def _timed(fn, b, n: int, reps: int):
    st = Stats()
    t0 = time.perf_counter_ns()
    fn(b, n, reps, ctypes.byref(st))
    return time.perf_counter_ns() - t0, st


def _paired(control, candidate, b, n: int, reps: int):
    ct = []
    nt = []
    c_last = Stats()
    n_last = Stats()
    for r in range(PAIRED_ROUNDS):
        if r & 1:
            x, n_last = _timed(candidate.run_fused, b, n, reps); nt.append(x)
            x, c_last = _timed(control.run_fused, b, n, reps); ct.append(x)
        else:
            x, c_last = _timed(control.run_fused, b, n, reps); ct.append(x)
            x, n_last = _timed(candidate.run_fused, b, n, reps); nt.append(x)
    return int(statistics.median(ct)), int(statistics.median(nt)), c_last, n_last


def run():
    rows = []
    control_mismatches = []
    candidate_mismatches = []
    with tempfile.TemporaryDirectory(prefix="one_sorted4_phase_") as td:
        control = _build_source(td, "control", _control_source())
        candidate = _build_source(td, "candidate", _candidate_source())
        cases = _cases()
        for name, data in cases.items():
            ref = _reference(data)
            if _native_cert(control, data) != ref:
                control_mismatches.append(name)
            if _native_cert(candidate, data) != ref:
                candidate_mismatches.append(name)
        for name, data in cases.items():
            b = _buf(data)
            n = len(data)
            reps = LARGE_REPS if n >= 1024 * 1024 - 1024 else (1024 if n >= 4096 else 65536)
            ct, nt, cs, ns = _paired(control, candidate, b, n, reps)
            rows.append(
                {
                    "case": name,
                    "input_bytes": n,
                    "internal_repetitions": reps,
                    "paired_rounds": PAIRED_ROUNDS,
                    "control_heap_median_ns": ct,
                    "candidate_sorted4_median_ns": nt,
                    "candidate_over_control": nt / ct,
                    "anchors_equal": int(cs.anchors) == int(ns.anchors),
                    "samples_equal": int(cs.samples) == int(ns.samples),
                    "admissions_control": int(cs.admissions),
                    "admissions_candidate": int(ns.admissions),
                    "replacements_control": int(cs.replacements),
                    "replacements_candidate": int(ns.replacements),
                    "control_witness_equal_reference": name not in control_mismatches,
                    "candidate_witness_equal_reference": name not in candidate_mismatches,
                }
            )
    by = {r["case"]: r for r in rows}
    large = [r for r in rows if r["case"] in GATE_NAMES]
    large_all = [r for r in rows if r["input_bytes"] >= 1024 * 1024 - 1024]
    large_median = statistics.median(r["candidate_over_control"] for r in large)
    exact = not control_mismatches and not candidate_mismatches and all(r["anchors_equal"] and r["samples_equal"] for r in rows)
    gate = (
        exact
        and large_median <= 0.90
        and all(r["candidate_over_control"] <= 1.03 for r in large_all)
        and by["tiny_4k"]["candidate_over_control"] <= 1.05
        and by["tiny_64b"]["candidate_over_control"] <= 1.10
        and MODELED_INCREMENTAL_STATE_BYTES <= 248
    )
    return {
        "schema": "cmpct-one-g02-sorted4-phase-witness-ab-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "control_source_sha": "df083da415fb8aa426c3f6a1ed84cd6d25f5e32d",
        "modeled_incremental_state_bytes": MODELED_INCREMENTAL_STATE_BYTES,
        "control_witness_mismatches": control_mismatches,
        "candidate_witness_mismatches": candidate_mismatches,
        "large_gate_median_candidate_over_control": large_median,
        "decision": "advance_sorted4_selector_rehabilitation" if gate else "retire_selection_local_rehabilitation",
        "claim_boundary": "selector rehabilitation only; unconditional fused certificate remains retired until original carrying-cost gate is rerun",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_sorted4_selector_rehabilitation" else 2)
