from dataclasses import replace

import pytest

from benchmarks.one.one_g02_relation_granularity_frontier import _candidate, _case
from benchmarks.one.one_g02_relation_root_fusion import decide
from experiments.one.ir import Node, OneError, Program
from experiments.one.relation_root_fusion import evaluate_relation_roots_fused
from experiments.one.vm import evaluate


@pytest.mark.parametrize("op", ["add8", "xor"])
@pytest.mark.parametrize("block", [512, 4096])
def test_relation_root_fusion_matches_reference(op: str, block: int) -> None:
    data, pairs = _case(op, 64 * 1024, block)
    program = _candidate(data, pairs, op, block)
    assert program is not None
    fused, stats = evaluate_relation_roots_fused(program)
    reference, _ = evaluate(program)
    assert fused == reference == {"root": data}
    assert stats.fused_relations == len(pairs)
    assert stats.materialized_bytes == len(data)


def test_relation_root_fusion_fails_closed_on_unsupported_root() -> None:
    data, pairs = _case("xor", 64 * 1024, 4096)
    program = _candidate(data, pairs, "xor", 4096)
    assert program is not None
    root_id = program.roots["root"].ref.node
    nodes = list(program.nodes)
    nodes[root_id] = replace(nodes[root_id], op="repeat", refs=(nodes[root_id].refs[0],), count=1)
    bad = Program(tuple(nodes), program.roots, program.limits)
    with pytest.raises(OneError):
        evaluate_relation_roots_fused(bad)


def test_unreachable_invalid_node_is_not_hidden_by_fusion() -> None:
    data, pairs = _case("add8", 64 * 1024, 4096)
    program = _candidate(data, pairs, "add8", 4096)
    assert program is not None
    # Append an invalid stored node. Reference preflight must reject it even though roots do
    # not reach it; fusion may not turn dead stored bytes into an integrity bypass.
    bad_node = Node("fill", count=-1, value=7, declared_length=-1)
    bad = Program(program.nodes + (bad_node,), program.roots, program.limits)
    with pytest.raises(OneError):
        evaluate_relation_roots_fused(bad)


def _row(size: int, block: int, op: str, **kw) -> dict:
    row = {
        "size": size,
        "block": block,
        "op": op,
        "semantic_ok": True,
        "root_ok": True,
        "wire_changed": False,
        "fused_work_ratio_vs_literal": 1.5,
        "fused_materialized_ratio_vs_literal": 1.1,
        "fused_wall_ratio_vs_literal": 1.5,
        "fused_cpu_ratio_vs_literal": 1.5,
        "fused_wall_ratio_vs_native": 0.5,
        "fused_cpu_ratio_vs_native": 0.5,
    }
    row.update(kw)
    return row


def _matrix() -> list[dict]:
    return [_row(size, block, op) for size in (64*1024, 256*1024, 1024*1024) for block in (512,1024,2048,4096) for op in ("add8","xor")]


def test_decision_law_requires_exact_matrix_and_hard_gates() -> None:
    rows = _matrix()
    assert decide(rows) == "ADVANCE_RELATION_ROOT_FUSION"
    assert decide(rows[:-1]) == "INVALIDATE_RELATION_ROOT_FUSION"
    dup = rows[:-1] + [rows[0]]
    assert decide(dup) == "INVALIDATE_RELATION_ROOT_FUSION"
    semantic = [dict(row) for row in rows]
    semantic[-1]["semantic_ok"] = False
    assert decide(semantic) == "INVALIDATE_RELATION_ROOT_FUSION"
    slow = [dict(row) for row in rows]
    slow[-1]["fused_wall_ratio_vs_literal"] = 1.500001
    assert decide(slow) == "HOLD_RELATION_ROOT_FUSION"
    weak = [dict(row) for row in rows]
    weak[-1]["fused_wall_ratio_vs_native"] = 0.500001
    assert decide(weak) == "HOLD_RELATION_ROOT_FUSION"
