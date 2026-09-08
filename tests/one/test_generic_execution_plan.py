from hashlib import sha256

import pytest

from benchmarks.one.one_g02_generic_execution_plan import FAMILIES, SIZES, decide
from experiments.one.generic_execution_plan import compile_execution_plan, execute_plan
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate


def _program(nodes, output, root_node=None, root_ref=None, max_work=8 * 1024 * 1024):
    if root_ref is None:
        root_ref = Ref(len(nodes) - 1 if root_node is None else root_node)
    return Program(
        tuple(nodes),
        {"root": Root(root_ref, len(output), sha256(output).hexdigest())},
        Limits(max_nodes=4096, max_output_bytes=2 * 1024 * 1024, max_work_bytes=max_work, max_depth=64),
    )


def _assert_same(program):
    reference, reference_stats = evaluate(program)
    plan = compile_execution_plan(program)
    candidate, stats = execute_plan(plan)
    assert candidate == reference
    assert stats.work_bytes == reference_stats.work_bytes
    assert stats.materialized_bytes == reference_stats.materialized_bytes
    assert stats.nodes_executed == reference_stats.nodes_evaluated


def test_all_six_operations_share_one_execution_plan():
    a = b"abcd"
    b = bytes([0x10, 0x20, 0x30, 0x40])
    x = bytes(left ^ right for left, right in zip(a, b))
    added = bytes((left + right) & 0xFF for left, right in zip(a, b))
    repeated = a * 3
    output = repeated + bytes([7]) * 5 + x + added + b"!"
    nodes = [
        Node("surprise", surprise=a),
        Node("surprise", surprise=b),
        Node("repeat", refs=(Ref(0),), count=3),
        Node("fill", count=5, value=7),
        Node("xor", refs=(Ref(0), Ref(1))),
        Node("add8", refs=(Ref(0), Ref(1))),
        Node("concat", refs=(Ref(2), Ref(3), Ref(4), Ref(5)), surprise=b"!", declared_length=len(output)),
    ]
    _assert_same(_program(nodes, output))


def test_sliced_reuse_and_multi_parent_concatenation():
    left = b"0123456789"
    right = b"abcdefghij"
    output = left[2:7] + right[1:5] + left[7:]
    nodes = [Node("surprise", surprise=left), Node("surprise", surprise=right), Node("concat", refs=(Ref(0, 2, 5), Ref(1, 1, 4), Ref(0, 7, 3)), declared_length=len(output))]
    _assert_same(_program(nodes, output))


def test_forward_reference_is_topologically_lowered():
    output = b"xyxy"
    nodes = [Node("repeat", refs=(Ref(1),), count=2, declared_length=4), Node("surprise", surprise=b"xy")]
    _assert_same(_program(nodes, output, root_node=0))


def test_root_slice_is_preserved():
    source = b"prefix--wanted--suffix"
    output = b"wanted"
    _assert_same(_program([Node("surprise", surprise=source)], output, root_ref=Ref(0, 8, 6)))


def test_bad_root_hash_fails_closed():
    program = Program((Node("surprise", surprise=b"abc"),), {"root": Root(Ref(0), 3, "00" * 32)}, Limits(max_output_bytes=1024, max_work_bytes=4096))
    with pytest.raises(OneError, match="sha256 mismatch"):
        execute_plan(compile_execution_plan(program))


def test_cycle_is_rejected_during_compilation():
    program = Program((Node("concat", refs=(Ref(1),)), Node("concat", refs=(Ref(0),))), {"root": Root(Ref(0), 1, sha256(b"x").hexdigest())}, Limits(max_output_bytes=1024, max_work_bytes=4096))
    with pytest.raises(OneError, match="cycle"):
        compile_execution_plan(program)


def test_resource_limit_is_not_bypassed_by_compilation():
    program = Program((Node("fill", count=4096, value=1),), {"root": Root(Ref(0), 4096, sha256(bytes([1]) * 4096).hexdigest())}, Limits(max_output_bytes=8192, max_work_bytes=1000))
    with pytest.raises(OneError, match="work"):
        compile_execution_plan(program)


def _green_rows():
    return [{"size": size, "family": family, "wall_ratio": 0.90, "cpu_ratio": 0.90} for size in SIZES for family in FAMILIES]


def test_decision_law_advances_only_complete_green_matrix():
    assert decide(_green_rows(), True) == "ADVANCE_GENERIC_EXECUTION_PLAN"


def test_decision_law_missing_or_duplicate_cell_invalidates():
    rows = _green_rows()
    assert decide(rows[:-1], True) == "INVALIDATE_GENERIC_EXECUTION_PLAN"
    duplicate = rows[:-1] + [dict(rows[0])]
    assert decide(duplicate, True) == "INVALIDATE_GENERIC_EXECUTION_PLAN"


def test_decision_law_semantic_failure_invalidates():
    assert decide(_green_rows(), False) == "INVALIDATE_GENERIC_EXECUTION_PLAN"


def test_decision_law_single_decisive_regression_holds():
    rows = _green_rows()
    target = next(row for row in rows if row["size"] == 1024 * 1024 and row["family"] == "xor2")
    target["wall_ratio"] = 1.051
    assert decide(rows, True) == "HOLD_GENERIC_EXECUTION_PLAN"


def test_decision_law_requires_eight_material_wins():
    rows = _green_rows()
    for row in rows:
        row["wall_ratio"] = 1.0
        row["cpu_ratio"] = 1.0
    for row in rows[:7]:
        row["wall_ratio"] = 0.94
        row["cpu_ratio"] = 0.94
    assert decide(rows, True) == "HOLD_GENERIC_EXECUTION_PLAN"
