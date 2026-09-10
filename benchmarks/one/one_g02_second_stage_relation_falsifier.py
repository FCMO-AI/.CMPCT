from __future__ import annotations

"""Transfer-only ONE-G0.2 oracle for a second sparse relation falsifier.

The candidate stage is rejection-only. It never accepts a Law; full exact proof remains the
only positive authority. Genesis inputs are never used.
"""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from experiments.one.general_law_archive import SAMPLE_POINTS, _sample_positions

OUT = Path("one-g02-second-stage-relation-falsifier.json")
FROZEN_SAMPLE_POINTS = 16
LENGTHS = (32, 256, 4096, 16384)
RELATIONS = ("add8", "xor")
KINDS = ("true", "stage2_collision", "dual_collision")


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _oracle_primary_positions(length: int) -> tuple[int, ...]:
    """Independent transcription of the frozen 16-point writer geometry."""
    if length <= 0:
        return ()
    if length <= FROZEN_SAMPLE_POINTS:
        return tuple(range(length))
    return tuple(
        sorted(
            {
                (i * (length - 1)) // (FROZEN_SAMPLE_POINTS - 1)
                for i in range(FROZEN_SAMPLE_POINTS)
            }
        )
    )


def _oracle_second_positions(primary: tuple[int, ...]) -> tuple[int, ...]:
    """Return midpoint probes that are strictly between adjacent primary probes."""
    points: set[int] = set()
    primary_set = set(primary)
    for left, right in zip(primary, primary[1:], strict=False):
        midpoint = left + (right - left) // 2
        if left < midpoint < right and midpoint not in primary_set:
            points.add(midpoint)
    return tuple(sorted(points))


def _relation_byte(relation: str, source: int) -> int:
    if relation == "add8":
        return (source + 37) & 0xFF
    if relation == "xor":
        return source ^ 0xA5
    raise KeyError(relation)


def _relation_holds_at(relation: str, source: bytes, target: bytes, positions: tuple[int, ...]) -> bool:
    return all(_relation_byte(relation, source[index]) == target[index] for index in positions)


def _full_relation_holds(relation: str, source: bytes, target: bytes) -> bool:
    return len(source) == len(target) and all(
        _relation_byte(relation, left) == right
        for left, right in zip(source, target, strict=True)
    )


def _first_outside(length: int, *position_sets: tuple[int, ...]) -> int:
    occupied: set[int] = set()
    for positions in position_sets:
        occupied.update(positions)
    for index in range(length):
        if index not in occupied:
            return index
    raise RuntimeError(f"no position outside sparse probes for length={length}")


def _build_case(relation: str, length: int, kind: str) -> tuple[bytes, bytes, int | None]:
    source = _hash_stream(length, f"one-g02-stage2-source-{relation}-{length}".encode())
    target = bytearray(_relation_byte(relation, value) for value in source)
    primary = _oracle_primary_positions(length)
    second = _oracle_second_positions(primary)

    poison: int | None = None
    if kind == "stage2_collision":
        if not second:
            raise RuntimeError(f"no second-stage poison position for {relation}-{length}")
        poison = second[0]
        target[poison] ^= 0x01
    elif kind == "dual_collision":
        poison = _first_outside(length, primary, second)
        target[poison] ^= 0x01
    elif kind != "true":
        raise KeyError(kind)

    return source, bytes(target), poison


def _row(relation: str, length: int, kind: str) -> dict[str, Any]:
    primary = _oracle_primary_positions(length)
    writer_primary = tuple(_sample_positions(length))
    second = _oracle_second_positions(primary)
    source, target, poison = _build_case(relation, length, kind)

    primary_pass = _relation_holds_at(relation, source, target, primary)
    second_pass = _relation_holds_at(relation, source, target, second)
    exact_pass = _full_relation_holds(relation, source, target)

    baseline_remaining = 2 * length
    second_stage_bytes = 2 * len(second)
    candidate_needs_exact = second_pass
    candidate_exact_bytes = baseline_remaining if candidate_needs_exact else 0
    candidate_remaining = second_stage_bytes + candidate_exact_bytes

    return {
        "case": f"{relation}-{length}-{kind}",
        "relation": relation,
        "length": length,
        "kind": kind,
        "poison_index": poison,
        "primary_positions": list(primary),
        "writer_primary_positions": list(writer_primary),
        "second_positions": list(second),
        "primary_matches_writer": primary == writer_primary,
        "second_nonempty": bool(second),
        "second_disjoint": not (set(primary) & set(second)),
        "dual_position_available": bool(set(range(length)) - set(primary) - set(second)),
        "primary_pass": primary_pass,
        "second_pass": second_pass,
        "exact_pass": exact_pass,
        "baseline_remaining_bytes": baseline_remaining,
        "second_stage_bytes": second_stage_bytes,
        "candidate_exact_proof_bytes": candidate_exact_bytes,
        "candidate_remaining_bytes": candidate_remaining,
        "remaining_delta_bytes": candidate_remaining - baseline_remaining,
        "exact_proof_bytes_avoided": baseline_remaining - candidate_exact_bytes,
        "stage2_kill_speedup_by_modeled_bytes": (
            baseline_remaining / candidate_remaining
            if kind == "stage2_collision" and candidate_remaining
            else None
        ),
    }


