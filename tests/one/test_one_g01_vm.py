from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate
from tests.one.oracle_g01 import evaluate as oracle_evaluate


# Hand-derived oracle bytes/hashes. These constants do not use the ONE evaluator to
# decide what the evaluator should produce.
FINAL = b"abc\x00\x00\x00\x00bdf"
FINAL_SHA256 = "3cd4e5daba35303ae4b0ae5a55318d8ea0946a4da129fded2c931564f7645be4"
ORACLE_SPEC = (
    ("surprise", b"abc"),
    ("repeat", (0, 0, None), 3),
    ("fill", 0, 4),
    ("surprise", b"ABC"),
    ("xor", ((0, 0, None), (3, 0, None)), b""),
    ("add8", ((0, 0, None),), b"\x01\x02\x03"),
    ("concat", ((1, 3, 3), (2, 0, None), (5, 0, None)), b""),
)


def root(ref: Ref, value: bytes) -> Root:
    return Root(ref=ref, length=len(value), sha256=sha256(value).hexdigest())


def conformance_program() -> Program:
    nodes = (
        Node("surprise", surprise=b"abc", declared_length=3),
        Node("repeat", refs=(Ref(0),), count=3, declared_length=9),
        Node("fill", value=0, count=4, declared_length=4),
        Node("surprise", surprise=b"ABC", declared_length=3),
        Node("xor", refs=(Ref(0), Ref(3)), declared_length=3),
        Node("add8", refs=(Ref(0),), surprise=b"\x01\x02\x03", declared_length=3),
        Node(
            "concat",
            refs=(Ref(1, 3, 3), Ref(2), Ref(5)),
            declared_length=len(FINAL),
        ),
    )
    return Program(
        nodes=nodes,
        roots={
            "literal": root(Ref(0), b"abc"),
            "repetition": root(Ref(1), b"abcabcabc"),
            "sparse": root(Ref(2), b"\x00" * 4),
            "xor": root(Ref(4), b"   "),
            "multi_parent": Root(Ref(6), len(FINAL), FINAL_SHA256),
        },
        limits=Limits(max_nodes=16, max_output_bytes=256, max_work_bytes=2048, max_depth=16),
    )


def test_independent_conformance_vector_covers_one_grammar() -> None:
    oracle = oracle_evaluate(ORACLE_SPEC)
    assert oracle == (
        b"abc",
        b"abcabcabc",
        b"\x00" * 4,
        b"ABC",
        b"   ",
        b"bdf",
        FINAL,
    )
    outputs, stats = evaluate(conformance_program())
    assert outputs == {
        "literal": oracle[0],
        "repetition": oracle[1],
        "sparse": oracle[2],
        "xor": oracle[4],
        "multi_parent": oracle[6],
    }
    assert outputs["multi_parent"] == FINAL
    assert sha256(outputs["multi_parent"]).hexdigest() == FINAL_SHA256
    assert stats.nodes_evaluated == 7
    assert stats.work_bytes <= stats.preflight_worst_work_bytes <= 2048
    assert stats.max_depth <= 16


def test_repeat_runs_are_byte_deterministic() -> None:
    first, first_stats = evaluate(conformance_program())
    second, second_stats = evaluate(conformance_program())
    assert first == second
    assert first_stats == second_stats


def test_add8_overflow_is_defined_modulo_256() -> None:
    expected = b"\x00\x01\xff"
    p = Program(
        nodes=(
            Node("surprise", surprise=b"\xff\xff\x00"),
            Node("add8", refs=(Ref(0),), surprise=b"\x01\x02\xff", declared_length=3),
        ),
        roots={"x": root(Ref(1), expected)},
    )
    assert evaluate(p)[0]["x"] == expected


def test_cycle_fails_closed() -> None:
    p = Program(
        nodes=(Node("concat", refs=(Ref(1),)), Node("concat", refs=(Ref(0),))),
        roots={"x": Root(Ref(0), 0, sha256(b"").hexdigest())},
    )
    with pytest.raises(OneError, match="cycle"):
        evaluate(p)


@pytest.mark.parametrize(
    "program, message",
    [
        (
            Program(nodes=(Node("surprise", surprise=b"abc"),), roots={"x": Root(Ref(0, 4, 1), 1, sha256(b"x").hexdigest())}),
            "starts past",
        ),
        (
            Program(nodes=(Node("fill", value=0, count=100),), roots={"x": root(Ref(0), b"\x00" * 100)}, limits=Limits(max_output_bytes=16)),
            "fill output exceeds",
        ),
        (
            Program(nodes=(Node("surprise", surprise=b"abc"),), roots={"x": Root(Ref(0), 3, "0" * 64)}),
            "sha256 mismatch",
        ),
        (
            Program(nodes=(Node("surprise", surprise=b"abc", declared_length=4),), roots={"x": root(Ref(0), b"abc")}),
            "declared length mismatch",
        ),
    ],
)
def test_hostile_programs_fail_closed(program: Program, message: str) -> None:
    with pytest.raises(OneError, match=message):
        evaluate(program)


def test_work_budget_blocks_amplification() -> None:
    p = Program(
        nodes=(
            Node("surprise", surprise=b"abcd"),
            Node("repeat", refs=(Ref(0),), count=8),
        ),
        roots={"x": root(Ref(1), b"abcd" * 8)},
        limits=Limits(max_output_bytes=128, max_work_bytes=20),
    )
    with pytest.raises(OneError, match="work exceeds"):
        evaluate(p)


def test_unknown_reader_visible_mechanism_is_rejected() -> None:
    p = Program(
        nodes=(Node("zstd", surprise=b"not allowed"),),
        roots={"x": Root(Ref(0), 0, sha256(b"").hexdigest())},
    )
    with pytest.raises(OneError, match="unknown operation"):
        evaluate(p)