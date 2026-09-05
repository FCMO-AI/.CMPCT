from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.bulk_wire import encode_program_bulk
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _root(node: int, data: bytes) -> Root:
    return Root(Ref(node), len(data), sha256(data).hexdigest())


def test_bulk_emitter_matches_canonical_all_ops_and_root_order() -> None:
    nodes = (
        Node("surprise", surprise=b"ab"),
        Node("surprise", surprise=b"\x01\x02"),
        Node("fill", value=0x5A, count=3, declared_length=3),
        Node("repeat", refs=(Ref(0),), count=2, declared_length=4),
        Node("concat", refs=(Ref(0), Ref(2)), surprise=b"!", declared_length=6),
        Node("xor", refs=(Ref(1), Ref(1)), declared_length=2),
        Node("add8", refs=(Ref(1), Ref(1)), declared_length=2),
    )
    expected = {
        "add": b"\x02\x04",
        "concat": b"abZZZ!",
        "fill": b"ZZZ",
        "repeat": b"abab",
        "surprise": b"ab",
        "xor": b"\x00\x00",
    }
    # Deliberately insert roots out of canonical lexical order. Both encoders must
    # sort identically rather than inheriting mapping insertion order.
    roots = {
        "xor": _root(5, expected["xor"]),
        "surprise": _root(0, expected["surprise"]),
        "repeat": _root(3, expected["repeat"]),
        "fill": _root(2, expected["fill"]),
        "concat": _root(4, expected["concat"]),
        "add": _root(6, expected["add"]),
    }
    program = Program(nodes=nodes, roots=roots, limits=Limits())

    baseline, baseline_stats = encode_program(program)
    candidate, candidate_stats = encode_program_bulk(program)

    assert candidate == baseline
    assert candidate_stats == baseline_stats
    decoded = decode_program(candidate)
    outputs, _stats = evaluate(decoded)
    assert outputs == expected


@pytest.mark.parametrize("count", [0, 1, 127, 128, 16383, 16384, 1 << 20])
def test_bulk_emitter_matches_varint_boundaries(count: int) -> None:
    data = bytes([0xA5]) * count
    program = Program(
        nodes=(Node("fill", value=0xA5, count=count, declared_length=count),),
        roots={"r": _root(0, data)},
        limits=Limits(max_output_bytes=max(1, count), max_work_bytes=max(1, count * 2)),
    )
    baseline, baseline_stats = encode_program(program)
    candidate, candidate_stats = encode_program_bulk(program)
    assert candidate == baseline
    assert candidate_stats == baseline_stats


def test_bulk_emitter_preserves_validation_boundary() -> None:
    invalid = Program(
        nodes=(Node("not-an-op"),),
        roots={"r": Root(Ref(0), 0, sha256(b"").hexdigest())},
    )
    with pytest.raises(OneError):
        encode_program(invalid)
    with pytest.raises(OneError):
        encode_program_bulk(invalid)
