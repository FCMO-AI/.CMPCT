"""ONE-G0.2 numeric morphology gate resource falsifier.

Promotion requires a real speed win on diverse numeric roots without hiding meaningful
reuse opportunity or regressing roots that should fall through to generic observation.
"""
from __future__ import annotations

import json
import statistics
import time

from experiments.one.morphology_gate import observe_morphology_gated
from experiments.one.observe import observe

SIZES = (256 * 1024, 1024 * 1024)
REPETITIONS = 15
WARMUPS = 3
NUMERIC_MAX_RELATIVE_WALL = 0.90
NUMERIC_MAX_RELATIVE_CPU = 0.90
FALLTHROUGH_MAX_RELATIVE_WALL = 1.08
FALLTHROUGH_MAX_RELATIVE_CPU = 1.08
MAX_SKIPPED_REUSE_FRACTION = 0.02


def diverse_numeric_root(size: int) -> bytes:
    rows = []
    index = 0
    total = 0
    while total < size:
        row = f"{1700000000 + index:010d},{(index * 7919) % 100000000:08d}.{index % 997:03d},{(index * 37) % 360:03d}\n".encode()
        rows.append(row)
        total += len(row)
        index += 1
    return b"".join(rows)[:size]


def repetitive_numeric_root(size: int) -> bytes:
    row = b"1700000000,12345.678,-91.25,42\n"
    return (row * ((size + len(row) - 1) // len(row)))[:size]


def phase_shift_numeric_root(size: int) -> bytes:
    prefix_size = min(16 * 1024, size // 4)
    prefix = diverse_numeric_root(prefix_size)
    return prefix + repetitive_numeric_root(size - len(prefix))


def binary_root(size: int) -> bytes:
    seed = bytes(range(256))
    return (seed * ((size + 255) // 256))[:size]


def _timed(fn, data: bytes) -> tuple[int, int]:
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    fn(data)
    cpu = time.process_time_ns() - cpu0
    wall = time.perf_counter_ns() - wall0
    return wall, cpu


def _pair(data: bytes) -> dict[str, float | int | bool]:
    baseline = observe(data)
    candidate = observe_morphology_gated(data)
    assert candidate.observation.runs == baseline.runs
    if not candidate.gate.gated:
        assert candidate.observation == baseline

    for _ in range(WARMUPS):
        observe(data)
        observe_morphology_gated(data)

    base_wall: list[int] = []
    base_cpu: list[int] = []
    cand_wall: list[int] = []
    cand_cpu: list[int] = []
    for rep in range(REPETITIONS):
        if rep % 2 == 0:
            bw, bc = _timed(observe, data)
            cw, cc = _timed(observe_morphology_gated, data)
        else:
            cw, cc = _timed(observe_morphology_gated, data)
            bw, bc = _timed(observe, data)
        base_wall.append(bw)
        base_cpu.append(bc)
        cand_wall.append(cw)
        cand_cpu.append(cc)

    base_wall_med = statistics.median(base_wall)
    base_cpu_med = statistics.median(base_cpu)
    cand_wall_med = statistics.median(cand_wall)
    cand_cpu_med = statistics.median(cand_cpu)
    return {
        "gated": candidate.gate.gated,
        "numeric_fraction": candidate.gate.numeric_fraction,
        "digit_fraction": candidate.gate.digit_fraction,
        "unique_chunk_fraction": candidate.gate.unique_chunk_fraction,
        "baseline_reuse_bytes": baseline.stats.reuse_opportunity_bytes,
        "baseline_reuse_fraction": baseline.stats.reuse_opportunity_bytes / len(data),
        "candidate_source_read_bytes": candidate.observation.stats.total_source_read_bytes,
        "baseline_source_read_bytes": baseline.stats.total_source_read_bytes,
        "wall_ratio": cand_wall_med / base_wall_med,
        "cpu_ratio": cand_cpu_med / base_cpu_med,
        "baseline_wall_ns": int(base_wall_med),
        "candidate_wall_ns": int(cand_wall_med),
        "baseline_cpu_ns": int(base_cpu_med),
        "candidate_cpu_ns": int(cand_cpu_med),
    }


def main() -> None:
    rows = []
    for size in SIZES:
        for family, maker, expected_gate in (
            ("diverse_numeric", diverse_numeric_root, True),
            ("repetitive_numeric", repetitive_numeric_root, False),
            ("phase_shift_numeric", phase_shift_numeric_root, False),
            ("binary_control", binary_root, False),
        ):
            data = maker(size)
            result = _pair(data)
            result.update({"family": family, "size": size})
            assert result["gated"] is expected_gate
            if expected_gate:
                assert result["baseline_reuse_fraction"] <= MAX_SKIPPED_REUSE_FRACTION
                assert result["wall_ratio"] <= NUMERIC_MAX_RELATIVE_WALL
                assert result["cpu_ratio"] <= NUMERIC_MAX_RELATIVE_CPU
            else:
                assert result["wall_ratio"] <= FALLTHROUGH_MAX_RELATIVE_WALL
                assert result["cpu_ratio"] <= FALLTHROUGH_MAX_RELATIVE_CPU
            rows.append(result)

    print(json.dumps({
        "experiment": "ONE-G0.2 numeric morphology gate",
        "repetitions": REPETITIONS,
        "gates": {
            "numeric_max_relative_wall": NUMERIC_MAX_RELATIVE_WALL,
            "numeric_max_relative_cpu": NUMERIC_MAX_RELATIVE_CPU,
            "fallthrough_max_relative_wall": FALLTHROUGH_MAX_RELATIVE_WALL,
            "fallthrough_max_relative_cpu": FALLTHROUGH_MAX_RELATIVE_CPU,
            "max_skipped_reuse_fraction": MAX_SKIPPED_REUSE_FRACTION,
        },
        "rows": rows,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
