from hashlib import sha256

import pytest

from benchmarks.one.one_g02_generic_execution_plan import _program
from experiments.one.generic_execution_plan import compile_execution_plan, execute_plan
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.native_plan_bulk import _bulk_equal, execute_native_bulk_plan
from experiments.one.vm import evaluate


@pytest.mark.parametrize("family", ["terminal_mix", "repeat", "slice_concat", "xor2", "add8_3", "shared_basis"])
def test_native_bulk_plan_matches_reference_across_generic_families(family):
    program = _program(family, 64 * 1024)
    reference, reference_stats = evaluate(program)
    plan = compile_execution_plan(program)
    generic, generic_stats = execute_plan(plan)
    native, native_stats = execute_native_bulk_plan(plan)
    assert native == generic == reference
    assert native_stats == generic_stats
    assert native_stats.work_bytes == reference_stats.work_bytes


def test_native_xor_handles_embedded_zero_bytes():
    left = bytes([0, 1, 0, 2, 0, 3, 0, 4])
    right = bytes([4, 0, 3, 0, 2, 0, 1, 0])
    expected = bytes(a ^ b for a, b in zip(left, right))
    assert _bulk_equal("xor", [left, right]) == expected


def test_native_add8_wraps_modulo_256():
    parts = [bytes([250, 255, 1]), bytes([10, 2, 255]), bytes([1, 1, 1])]
    assert _bulk_equal("add8", parts) == bytes([5, 2, 1])


def test_native_bulk_rejects_bad_operation_widths_and_operand_counts():
    with pytest.raises(OneError, match="unknown native bulk operation"):
        _bulk_equal("concat", [b"abc", b"abc"])
    with pytest.raises(OneError, match="operand count"):
        _bulk_equal("xor", [b"abc"])
    with pytest.raises(OneError, match="differ"):
        _bulk_equal("xor", [b"abc", b"ab"])


def test_root_authentication_still_fails_closed():
    program = Program(
        (Node("surprise", surprise=b"abc"), Node("surprise", surprise=b"xyz"), Node("xor", refs=(Ref(0), Ref(1)))),
        {"root": Root(Ref(2), 3, "00" * 32)},
        Limits(max_output_bytes=1024, max_work_bytes=8192),
    )
    with pytest.raises(OneError, match="sha256 mismatch"):
        execute_native_bulk_plan(compile_execution_plan(program))
