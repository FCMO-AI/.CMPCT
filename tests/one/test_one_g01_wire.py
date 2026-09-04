from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import MAGIC, decode_program, encode_program


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref, len(value), sha256(value).hexdigest())


def _program() -> Program:
    final = b"prefix:" + b"abc" * 3 + b"\x00" * 8
    nodes = (
        Node("surprise", surprise=b"abc", declared_length=3),
        Node("repeat", refs=(Ref(0),), count=3, declared_length=9),
        Node("fill", value=0, count=8, declared_length=8),
        Node("concat", refs=(Ref(1), Ref(2)), surprise=b"prefix:", declared_length=len(final)),
    )
    return Program(
        nodes=nodes,
        roots={"out": _root(Ref(3), final)},
        limits=Limits(max_nodes=16, max_output_bytes=1024, max_work_bytes=8192, max_depth=16),
    )


def test_wire_round_trip_preserves_semantics_and_is_deterministic() -> None:
    program = _program()
    encoded_a, stats_a = encode_program(program)
    encoded_b, stats_b = encode_program(program)
    assert encoded_a == encoded_b
    assert stats_a == stats_b
    assert encoded_a.startswith(MAGIC)

    decoded = decode_program(encoded_a)
    before = evaluate(program)[0]
    after = evaluate(decoded)[0]
    assert before == after == {"out": b"prefix:" + b"abc" * 3 + b"\x00" * 8}

    # Surprise accounting includes only irreducible bytes carried by nodes. Everything
    # else is explicit Law/control/resource/integrity cost rather than gifted metadata.
    assert stats_a.surprise_bytes == len(b"abc") + len(b"prefix:")
    assert stats_a.total_bytes == stats_a.surprise_bytes + stats_a.control_integrity_bytes
    assert stats_a.control_integrity_bytes > 0


def test_root_serialization_order_is_canonical() -> None:
    value = b"x"
    node = Node("surprise", surprise=value)
    a = Program(nodes=(node,), roots={"z": _root(Ref(0), value), "a": _root(Ref(0), value)})
    b = Program(nodes=(node,), roots={"a": _root(Ref(0), value), "z": _root(Ref(0), value)})
    assert encode_program(a)[0] == encode_program(b)[0]


def test_trailing_bytes_are_rejected() -> None:
    wire = encode_program(_program())[0]
    with pytest.raises(OneError, match="trailing bytes"):
        decode_program(wire + b"x")


def test_noncanonical_varint_is_rejected_before_semantics() -> None:
    wire = bytearray(encode_program(_program())[0])
    # First field after magic is max_nodes=16, canonically one byte. Encode the same
    # value redundantly as 0x90 0x00 and preserve the remainder.
    assert wire[len(MAGIC)] == 16
    wire[len(MAGIC) : len(MAGIC) + 1] = b"\x90\x00"
    with pytest.raises(OneError, match="non-canonical uvarint"):
        decode_program(bytes(wire))


def test_encoded_resource_claim_cannot_raise_reader_caps() -> None:
    program = _program()
    wire = encode_program(program)[0]
    caps = Limits(max_nodes=8, max_output_bytes=1024, max_work_bytes=8192, max_depth=16)
    with pytest.raises(OneError, match="encoded max_nodes exceeds reader cap"):
        decode_program(wire, caps=caps)


def test_corrupt_opcode_is_rejected() -> None:
    wire = bytearray(encode_program(_program())[0])
    # Parse the five fixed-header varints in this vector: each is one or two bytes, so
    # use the real decoder invariant rather than depending on a hard-coded node offset.
    pos = len(MAGIC)
    for _ in range(5):
        while wire[pos] & 0x80:
            pos += 1
        pos += 1
    wire[pos] = 255
    with pytest.raises(OneError, match="unknown ONE wire opcode"):
        decode_program(bytes(wire))


def test_dead_fields_do_not_gain_an_unaccounted_channel() -> None:
    p = Program(
        nodes=(Node("fill", value=0, count=4, surprise=b"hidden"),),
        roots={"x": _root(Ref(0), b"\x00" * 4)},
    )
    with pytest.raises(OneError, match="fill requires only"):
        encode_program(p)
