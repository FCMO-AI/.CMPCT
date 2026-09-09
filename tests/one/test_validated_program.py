from __future__ import annotations

import pytest

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.native_law_range_plan import (
    compile_validated_native_law_range_plan,
    execute_native_law_range_plan,
)
from experiments.one.range_vm import RangeEvaluator
from experiments.one.validated_program import (
    ValidatedProgram,
    validate_program_snapshot,
    validate_program_snapshot_compact,
)


@pytest.mark.parametrize("family", ["add8", "xor", "add8_crack", "xor_crack"])
def test_validated_range_plan_matches_generic_reader(family):
    program = _case(128 * 1024, family)
    validated = validate_program_snapshot(program)
    for start, length in [(0, 4096), (65500, 211), (128 * 1024 - 4096, 4096)]:
        expected, _ = RangeEvaluator(program).reconstruct("current", start, length)
        plan = compile_validated_native_law_range_plan(validated, "current", start, length)
        assert execute_native_law_range_plan(plan) == expected


@pytest.mark.parametrize("family", ["add8", "xor", "add8_crack", "xor_crack"])
def test_validated_generic_range_baseline_matches_raw_evaluator_across_repeated_reads(family):
    program = _case(128 * 1024, family)
    validated = validate_program_snapshot(program)
    reused = RangeEvaluator.from_validated(validated)
    for start, length in [(0, 4096), (65500, 211), (128 * 1024 - 4096, 4096)]:
        expected, expected_stats = RangeEvaluator(program).reconstruct("current", start, length)
        actual, actual_stats = reused.reconstruct("current", start, length)
        assert actual == expected
        assert actual_stats == expected_stats


@pytest.mark.parametrize("family", ["add8", "xor", "add8_crack", "xor_crack"])
def test_compact_validated_generic_range_matches_ordinary_validated(family):
    program = _case(128 * 1024, family)
    ordinary = validate_program_snapshot(program)
    compact = validate_program_snapshot_compact(program)
    assert compact.uses_compact_lengths
    assert not ordinary.uses_compact_lengths
    assert compact.preflight_entry_count == ordinary.preflight_entry_count
    assert compact.preflight.max_depth == ordinary.preflight.max_depth
    assert compact.preflight.worst_work_bytes == ordinary.preflight.worst_work_bytes
    assert tuple(compact.preflight.lengths) == tuple(ordinary.preflight.lengths)

    compact_reader = RangeEvaluator.from_validated(compact)
    ordinary_reader = RangeEvaluator.from_validated(ordinary)
    for start, length in [(0, 4096), (65500, 211), (128 * 1024 - 4096, 4096)]:
        expected, expected_stats = ordinary_reader.reconstruct("current", start, length)
        actual, actual_stats = compact_reader.reconstruct("current", start, length)
        assert actual == expected
        assert actual_stats == expected_stats


def test_compact_validation_certificate_reduces_retained_python_preflight_state():
    program = _case(128 * 1024, "xor_crack")
    ordinary = validate_program_snapshot(program)
    compact = validate_program_snapshot_compact(program)
    assert compact.python_preflight_bytes < ordinary.python_preflight_bytes
    assert compact.modeled_preflight_bytes == ordinary.modeled_preflight_bytes


def test_compact_lengths_are_immutable_by_construction():
    compact = validate_program_snapshot_compact(_case(32 * 1024, "xor"))
    lengths = compact.preflight.lengths
    with pytest.raises(TypeError):
        lengths[0] = 1
    assert lengths[0] >= 0


def test_compact_validation_falls_back_without_narrowing_wide_logical_domain():
    huge = 1 << 64
    program = Program(
        nodes=(Node("fill", count=huge, value=7, declared_length=huge),),
        roots={"root": Root(Ref(0), huge, "0" * 64)},
        limits=Limits(
            max_nodes=1,
            max_output_bytes=huge,
            max_work_bytes=3 * huge,
            max_depth=1,
        ),
    )
    ordinary = validate_program_snapshot(program)
    compact = validate_program_snapshot_compact(program)
    assert not compact.uses_compact_lengths
    assert compact.preflight == ordinary.preflight


def test_validated_generic_range_baseline_rejects_raw_program():
    program = _case(32 * 1024, "xor")
    with pytest.raises(TypeError, match="ValidatedProgram"):
        RangeEvaluator.from_validated(program)


def test_validated_snapshot_isolated_from_caller_root_mapping_mutation():
    original = _case(32 * 1024, "xor")
    roots = dict(original.roots)
    caller_program = Program(original.nodes, roots, original.limits)
    validated = validate_program_snapshot(caller_program)

    roots["current"] = Root(Ref(0), original.roots["previous"].length, "0" * 64)
    roots["injected"] = Root(Ref(0), original.roots["previous"].length, "0" * 64)

    assert "injected" not in validated.program.roots
    assert validated.program.roots["current"] == original.roots["current"]
    plan = compile_validated_native_law_range_plan(validated, "current", 123, 4096)
    expected, _ = RangeEvaluator(original).reconstruct("current", 123, 4096)
    assert execute_native_law_range_plan(plan) == expected


@pytest.mark.parametrize("builder", [validate_program_snapshot, validate_program_snapshot_compact])
def test_validated_authority_is_sealed_against_program_rebinding(builder):
    original = _case(32 * 1024, "xor")
    other = _case(32 * 1024, "add8")
    validated = builder(original)
    with pytest.raises(AttributeError, match="immutable"):
        validated._program = other
    assert validated.program == builder(original).program


def test_validated_authority_cannot_be_constructed_directly():
    program = _case(32 * 1024, "add8")
    with pytest.raises(TypeError, match="validate_program_snapshot"):
        ValidatedProgram(program, object(), _token=object())


@pytest.mark.parametrize("builder", [validate_program_snapshot, validate_program_snapshot_compact])
def test_cycle_cannot_obtain_validated_authority(builder):
    program = Program(
        nodes=(Node("concat", refs=(Ref(0),), declared_length=1),),
        roots={"root": Root(Ref(0), 1, "0" * 64)},
    )
    with pytest.raises(OneError, match="cycle"):
        builder(program)


def test_wrong_type_cannot_use_validated_fast_path():
    with pytest.raises(TypeError, match="ValidatedProgram"):
        compile_validated_native_law_range_plan(object(), "root", 0, 1)