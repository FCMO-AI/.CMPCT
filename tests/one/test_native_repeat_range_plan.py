from __future__ import annotations

from hashlib import sha256

from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.ir import Limits, Node, Program, Ref, Root
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
        assert plan.packed_source_bytes == length
        assert plan.source_read_bytes == length
        assert plan.source_plan_write_bytes == length
        assert plan.sink_write_bytes == length


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
        assert stats.packed_source_bytes == stats.cone_bytes


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
            )
        )
    assert observed[0] == observed[1] == observed[2]
