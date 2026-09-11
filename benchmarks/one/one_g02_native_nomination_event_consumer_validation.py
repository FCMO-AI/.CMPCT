"""ONE-G0.2: validate native consumption of the proven nomination anchor trace.

Frozen by `ONE_G02_NATIVE_NOMINATION_EVENT_CONSUMER_PREREG_2026-09-06.md`.
This stage removes Python event/index consumption from the semantic boundary while
intentionally retaining two passes: native selector trace production, then native
nomination consumption.  It therefore has no fused-observer speed authority.
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW
from benchmarks.one.one_g02_native_nomination_trace_bridge import (
    NativeResult,
    _native_anchor_positions,
    _python_anchor_positions,
)
from benchmarks.one.one_g02_relation_shared_observer_validation import (
    MINIMIZER_SPAN,
    _cases,
    _cross_object_reuse_nominations,
)

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)


class ConsumerResult(ctypes.Structure):
    _fields_ = [
        ("cross_auditions", ctypes.c_uint64),
        ("cross_exact", ctypes.c_uint64),
        ("local_peak_entries", ctypes.c_uint64),
        ("global_peak_entries", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64),
        ("extension_read_bytes", ctypes.c_uint64),
        ("anchors_consumed", ctypes.c_uint64),
    ]


def _build_native():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-nominator-consumer-")
    lib = Path(td.name) / "libnominator.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O3",
            "-std=c11",
            "-fPIC",
            "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_native_nomination_event_consumer_kernel.c"),
            "-o",
            str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    selector = c.one_g02_minimizer_offset_only_kernel
    selector.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(NativeResult),
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
    ]
    selector.restype = ctypes.c_int

    consumer = c.one_g02_native_nomination_event_consumer
    consumer.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
        ctypes.POINTER(ConsumerResult),
    ]
    consumer.restype = ctypes.c_int
    return selector, consumer, td


def _consume(consumer, data: bytes, boundary: int, anchors: list[int]) -> ConsumerResult:
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    anchor_buf = (ctypes.c_uint64 * max(1, len(anchors)))(*(anchors or [0]))
    out = ConsumerResult()
    rc = consumer(
        buf,
        len(data),
        boundary,
        gear,
        anchor_buf,
        len(anchors),
        ctypes.byref(out),
    )
    if rc != 0:
        raise RuntimeError(f"native nomination event consumer failed: rc={rc}")
    return out


def run() -> dict[str, object]:
    selector, consumer, td = _build_native()
    rows: list[dict[str, object]] = []
    trace_mismatches: list[tuple[int, int, str]] = []
    audition_mismatches: list[tuple[int, int, str]] = []
    exact_mismatches: list[tuple[int, int, str]] = []
    false_exact_nominations: list[tuple[int, int, str]] = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    data = source + target
                    anchors, selector_stats = _native_anchor_positions(selector, data)
                    python_anchors = _python_anchor_positions(data)
                    if anchors != python_anchors:
                        trace_mismatches.append((size, seed, name))

                    native = _consume(consumer, data, len(source), anchors)
                    ref_exact, ref_auditions, _ = _cross_object_reuse_nominations(source, target)
                    native_auditions = int(native.cross_auditions)
                    native_exact = int(native.cross_exact)
                    if native_auditions != ref_auditions:
                        audition_mismatches.append((size, seed, name))
                    if native_exact != ref_exact:
                        exact_mismatches.append((size, seed, name))
                    if ref_exact == 0 and native_exact != 0:
                        false_exact_nominations.append((size, seed, name))

                    rows.append(
                        {
                            "relation_bytes": size,
                            "seed": seed,
                            "case": name,
                            "native_anchor_count": len(anchors),
                            "python_anchor_count": len(python_anchors),
                            "selector_reserved_state_bytes": int(selector_stats.reserved_state_bytes),
                            "reference_cross_auditions": ref_auditions,
                            "native_cross_auditions": native_auditions,
                            "reference_cross_exact": ref_exact,
                            "native_cross_exact": native_exact,
                            "native_local_peak_entries": int(native.local_peak_entries),
                            "native_global_peak_entries": int(native.global_peak_entries),
                            "native_verification_read_bytes": int(native.verification_read_bytes),
                            "native_extension_read_bytes": int(native.extension_read_bytes),
                            "native_anchors_consumed": int(native.anchors_consumed),
                        }
                    )

        passed = not (
            trace_mismatches
            or audition_mismatches
            or exact_mismatches
            or false_exact_nominations
        )
        return {
            "schema": "cmpct-one-g02-native-nomination-event-consumer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "sizes": list(SIZES),
            "seeds": list(SEEDS),
            "rows": rows,
            "trace_mismatches": trace_mismatches,
            "audition_mismatches": audition_mismatches,
            "exact_mismatches": exact_mismatches,
            "false_exact_nominations": false_exact_nominations,
            "decision": "advance_native_nomination_event_consumer" if passed else "repair_native_nomination_event_consumer",
            "claim_boundary": (
                "native semantic/event-consumption bridge only; selector trace production and event consumption "
                "remain separate passes, so elapsed time is not fused-observer or product-writer authority"
            ),
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_native_nomination_event_consumer" else 1)
