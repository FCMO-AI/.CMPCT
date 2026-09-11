"""ONE-G0.2 compiled causal A/B for the byte-history starvation gate.

Referee freeze before result-bearing execution
==============================================
The Python byte-history candidate preserved all 35 generator-distinct hard-rescue rows while
reducing modeled retained history to 4,112 B, but missed its frozen hosted performance gate by
0.01 percentage point (negative-control median 0.900100x) and slowed the tiny hard row. This
experiment does not change the 4,096-position gate, transfer corpus, Gear signal or 8,192-byte
promoted size boundary. It asks whether that loss is principally Python ring/replay overhead.

The compiled candidate is compared against the current promoted tail-return 8 KiB selector
baseline. The candidate's emitted nomination trace is first checked against an independent
Python implementation of the exact gated recurrence. No exact proof/index/Law work is hidden
inside either selector timing.

Falsification: native trace/state mismatch rejects correctness; median candidate/baseline
>=0.90 on either 1 MiB entropy-dense control rejects the claim that compilation rehabilitates
the negative-path compute shape. State growth is reported independently and cannot be hidden
by elapsed improvement.
"""
from __future__ import annotations

from collections import deque
import ctypes
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time
import zlib

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _U64_MASK, WINDOW
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_size_dispatch_tail_ab import _bind_dispatch, _call_dispatch

ANCHOR_MASK = 1023
ROUNDS = 13


class _GateResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
        ("sparse_anchors", ctypes.c_uint64),
        ("rescue_active_positions", ctypes.c_uint64),
        ("replayed_history_bytes", ctypes.c_uint64),
        ("peak_queue_entries", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-starvation-native-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            str(here / "one_g02_starvation_byte_history_kernel.c"),
            "-o", str(lib),
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _bind_gate(lib):
    fn = lib.one_g02_starvation_byte_history_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_GateResult),
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_gate(fn, gear, arr, length: int, trace=None, capacity: int = 0):
    out = _GateResult()
    rc = fn(arr, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out), trace, capacity)
    if rc != 0:
        raise RuntimeError(f"starvation byte-history kernel failed: {rc}")
    return out


def _python_trace(data: bytes):
    history = bytearray(MINIMIZER_SPAN)
    history_count = history_next = 0
    history_seed = 0
    minima: deque[tuple[int, int]] = deque()
    state = 0
    last_sparse = None
    last_emitted = None
    active = False
    trace: list[int] = []
    sparse_anchors = active_positions = replayed = 0
    run_value = data[0] if data else 0
    run_length = 0
    positions = 0

    for position, value in enumerate(data):
        if run_length == 0:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            run_value, run_length = value, 1
        before = state
        state = ((state << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        positions += 1
        if history_count == 0:
            history_seed = before
        elif history_count == MINIMIZER_SPAN:
            oldest = history[history_next]
            history_seed = ((history_seed << 1) + _GEAR[oldest]) & _U64_MASK
        history[history_next] = value
        history_next = (history_next + 1) % MINIMIZER_SPAN
        history_count = min(history_count + 1, MINIMIZER_SPAN)

        run_dominated = run_length >= max(8, WINDOW)
        if not (state & ANCHOR_MASK) and not run_dominated:
            sparse_anchors += 1
            last_sparse = position
            active = False
            minima.clear()
            last_emitted = None
            continue
        gap = position - last_sparse if last_sparse is not None else position + 1 - WINDOW
        if run_dominated or gap < MINIMIZER_SPAN:
            continue
        active_positions += 1
        if not active:
            if history_count < MINIMIZER_SPAN:
                continue
            minima.clear()
            replay_state = history_seed
            oldest_position = position + 1 - history_count
            oldest_slot = history_next
            for j in range(history_count):
                rv = history[(oldest_slot + j) % MINIMIZER_SPAN]
                replay_state = ((replay_state << 1) + _GEAR[rv]) & _U64_MASK
                hp = oldest_position + j
                while minima and minima[-1][0] >= replay_state:
                    minima.pop()
                minima.append((replay_state, hp))
            assert replay_state == state
            replayed += history_count
            active = True
        else:
            first_valid = position - MINIMIZER_SPAN + 1
            while minima and minima[0][1] < first_valid:
                minima.popleft()
            while minima and minima[-1][0] >= state:
                minima.pop()
            minima.append((state, position))
        anchor = minima[0][1]
        if anchor != last_emitted:
            trace.append(anchor)
            last_emitted = anchor
    return trace, state, positions, sparse_anchors, active_positions, replayed


def _abba(a, b):
    ratios = []
    for i in range(ROUNDS):
        if i % 2 == 0:
            t0 = time.perf_counter_ns(); a(); ta = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); b(); tb = time.perf_counter_ns() - t0
        else:
            t0 = time.perf_counter_ns(); b(); tb = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); a(); ta = time.perf_counter_ns() - t0
        ratios.append(tb / ta)
    return ratios


