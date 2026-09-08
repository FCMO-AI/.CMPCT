from __future__ import annotations

from hashlib import sha256

import pytest

from benchmarks.one.one_g02_native_terminal_fill_batch import SIZES, adjudicate
from benchmarks.one.one_g02_compact_observer_handoff_writer import FAMILIES
from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.native_terminal_fill import _apply_fill_schedule, evaluate_terminal_roots_bulk_fill
from experiments.one.observe import RunOpportunity
from experiments.one.run_fill_law import program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _roundtrip(program: Program) -> Program:
    wire, _ = encode_program(program)
    return decode_program(wire)


def test_bulk_fill_matches_reference_and_scalar_fused_reader():
    source = b"source" * 128
    target = b"head" + b"A" * 80 + b"middle" + b"B" * 96 + b"tail"
    runs = (RunOpportunity(4, 80, ord("A")), RunOpportunity(90, 96, ord("B")))
    program, _ = program_from_observed_runs(source, target, runs)
    decoded = _roundtrip(program)
    reference, _ = evaluate(decoded)
    scalar, scalar_stats = evaluate_terminal_roots_fused(decoded)
    bulk, bulk_stats = evaluate_terminal_roots_bulk_fill(decoded)
    assert bulk == scalar == reference == {"previous": source, "current": target}
    assert bulk_stats.modeled_memory_traffic_bytes == scalar_stats.modeled_memory_traffic_bytes
    assert bulk_stats.peak_temporary_bytes == scalar_stats.peak_temporary_bytes


def test_bulk_full_fill_avoids_stored_payload_read():
    source = b"previous" * 128
    target = bytes([17]) * 4096
    program, _ = program_from_observed_runs(source, target, (RunOpportunity(0, len(target), 17),))
    decoded = _roundtrip(program)
    bulk, stats = evaluate_terminal_roots_bulk_fill(decoded)
    assert bulk["current"] == target
    assert stats.stored_surprise_read_bytes == len(source)


def test_native_schedule_rejects_out_of_bounds_command():
    sink = bytearray(16)
    with pytest.raises(OneError, match="status 2"):
        _apply_fill_schedule(sink, [(12, 8, 1)])


def test_bulk_reader_rejects_tampered_root():
    source = b"source"
    target = b"Z" * 256
    program, _ = program_from_observed_runs(source, target, (RunOpportunity(0, 256, ord("Z")),))
    roots = dict(program.roots)
    roots["current"] = Root(program.roots["current"].ref, len(target), "00" * 32)
    with pytest.raises(OneError, match="sha256 mismatch"):
        evaluate_terminal_roots_bulk_fill(Program(program.nodes, roots, program.limits))


def test_bulk_reader_fails_closed_on_nonterminal_child():
    payload = b"abcd"
    program = Program(
        (Node("surprise", surprise=payload), Node("repeat", refs=(Ref(0),), count=2, declared_length=8), Node("concat", refs=(Ref(1),), declared_length=8)),
        {"current": Root(Ref(2), 8, sha256(payload * 2).hexdigest())},
    )
    with pytest.raises(OneError, match="non-terminal"):
        evaluate_terminal_roots_bulk_fill(program)


def _green_rows() -> list[dict]:
    rows=[]
    for size in SIZES:
        for family in FAMILIES:
            rows.append({
                "bytes": size,
                "family": family,
                "semantic_ok": True,
                "bulk_over_control_wall": 1.0,
                "bulk_over_control_cpu": 1.0,
                "bulk_over_scalar_wall": 0.60 if family == "long_runs" else 1.0,
                "bulk_over_scalar_cpu": 0.60 if family == "long_runs" else 1.0,
                "bulk_over_control_traffic": 0.90 if family == "long_runs" else 1.0,
                "bulk_over_control_peak_temporary": 1.0,
                "candidate_over_control_wire": 0.50 if family == "long_runs" else (0.875 if family == "structured" else 1.0),
            })
    return rows


def test_batch_adjudicator_requires_complete_green_matrix():
    assert adjudicate(_green_rows()) == "ADVANCE_NATIVE_TERMINAL_FILL_BATCH"
    assert adjudicate(_green_rows()[:-1]) == "INVALIDATE_NATIVE_TERMINAL_FILL_BATCH"


def test_batch_adjudicator_holds_regression_or_weak_causal_win():
    rows=_green_rows(); rows[0]["bulk_over_control_wall"] = 1.051
    assert adjudicate(rows) == "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    rows=_green_rows(); next(r for r in rows if r["family"] == "long_runs")["bulk_over_scalar_cpu"] = 0.751
    assert adjudicate(rows) == "HOLD_NATIVE_TERMINAL_FILL_BATCH"


def test_batch_adjudicator_invalidates_semantic_failure_or_duplicate_cell():
    rows=_green_rows(); rows[0]["semantic_ok"] = False
    assert adjudicate(rows) == "INVALIDATE_NATIVE_TERMINAL_FILL_BATCH"
    rows=_green_rows(); rows[-1] = dict(rows[-2])
    assert adjudicate(rows) == "INVALIDATE_NATIVE_TERMINAL_FILL_BATCH"
