"""ONE-G0.2 fused-cache versus native fresh-observer falsifier."""
from __future__ import annotations

import gc
import json
import os
import random
import statistics
import time
import zlib

from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.native_observe import observe_native

SIZES = (256 << 10, 1 << 20)
REPETITIONS = 15
BLOCK_SIZE = 4096
PAYLOAD_LIMIT = 0.20
PRODUCTIVE_LIMITS = {
    "exact_repeat": 0.90,
    "sparse_one_block": 0.90,
    "sparse_eight_blocks": 0.95,
}
PRODUCTIVE_WORST_LIMIT = 1.05
SHIFTED_CONTROL_LIMIT = 1.25


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


FAMILIES = {
    "structured": _structured,
    "random": _random,
    "compressed_like": _compressed_like,
}


def _mutate_one_block(data: bytes) -> bytes:
    out = bytearray(data)
    pos = len(out) // 2
    out[pos] ^= 0x5A
    return bytes(out)


def _mutate_eight_blocks(data: bytes) -> bytes:
    out = bytearray(data)
    blocks = max(1, len(out) // BLOCK_SIZE)
    for i in range(8):
        block = min(blocks - 1, ((i + 1) * blocks) // 9)
        pos = min(len(out) - 1, block * BLOCK_SIZE + 17)
        out[pos] ^= (0x31 + i)
    return bytes(out)


def _shift_insert(data: bytes) -> bytes:
    pos = len(data) // 2
    return data[:pos] + b"\xA7" + data[pos:]


def _median_pair(native_fn, cache_fn):
    native_wall: list[int] = []
    native_cpu: list[int] = []
    cache_wall: list[int] = []
    cache_cpu: list[int] = []
    last_native = None
    last_cache = None
    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for rep in range(REPETITIONS):
            order = (("native", native_fn), ("cache", cache_fn))
            if rep % 2:
                order = tuple(reversed(order))
            for label, fn in order:
                c0 = time.process_time_ns()
                w0 = time.perf_counter_ns()
                result = fn()
                w1 = time.perf_counter_ns()
                c1 = time.process_time_ns()
                if label == "native":
                    last_native = result
                    native_wall.append(w1 - w0)
                    native_cpu.append(c1 - c0)
                else:
                    last_cache = result
                    cache_wall.append(w1 - w0)
                    cache_cpu.append(c1 - c0)
    finally:
        if was_enabled:
            gc.enable()
    return {
        "native_wall_ns": float(statistics.median(native_wall)),
        "native_cpu_ns": float(statistics.median(native_cpu)),
        "cache_wall_ns": float(statistics.median(cache_wall)),
        "cache_cpu_ns": float(statistics.median(cache_cpu)),
        "native": last_native,
        "cache": last_cache,
    }


def run():
    observe_native(b"warmup" * 32)
    rows = []
    semantic_ok = True
    payload_ok = True
    productive_ok = True
    control_ok = True

    for size in SIZES:
        for family, builder in FAMILIES.items():
            base = builder(size)
            previous = observe_incremental(base)
            payload_ratio = previous.stats.persistent_payload_bytes / max(1, len(base))
            payload_ok &= payload_ratio <= PAYLOAD_LIMIT

            cases = {
                "exact_repeat": base,
                "sparse_one_block": _mutate_one_block(base),
                "sparse_eight_blocks": _mutate_eight_blocks(base),
                "shifted_insert_control": _shift_insert(base),
            }

            for case, current in cases.items():
                measured = _median_pair(
                    lambda current=current: observe_native(current),
                    lambda current=current: observe_incremental(current, previous=previous.cache),
                )
                native = measured.pop("native")
                cached = measured.pop("cache")
                same = cached.observation == native
                semantic_ok &= same
                if not same:
                    raise AssertionError(
                        f"cache/native semantic divergence: {size=} {family=} {case=}"
                    )

                wall_ratio = measured["cache_wall_ns"] / measured["native_wall_ns"]
                cpu_ratio = measured["cache_cpu_ns"] / measured["native_cpu_ns"]
                if case in PRODUCTIVE_LIMITS:
                    limit = PRODUCTIVE_LIMITS[case]
                    passed = (
                        wall_ratio <= limit
                        and cpu_ratio <= limit
                        and wall_ratio <= PRODUCTIVE_WORST_LIMIT
                        and cpu_ratio <= PRODUCTIVE_WORST_LIMIT
                    )
                    productive_ok &= passed
                else:
                    limit = SHIFTED_CONTROL_LIMIT
                    passed = wall_ratio <= limit and cpu_ratio <= limit
                    control_ok &= passed

                rows.append({
                    "size": size,
                    "family": family,
                    "case": case,
                    **measured,
                    "wall_ratio_cache_over_native": wall_ratio,
                    "cpu_ratio_cache_over_native": cpu_ratio,
                    "gate_limit": limit,
                    "gate_pass": passed,
                    "persistent_payload_bytes": previous.stats.persistent_payload_bytes,
                    "persistent_payload_ratio": payload_ratio,
                    "recomputed_blocks": cached.stats.recomputed_blocks,
                    "reused_blocks": cached.stats.reused_blocks,
                    "validation_read_bytes": cached.stats.validation_read_bytes,
                    "feature_recompute_bytes": cached.stats.feature_recompute_bytes,
                    "cache_integrity_hash_bytes": cached.stats.cache_integrity_hash_bytes,
                    "cache_feature_payload_read_bytes": cached.stats.cache_feature_payload_read_bytes,
                    "verification_read_bytes": cached.stats.verification_read_bytes,
                })

    if not semantic_ok:
        decision = "INVALIDATE_COMPARISON"
    elif payload_ok and productive_ok and control_ok:
        decision = "ADVANCE_CACHE_OVER_NATIVE"
    else:
        decision = "DEMOTE_CACHE_PROMOTE_NATIVE_BASELINE"

    return {
        "schema": "cmpct-one-g02-cache-vs-native-fresh-observer-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "repetitions": REPETITIONS,
        "timing_order": "paired alternating native/cache-cache/native",
        "block_size": BLOCK_SIZE,
        "payload_limit": PAYLOAD_LIMIT,
        "productive_limits": PRODUCTIVE_LIMITS,
        "productive_worst_limit": PRODUCTIVE_WORST_LIMIT,
        "shifted_control_limit": SHIFTED_CONTROL_LIMIT,
        "semantic_gates_pass": semantic_ok,
        "payload_gate_pass": payload_ok,
        "productive_timing_gates_pass": productive_ok,
        "shifted_control_gate_pass": control_ok,
        "decision": decision,
        "claim_boundary": (
            "component-level comparison of current positional fused cache against semantically "
            "equivalent native fresh observation; no total-writer, reader, density, access, or "
            "frozen-comparator superiority claim"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] != "INVALIDATE_COMPARISON" else 1)
