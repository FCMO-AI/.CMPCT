"""ONE-G0.2 damaged-relation expression through generic ONE Law + Surprise.

Frozen by ONE_G02_DAMAGED_RELATION_LAW_EXPRESSION_PREREG_2026-09-05.md.
This is representation viability: no relation-specific reader operation exists.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import time

from benchmarks.one import one_g02_temporal_adjacency_writer_integration as temporal
from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import _relation_cases
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program

SIZES = (4*1024, 8*1024, 16*1024, 32*1024, 64*1024, 128*1024, 256*1024)
CASES = ("shift_plus1_damage_quarter", "fragmented_every96")
ROUNDS = 31
MAX_AGG_WIRE_RATIO = 0.75
MAX_CONTROL_DEBT_SHARE = 0.25
MAX_READER_WORK_RATIO = 1.75
MAX_MATERIALIZED_RATIO = 1.25


def _encode_literal(source: bytes, target: bytes):
    program = temporal._literal_program(source, target)
    wire, stats = encode_program(program)
    return program, wire, stats


def _encode_law(source: bytes, target: bytes):
    program = temporal._relation_program_plus1(source, target)
    wire, stats = encode_program(program)
    return program, wire, stats


def _verify(wire: bytes, source: bytes, target: bytes):
    program = decode_program(wire)
    outputs, stats = evaluate(program)
    if outputs != {"previous": source, "current": target}:
        raise AssertionError("damaged relation generic ONE reconstruction mismatch")
    return stats


def _timed(builder, source: bytes, target: bytes):
    t0 = time.perf_counter_ns()
    builder(source, target)
    return time.perf_counter_ns() - t0


def run():
    frozen = []
    for size in SIZES:
        generated = _relation_cases(size)
        for case in CASES:
            source, target, expected, shift = generated[case]
            if not expected or shift != 1:
                raise AssertionError(f"frozen productive relation changed: {size} {case}")
            frozen.append((size, case, source, target))

    rows = []
    aggregate_literal_wire = 0
    aggregate_candidate_wire = 0
    all_exact = True
    all_row_density = True
    all_control = True
    all_reader = True
    all_materialized = True
    all_nodes = True

    for size, case, source, target in frozen:
        literal_samples = []
        candidate_samples = []
        for round_id in range(ROUNDS):
            order = ((_encode_literal, literal_samples), (_encode_law, candidate_samples))
            if round_id & 1:
                order = tuple(reversed(order))
            for builder, samples in order:
                samples.append(_timed(builder, source, target))

        lp, lw, ls = _encode_literal(source, target)
        cp, cw, cs = _encode_law(source, target)
        lvm = _verify(lw, source, target)
        cvm = _verify(cw, source, target)

        exact = True
        eliminated = ls.total_bytes - cs.total_bytes
        row_ratio = cs.total_bytes / ls.total_bytes
        control_debt = max(0, cs.control_integrity_bytes - ls.control_integrity_bytes)
        control_debt_share = control_debt / max(1, eliminated)
        reader_ratio = cvm.work_bytes / max(1, lvm.work_bytes)
        materialized_ratio = cvm.materialized_bytes / max(1, lvm.materialized_bytes)
        node_limit = max(8, math.ceil(size / 64) + 8)
        node_count = len(cp.nodes)
        row_density_pass = eliminated > 0
        control_pass = control_debt_share <= MAX_CONTROL_DEBT_SHARE
        reader_pass = reader_ratio <= MAX_READER_WORK_RATIO
        materialized_pass = materialized_ratio <= MAX_MATERIALIZED_RATIO
        nodes_pass = node_count <= node_limit

        aggregate_literal_wire += ls.total_bytes
        aggregate_candidate_wire += cs.total_bytes
        all_exact &= exact
        all_row_density &= row_density_pass
        all_control &= control_pass
        all_reader &= reader_pass
        all_materialized &= materialized_pass
        all_nodes &= nodes_pass

        literal_med = float(statistics.median(literal_samples))
        candidate_med = float(statistics.median(candidate_samples))
        rows.append({
            "relation_bytes": size,
            "case": case,
            "roundtrip_exact": exact,
            "literal_wire_bytes": ls.total_bytes,
            "candidate_wire_bytes": cs.total_bytes,
            "candidate_over_literal_wire": row_ratio,
            "bytes_eliminated": eliminated,
            "literal_surprise_bytes": ls.surprise_bytes,
            "candidate_surprise_bytes": cs.surprise_bytes,
            "literal_control_integrity_bytes": ls.control_integrity_bytes,
            "candidate_control_integrity_bytes": cs.control_integrity_bytes,
            "incremental_control_debt_bytes": control_debt,
            "control_debt_over_bytes_eliminated": control_debt_share,
            "candidate_node_count": node_count,
            "frozen_node_limit": node_limit,
            "nodes_pass": nodes_pass,
            "literal_reader_work_bytes": lvm.work_bytes,
            "candidate_reader_work_bytes": cvm.work_bytes,
            "candidate_over_literal_reader_work": reader_ratio,
            "literal_materialized_bytes": lvm.materialized_bytes,
            "candidate_materialized_bytes": cvm.materialized_bytes,
            "candidate_over_literal_materialized": materialized_ratio,
            "literal_nodes_evaluated": lvm.nodes_evaluated,
            "candidate_nodes_evaluated": cvm.nodes_evaluated,
            "literal_build_encode_median_ns": literal_med,
            "candidate_build_encode_median_ns": candidate_med,
            "candidate_over_literal_build_encode": candidate_med / literal_med,
            "row_density_pass": row_density_pass,
            "control_pass": control_pass,
            "reader_pass": reader_pass,
            "materialized_pass": materialized_pass,
        })

    aggregate_ratio = aggregate_candidate_wire / aggregate_literal_wire
    passed = (
        all_exact and all_row_density and all_control and all_reader and
        all_materialized and all_nodes and aggregate_ratio <= MAX_AGG_WIRE_RATIO
    )
    return {
        "schema": "cmpct-one-g02-damaged-relation-law-expression-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "frozen_sizes": list(SIZES),
        "frozen_cases": list(CASES),
        "frozen_rounds": ROUNDS,
        "frozen_max_aggregate_wire_ratio": MAX_AGG_WIRE_RATIO,
        "frozen_max_control_debt_share": MAX_CONTROL_DEBT_SHARE,
        "frozen_max_reader_work_ratio": MAX_READER_WORK_RATIO,
        "frozen_max_materialized_ratio": MAX_MATERIALIZED_RATIO,
        "aggregate_literal_wire_bytes": aggregate_literal_wire,
        "aggregate_candidate_wire_bytes": aggregate_candidate_wire,
        "aggregate_candidate_over_literal_wire": aggregate_ratio,
        "decision": "advance_damaged_relation_law_expression" if passed else "hold_damaged_relation_law_expression",
        "claim_boundary": "generic ONE representation viability only; reference-Python construction timing is diagnostic, not product-speed authority",
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_damaged_relation_law_expression" else 1)
