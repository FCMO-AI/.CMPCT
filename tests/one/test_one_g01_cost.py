from __future__ import annotations

from hashlib import sha256

from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.wire import encode_program

LIMITS = Limits(max_nodes=64, max_output_bytes=2 * 1024 * 1024, max_work_bytes=16 * 1024 * 1024, max_depth=16)


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref, len(value), sha256(value).hexdigest())


def test_one_byte_literal_pays_complete_integrity_and_control_cost() -> None:
    # Independently derived from the G0.1 grammar:
    # 4 magic + 8 limit/count bytes + 4 node bytes + 1 root-count byte
    # + (1 name-len + 4 name + 3 ref + 1 logical-len + 32 SHA) = 61.
    p = Program(nodes=(Node("surprise", surprise=b"x", declared_length=1),), roots={"tiny": _root(Ref(0), b"x")}, limits=LIMITS)
    wire, stats = encode_program(p)
    assert len(wire) == stats.total_bytes == 61
    assert stats.surprise_bytes == 1
    assert stats.control_integrity_bytes == 60


def test_tiny_repeat_is_a_scoped_negative_not_a_fake_win() -> None:
    value = b"A" * 16
    p = Program(
        nodes=(Node("surprise", surprise=b"A", declared_length=1), Node("repeat", refs=(Ref(0),), count=16, declared_length=16)),
        roots={"tiny-repeat": _root(Ref(1), value)},
        limits=LIMITS,
    )
    wire, stats = encode_program(p)
    # The Law is real but the complete representation is 74 B for 16 logical B.
    # ONE must amortize/share framing for tiny objects rather than hiding this debt.
    assert len(wire) == stats.total_bytes == 74
    assert stats.total_bytes > len(value)
    assert stats.surprise_bytes == 1


def test_large_repeat_crosses_the_same_control_cost_without_new_opcode() -> None:
    base = bytes(range(64))
    value = base * 1024
    p = Program(
        nodes=(Node("surprise", surprise=base, declared_length=64), Node("repeat", refs=(Ref(0),), count=1024, declared_length=len(value))),
        roots={"repeat": _root(Ref(1), value)},
        limits=LIMITS,
    )
    wire, stats = encode_program(p)
    assert len(wire) == stats.total_bytes == 137
    assert stats.surprise_bytes == 64
    assert stats.control_integrity_bytes == 73
    assert stats.total_bytes < len(value) // 400


def test_sparse_fill_has_zero_surprise_but_still_pays_honest_control() -> None:
    value = b"\0" * 65536
    p = Program(nodes=(Node("fill", value=0, count=len(value), declared_length=len(value)),), roots={"sparse": _root(Ref(0), value)}, limits=LIMITS)
    wire, stats = encode_program(p)
    assert len(wire) == stats.total_bytes == 69
    assert stats.surprise_bytes == 0
    assert stats.control_integrity_bytes == 69
