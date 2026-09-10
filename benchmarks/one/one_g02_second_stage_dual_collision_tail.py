from __future__ import annotations

"""Hosted hostile supplement for the ONE-G0.2 second-stage relation kernel.

Measures only the post-primary-sampler relation-check boundary. This deliberately
constructs false ADD8/XOR candidates that evade both sparse stages and fail late
in the mandatory exact proof. It is not a writer/product/Genesis benchmark.
"""

import json
from pathlib import Path
import statistics
import time
from typing import Any, Callable

from benchmarks.one.one_g02_second_stage_relation_kernel_ab import (
    _apply,
    _baseline_prepared,
    _candidate_prepared,
    _nomination_constant,
    _primary_pass,
    _stream,
)
from experiments.one.general_law_archive import _sample_positions

OUT = Path("one-g02-second-stage-dual-collision-tail.json")
LENGTHS = (4096, 16384, 65536, 262144)
RELATIONS = ("add8", "xor")
REPETITIONS = 101


def _oracle_second_positions(primary: tuple[int, ...]) -> tuple[int, ...]:
    """Independent copy of the frozen midpoint geometry for hostile checking."""
    used = set(primary)
    mids: list[int] = []
    for left, right in zip(primary, primary[1:], strict=False):
        midpoint = left + (right - left) // 2
        if left < midpoint < right and midpoint not in used:
            mids.append(midpoint)
    return tuple(sorted(set(mids)))


def _last_outside_sparse(length: int, primary: tuple[int, ...]) -> tuple[int, tuple[int, ...]]:
    second = _oracle_second_positions(primary)
    used = set(primary) | set(second)
    for index in range(length - 1, -1, -1):
        if index not in used:
            return index, second
    raise RuntimeError(f"no dual-collision tail position for length={length}")


def _make_case(relation: str, length: int) -> tuple[bytes, bytes, int, tuple[int, ...], tuple[int, ...]]:
    source = _stream(length, f"one-g02-stage2-dual-tail-{relation}-{length}")
    target = bytearray(_apply(relation, source))
    primary = tuple(_sample_positions(length))
    poison, second = _last_outside_sparse(length, primary)
    target[poison] ^= 1
    return source, bytes(target), poison, primary, second


PreparedFn = Callable[[str, bytes, bytes, int, tuple[int, ...]], bool]


def _measure(
    fn: PreparedFn,
    relation: str,
    source: bytes,
    target: bytes,
    constant: int,
    primary: tuple[int, ...],
) -> tuple[bool, int, int]:
    t0w = time.perf_counter_ns()
    t0c = time.process_time_ns()
    value = fn(relation, source, target, constant, primary)
    cpu = time.process_time_ns() - t0c
    wall = time.perf_counter_ns() - t0w
    return value, wall, cpu


def _row(relation: str, length: int) -> dict[str, Any]:
    source, target, poison, primary, oracle_second = _make_case(relation, length)
    constant = _nomination_constant(relation, source, target, primary)

    # Hostile construction must fool the already-paid primary sampler and both
    # sparse sets. The imported candidate still owns the actual timed stage-2
    # implementation; this oracle geometry is computed independently here.
    assert _primary_pass(relation, source, target)
    assert poison not in set(primary)
    assert poison not in set(oracle_second)
    assert _baseline_prepared(relation, source, target, constant, primary) is False
    assert _candidate_prepared(relation, source, target, constant, primary) is False

    _baseline_prepared(relation, source, target, constant, primary)
    _candidate_prepared(relation, source, target, constant, primary)

    bw: list[int] = []
    bc: list[int] = []
    cw: list[int] = []
    cc: list[int] = []
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep & 1 else ("baseline", "candidate")
        for arm in order:
            fn = _candidate_prepared if arm == "candidate" else _baseline_prepared
            value, wall, cpu = _measure(fn, relation, source, target, constant, primary)
            if value is not False:
                raise AssertionError(f"false relation survived: {relation=} {length=}")
            if arm == "candidate":
                cw.append(wall)
                cc.append(cpu)
            else:
                bw.append(wall)
                bc.append(cpu)

    bwm = int(statistics.median(bw))
    bcm = int(statistics.median(bc))
    cwm = int(statistics.median(cw))
    ccm = int(statistics.median(cc))
    baseline_modeled = 2 * length
    second_bytes = 2 * len(oracle_second)
    candidate_modeled = baseline_modeled + second_bytes

    return {
        "case": f"{relation}-{length}-dual_collision_late",
        "relation": relation,
        "length": length,
        "kind": "dual_collision_late",
        "poison_index": poison,
        "primary_positions": len(primary),
        "second_stage_positions": len(oracle_second),
        "primary_pass": True,
        "baseline_value": False,
        "candidate_value": False,
        "baseline_wall_ns": bwm,
        "candidate_wall_ns": cwm,
        "baseline_cpu_ns": bcm,
        "candidate_cpu_ns": ccm,
        "wall_ratio": cwm / bwm,
        "cpu_ratio": ccm / bcm,
        "baseline_modeled_remaining_bytes": baseline_modeled,
        "candidate_modeled_remaining_bytes": candidate_modeled,
        "modeled_extra_sparse_bytes": second_bytes,
        "modeled_byte_ratio": candidate_modeled / baseline_modeled,
    }


