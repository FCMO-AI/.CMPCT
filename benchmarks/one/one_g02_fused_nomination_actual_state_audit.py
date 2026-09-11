"""ONE-G0.2 actual-state audit for the fused native nomination kernel.

Frozen by ONE_G02_FUSED_NOMINATION_ACTUAL_STATE_AUDIT_PREREG_2026-09-06.md.
This is a semantic/state audit, not an elapsed benchmark.
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases

SIZES = (64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
CASES = (
    "shift_plus1", "damage_quarter", "fragmented_every96",
    "hostile_fixed_bands", "fragmented_every32", "independent_random",
)
WINDOW = 64
FIXED_RESEARCH_INDEX_BYTES = 198_144


class SelectorResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64), ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64), ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64), ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
    ]


class ConsumerResult(ctypes.Structure):
    _fields_ = [
        ("cross_auditions", ctypes.c_uint64), ("cross_exact", ctypes.c_uint64),
        ("local_peak_entries", ctypes.c_uint64), ("global_peak_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64), ("extension_read_bytes", ctypes.c_uint64),
        ("anchors_consumed", ctypes.c_uint64),
    ]


class FusedResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64), ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64), ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64), ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
        ("cross_auditions", ctypes.c_uint64), ("cross_exact", ctypes.c_uint64),
        ("local_peak_entries", ctypes.c_uint64), ("global_peak_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64), ("extension_read_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fused-state-")
    lib = Path(td.name) / "libstate.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_minimizer_offset_only_kernel.c"),
        str(here / "one_g02_native_nomination_event_consumer_kernel.c"),
        str(here / "one_g02_fused_native_nomination_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    selector = c.one_g02_minimizer_offset_only_kernel
    selector.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(SelectorResult), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
    selector.restype = ctypes.c_int
    consumer = c.one_g02_native_nomination_event_consumer
    consumer.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
        ctypes.POINTER(ConsumerResult)]
    consumer.restype = ctypes.c_int
    fused = c.one_g02_fused_native_nomination
    fused.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(FusedResult), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
    fused.restype = ctypes.c_int
    return selector, consumer, fused, td


def run() -> dict[str, object]:
    selector, consumer, fused, td = _build()
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    rows: list[dict[str, object]] = []
    mismatches: list[tuple[int, int, str]] = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                generated = _cases(size, seed)
                for name in CASES:
                    source, target = generated[name]
                    data = source + target
                    boundary = len(source)
                    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
                    trace = (ctypes.c_uint64 * (len(data) + 1))()
                    sr = SelectorResult()
                    cr = ConsumerResult()
                    fr = FusedResult()
                    rc = selector(buf, len(data), gear, WINDOW, MINIMIZER_SPAN,
                                  ctypes.byref(sr), trace, len(data) + 1)
                    if rc != 0:
                        raise RuntimeError(f"selector rc={rc}")
                    rc = consumer(buf, len(data), boundary, gear, trace, int(sr.emitted), ctypes.byref(cr))
                    if rc != 0:
                        raise RuntimeError(f"consumer rc={rc}")
                    rc = fused(buf, len(data), boundary, gear, WINDOW, MINIMIZER_SPAN,
                               ctypes.byref(fr), None, 0)
                    if rc != 0:
                        raise RuntimeError(f"fused rc={rc}")
                    if (sr.emitted != fr.emitted or sr.final_state != fr.final_state or
                        cr.cross_auditions != fr.cross_auditions or cr.cross_exact != fr.cross_exact):
                        mismatches.append((size, seed, name))
                    ratio = float(fr.reserved_state_bytes) / float(sr.reserved_state_bytes)
                    rows.append({
                        "relation_bytes": size, "seed": seed, "case": name,
                        "selector_reserved_state_bytes": int(sr.reserved_state_bytes),
                        "fused_reserved_state_bytes": int(fr.reserved_state_bytes),
                        "fused_over_selector_state": ratio,
                        "fused_local_peak_entries": int(fr.local_peak_entries),
                        "fused_global_peak_entries": int(fr.global_peak_entries),
                        "cross_auditions": int(fr.cross_auditions), "cross_exact": int(fr.cross_exact),
                    })
        max_state = max(int(r["fused_reserved_state_bytes"]) for r in rows)
        max_ratio = max(float(r["fused_over_selector_state"]) for r in rows)
        all_below_fixed = all(int(r["fused_reserved_state_bytes"]) < FIXED_RESEARCH_INDEX_BYTES for r in rows)
        if mismatches or not all_below_fixed:
            decision = "reject_actual_state_rehabilitation"
        elif max_state <= 65_536 and max_ratio <= 1.35:
            decision = "advance_actual_state_rehabilitation"
        else:
            decision = "hold_actual_state_rehabilitation"
        return {
            "schema": "cmpct-one-g02-fused-nomination-actual-state-audit-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "fixed_research_index_bytes": FIXED_RESEARCH_INDEX_BYTES,
            "semantic_mismatches": mismatches,
            "max_fused_reserved_state_bytes": max_state,
            "max_fused_over_selector_state": max_ratio,
            "all_fused_rows_below_fixed_research_index": all_below_fixed,
            "decision": decision,
            "rows": rows,
            "claim_boundary": "native semantic/state audit only; existing carrying-cost run remains elapsed authority",
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "reject_actual_state_rehabilitation" else 1)
