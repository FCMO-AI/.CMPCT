"""ONE-G0.2 fused native nomination semantic/traffic gate.

Compares a one-pass fused minimizer+nominator against the exact terminal two-stage
native oracle.  Frozen by ONE_G02_FUSED_NATIVE_NOMINATION_PREREG_2026-09-06.md.
No elapsed-time promotion claim is made here.
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_native_nomination_trace_bridge import NativeResult, _native_anchor_positions
from benchmarks.one.one_g02_native_nomination_event_consumer_validation import ConsumerResult, _consume
from benchmarks.one.one_g02_relation_shared_observer_validation import MINIMIZER_SPAN, _cases

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
WINDOW = 64
LOCAL_ENTRIES = 64
GLOBAL_ENTRIES = 8192


class FusedResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
        ("cross_auditions", ctypes.c_uint64),
        ("cross_exact", ctypes.c_uint64),
        ("local_peak_entries", ctypes.c_uint64),
        ("global_peak_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64),
        ("extension_read_bytes", ctypes.c_uint64),
    ]


class IndexEntryLayout(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_uint64),
        ("start", ctypes.c_size_t),
        ("used", ctypes.c_int),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fused-native-nomination-")
    lib = Path(td.name) / "libfused.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_native_nomination_event_consumer_kernel.c"),
            str(here / "one_g02_fused_native_nomination_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    selector = c.one_g02_minimizer_offset_only_kernel
    selector.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(NativeResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    selector.restype = ctypes.c_int
    consumer = c.one_g02_native_nomination_event_consumer
    consumer.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.POINTER(ConsumerResult),
    ]
    consumer.restype = ctypes.c_int
    fused = c.one_g02_fused_native_nomination
    fused.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(FusedResult), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fused.restype = ctypes.c_int
    return selector, consumer, fused, td


def _fused(fused, data: bytes, boundary: int, *, collect_trace: bool):
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    out = FusedResult()
    cap = len(data) + 1
    trace_buf = (ctypes.c_uint64 * cap)() if collect_trace else None
    rc = fused(
        buf, len(data), boundary, gear, WINDOW, MINIMIZER_SPAN,
        ctypes.byref(out), trace_buf, cap if collect_trace else 0,
    )
    if rc != 0:
        raise RuntimeError(f"fused native nomination failed: rc={rc}")
    trace = [int(trace_buf[i]) for i in range(int(out.emitted))] if collect_trace else []
    return out, trace


def _selector_sig(x) -> tuple[int, ...]:
    return tuple(int(getattr(x, name)) for name, _ in NativeResult._fields_)


def _nomination_sig(x) -> tuple[int, ...]:
    return (
        int(x.cross_auditions), int(x.cross_exact), int(x.local_peak_entries),
        int(x.global_peak_entries), int(x.verification_read_bytes), int(x.extension_read_bytes),
    )


def run() -> dict[str, object]:
    selector, consumer, fused, td = _build()
    rows = []
    selector_mismatches = []
    trace_mismatches = []
    nomination_mismatches = []
    no_trace_mismatches = []
    false_exact_nominations = []
    traffic_mismatches = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    data = source + target
                    anchors, baseline_selector = _native_anchor_positions(selector, data)
                    baseline_consumer = _consume(consumer, data, len(source), anchors)
                    fused_out, fused_trace = _fused(fused, data, len(source), collect_trace=True)
                    fused_no_trace, _ = _fused(fused, data, len(source), collect_trace=False)

                    fused_selector_sig = tuple(int(getattr(fused_out, n)) for n, _ in NativeResult._fields_)
                    if fused_selector_sig != _selector_sig(baseline_selector):
                        selector_mismatches.append((size, seed, name))
                    if fused_trace != anchors:
                        trace_mismatches.append((size, seed, name))
                    if _nomination_sig(fused_out) != _nomination_sig(baseline_consumer):
                        nomination_mismatches.append((size, seed, name))
                    if tuple(int(getattr(fused_out, n)) for n, _ in FusedResult._fields_) != tuple(
                        int(getattr(fused_no_trace, n)) for n, _ in FusedResult._fields_
                    ):
                        no_trace_mismatches.append((size, seed, name))
                    if int(baseline_consumer.cross_exact) == 0 and int(fused_out.cross_exact) != 0:
                        false_exact_nominations.append((size, seed, name))

                    baseline_sequential = 2 * len(data)
                    fused_sequential = len(data)
                    ratio = fused_sequential / baseline_sequential
                    if ratio != 0.5:
                        traffic_mismatches.append((size, seed, name, ratio))

                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "baseline_anchor_count": len(anchors),
                        "fused_anchor_count": int(fused_out.emitted),
                        "baseline_cross_auditions": int(baseline_consumer.cross_auditions),
                        "fused_cross_auditions": int(fused_out.cross_auditions),
                        "baseline_cross_exact": int(baseline_consumer.cross_exact),
                        "fused_cross_exact": int(fused_out.cross_exact),
                        "baseline_sequential_observation_bytes": baseline_sequential,
                        "fused_sequential_observation_bytes": fused_sequential,
                        "fused_over_baseline_sequential_traffic": ratio,
                        "baseline_requires_intermediate_anchor_trace": True,
                        "fused_requires_intermediate_anchor_trace": False,
                        "fused_local_peak_entries": int(fused_out.local_peak_entries),
                        "fused_global_peak_entries": int(fused_out.global_peak_entries),
                        "fused_verification_read_bytes": int(fused_out.verification_read_bytes),
                        "fused_extension_read_bytes": int(fused_out.extension_read_bytes),
                    })

        event_index_storage_bytes = ctypes.sizeof(IndexEntryLayout) * (LOCAL_ENTRIES + GLOBAL_ENTRIES)
        passed = not (
            selector_mismatches or trace_mismatches or nomination_mismatches
            or no_trace_mismatches or false_exact_nominations or traffic_mismatches
        )
        return {
            "schema": "cmpct-one-g02-fused-native-nomination-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "sizes": list(SIZES),
            "seeds": list(SEEDS),
            "selector_mismatches": selector_mismatches,
            "trace_mismatches": trace_mismatches,
            "nomination_mismatches": nomination_mismatches,
            "no_trace_mismatches": no_trace_mismatches,
            "false_exact_nominations": false_exact_nominations,
            "traffic_mismatches": traffic_mismatches,
            "research_event_index_storage_bytes": event_index_storage_bytes,
            "decision": "advance_fused_native_nomination_semantics" if passed else "repair_fused_native_nomination",
            "claim_boundary": (
                "one-pass semantic/traffic evidence only; fixed research index storage is intentionally charged "
                "and elapsed-time promotion requires a later native carrying-cost gate"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_fused_native_nomination_semantics" else 1)
