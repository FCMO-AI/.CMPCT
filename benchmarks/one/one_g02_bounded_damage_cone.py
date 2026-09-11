"""ONE-G0.2 bounded damaged-relation cone through generic ONE Law + Surprise.

Frozen by ONE_G02_BOUNDED_DAMAGE_CONE_PREREG_2026-09-05.md.
Fanout is derived from the existing 4096-node resource envelope: isqrt(4096)=64.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import time

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
FANOUT = math.isqrt(LIMITS.max_nodes)
MAX_CONE_DEPTH = 4


def _relation_parts_plus1(nodes: list[Node], source: bytes, target: bytes):
    parts: list[tuple[Ref, int]] = []
    i = 0
    n = len(target)
    while i < n:
        if i > 0 and target[i] == source[i - 1]:
            start = i
            i += 1
            while i < n and target[i] == source[i - 1]:
                i += 1
            length = i - start
            parts.append((Ref(0, start - 1, length), length))
        else:
            start = i
            i += 1
            while i < n and not (i > 0 and target[i] == source[i - 1]):
                i += 1
            payload = target[start:i]
            node_id = len(nodes)
            nodes.append(Node("surprise", surprise=payload))
            parts.append((Ref(node_id), len(payload)))
    return parts


def _bounded_concat(nodes: list[Node], parts: list[tuple[Ref, int]]):
    if not parts:
        raise AssertionError("bounded cone has no parts")
    depth = 0
    max_fanout = 0
    current = parts
    while len(current) > 1:
        next_level: list[tuple[Ref, int]] = []
        for start in range(0, len(current), FANOUT):
            group = current[start:start + FANOUT]
            refs = tuple(ref for ref, _length in group)
            declared = sum(length for _ref, length in group)
            max_fanout = max(max_fanout, len(refs))
            node_id = len(nodes)
            nodes.append(Node("concat", refs=refs, declared_length=declared))
            next_level.append((Ref(node_id), declared))
        current = next_level
        depth += 1
    return current[0][0], depth, max_fanout


def _encode_bounded(source: bytes, target: bytes):
    nodes: list[Node] = [Node("surprise", surprise=source)]
    parts = _relation_parts_plus1(nodes, source, target)
    current_ref, cone_depth, max_fanout = _bounded_concat(nodes, parts)
    program = Program(
        tuple(nodes),
        {"previous": temporal._root(0, source), "current": temporal.Root(current_ref, len(target), temporal.sha256(target).hexdigest())},
        LIMITS,
    )
    wire, stats = encode_program(program)
    return program, wire, stats, cone_depth, max_fanout, len(parts)


def _encode_bounded_public(source: bytes, target: bytes):
    program, wire, stats, _depth, _fanout, _parts = _encode_bounded(source, target)
    return program, wire, stats


def _timed(builder, source: bytes, target: bytes):
    t0 = time.perf_counter_ns()
    builder(source, target)
    return time.perf_counter_ns() - t0


def _verify(wire: bytes, source: bytes, target: bytes):
    program = decode_program(wire)
    outputs, stats = evaluate(program)
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("bounded damaged relation reconstruction mismatch")
    return program, stats


def run():
    rows = []
    aggregate_literal_wire = 0
    aggregate_candidate_wire = 0
    all_exact = all_density = all_control = all_reader = True
    all_materialized = all_nodes = all_fanout = all_depth = True

    for size in SIZES:
        generated = _relation_cases(size)
        for case in CASES:
            source, target, expected, shift = generated[case]
            if not expected or shift != 1:
                raise AssertionError(f"frozen productive relation changed: {size} {case}")

            literal_samples = []
            candidate_samples = []
            for round_id in range(ROUNDS):
                order = ((flat._encode_literal, literal_samples), (_encode_bounded_public, candidate_samples))
                if round_id & 1:
                    order = tuple(reversed(order))
                for builder, samples in order:
                    samples.append(_timed(builder, source, target))

            _lp, lw, ls = flat._encode_literal(source, target)
            cp, cw, cs, cone_depth, max_fanout, leaf_parts = _encode_bounded(source, target)
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
            fanout_pass = max_fanout <= FANOUT
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
                "candidate_node_count": node_count,
                "frozen_node_limit": node_limit,
                "max_concat_fanout": max_fanout,
                "derived_fanout_limit": FANOUT,
                "concat_cone_depth": cone_depth,
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
    passed = (all_exact and all_density and all_control and all_reader and all_materialized
              and all_nodes and all_fanout and all_depth and aggregate_ratio <= MAX_AGG_WIRE_RATIO)
    return {
        "schema": "cmpct-one-g02-bounded-damage-cone-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "derived_concat_fanout": FANOUT,
        "frozen_max_cone_depth": MAX_CONE_DEPTH,
        "frozen_sizes": list(SIZES),
        "frozen_cases": list(CASES),
        "frozen_rounds": ROUNDS,
        "aggregate_literal_wire_bytes": aggregate_literal_wire,
        "aggregate_candidate_wire_bytes": aggregate_candidate_wire,
        "aggregate_candidate_over_literal_wire": aggregate_ratio,
        "decision": "advance_bounded_damage_cone" if passed else "hold_bounded_damage_cone",
        "claim_boundary": "generic ONE bounded representation viability only; reference-Python creation timing is diagnostic",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_bounded_damage_cone" else 1)
