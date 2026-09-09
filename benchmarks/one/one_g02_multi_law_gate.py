"""Frozen ONE-G0.2 multi-Law opportunity-gate falsifier."""
from __future__ import annotations

import json
import random
import statistics
import time
import zlib

from experiments.one.multi_law_gate import observe_multi_law_gate

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
FAMILIES = (
    "long_runs",
    "exact_repeat",
    "add8_ramp",
    "xor_chain",
    "mixed_structured",
    "random",
    "compressed_like",
    "false_pattern",
)
REPETITIONS = 9
MAX_FALSE_NEGATIVES = 0
MAX_NEGATIVE_NOMINATIONS = 1
MAX_RETAINED_FRACTION = 0.15


def _repeat_to_size(seed: bytes, size: int) -> bytes:
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def make_case(family: str, size: int) -> bytes:
    rng = random.Random((size << 8) ^ sum(map(ord, family)))
    if family == "long_runs":
        out = bytearray()
        value = 0
        while len(out) < size:
            out.extend(bytes((value,)) * min(4096, size - len(out)))
            value = (value + 37) & 0xFF
        return bytes(out)
    if family == "exact_repeat":
        block = bytes(rng.randrange(256) for _ in range(4096))
        return _repeat_to_size(block, size)
    if family == "add8_ramp":
        start, delta = 17, 5
        return bytes((start + delta * i) & 0xFF for i in range(size))
    if family == "xor_chain":
        base = bytearray(rng.randrange(256) for _ in range(64))
        out = bytearray(base)
        mask = 0x5A
        while len(out) < size:
            prev = out[-64:]
            out.extend(bytes(value ^ mask for value in prev))
        return bytes(out[:size])
    if family == "mixed_structured":
        quarter = size // 4
        a = bytes((11 + 3 * i) & 0xFF for i in range(quarter))
        b = bytes((0xA5,)) * quarter
        c = _repeat_to_size(bytes(rng.randrange(256) for _ in range(256)), quarter)
        d = bytes(value ^ 0x3C for value in c)
        return (a + b + c + d + bytes((0,)) * size)[:size]
    if family == "random":
        return bytes(rng.randrange(256) for _ in range(size))
    if family == "compressed_like":
        source = bytes(rng.randrange(16) + 65 for _ in range(size * 2))
        packed = zlib.compress(source, 9)
        return _repeat_to_size(packed, size)
    if family == "false_pattern":
        # Short local coincidences deliberately below the global arithmetic/xor gate.
        out = bytearray(rng.randrange(256) for _ in range(size))
        for start in range(1024, size, 8192):
            end = min(start + 96, size)
            for i in range(start, end):
                out[i] = (7 + 5 * (i - start)) & 0xFF
        return bytes(out)
    raise ValueError(family)


def oracle_expected(family: str) -> set[str]:
    if family == "long_runs":
        return {"run", "reuse"}
    if family == "exact_repeat":
        return {"reuse"}
    if family == "add8_ramp":
        return {"reuse", "add8"}
    if family == "xor_chain":
        return {"reuse", "xor"}
    if family == "mixed_structured":
        return {"run", "reuse"}
    return set()


def _measure(data: bytes) -> tuple[object, float, float]:
    walls, cpus = [], []
    result = None
    for _ in range(REPETITIONS):
        t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
        result = observe_multi_law_gate(data)
        walls.append(time.perf_counter_ns() - t0w)
        cpus.append(time.process_time_ns() - t0c)
    assert result is not None
    return result, statistics.median(walls) / 1e9, statistics.median(cpus) / 1e9


def decide(rows: list[dict]) -> str:
    if len(rows) != len(SIZES) * len(FAMILIES):
        return "INVALIDATE_MULTI_LAW_GATE"
    keys = {(row["size"], row["family"]) for row in rows}
    if len(keys) != len(rows):
        return "INVALIDATE_MULTI_LAW_GATE"
    if any(row["source_scan_ratio"] != 1.0 for row in rows):
        return "INVALIDATE_MULTI_LAW_GATE"
    if any(row["retained_fraction"] > MAX_RETAINED_FRACTION for row in rows):
        return "HOLD_MULTI_LAW_GATE"
    if sum(row["false_negatives"] for row in rows) > MAX_FALSE_NEGATIVES:
        return "HOLD_MULTI_LAW_GATE"
    negative_rows = [row for row in rows if not row["expected"]]
    if sum(row["unexpected_nominations"] for row in negative_rows) > MAX_NEGATIVE_NOMINATIONS:
        return "HOLD_MULTI_LAW_GATE"
    return "ADVANCE_MULTI_LAW_GATE"


def main() -> int:
    rows = []
    for size in SIZES:
        for family in FAMILIES:
            data = make_case(family, size)
            result, wall, cpu = _measure(data)
            actual = {
                name for name in ("run", "reuse", "add8", "xor")
                if getattr(result.decision, name)
            }
            expected = oracle_expected(family)
            false_negatives = len(expected - actual)
            unexpected = len(actual) if not expected else 0
            rows.append({
                "size": size,
                "family": family,
                "expected": sorted(expected),
                "actual": sorted(actual),
                "false_negatives": false_negatives,
                "unexpected_nominations": unexpected,
                "wall_seconds": wall,
                "cpu_seconds": cpu,
                "source_scan_ratio": result.stats.source_scan_bytes / len(data),
                "retained_fraction": result.stats.retained_feature_payload_bytes / len(data),
                "support": {
                    "run": result.decision.run_support_bytes,
                    "reuse": result.decision.reuse_support_bytes,
                    "add8": result.decision.add8_support_bytes,
                    "xor": result.decision.xor_support_bytes,
                },
            })
    decision = decide(rows)
    print(json.dumps({
        "experiment": "ONE-G0.2 multi-Law opportunity gate",
        "decision": decision,
        "repetitions": REPETITIONS,
        "rows": rows,
    }, sort_keys=True))
    return 0 if decision == "ADVANCE_MULTI_LAW_GATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
