from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Node, OneError
from experiments.one.observe import RunOpportunity
from experiments.one.run_fill_law import MIN_FILL_RUN, program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _roundtrip(source: bytes, target: bytes, runs: tuple[RunOpportunity, ...]):
    program, stats = program_from_observed_runs(source, target, runs)
    program.validate_shape()
    wire, wire_stats = encode_program(program)
    outputs, vm_stats = evaluate(decode_program(wire))
    assert outputs == {"previous": source, "current": target}
    assert program.roots["previous"].sha256 == sha256(source).hexdigest()
    assert program.roots["current"].sha256 == sha256(target).hexdigest()
    return program, stats, wire, wire_stats, vm_stats


def test_long_constant_run_compiles_to_existing_fill_relation():
    source = bytes(range(64)) * 16
    target = b"prefix" + bytes([0xA5]) * 512 + b"suffix"
    run = RunOpportunity(start=6, length=512, value=0xA5)
    program, stats, _wire, wire_stats, _vm = _roundtrip(source, target, (run,))
    assert stats.qualifying_runs == 1
    assert stats.fill_bytes == 512
    assert stats.surprise_bytes_current == len(b"prefixsuffix")
    assert {node.op for node in program.nodes} <= {"surprise", "fill", "concat"}
    assert any(node.op == "fill" and node.count == 512 and node.value == 0xA5 for node in program.nodes)
    # Both roots are stored in the pair; nevertheless replacing 512 explicit current
    # bytes with generic Law must reduce Surprise by exactly that amount.
    assert wire_stats.surprise_bytes == len(source) + len(target) - 512


def test_subeconomic_run_stays_literal_without_new_mode():
    source = b"s" * 256
    target = b"a" * (MIN_FILL_RUN - 1) + b"tail"
    run = RunOpportunity(start=0, length=MIN_FILL_RUN - 1, value=ord("a"))
    program, stats, _wire, wire_stats, _vm = _roundtrip(source, target, (run,))
    assert stats.qualifying_runs == 0
    assert len(program.nodes) == 2
    assert all(node.op == "surprise" for node in program.nodes)
    assert wire_stats.surprise_bytes == len(source) + len(target)


def test_single_full_root_run_needs_no_concat():
    source = b"source" * 32
    target = bytes([17]) * 4096
    run = RunOpportunity(0, len(target), 17)
    program, stats, _wire, _wire_stats, _vm = _roundtrip(source, target, (run,))
    assert stats.concat_refs == 0
    assert program.nodes[program.roots["current"].ref.node].op == "fill"


def test_rejects_non_exact_or_overlapping_observation_evidence():
    source = b"x" * 128
    target = b"a" * 128
    with pytest.raises(ValueError):
        program_from_observed_runs(source, target, (RunOpportunity(0, 64, ord("b")),))
    with pytest.raises(ValueError):
        program_from_observed_runs(
            source,
            target,
            (RunOpportunity(0, 64, ord("a")), RunOpportunity(32, 64, ord("a"))),
        )


def test_compiler_never_accepts_foreign_reader_operation():
    source = b"q" * 64
    target = b"r" * 512
    program, _stats = program_from_observed_runs(source, target, (RunOpportunity(0, 512, ord("r")),))
    assert all(node.op in {"surprise", "fill", "concat"} for node in program.nodes)
