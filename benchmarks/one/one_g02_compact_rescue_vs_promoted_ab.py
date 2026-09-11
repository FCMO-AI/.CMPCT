"""ONE-G0.2 end-to-end carrying-cost A/B for compact starvation rescue.

Referee freeze before result-bearing execution
==============================================
The compact modulo-position queue passed its internal representation gate at exact source
7fe2f7f2...: 47,104 B vs 71,680 B state with exact recurrence traces and no material
queue-vs-queue compute loss. That does not establish global value. The earlier unoptimized
compiled starvation gate was 5.3-7.1% slower than the promoted 8 KiB tail-return minimizer
on entropy controls and 3.77x slower on the tiny hard-rescue row.

This experiment charges the complete compact starvation path (Gear signal, 4,096-byte
history, activation replay, compact exact queue) against the current promoted tail-return
8 KiB selector on the same native runner. It does not change the gate, Gear table, 4,096
span, 8,192 promoted dispatch boundary, or recurrence semantics.

Falsifiable hypothesis: after linear activation build + compact positions, the rescue path
reverses the ordinary-path compute debt enough to be a credible research seed while
preserving its exact gated recurrence. Promotion is NOT at issue.

Frozen seed gate:
- exact gated trace/state/accounting against the independent Python recurrence on every row;
- candidate state <=1.15x promoted state on every >=8 KiB row;
- median candidate/promoted <=0.98 on random and zlib-random 1 MiB;
- median <=1.02 on repeated and shifted large controls;
- any large ordinary row >1.05 retires this implementation as a global carrying path.
The tiny hard-rescue row is measured but not averaged away: >1.20x opens explicit small-case
creation debt; <=1.20x closes that debt for this research gate.

Claim boundary: encoder-discovery research only. No stored-byte, reader, product, comparator,
release, access, integrity, recovery, or portability authority.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _python_trace, _cases
from benchmarks.one.one_g02_starvation_compact_queue_ab import _R, _bind, _call

ROUNDS = 13


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-compact-carry-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
        str(here / "one_g02_minimizer_offset_only_kernel.c"),
        str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
        str(here / "one_g02_starvation_compact_queue_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)), td


def _paired(base, cand):
    ratios=[]; base_ns=[]; cand_ns=[]
    for i in range(ROUNDS):
        if i % 2 == 0:
            t=time.perf_counter_ns(); base(); a=time.perf_counter_ns()-t
            t=time.perf_counter_ns(); cand(); b=time.perf_counter_ns()-t
        else:
            t=time.perf_counter_ns(); cand(); b=time.perf_counter_ns()-t
            t=time.perf_counter_ns(); base(); a=time.perf_counter_ns()-t
        base_ns.append(a); cand_ns.append(b); ratios.append(b/a)
    return ratios, base_ns, cand_ns


def run():
    lib, td = _build()
    try:
        baseline = _bind_dispatch(lib)
        compact = _bind(lib, "one_g02_starvation_compact_queue_kernel")
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows=[]
        for name,data in _cases().items():
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data)
            cap=max(1,len(data)); trace=(ctypes.c_uint64*cap)()
            co=_call(compact,gear,arr,len(data),trace,cap)
            expected=_python_trace(data)
            actual=[int(trace[i]) for i in range(int(co.emitted))]
            exact=(actual==expected[0] and int(co.final_state)==expected[1]
                   and int(co.positions_considered)==expected[2]
                   and int(co.sparse_anchors)==expected[3]
                   and int(co.rescue_active_positions)==expected[4]
                   and int(co.replayed_history_bytes)==expected[5])
            if not exact:
                raise AssertionError((name,"compact gated recurrence mismatch"))
            bo=_call_dispatch(baseline,gear,arr,len(data))
            ratios,bns,cns=_paired(
                lambda:_call_dispatch(baseline,gear,arr,len(data)),
                lambda:_call(compact,gear,arr,len(data)))
            rows.append({
                "case":name,"input_bytes":len(data),"exact_gated_recurrence":exact,
                "median_compact_over_promoted":statistics.median(ratios),
                "p90_compact_over_promoted":sorted(ratios)[int(.9*(len(ratios)-1))],
                "median_promoted_ns":statistics.median(bns),
                "median_compact_ns":statistics.median(cns),
                "promoted_reserved_state_bytes":int(bo.reserved_state_bytes),
                "compact_reserved_state_bytes":int(co.reserved_state_bytes),
                "state_ratio":int(co.reserved_state_bytes)/int(bo.reserved_state_bytes),
                "sparse_anchors":int(co.sparse_anchors),
                "rescue_active_positions":int(co.rescue_active_positions),
                "replayed_history_bytes":int(co.replayed_history_bytes),
                "peak_queue_entries":int(co.peak_queue_entries),
                "rescue_emitted":int(co.emitted),
            })
        m={r["case"]:r for r in rows}
        large_ok=(m["random_1mib"]["median_compact_over_promoted"]<=.98
                  and m["zlib_random_1mib"]["median_compact_over_promoted"]<=.98
                  and m["repeat_64k_basis_1mib"]["median_compact_over_promoted"]<=1.02
                  and m["shifted_512k_insert1"]["median_compact_over_promoted"]<=1.02
                  and max(m[k]["median_compact_over_promoted"] for k in
                          ("random_1mib","zlib_random_1mib","repeat_64k_basis_1mib","shifted_512k_insert1"))<=1.05)
        state_ok=all(r["state_ratio"]<=1.15 for r in rows if r["input_bytes"]>=8192)
        hard=m["transfer_starved_seed10_insert1"]["median_compact_over_promoted"]
        if large_ok and state_ok:
            decision=("advance_compact_rescue_for_integration" if hard<=1.20
                      else "advance_compact_rescue_seed_with_small_case_debt")
        else:
            decision="retire_compact_rescue_as_global_carrying_path"
        return {
            "schema":"cmpct-one-g02-compact-rescue-vs-promoted-ab-v1",
            "experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds":ROUNDS,
            "frozen_seed_gate":{"entropy_max_ratio":.98,"repeated_shifted_max_ratio":1.02,
                "large_retire_ratio":1.05,"max_state_ratio":1.15,"small_case_debt_ratio":1.20},
            "decision":decision,
            "claim_boundary":"encoder-discovery research only; no stored-byte/reader/product/comparator/release authority",
            "rows":rows,
        }
    finally:
        td.cleanup()

if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
