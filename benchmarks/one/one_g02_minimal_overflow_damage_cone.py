"""ONE-G0.2 minimal-overflow damaged relation cone.

Frozen by ONE_G02_MINIMAL_OVERFLOW_DAMAGE_CONE_PREREG_2026-09-05.md.
Hierarchy is introduced only when the existing 4096-ref concat envelope requires it,
and only the minimum-count / minimum-byte contiguous window is grouped.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import time

from benchmarks.one import one_g02_bounded_damage_cone as bounded
from benchmarks.one import one_g02_damaged_relation_law_expression as flat
from benchmarks.one import one_g02_temporal_adjacency_writer_integration as temporal
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.ir import Limits, Node, Program, Ref
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = flat.SIZES
CASES = flat.CASES
ROUNDS = flat.ROUNDS
MAX_AGG_WIRE_RATIO = flat.MAX_AGG_WIRE_RATIO
MAX_CONTROL_DEBT_SHARE = flat.MAX_CONTROL_DEBT_SHARE
MAX_READER_WORK_RATIO = flat.MAX_READER_WORK_RATIO
MAX_MATERIALIZED_RATIO = flat.MAX_MATERIALIZED_RATIO
LIMITS = Limits(max_nodes=4096, max_output_bytes=64*1024*1024,
                max_work_bytes=256*1024*1024, max_depth=64)
CAP = LIMITS.max_nodes
MAX_CONE_DEPTH = 4


def _minimum_byte_window(parts: list[tuple[Ref, int]], width: int) -> int:
    if width <= 0 or width > len(parts):
        raise AssertionError("invalid overflow window width")
    running = sum(length for _ref, length in parts[:width])
    best_sum = running
    best_start = 0
    for start in range(1, len(parts) - width + 1):
        running += parts[start + width - 1][1] - parts[start - 1][1]
        if running < best_sum:
            best_sum = running
            best_start = start
    return best_start


def _compile_group(nodes: list[Node], parts: list[tuple[Ref, int]], depth: int = 1):
    """Return one Ref for parts while never exceeding CAP refs per concat."""
    if not parts:
        raise AssertionError("cannot compile empty group")
    if len(parts) <= CAP:
        declared = sum(length for _ref, length in parts)
        refs = tuple(ref for ref, _length in parts)
        node_id = len(nodes)
        nodes.append(Node("concat", refs=refs, declared_length=declared))
        return Ref(node_id), declared, depth, len(refs), len(refs)

    # Recursively create the minimum hierarchy needed for this group.
    reduction = len(parts) - CAP
    width = reduction + 1
    start = _minimum_byte_window(parts, width)
    child_ref, child_len, child_depth, child_max_fanout, child_refs_traversed = _compile_group(
        nodes, parts[start:start + width], depth + 1
    )
    reduced = parts[:start] + [(child_ref, child_len)] + parts[start + width:]
    parent_ref, declared, parent_depth, parent_max_fanout, parent_refs_traversed = _compile_group(
        nodes, reduced, depth
    )
    return (
        parent_ref,
        declared,
        max(child_depth, parent_depth),
        max(child_max_fanout, parent_max_fanout),
        child_refs_traversed + parent_refs_traversed,
    )


def _encode_minimal(source: bytes, target: bytes):
    nodes: list[Node] = [Node("surprise", surprise=source)]
    parts = bounded._relation_parts_plus1(nodes, source, target)
    original_parts = len(parts)
    grouped_overflow_parts = 0
    grouped_overflow_bytes = 0

    if len(parts) <= CAP:
        root_ref, _declared, cone_depth, max_fanout, refs_traversed = _compile_group(nodes, parts, 1)
    else:
        reduction = len(parts) - CAP
        width = reduction + 1
        start = _minimum_byte_window(parts, width)
        grouped = parts[start:start + width]
        grouped_overflow_parts = width
        grouped_overflow_bytes = sum(length for _ref, length in grouped)
        child_ref, child_len, child_depth, child_max_fanout, child_refs = _compile_group(nodes, grouped, 2)
        reduced = parts[:start] + [(child_ref, child_len)] + parts[start + width:]
        root_ref, _declared, root_depth, root_max_fanout, root_refs = _compile_group(nodes, reduced, 1)
        cone_depth = max(child_depth, root_depth)
        max_fanout = max(child_max_fanout, root_max_fanout)
        refs_traversed = child_refs + root_refs

    program = Program(
        tuple(nodes),
        {
            "previous": temporal._root(0, source),
            "current": temporal.Root(root_ref, len(target), temporal.sha256(target).hexdigest()),
        },
        LIMITS,
    )
    wire, stats = encode_program(program)
    return (
        program,
        wire,
        stats,
        cone_depth,
        max_fanout,
        original_parts,
        grouped_overflow_parts,
        grouped_overflow_bytes,
        refs_traversed,
    )


def _encode_minimal_public(source: bytes, target: bytes):
    program, wire, stats, *_rest = _encode_minimal(source, target)
    return program, wire, stats


def _timed(builder, source: bytes, target: bytes):
    t0 = time.perf_counter_ns()
    builder(source, target)
    return time.perf_counter_ns() - t0


def _verify(wire: bytes, source: bytes, target: bytes):
    program = decode_program(wire)
    outputs, stats = evaluate(program)
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("minimal-overflow damaged relation reconstruction mismatch")
    return program, stats


def run():
    rows = []
    aggregate_literal_wire = 0
    aggregate_candidate_wire = 0
    all_density = all_control = all_reader = all_materialized = True
    all_nodes = all_fanout = all_depth = True

    for size in SIZES:
        generated = _relation_cases(size)
        for case in CASES:
            source, target, expected, shift = generated[case]
            if not expected or shift != 1:
                raise AssertionError(f"frozen productive relation changed: {size} {case}")

            literal_samples = []
            candidate_samples = []
            for round_id in range(ROUNDS):
                order = ((flat._encode_literal, literal_samples), (_encode_minimal_public, candidate_samples))
                if round_id & 1:
                    order = tuple(reversed(order))
                for builder, samples in order:
                    samples.append(_timed(builder, source, target))

            _lp, lw, ls = flat._encode_literal(source, target)
            (
                cp, cw, cs, cone_depth, max_fanout, leaf_parts,
                grouped_parts, grouped_bytes, refs_traversed,
            ) = _encode_minimal(source, target)
            _ld, lvm = _verify(lw, source, target)
            _cd, cvm = _verify(cw, source, target)

            eliminated = ls.total_bytes - cs.total_bytes
            wire_ratio = cs.total_bytes / ls.total_bytes
            control_debt = max(0, cs.control_integrity_bytes - ls.control_integrity_bytes)
            control_share = control_debt / max(1, eliminated)
            reader_ratio = cvm.work_bytes / max(1, lvm.work_bytes)
            materialized_ratio = cvm.materialized_bytes / max(1, lvm.materialized_bytes)
            node_limit = max(8, math.ceil(size / 64) + 8)
            node_count = len(cp.nodes)

            density_pass = eliminated > 0
            control_pass = control_share <= MAX_CONTROL_DEBT_SHARE
            reader_pass = reader_ratio <= MAX_READER_WORK_RATIO
            materialized_pass = materialized_ratio <= MAX_MATERIALIZED_RATIO
            nodes_pass = node_count <= node_limit and node_count <= LIMITS.max_nodes
            fanout_pass = max_fanout <= CAP
            depth_pass = cone_depth <= MAX_CONE_DEPTH

            aggregate_literal_wire += ls.total_bytes
            aggregate_candidate_wire += cs.total_bytes
            all_density &= density_pass
            all_control &= control_pass
            all_reader &= reader_pass
            all_materialized &= materialized_pass
            all_nodes &= nodes_pass
            all_fanout &= fanout_pass
            all_depth &= depth_pass

            lmed = float(statistics.median(literal_samples))
            cmed = float(statistics.median(candidate_samples))
            rows.append({
                "relation_bytes": size,
                "case": case,
                "roundtrip_exact": True,
                "literal_wire_bytes": ls.total_bytes,
                "candidate_wire_bytes": cs.total_bytes,
                "candidate_over_literal_wire": wire_ratio,
                "bytes_eliminated": eliminated,
                "literal_surprise_bytes": ls.surprise_bytes,
                "candidate_surprise_bytes": cs.surprise_bytes,
                "literal_control_integrity_bytes": ls.control_integrity_bytes,
                "candidate_control_integrity_bytes": cs.control_integrity_bytes,
                "incremental_control_debt_bytes": control_debt,
                "control_debt_over_bytes_eliminated": control_share,
                "leaf_relation_parts": leaf_parts,
                "grouped_overflow_parts": grouped_parts,
                "grouped_overflow_bytes": grouped_bytes,
                "candidate_node_count": node_count,
                "frozen_node_limit": node_limit,
                "max_concat_fanout": max_fanout,
                "hard_concat_cap": CAP,
                "concat_cone_depth": cone_depth,
                "total_concat_refs_traversed": refs_traversed,
                "literal_reader_work_bytes": lvm.work_bytes,
                "candidate_reader_work_bytes": cvm.work_bytes,
                "candidate_over_literal_reader_work": reader_ratio,
                "literal_materialized_bytes": lvm.materialized_bytes,
                "candidate_materialized_bytes": cvm.materialized_bytes,
                "candidate_over_literal_materialized": materialized_ratio,
                "literal_nodes_evaluated": lvm.nodes_evaluated,
                "candidate_nodes_evaluated": cvm.nodes_evaluated,
                "literal_build_encode_median_ns": lmed,
                "candidate_build_encode_median_ns": cmed,
                "candidate_over_literal_build_encode": cmed / lmed,
                "density_pass": density_pass,
                "control_pass": control_pass,
                "reader_pass": reader_pass,
                "materialized_pass": materialized_pass,
                "nodes_pass": nodes_pass,
                "fanout_pass": fanout_pass,
                "depth_pass": depth_pass,
            })

    aggregate_ratio = aggregate_candidate_wire / aggregate_literal_wire
    passed = (
        all_density and all_control and all_reader and all_materialized and
        all_nodes and all_fanout and all_depth and aggregate_ratio <= MAX_AGG_WIRE_RATIO
    )
    return {
        "schema": "cmpct-one-g02-minimal-overflow-damage-cone-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "hard_concat_cap": CAP,
        "frozen_max_cone_depth": MAX_CONE_DEPTH,
        "frozen_sizes": list(SIZES),
        "frozen_cases": list(CASES),
        "frozen_rounds": ROUNDS,
        "aggregate_literal_wire_bytes": aggregate_literal_wire,
        "aggregate_candidate_wire_bytes": aggregate_candidate_wire,
        "aggregate_candidate_over_literal_wire": aggregate_ratio,
        "decision": "advance_minimal_overflow_damage_cone" if passed else "hold_minimal_overflow_damage_cone",
        "claim_boundary": "generic ONE bounded representation viability only; Python creation timing is diagnostic",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_minimal_overflow_damage_cone" else 1)
