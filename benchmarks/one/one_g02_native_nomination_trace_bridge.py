"""ONE-G0.2: validate a native minimizer-trace bridge for shared-observer pair nomination.

This is deliberately a semantic bridge, not a speed benchmark.  The promoted native
minimizer already emits the exact selected anchor *positions*.  Rather than copy that
selector into a second native implementation, this harness proves that those native
positions, paired with the Gear state already defined by the observer, reproduce the
reference minimizer trace and the existing cross-object exact-reuse nomination semantics.

A future result-bearing integration may move signal/event emission into the native hot
loop.  Until then, timings from this bridge have no writer-speed authority.
"""
from __future__ import annotations

from collections import OrderedDict, deque
import ctypes
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _U64_MASK,
    _extend_left,
    _extend_right,
    GEAR_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_relation_shared_observer_validation import (
    LOCAL_ENTRIES,
    MINIMIZER_SPAN,
    _cases,
    _cross_object_reuse_nominations,
)

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)


class NativeResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
        ("derived_state_reads", ctypes.c_uint64),
        ("suffix_blocks_built", ctypes.c_uint64),
        ("suffix_blocks_skipped_dead", ctypes.c_uint64),
        ("suffix_value_indirect_loads", ctypes.c_uint64),
    ]


def _build_native_selector():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-nomination-trace-")
    lib = Path(td.name) / "libselector.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O3",
            "-std=c11",
            "-fPIC",
            "-shared",
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            "-o",
            str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_minimizer_offset_only_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(NativeResult),
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn, td


def _gear_states(data: bytes) -> list[int]:
    states: list[int] = []
    h = 0
    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 >= WINDOW:
            states.append(h)
    return states


def _python_anchor_positions(data: bytes) -> list[int]:
    if len(data) < MINIMIZER_SPAN + WINDOW:
        return []
    minima: deque[tuple[int, int]] = deque()
    anchors: list[int] = []
    last = -1
    h = 0
    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        if first_valid < WINDOW - 1:
            continue
        anchor = minima[0][1]
        if anchor != last:
            anchors.append(anchor)
            last = anchor
    return anchors


def _native_anchor_positions(fn, data: bytes) -> tuple[list[int], NativeResult]:
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    gear = (ctypes.c_uint64 * 256)(*_GEAR)
    # An anchor cannot be emitted more than once per Gear-state position.
    capacity = max(1, len(data) - WINDOW + 1)
    trace = (ctypes.c_uint64 * capacity)()
    out = NativeResult()
    rc = fn(
        buf,
        len(data),
        gear,
        WINDOW,
        MINIMIZER_SPAN,
        ctypes.byref(out),
        trace,
        capacity,
    )
    if rc != 0:
        raise RuntimeError(f"native minimizer failed: rc={rc}")
    return [int(trace[i]) for i in range(int(out.emitted))], out


def _bridge_nominations(data: bytes, boundary: int, anchors: list[int]) -> tuple[int, int]:
    """Replay existing nomination policy using native-selected global anchor positions.

    Local fixed-window auditions stay in Python here on purpose.  This validator isolates
    whether the native minimizer trace is a semantics-preserving bridge; it does not claim
    that the complete nominator is native yet.
    """
    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    anchor_iter = iter(anchors)
    next_anchor = next(anchor_iter, None)
    h = 0
    run_value = data[0]
    run_length = 0
    covered_until = 0
    cross_auditions = 0
    cross_exact = 0

    def audition(start: int, prior: int | None) -> None:
        nonlocal covered_until, cross_auditions, cross_exact
        if prior is None or start < covered_until:
            return
        is_cross = prior < boundary <= start
        if is_cross:
            cross_auditions += 1
        if data[prior : prior + WINDOW] != data[start : start + WINDOW]:
            return
        left, _ = _extend_left(data, prior, start, covered_until)
        right, _ = _extend_right(data, prior, start)
        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end > target_start:
            if is_cross:
                cross_exact += 1
            covered_until = target_end

    for position, value in enumerate(data):
        if not run_length:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            run_value, run_length = value, 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)

        if not run_dominated and (position + 1) % WINDOW == 0:
            prior = local_index.get(h)
            audition(start, prior)
            if prior is None:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)

        if next_anchor is not None and position == next_anchor:
            signal = h
            anchor_start = position + 1 - WINDOW
            prior = global_index.get(signal)
            audition(anchor_start, prior)
            if prior is None and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
                global_index[signal] = anchor_start
            next_anchor = next(anchor_iter, None)

    if next_anchor is not None:
        raise AssertionError("native anchor trace contains an unreachable position")
    return cross_exact, cross_auditions


def run() -> dict[str, object]:
    native, td = _build_native_selector()
    rows: list[dict[str, object]] = []
    trace_mismatches: list[tuple[int, int, str]] = []
    nomination_mismatches: list[tuple[int, int, str]] = []
    signal_mismatches: list[tuple[int, int, str]] = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                # Reuse the established generator family but use fresh validation seeds.
                for name, (source, target) in _cases(size, seed).items():
                    data = source + target
                    native_anchors, native_stats = _native_anchor_positions(native, data)
                    python_anchors = _python_anchor_positions(data)
                    if native_anchors != python_anchors:
                        trace_mismatches.append((size, seed, name))

                    # Validate the signal implied by every native anchor independently.
                    states = _gear_states(data)
                    native_signals = [states[p - (WINDOW - 1)] for p in native_anchors]
                    reference_signals = []
                    h = 0
                    wanted = set(python_anchors)
                    for position, value in enumerate(data):
                        h = ((h << 1) + _GEAR[value]) & _U64_MASK
                        if position in wanted:
                            reference_signals.append((position, h))
                    expected_signals = [hval for _, hval in reference_signals]
                    if native_signals != expected_signals:
                        signal_mismatches.append((size, seed, name))

                    ref_exact, ref_auditions, _ = _cross_object_reuse_nominations(source, target)
                    bridge_exact, bridge_auditions = _bridge_nominations(data, len(source), native_anchors)
                    if (bridge_exact, bridge_auditions) != (ref_exact, ref_auditions):
                        nomination_mismatches.append((size, seed, name))

                    rows.append(
                        {
                            "relation_bytes": size,
                            "seed": seed,
                            "case": name,
                            "native_anchor_count": len(native_anchors),
                            "python_anchor_count": len(python_anchors),
                            "native_reserved_state_bytes": int(native_stats.reserved_state_bytes),
                            "reference_cross_exact": ref_exact,
                            "bridge_cross_exact": bridge_exact,
                            "reference_cross_auditions": ref_auditions,
                            "bridge_cross_auditions": bridge_auditions,
                        }
                    )

        passed = not trace_mismatches and not signal_mismatches and not nomination_mismatches
        return {
            "schema": "cmpct-one-g02-native-nomination-trace-bridge-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "sizes": list(SIZES),
            "seeds": list(SEEDS),
            "rows": rows,
            "trace_mismatches": trace_mismatches,
            "signal_mismatches": signal_mismatches,
            "nomination_mismatches": nomination_mismatches,
            "decision": "advance_native_nomination_trace_bridge" if passed else "reject_native_nomination_trace_bridge",
            "claim_boundary": (
                "semantic bridge only: native selector positions plus independently reconstructed Gear signal; "
                "local auditions and event consumption remain Python, so no native writer-speed claim"
            ),
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_native_nomination_trace_bridge" else 1)
