from dataclasses import replace

import pytest

from benchmarks.one.one_g02_relation_granularity_frontier import _candidate, _case, _literal
from experiments.one.fused_root_law_plan import compile_fused_root_law_plan, execute_fused_root_law_plan
from experiments.one.generic_execution_plan import compile_execution_plan
from experiments.one.ir import Node, OneError, Program, Ref, Root
from hashlib import sha256


@pytest.mark.parametrize("op", ["add8", "xor"])
@pytest.mark.parametrize("block", [512, 4096])
def test_fused_root_law_matches_existing_program(op, block):
    data, pairs = _case(op, 64 * 1024, block)
    program = _candidate(data, pairs, op, block)
    assert program is not None
    fused = compile_fused_root_law_plan(compile_execution_plan(program))
    outputs, stats = execute_fused_root_law_plan(fused)
    assert outputs["root"] == data
    assert stats.root_bytes == len(data)
    assert stats.modeled_traffic_bytes == 3 * len(data)


def test_fused_root_law_rejects_literal_root_without_concat():
    data = b"x" * 4096
    plan = compile_execution_plan(_literal(data))
    with pytest.raises(OneError):
        compile_fused_root_law_plan(plan)


def test_fused_root_law_rejects_non_uniform_relation_operand():
    a = bytes(range(64))
    b = bytes(reversed(range(64)))
    out = bytes(x ^ y for x, y in zip(a, b))
    data = a + out
    nodes = (
        Node("surprise", surprise=a, declared_length=64),
        Node("surprise", surprise=b, declared_length=64),
        Node("xor", refs=(Ref(0), Ref(1)), declared_length=64),
        Node("concat", refs=(Ref(0), Ref(2)), declared_length=128),
    )
    program = Program(nodes, {"root": Root(Ref(3), 128, sha256(data).hexdigest())}, _literal(data).limits)
    with pytest.raises(OneError):
        compile_fused_root_law_plan(compile_execution_plan(program))


def test_fused_root_law_authentication_still_fails_closed():
    data, pairs = _case("add8", 64 * 1024, 4096)
    program = _candidate(data, pairs, "add8", 4096)
    assert program is not None
    fused = compile_fused_root_law_plan(compile_execution_plan(program))
    bad = replace(fused, root_sha256="00" * 32)
    with pytest.raises(OneError):
        execute_fused_root_law_plan(bad)