def decide(rows: list[dict[str, Any]]) -> tuple[str, dict[str, bool]]:
    h1 = all(
        row["primary_pass"]
        and row["baseline_value"] is False
        and row["candidate_value"] is False
        and row["poison_index"] < row["length"]
        for row in rows
    )
    h2 = all(row["cpu_ratio"] <= 1.20 and row["wall_ratio"] <= 1.20 for row in rows)
    h3 = (
        statistics.median(row["cpu_ratio"] for row in rows) <= 1.05
        and statistics.median(row["wall_ratio"] for row in rows) <= 1.05
    )
    h4 = all(
        row["baseline_modeled_remaining_bytes"] == 2 * row["length"]
        and row["candidate_modeled_remaining_bytes"]
        == row["baseline_modeled_remaining_bytes"] + row["modeled_extra_sparse_bytes"]
        and row["modeled_extra_sparse_bytes"] == 2 * row["second_stage_positions"]
        for row in rows
    )
    hypotheses = {
        "H1_correctness_and_hostile_construction": h1,
        "H2_per_row_survivor_debt": h2,
        "H3_broad_survivor_debt": h3,
        "H4_modeled_accounting": h4,
    }
    if not h1:
        return "RETIRE_SECOND_STAGE_DUAL_COLLISION_TAIL", hypotheses
    if not all((h2, h3, h4)):
        return "HOLD_SECOND_STAGE_DUAL_COLLISION_TAIL", hypotheses
    return "ADVANCE_SECOND_STAGE_DUAL_COLLISION_TAIL_SAFETY_ONLY", hypotheses


def run() -> dict[str, Any]:
    rows = [_row(relation, length) for relation in RELATIONS for length in LENGTHS]
    decision, hypotheses = decide(rows)
    return {
        "schema": "cmpct-one-g02-second-stage-dual-collision-tail-v1",
        "experimental_version": "ONE-G0.2",
        "timing_boundary": "post-primary-sampler-and-nomination",
        "relations": list(RELATIONS),
        "lengths": list(LENGTHS),
        "kind": "dual_collision_late",
        "repetitions": REPETITIONS,
        "rows": rows,
        "summary": {
            "median_cpu_ratio": statistics.median(row["cpu_ratio"] for row in rows),
            "median_wall_ratio": statistics.median(row["wall_ratio"] for row in rows),
            "worst_cpu_ratio": max(row["cpu_ratio"] for row in rows),
            "worst_wall_ratio": max(row["wall_ratio"] for row in rows),
            "max_modeled_extra_sparse_bytes": max(row["modeled_extra_sparse_bytes"] for row in rows),
        },
        "hypotheses": hypotheses,
        "decision": decision,
        "claim_boundary": "hostile post-primary relation-check survivor tax only; no writer/product/runtime or Genesis claim",
        "does_not_modify_v3_kernel_decision": True,
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }


def main() -> int:
    result = run()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