def _cases():
    rnd = random.Random(8801).randbytes(1024 * 1024)
    basis = random.Random(8802).randbytes(64 * 1024)
    shifted = random.Random(8803).randbytes(512 * 1024)
    hard = random.Random(10).randbytes(4096)
    return {
        "random_1mib": rnd,
        "zlib_random_1mib": zlib.compress(rnd, level=9),
        "repeat_64k_basis_1mib": basis * 16,
        "shifted_512k_insert1": shifted + b"X" + shifted,
        "transfer_starved_seed10_insert1": hard + b"X" + hard,
    }


def run():
    lib, td = _build()
    try:
        gate = _bind_gate(lib)
        baseline = _bind_dispatch(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        correctness = True
        for name, data in _cases().items():
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected = _python_trace(data)
            trace = (ctypes.c_uint64 * max(1, len(data)))()
            once = _call_gate(gate, gear, arr, len(data), trace, len(data))
            actual_trace = [int(trace[i]) for i in range(int(once.emitted))]
            equal = (
                actual_trace == expected[0]
                and int(once.final_state) == expected[1]
                and int(once.positions_considered) == expected[2]
                and int(once.sparse_anchors) == expected[3]
                and int(once.rescue_active_positions) == expected[4]
                and int(once.replayed_history_bytes) == expected[5]
            )
            correctness &= equal
            if not equal:
                raise AssertionError((name, "native-gate semantic mismatch"))
            base_once = _call_dispatch(baseline, gear, arr, len(data))
            ratios = _abba(
                lambda: _call_dispatch(baseline, gear, arr, len(data)),
                lambda: _call_gate(gate, gear, arr, len(data)),
            )
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "trace_equal": equal,
                "median_gate_over_promoted_baseline": statistics.median(ratios),
                "min_gate_over_promoted_baseline": min(ratios),
                "max_gate_over_promoted_baseline": max(ratios),
                "promoted_baseline_reserved_state_bytes": int(base_once.reserved_state_bytes),
                "gate_reserved_state_bytes": int(once.reserved_state_bytes),
                "sparse_anchors": int(once.sparse_anchors),
                "rescue_active_positions": int(once.rescue_active_positions),
                "replayed_history_bytes": int(once.replayed_history_bytes),
                "peak_queue_entries": int(once.peak_queue_entries),
            })
        controls = {r["case"]: r for r in rows}
        compiled_compute_survives = (
            correctness
            and controls["random_1mib"]["median_gate_over_promoted_baseline"] < 0.90
            and controls["zlib_random_1mib"]["median_gate_over_promoted_baseline"] < 0.90
        )
        return {
            "schema": "cmpct-one-g02-starvation-byte-history-native-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "frozen_gate_gap_positions": MINIMIZER_SPAN,
            "promoted_dispatch_boundary_bytes": 8192,
            "hypothesis": "the byte-history near-miss is primarily interpreter/control overhead; compiled execution materially beats the promoted tail-return selector baseline on both 1 MiB entropy-dense controls without changing gated recurrence semantics",
            "disproof": "native gated recurrence mismatch or median gate/baseline >=0.90 on either entropy-dense 1 MiB control rejects compiled compute rehabilitation",
            "decision": "advance_compiled_starvation_gate" if compiled_compute_survives else "reject_or_rehabilitate_compiled_starvation_gate",
            "claim_boundary": "compiled encoder-discovery selector A/B only; excludes exact proof/index/Law work; state is charged separately; no product/native-reader/stored-byte/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
