"""ONE-G0.2 native fresh-observer semantic/performance transfer gate."""
from __future__ import annotations

import gc
import json
import os
import random
import statistics
import time
import zlib

from experiments.one.native_observe import observe_native
from experiments.one.observe import observe

SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 15
LIMIT = 0.25


def _structured(size: int) -> bytes:
    motif = b"ONE-law-surprise:" + bytes(range(32))
    out = bytearray()
    while len(out) < size:
        out.extend(motif * 3)
        out.extend(b"A" * 96)
        out.extend(motif)
        out.extend(b"BC" * 37)
    return bytes(out[:size])


def _random(size: int) -> bytes:
    return random.Random(0xC0A57 + size).randbytes(size)


def _compressed_like(size: int) -> bytes:
    seed = zlib.compress(_structured(max(size * 2, 1024)), level=9)
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def _long_runs(size: int) -> bytes:
    pattern = b"A" * 257 + b"B" * 64 + b"C" * 7 + b"D" * 129 + bytes(range(64))
    return (pattern * ((size + len(pattern) - 1) // len(pattern)))[:size]


def _near_repeats(size: int) -> bytes:
    chunks = []
    for i in range(max(1, (size + 63) // 64)):
        chunk = bytearray((b"near-repeat-pattern" * 4)[:64])
        chunk[-1] ^= i & 0xFF
        chunks.append(bytes(chunk))
    return b"".join(chunks)[:size]


FAMILIES = {
    "structured": _structured,
    "random": _random,
    "compressed_like": _compressed_like,
    "long_runs": _long_runs,
    "near_repeats": _near_repeats,
}


def _measure(fn, data: bytes):
    wall = []
    cpu = []
    last = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for _ in range(REPETITIONS):
            c0 = time.process_time_ns()
            w0 = time.perf_counter_ns()
            last = fn(data)
            w1 = time.perf_counter_ns()
            c1 = time.process_time_ns()
            wall.append(w1 - w0)
            cpu.append(c1 - c0)
    finally:
        if was_enabled:
            gc.enable()
    return float(statistics.median(wall)), float(statistics.median(cpu)), last


def run():
    # Force compilation outside all timed samples.
    observe_native(b"warmup" * 16)
    rows = []
    semantic_ok = True
    timing_ok = True
    for size in SIZES:
        for family, builder in FAMILIES.items():
            data = builder(size)
            expected = observe(data)
            actual = observe_native(data)
            same = actual == expected
            semantic_ok &= same
            if not same:
                raise AssertionError(f"native observer semantic divergence: {size=} {family=}")

            # Paired alternating order to reduce systematic thermal/order skew.
            py_wall = []
            py_cpu = []
            native_wall = []
            native_cpu = []
            was_enabled = gc.isenabled()
            try:
                if was_enabled:
                    gc.disable()
                for rep in range(REPETITIONS):
                    order = (("python", observe), ("native", observe_native))
                    if rep % 2:
                        order = tuple(reversed(order))
                    for label, fn in order:
                        c0 = time.process_time_ns()
                        w0 = time.perf_counter_ns()
                        result = fn(data)
                        w1 = time.perf_counter_ns()
                        c1 = time.process_time_ns()
                        if result != expected:
                            raise AssertionError(f"timed semantic divergence: {size=} {family=} {label=}")
                        if label == "python":
                            py_wall.append(w1 - w0)
                            py_cpu.append(c1 - c0)
                        else:
                            native_wall.append(w1 - w0)
                            native_cpu.append(c1 - c0)
            finally:
                if was_enabled:
                    gc.enable()

            pwall = float(statistics.median(py_wall))
            pcpu = float(statistics.median(py_cpu))
            nwall = float(statistics.median(native_wall))
            ncpu = float(statistics.median(native_cpu))
            wall_ratio = nwall / pwall
            cpu_ratio = ncpu / pcpu
            passed = wall_ratio <= LIMIT and cpu_ratio <= LIMIT
            timing_ok &= passed
            rows.append({
                "size": size,
                "family": family,
                "python_wall_ns": pwall,
                "native_wall_ns": nwall,
                "python_cpu_ns": pcpu,
                "native_cpu_ns": ncpu,
                "wall_ratio": wall_ratio,
                "cpu_ratio": cpu_ratio,
                "gate_limit": LIMIT,
                "gate_pass": passed,
                "runs": len(actual.runs),
                "reuse": len(actual.reuse),
                "source_read_bytes": actual.stats.total_source_read_bytes,
                "verification_read_bytes": actual.stats.verification_read_bytes,
                "peak_index_entries": actual.stats.peak_index_entries,
                "retained_index_payload_bytes": actual.stats.retained_index_payload_bytes,
                "exact_stats": actual.stats == expected.stats,
            })

    decision = (
        "INVALIDATE_NATIVE_OBSERVER" if not semantic_ok else
        "HOLD_NATIVE_OBSERVER_TRANSFER" if not timing_ok else
        "ADVANCE_NATIVE_FRESH_OBSERVER"
    )
    return {
        "schema": "cmpct-one-g02-native-fresh-observer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "compiler": "cc -O3 -std=c11 -fPIC -shared",
        "repetitions": REPETITIONS,
        "timing_order": "paired alternating A/B-B/A",
        "semantic_gates_pass": semantic_ok,
        "timing_gates_pass": timing_ok,
        "decision": decision,
        "claim_boundary": (
            "native implementation transfer of current G0.2 fresh observation semantics; no cache, reader, "
            "wire-format, density, authenticated placement or comparator supremacy claim"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_NATIVE_FRESH_OBSERVER" else 1)