def run() -> dict[str, Any]:
    rows = [
        _row(relation, length, kind)
        for relation in RELATIONS
        for length in LENGTHS
        for kind in KINDS
    ]

    h1 = SAMPLE_POINTS == FROZEN_SAMPLE_POINTS and all(
        row["primary_matches_writer"]
        and row["second_nonempty"]
        and row["second_disjoint"]
        and row["dual_position_available"]
        for row in rows
    )
    h2 = all(
        row["primary_pass"] and row["second_pass"] and row["exact_pass"]
        for row in rows
        if row["kind"] == "true"
    )
    h3 = all(
        row["primary_pass"]
        and not row["second_pass"]
        and not row["exact_pass"]
        and row["candidate_exact_proof_bytes"] == 0
        and row["candidate_remaining_bytes"] < row["baseline_remaining_bytes"]
        for row in rows
        if row["kind"] == "stage2_collision"
    )
    h4 = all(
        row["primary_pass"]
        and row["second_pass"]
        and not row["exact_pass"]
        and row["candidate_exact_proof_bytes"] == row["baseline_remaining_bytes"]
        and row["remaining_delta_bytes"] == row["second_stage_bytes"]
        for row in rows
        if row["kind"] == "dual_collision"
    )
    h5 = all(
        row["exact_proof_bytes_avoided"] == row["baseline_remaining_bytes"]
        and row["stage2_kill_speedup_by_modeled_bytes"] is not None
        and row["stage2_kill_speedup_by_modeled_bytes"] > 1.0
        for row in rows
        if row["kind"] == "stage2_collision"
    )

    if not h1 or not h2:
        decision = "RETIRE_OR_REPAIR_SECOND_STAGE_FALSIFIER"
    elif not h3 or not h4 or not h5:
        decision = "HOLD_SECOND_STAGE_FALSIFIER"
    else:
        decision = "ADVANCE_SECOND_STAGE_FALSIFIER_ORACLE_ONLY"

    stage2_rows = [row for row in rows if row["kind"] == "stage2_collision"]
    dual_rows = [row for row in rows if row["kind"] == "dual_collision"]
    true_rows = [row for row in rows if row["kind"] == "true"]

    return {
        "schema": "cmpct-one-g02-second-stage-relation-falsifier-v1",
        "experimental_version": "ONE-G0.2",
        "writer_sample_points": SAMPLE_POINTS,
        "frozen_oracle_sample_points": FROZEN_SAMPLE_POINTS,
        "relations": list(RELATIONS),
        "lengths": list(LENGTHS),
        "kinds": list(KINDS),
        "rows": rows,
        "summary": {
            "stage2_kill_rows": len(stage2_rows),
            "stage2_total_exact_proof_bytes_avoided": sum(row["exact_proof_bytes_avoided"] for row in stage2_rows),
            "stage2_total_candidate_remaining_bytes": sum(row["candidate_remaining_bytes"] for row in stage2_rows),
            "dual_total_added_sparse_bytes": sum(row["remaining_delta_bytes"] for row in dual_rows),
            "true_total_added_sparse_bytes": sum(row["remaining_delta_bytes"] for row in true_rows),
            "max_stage2_kill_speedup_by_modeled_bytes": max(row["stage2_kill_speedup_by_modeled_bytes"] for row in stage2_rows),
            "min_stage2_kill_speedup_by_modeled_bytes": min(row["stage2_kill_speedup_by_modeled_bytes"] for row in stage2_rows),
        },
        "hypotheses": {
            "H1_independent_geometry": h1,
            "H2_true_law_retention": h2,
            "H3_stage2_kill": h3,
            "H4_dual_collision_honesty": h4,
            "H5_information_yield_accounting": h5,
        },
        "decision": decision,
        "claim_boundary": "modeled relation-check traffic oracle only; no product runtime claim, no representation change, not Genesis",
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
