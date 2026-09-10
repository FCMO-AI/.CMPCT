from __future__ import annotations

"""Causal hosted A/B for ONE-G0.2 second-stage ADD8/XOR rejection.

This benchmark starts after the existing primary sampler and economic gate.  It measures
only the relation-check boundary; it is not an archive/product/Genesis benchmark.
"""

from hashlib import sha256
import json
from pathlib import Path
import statistics
import time
from typing import Any, Callable

from experiments.one.general_law_archive import _all_add8, _all_xor, _sample_positions

OUT = Path("one-g02-second-stage-relation-kernel-ab.json")
LENGTHS = (256, 4096, 16384, 65536, 262144)
RELATIONS = ("add8", "xor")
KINDS = ("true", "stage2_collision", "dual_collision")
REPETITIONS = 101


def _stream(n: int, label: str) -> bytes:
    out = bytearray()
    counter = 0
    seed = label.encode("utf-8")
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _second_positions(length: int) -> tuple[int, ...]:
    primary = _sample_positions(length)
    pset = set(primary)
    mids = {
        left + (right - left) // 2
        for left, right in zip(primary, primary[1:], strict=False)
        if left < left + (right - left) // 2 < right
    }
    return tuple(sorted(mids - pset))


def _outside_sparse(length: int) -> int:
    used = set(_sample_positions(length)) | set(_second_positions(length))
    for i in range(length):
        if i not in used:
            return i
    raise RuntimeError(f"no dual-collision position for {length}")


def _apply(relation: str, source: bytes) -> bytes:
    if relation == "add8":
        return bytes((b + 37) & 0xFF for b in source)
    if relation == "xor":
        return bytes(b ^ 0xA5 for b in source)
    raise KeyError(relation)


def _make_case(relation: str, length: int, kind: str) -> tuple[bytes, bytes]:
    source = _stream(length, f"one-g02-stage2-kernel-{relation}-{length}")
    target = bytearray(_apply(relation, source))
    if kind == "stage2_collision":
        second = _second_positions(length)
        if not second:
            raise RuntimeError("missing second-stage positions")
        target[second[0]] ^= 1
    elif kind == "dual_collision":
        target[_outside_sparse(length)] ^= 1
    elif kind != "true":
        raise KeyError(kind)
    return source, bytes(target)


def _primary_pass(relation: str, source: bytes, target: bytes) -> bool:
    positions = _sample_positions(len(source))
    if relation == "add8":
        d = (target[positions[0]] - source[positions[0]]) & 0xFF
        return all(((source[i] + d) & 0xFF) == target[i] for i in positions)
    m = source[positions[0]] ^ target[positions[0]]
    return all((source[i] ^ m) == target[i] for i in positions)


def _baseline(relation: str, source: bytes, target: bytes) -> bool:
    if relation == "add8":
        d = (target[_sample_positions(len(source))[0]] - source[_sample_positions(len(source))[0]]) & 0xFF
        return _all_add8(source, target, d)
    m = source[_sample_positions(len(source))[0]] ^ target[_sample_positions(len(source))[0]]
    return _all_xor(source, target, m)


def _candidate(relation: str, source: bytes, target: bytes) -> bool:
    primary = _sample_positions(len(source))
    second = _second_positions(len(source))
    if relation == "add8":
        d = (target[primary[0]] - source[primary[0]]) & 0xFF
        if not all(((source[i] + d) & 0xFF) == target[i] for i in second):
            return False
        return _all_add8(source, target, d)
    m = source[primary[0]] ^ target[primary[0]]
    if not all((source[i] ^ m) == target[i] for i in second):
        return False
    return _all_xor(source, target, m)


def _measure(fn: Callable[[str, bytes, bytes], bool], relation: str, source: bytes, target: bytes) -> tuple[bool, int, int]:
    t0w = time.perf_counter_ns()
    t0c = time.process_time_ns()
    value = fn(relation, source, target)
    cpu = time.process_time_ns() - t0c
    wall = time.perf_counter_ns() - t0w
    return value, wall, cpu


