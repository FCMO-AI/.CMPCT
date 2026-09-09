from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.native_law_range_plan import (
    compile_validated_native_law_range_plan,
    execute_native_law_range_plan,
)
from experiments.one.validated_program import validate_program_snapshot_compact


def _repeat_program(basis_bytes: int, root_bytes: int) -> tuple[Program, bytes]:
    assert root_bytes % basis_bytes == 0
    basis = bytes((index * 73 + 19) & 255 for index in range(basis_bytes))
    full = basis * (root_bytes // basis_bytes)
    nodes = (
        Node("surprise", surprise=basis, declared_length=basis_bytes),
        Node("repeat", refs=(Ref(0),), count=root_bytes // basis_bytes, declared_length=root_bytes),
    )
    root = Root(Ref(1), root_bytes, sha256(full).hexdigest())
    limits = Limits(max_output_bytes=root_bytes * 2, max_work_bytes=root_bytes * 8)
    return Program(nodes, {"current": root}, limits), full


def test_native_repeat_range_plan_handles_period_boundaries() -> None:
    program, full = _repeat_program(64, 128 * 1024)
    validated = validate_program_snapshot_compact(program)
    for start, length in ((0, 64), (63, 4096), (64 * 137 + 17, 8192), (len(full) - 257, 257)):
        plan = compile_validated_native_law_range_plan(validated, "current", start, length)
        value = execute_native_law_range_plan(plan)
        assert value == full[start : start + length]
        assert plan.bulk_periodic
        assert plan.packed_source_bytes == 0
        assert plan.source_read_bytes == length
        assert plan.source_plan_write_bytes == 0
        assert plan.sink_write_bytes == length
        assert plan.command_count == 1


def test_authenticated_native_repeat_range_matches_reference() -> None:
    program, full = _repeat_program(256, 128 * 1024)
    validated = validate_program_snapshot_compact(program)
    tree = build_auth_tree(full, 4096)
    for start, length in ((0, 64), (255, 4096), (65536 - 1000, 8192), (len(full) - 257, 257)):
        value, stats = reconstruct_validated_authenticated_native_range(
            validated, "current", tree, tree.root, start, length
        )
        assert value == full[start : start + length]
        assert stats.cone_bytes in {4096, 8192, 12288}
        assert stats.packed_source_bytes == 0
        assert stats.source_plan_write_bytes == 0
        assert stats.plan_commands == 1


def test_repeat_selective_plan_is_root_size_independent_for_fixed_cone() -> None:
    observed = []
    for root_bytes in (32 * 1024, 128 * 1024, 512 * 1024):
        program, full = _repeat_program(64, root_bytes)
        validated = validate_program_snapshot_compact(program)
        tree = build_auth_tree(full, 4096)
        _value, stats = reconstruct_validated_authenticated_native_range(
            validated, "current", tree, tree.root, 0, 4096
        )
        observed.append(
            (
                stats.cone_bytes,
                stats.packed_source_bytes,
                stats.source_read_bytes,
                stats.source_plan_write_bytes,
                stats.sink_write_bytes,
                stats.plan_commands,
            )
        )
    assert observed[0] == observed[1] == observed[2]
    assert observed[0] == (4096, 0, 4096, 0, 4096, 1)


def test_bulk_repeat_honors_sliced_root_phase() -> None:
    basis = bytes((i * 29 + 7) & 255 for i in range(64))
    full = basis * 256
    sliced = full[17 : 17 + 4096]
    program = Program(
        nodes=(
            Node("surprise", surprise=basis, declared_length=len(basis)),
            Node("repeat", refs=(Ref(0),), count=256, declared_length=len(full)),
        ),
        roots={"current": Root(Ref(1, 17, 4096), 4096, sha256(sliced).hexdigest())},
        limits=Limits(max_output_bytes=8192, max_work_bytes=32768),
    )
    validated = validate_program_snapshot_compact(program)
    for start, length in ((0, 64), (13, 257), (1000, 2048)):
        plan = compile_validated_native_law_range_plan(validated, "current", start, length)
        assert plan.bulk_periodic
        assert execute_native_law_range_plan(plan) == sliced[start : start + length]


def test_repeat_count_one_and_zero_count_semantics() -> None:
    basis = b"periodic-law"
    one = Program(
        nodes=(
            Node("surprise", surprise=basis, declared_length=len(basis)),
            Node("repeat", refs=(Ref(0),), count=1, declared_length=len(basis)),
        ),
        roots={"current": Root(Ref(1), len(basis), sha256(basis).hexdigest())},
        limits=Limits(max_output_bytes=1024, max_work_bytes=4096),
    )
    one_validated = validate_program_snapshot_compact(one)
    one_plan = compile_validated_native_law_range_plan(one_validated, "current", 0, len(basis))
    assert one_plan.bulk_periodic
    assert execute_native_law_range_plan(one_plan) == basis

    zero = Program(
        nodes=(
            Node("surprise", surprise=basis, declared_length=len(basis)),
            Node("repeat", refs=(Ref(0),), count=0, declared_length=0),
        ),
        roots={"current": Root(Ref(1), 0, sha256(b"").hexdigest())},
        limits=Limits(max_output_bytes=1024, max_work_bytes=4096),
    )
    zero_validated = validate_program_snapshot_compact(zero)
    zero_plan = compile_validated_native_law_range_plan(zero_validated, "current", 0, 0)
    assert execute_native_law_range_plan(zero_plan) == b""
    with pytest.raises(OneError, match="requested range exceeds root"):
        compile_validated_native_law_range_plan(zero_validated, "current", 0, 1)


def test_empty_repeat_source_allows_only_empty_output() -> None:
    program = Program(
        nodes=(
            Node("surprise", surprise=b"", declared_length=0),
            Node("repeat", refs=(Ref(0),), count=8, declared_length=0),
        ),
        roots={"current": Root(Ref(1), 0, sha256(b"").hexdigest())},
        limits=Limits(max_output_bytes=1024, max_work_bytes=4096),
    )
    validated = validate_program_snapshot_compact(program)
    plan = compile_validated_native_law_range_plan(validated, "current", 0, 0)
    assert execute_native_law_range_plan(plan) == b""
