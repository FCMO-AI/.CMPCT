from __future__ import annotations

import pytest

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.native_law_range_plan import (
    compile_validated_native_law_range_plan,
    execute_native_law_range_plan,
)
from experiments.one.range_vm import RangeEvaluator
from experiments.one.validated_program import ValidatedProgram, validate_program_snapshot


@pytest.mark.parametrize("family", ["add8", "xor", "add8_crack", "xor_crack"])
def test_validated_range_plan_matches_generic_reader(family):
    program = _case(128 * 1024, family)
    validated = validate_program_snapshot(program)
    for start, length in [(0, 4096), (65500, 211), (128 * 1024 - 4096, 4096)]:
        expected, _ = RangeEvaluator(program).reconstruct("current", start, length)
        plan = compile_validated_native_law_range_plan(validated, "current", start, length)
        assert execute_native_law_range_plan(plan) == expected


def test_validated_snapshot_isolated_from_caller_root_mapping_mutation():
    original = _case(32 * 1024, "xor")
    roots = dict(original.roots)
    caller_program = Program(original.nodes, roots, original.limits)
    validated = validate_program_snapshot(caller_program)

    # Caller-owned mapping is mutable by design; validated authority must not alias it.
    roots["current"] = Root(Ref(0), original.roots["previous"].length, "0" * 64)
    roots["injected"] = Root(Ref(0), original.roots["previous"].length, "0" * 64)

    assert "injected" not in validated.program.roots
    assert validated.program.roots["current"] == original.roots["current"]
    plan = compile_validated_native_law_range_plan(validated, "current", 123, 4096)
    expected, _ = RangeEvaluator(original).reconstruct("current", 123, 4096)
    assert execute_native_law_range_plan(plan) == expected


def test_validated_authority_is_sealed_against_program_rebinding():
    original = _case(32 * 1024, "xor")
    other = _case(32 * 1024, "add8")
    validated = validate_program_snapshot(original)
    with pytest.raises(AttributeError, match="immutable"):
        validated._program = other
    assert validated.program == validate_program_snapshot(original).program


def test_validated_authority_cannot_be_constructed_directly():
    program = _case(32 * 1024, "add8")
    with pytest.raises(TypeError, match="validate_program_snapshot"):
        ValidatedProgram(program, object(), _token=object())


def test_cycle_cannot_obtain_validated_authority():
    program = Program(
        nodes=(Node("concat", refs=(Ref(0),), declared_length=1),),
        roots={"root": Root(Ref(0), 1, "0" * 64)},
    )
    with pytest.raises(OneError, match="cycle"):
        validate_program_snapshot(program)


def test_wrong_type_cannot_use_validated_fast_path():
    with pytest.raises(TypeError, match="ValidatedProgram"):
        compile_validated_native_law_range_plan(object(), "root", 0, 1)
