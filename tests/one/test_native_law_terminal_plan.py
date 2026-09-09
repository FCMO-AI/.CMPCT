from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.native_law_terminal_plan import (
    compile_native_law_terminal_plan,
    execute_native_law_terminal_plan,
)
from experiments.one.vm import evaluate


def _roots(previous: bytes, current_ref: Ref, current: bytes):
    return {
        "previous": Root(Ref(0), len(previous), sha256(previous).hexdigest()),
        "current": Root(current_ref, len(current), sha256(current).hexdigest()),
    }


@pytest.mark.parametrize("op,value", [("add8", 37), ("xor", 0xA7)])
def test_native_law_terminal_matches_reference(op, value):
    source = bytes(range(256)) * 4
    current = bytes(((b + value) & 255) if op == "add8" else (b ^ value) for b in source)
    nodes = (
        Node("surprise", surprise=source, declared_length=len(source)),
        Node("fill", count=len(source), value=value, declared_length=len(source)),
        Node(op, refs=(Ref(0), Ref(1)), declared_length=len(source)),
    )
    program = Program(nodes, _roots(source, Ref(2), current), Limits())
    expected, _ = evaluate(program)
    plan = compile_native_law_terminal_plan(program)
    actual, stats = execute_native_law_terminal_plan(plan)
    assert actual == expected == {"previous": source, "current": current}
    assert plan.command_count == 2
    assert stats.peak_temporary_bytes == len(source)


@pytest.mark.parametrize("op,value", [("add8", 11), ("xor", 0x5A)])
def test_native_law_terminal_concat_ranges(op, value):
    source = bytes((i * 29 + 7) & 255 for i in range(4096))
    transformed = bytes(((b + value) & 255) if op == "add8" else (b ^ value) for b in source)
    crack = b"ONE!"
    split = 2048
    current = transformed[:split] + crack + transformed[split + len(crack):]
    nodes = (
        Node("surprise", surprise=source, declared_length=len(source)),
        Node("fill", count=len(source), value=value, declared_length=len(source)),
        Node(op, refs=(Ref(0, 0, split), Ref(1, 0, split)), declared_length=split),
        Node("surprise", surprise=crack, declared_length=len(crack)),
        Node(
            op,
            refs=(
                Ref(0, split + len(crack), len(source) - split - len(crack)),
                Ref(1, split + len(crack), len(source) - split - len(crack)),
            ),
            declared_length=len(source) - split - len(crack),
        ),
        Node("concat", refs=(Ref(2), Ref(3), Ref(4)), declared_length=len(source)),
    )
    program = Program(nodes, _roots(source, Ref(5), current), Limits())
    expected, _ = evaluate(program)
    plan = compile_native_law_terminal_plan(program)
    actual, _ = execute_native_law_terminal_plan(plan)
    assert actual == expected
    assert plan.command_count == 4


def test_native_law_terminal_rejects_partial_root_for_incumbent_fallback():
    payload = b"abcdef"
    program = Program(
        (Node("surprise", surprise=payload, declared_length=len(payload)),),
        {"r": Root(Ref(0, 1, 3), 3, sha256(payload[1:4]).hexdigest())},
        Limits(),
    )
    expected, _ = evaluate(program)
    assert expected["r"] == b"bcd"
    with pytest.raises(OneError, match="complete root"):
        compile_native_law_terminal_plan(program)


def test_native_law_terminal_rejects_nonconstant_law_shape():
    a = bytes(range(64))
    b = bytes(reversed(range(64)))
    out = bytes(x ^ y for x, y in zip(a, b))
    program = Program(
        (
            Node("surprise", surprise=a, declared_length=len(a)),
            Node("surprise", surprise=b, declared_length=len(b)),
            Node("xor", refs=(Ref(0), Ref(1)), declared_length=len(a)),
        ),
        {"r": Root(Ref(2), len(out), sha256(out).hexdigest())},
        Limits(),
    )
    expected, _ = evaluate(program)
    assert expected["r"] == out
    with pytest.raises(OneError, match="one Surprise and one Fill"):
        compile_native_law_terminal_plan(program)