def _timed_row(relation: str, length: int, kind: str) -> dict[str, Any]:
    source, target = _make_case(relation, length, kind)
    assert _primary_pass(relation, source, target)
    expected = kind == "true"
    assert _baseline(relation, source, target) is expected
    assert _candidate(relation, source, target) is expected

    # Warm both paths before timing.
    _baseline(relation, source, target)
    _candidate(relation, source, target)

    bw: list[int] = []
    bc: list[int] = []
    cw: list[int] = []
    cc: list[int] = []
    checksum = 0
    for rep in range(REPETITIONS):
        order = ("candidate", "baseline") if rep & 1 else ("baseline", "candidate")
        for arm in order:
            fn = _candidate if arm == "candidate" else _baseline
            value, wall, cpu = _measure(fn, relation, source, target)
            checksum ^= int(value)
            if arm == "candidate":
                cw.append(wall)
                cc.append(cpu)
            else:
                bw.append(wall)
                bc.append(cpu)
    if checksum not in (0, 1):
        raise AssertionError("unreachable checksum")

    bwm = int(statistics.median(bw))
    bcm = int(statistics.median(bc))
    cwm = int(statistics.median(cw))
    ccm = int(statistics.median(cc))
    second_bytes = 2 * len(_second_positions(length))
    baseline_modeled = 2 * length
    candidate_modeled = second_bytes + (baseline_modeled if kind != "stage2_collision" else 0)

    return {
        "case": f"{relation}-{length}-{kind}",
        "relation": relation,
        "length": length,
        "kind": kind,
        "expected": expected,
        "primary_pass": True,
        "baseline_value": expected,
        "candidate_value": expected,
        "second_positions": len(_second_positions(length)),
        "baseline_wall_ns": bwm,
        "candidate_wall_ns": cwm,
        "baseline_cpu_ns": bcm,
        "candidate_cpu_ns": ccm,
        "wall_ratio": cwm / bwm,
        "cpu_ratio": ccm / bcm,
        "baseline_modeled_remaining_bytes": baseline_modeled,
        "candidate_modeled_remaining_bytes": candidate_modeled,
        "modeled_byte_ratio": candidate_modeled / baseline_modeled,
    }


def _within_noise(candidate_ns: int, baseline_ns: int) -> bool:
    return candidate_ns <= max(int(baseline_ns * 1.05), baseline_ns + 3_000_000)


def decide(rows: list[dict[str, Any]]) -> tuple[str, dict[str, bool]]:
    h1 = all(
        row["primary_pass"]
        and row["baseline_value"] == row["candidate_value"] == row["expected"]
        for row in rows
    )
    hostile = [row for row in rows if row["kind"] == "stage2_collision"]
    h2 = all(
        _within_noise(row["candidate_cpu_ns"], row["baseline_cpu_ns"])
        and _within_noise(row["candidate_wall_ns"], row["baseline_wall_ns"])
        for row in hostile
    ) and all(
        row["cpu_ratio"] <= 0.50 or row["wall_ratio"] <= 0.50
        for row in hostile
        if row["length"] >= 4096
    )
    survivors = [row for row in rows if row["kind"] in {"true", "dual_collision"} and row["length"] >= 4096]
    h3 = all(row["cpu_ratio"] <= 1.20 and row["wall_ratio"] <= 1.20 for row in survivors)
    broad = [row for row in rows if row["length"] >= 4096]
    h4 = (
        statistics.median(row["cpu_ratio"] for row in broad) <= 1.00
        and statistics.median(row["wall_ratio"] for row in broad) <= 1.00
    )
    hypotheses = {
        "H1_correctness": h1,
        "H2_hostile_benefit": h2,
        "H3_survivor_debt": h3,
        "H4_broad_kernel_economics": h4,
    }
    if not h1:
        return "RETIRE_SECOND_STAGE_RELATION_KERNEL", hypotheses
    if not all((h2, h3, h4)):
        return "HOLD_SECOND_STAGE_RELATION_KERNEL", hypotheses
    return "ADVANCE_SECOND_STAGE_RELATION_KERNEL_TO_WRITER_AB", hypotheses


def run() -> dict[str, Any]:
    rows = [
        _timed_row(relation, length, kind)
        for relation in RELATIONS
        for length in LENGTHS
        for kind in KINDS
    ]
    decision, hypotheses = decide(rows)
    broad = [row for row in rows if row["length"] >= 4096]
    kills = [row for row in rows if row["kind"] == "stage2_collision"]
    survivors = [row for row in rows if row["kind"] in {"true", "dual_collision"}]
    return {
        "schema": "cmpct-one-g02-second-stage-relation-kernel-ab-v1",
        "experimental_version": "ONE-G0.2",
        "repetitions": REPETITIONS,
        "relations": list(RELATIONS),
        "lengths": list(LENGTHS),
        "kinds": list(KINDS),
        "rows": rows,
        "summary": {
            "broad_median_cpu_ratio": statistics.median(row["cpu_ratio"] for row in broad),
            "broad_median_wall_ratio": statistics.median(row["wall_ratio"] for row in broad),
            "kill_median_cpu_ratio": statistics.median(row["cpu_ratio"] for row in kills),
            "kill_median_wall_ratio": statistics.median(row["wall_ratio"] for row in kills),
            "survivor_median_cpu_ratio": statistics.median(row["cpu_ratio"] for row in survivors),
            "survivor_median_wall_ratio": statistics.median(row["wall_ratio"] for row in survivors),
        },
        "hypotheses": hypotheses,
        "decision": decision,
        "claim_boundary": "relation-check kernel timing only; no writer/product/runtime or Genesis claim",
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
