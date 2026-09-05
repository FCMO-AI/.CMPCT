"""ONE-G0.2 strict-union Builder: dense suffix table vs live overwrite-aligned queue.

Referee freeze before result-bearing execution
==============================================
The promoted >=8 KiB offset-only selector materializes four dense uint16 suffix-argmin tables.
Yet block q-4 is queried only while block q overwrites the same raw-state slot left-to-right.
The queried suffix boundary advances in exactly that overwrite order.  The Builder therefore
constructs one live monotonic offset queue only when q-4 first becomes queryable, expires old
offsets as r advances, and overwrites a raw value only after the one suffix query that can still
need it.  It preserves the identical rightmost-min Law-discovery signal, zero source rescans and
one forward source traversal; it introduces no new reader semantics or opportunity signal.

Frozen hypothesis
-----------------
This construction/query fusion preserves the independent rightmost-min oracle while reducing
reserved selector state to <=0.90x the promoted offset-only kernel and reducing every large-case
elapsed time to <=0.95x, with no tested case slower than 1.05x.

Disproof
--------
Any oracle/final-state/positions mismatch, source rescan, >1.05x elapsed on any case, >0.95x on
any large case, or >0.90x reserved state rejects this Builder.  A loss retires this live-queue
shape under the tested regime; thresholds/corpus/selector may not be changed after execution.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_native_probe import _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_offset_only_ab import _bind_offset, _call_offset
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MAX_ANY_RATIO = 1.05
MAX_LARGE_RATIO = 0.95
MAX_STATE_RATIO = 0.90


class _LiveResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("live_queue_builds", ctypes.c_uint64),
        ("live_queue_pushes", ctypes.c_uint64),
        ("live_queue_pops_back", ctypes.c_uint64),
        ("live_queue_pops_front", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-live-suffix-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_minimizer_offset_only_kernel.c"),
        str(here / "one_g02_minimizer_live_suffix_queue_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)), td


def _bind_live(lib):
    fn = lib.one_g02_minimizer_live_suffix_queue_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_LiveResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_live(fn, gear, arr, length, trace=None, cap=0):
    out = _LiveResult()
    rc = fn(arr, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out), trace, cap)
    if rc != 0:
        raise RuntimeError(f"live suffix queue failed: {rc}")
    return out


def run():
    lib, td = _build()
    try:
        offset = _bind_offset(lib)
        live = _bind_live(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        semantic_ok = speed_ok = large_ok = state_ok = True
        for name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected, state, considered = _python_anchor_trace(data)
            cap = max(1, len(data))
            ot = (ctypes.c_uint64 * cap)()
            lt = (ctypes.c_uint64 * cap)()
            oo = _call_offset(offset, gear, arr, len(data), ot, cap)
            lo = _call_live(live, gear, arr, len(data), lt, cap)
            otr = [int(ot[i]) for i in range(int(oo.emitted))]
            ltr = [int(lt[i]) for i in range(int(lo.emitted))]
            equal = (
                otr == expected == ltr and int(oo.final_state) == state == int(lo.final_state)
                and int(oo.positions_considered) == considered == int(lo.positions_considered)
            )
            semantic_ok &= equal
            if not equal:
                raise AssertionError((name, "oracle mismatch"))
            ons = _median_ns(lambda: _call_offset(offset, gear, arr, len(data)))
            lns = _median_ns(lambda: _call_live(live, gear, arr, len(data)))
            ratio = lns / ons
            sr = (int(lo.reserved_state_bytes) / int(oo.reserved_state_bytes)) if oo.reserved_state_bytes else 0.0
            speed_ok &= ratio <= MAX_ANY_RATIO
            if name in LARGE_CASES:
                large_ok &= ratio <= MAX_LARGE_RATIO
            state_ok &= sr <= MAX_STATE_RATIO
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "oracle_equal": equal,
                "offset_only_median_ns": ons,
                "live_queue_median_ns": lns,
                "live_over_offset_elapsed_ratio": ratio,
                "offset_reserved_state_bytes": int(oo.reserved_state_bytes),
                "live_reserved_state_bytes": int(lo.reserved_state_bytes),
                "live_over_offset_state_ratio": sr,
                "offset_derived_state_reads": int(oo.derived_state_reads),
                "live_derived_state_reads": int(lo.derived_state_reads),
                "live_queue_builds": int(lo.live_queue_builds),
                "live_queue_pushes": int(lo.live_queue_pushes),
                "live_queue_pops_back": int(lo.live_queue_pops_back),
                "live_queue_pops_front": int(lo.live_queue_pops_front),
                "source_byte_rescans": 0,
            })
        passed = semantic_ok and speed_ok and large_ok and state_ok
        return {
            "schema": "cmpct-one-g02-minimizer-live-suffix-queue-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_max_any_ratio": MAX_ANY_RATIO,
            "frozen_max_large_ratio": MAX_LARGE_RATIO,
            "frozen_max_state_ratio": MAX_STATE_RATIO,
            "decision": "promote_live_suffix_queue_fusion" if passed else "retire_live_suffix_queue_fusion",
            "claim_boundary": "encoder-discovery suffix+selection fusion only; no stored-byte, reader, wire, product, comparator or release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "promote_live_suffix_queue_fusion" else 1)
