from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.observe import RunOpportunity
from experiments.one.run_fill_law import program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _roundtrip(program: Program) -> Program:
    wire, _ = encode_program(program)
    return decode_program(wire)


def test_fused_reader_matches_reference_for_run_fill_graph():
    source = b"source" * 128
    target = b"head" + b"A" * 80 + b"middle" + b"B" * 96 + b"tail"
    runs = (
        RunOpportunity(start=4, length=80, value=ord("A")),
        RunOpportunity(start=90, length=96, value=ord("B")),
    )
    program, _ = program_from_observed_runs(source, target, runs)
    decoded = _roundtrip(program)
    reference, _ = evaluate(decoded)
    fused, stats = evaluate_terminal_roots_fused(decoded)
    assert fused == reference == {"previous": source, "current": target}
    assert stats.roots_reconstructed == 2
    assert stats.root_sink_write_bytes == len(source) + len(target)
    assert stats.root_hash_read_bytes == len(source) + len(target)


def test_fused_reader_matches_literal_pair_and_accounts_stored_reads():
    source = b"a" * 4096
    target = b"b" * 8192
    program, _ = program_from_observed_runs(source, target, ())
    decoded = _roundtrip(program)
    reference, _ = evaluate(decoded)
    fused, stats = evaluate_terminal_roots_fused(decoded)
    assert fused == reference
    assert stats.stored_surprise_read_bytes == len(source) + len(target)
    assert stats.root_sink_write_bytes == len(source) + len(target)


def test_full_fill_avoids_stored_current_payload_read():
    source = b"previous" * 128
    target = bytes([17]) * 4096
    program, _ = program_from_observed_runs(source, target, (RunOpportunity(0, len(target), 17),))
    decoded = _roundtrip(program)
    fused, stats = evaluate_terminal_roots_fused(decoded)
    assert fused["current"] == target
    assert stats.stored_surprise_read_bytes == len(source)


def test_fused_reader_rejects_nonterminal_concat_child():
    payload = b"abcd"
    digest = sha256(payload * 2).hexdigest()
    program = Program(
        (
            Node("surprise", surprise=payload),
            Node("repeat", refs=(Ref(0),), count=2, declared_length=8),
            Node("concat", refs=(Ref(1),), declared_length=8),
        ),
        {"current": Root(Ref(2), 8, digest)},
    )
    with pytest.raises(OneError, match="non-terminal"):
        evaluate_terminal_roots_fused(program)


def test_fused_reader_rejects_tampered_root_commitment():
    source = b"source"
    target = b"Z" * 256
    program, _ = program_from_observed_runs(source, target, (RunOpportunity(0, 256, ord("Z")),))
    bad_roots = dict(program.roots)
    bad_roots["current"] = Root(program.roots["current"].ref, len(target), "00" * 32)
    with pytest.raises(OneError, match="sha256 mismatch"):
        evaluate_terminal_roots_fused(Program(program.nodes, bad_roots, program.limits))
