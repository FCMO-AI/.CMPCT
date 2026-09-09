from __future__ import annotations

import ctypes

import pytest

from benchmarks.one.one_g02_native_law_terminal_reader import FAMILIES, _case
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.native_law_range_plan import (
    compile_native_law_range_plan,
    execute_native_law_range_plan,
)
from experiments.one.range_vm import RangeEvaluator


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("n", [32 * 1024, 128 * 1024])
def test_native_range_matches_generic_range(family, n):
    program = _case(n, family)
    probes = [
        (0, 1),
        (17, 257),
        (n // 2 - 31, 127),
        (n - 4096, 4096),
    ]
    for start, length in probes:
        expected, _ = RangeEvaluator(program).reconstruct("current", start, length)
        plan = compile_native_law_range_plan(program, "current", start, length)
        got = execute_native_law_range_plan(plan)
        assert got == expected
        assert plan.length == length
        assert plan.packed_source_bytes <= length
        assert plan.source_plan_write_bytes == plan.packed_source_bytes
        assert plan.sink_write_bytes == length


def test_native_source_buffer_views_single_plan_backing_allocation():
    program = _case(32 * 1024, "xor")
    plan = compile_native_law_range_plan(program, "current", 4096, 4096)
    assert isinstance(plan.source_blob, bytearray)
    assert plan.source_buffer is not None
    second_view = (ctypes.c_uint8 * len(plan.source_blob)).from_buffer(plan.source_blob)
    assert ctypes.addressof(plan.source_buffer) == ctypes.addressof(second_view)


def test_native_range_crosses_sparse_crack_boundaries():
    n = 128 * 1024
    program = _case(n, "xor_crack")
    crack_at = n // 2
    start = crack_at - 23
    length = 101
    expected, _ = RangeEvaluator(program).reconstruct("current", start, length)
    plan = compile_native_law_range_plan(program, "current", start, length)
    assert plan.command_count == 3
    assert execute_native_law_range_plan(plan) == expected


def test_repeat_lowers_through_existing_terminal_schedule():
    data = b"abcd"
    program = Program(
        nodes=(
            Node("surprise", surprise=data, declared_length=4),
            Node("repeat", refs=(Ref(0),), count=8, declared_length=32),
        ),
        roots={"root": Root(Ref(1), 32, "0" * 64)},
    )
    start, length = 3, 11
    expected = (data * 8)[start : start + length]
    plan = compile_native_law_range_plan(program, "root", start, length)
    assert execute_native_law_range_plan(plan) == expected
    assert plan.command_count == 4
    assert plan.packed_source_bytes == length


def test_concat_surprise_tail_is_explicitly_unsupported():
    program = Program(
        nodes=(
            Node("surprise", surprise=b"abcd", declared_length=4),
            Node("concat", refs=(Ref(0),), surprise=b"ef", declared_length=6),
        ),
        roots={"root": Root(Ref(1), 6, "0" * 64)},
    )
    with pytest.raises(OneError, match="Surprise tail"):
        compile_native_law_range_plan(program, "root", 3, 3)
