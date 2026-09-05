from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import evaluate


def _root(node: int, data: bytes) -> Root:
    return Root(Ref(node), len(data), sha256(data).hexdigest())


def _assert_ranges(program: Program, root_name: str) -> None:
    outputs, _ = evaluate(program)
    expected = outputs[root_name]
    probes = [(0, 0), (0, min(3, len(expected))), (len(expected)//3, min(5, len(expected)-len(expected)//3)),
              (max(0, len(expected)-4), min(4, len(expected))), (0, len(expected))]
    for start, length in probes:
        got, stats = reconstruct_range_unverified(program, root_name, start, length)
        assert got == expected[start:start+length]
        assert stats.requested_bytes == length
        assert stats.authenticated is False
        assert stats.work_bytes <= program.limits.max_work_bytes


def test_range_all_generic_ops_match_full_reference_oracle():
    a = b"abcdefghijklmnop"
    b = bytes(range(16))
    nodes = (
        Node("surprise", surprise=a, declared_length=16),                  # 0
        Node("fill", value=0x11, count=16, declared_length=16),           # 1
        Node("concat", refs=(Ref(0, 2, 7), Ref(1, 0, 5)), surprise=b"XY", declared_length=14), # 2
        Node("repeat", refs=(Ref(0, 1, 4),), count=5, declared_length=20), # 3
        Node("xor", refs=(Ref(0), Ref(1)), declared_length=16),           # 4
        Node("surprise", surprise=b, declared_length=16),                 # 5
        Node("add8", refs=(Ref(4), Ref(5)), surprise=bytes([1])*16, declared_length=16), # 6
    )
    limits = Limits(max_nodes=32, max_output_bytes=1024, max_work_bytes=8192, max_depth=16)
    roots = {}
    for idx, name in [(2,"concat"),(3,"repeat"),(4,"xor"),(6,"add8")]:
        tmp = Program(nodes, {"tmp": Root(Ref(idx), nodes[idx].declared_length or 0, "0"*64)}, limits)
        # Use the generic evaluator itself only to derive bytes before the digest-bearing final program.
        # Each final range probe is independently compared against evaluate().
        from experiments.one.vm import Evaluator
        ev = Evaluator(tmp)
        data = ev._slice(Ref(idx), 1)
        roots[name] = _root(idx, data)
    program = Program(nodes, roots, limits)
    for name in roots:
        _assert_ranges(program, name)


def test_translation_shape_middle_range_touches_only_needed_surprises():
    base = bytes(range(256)) * 256
    edited = bytearray(base)
    edited[10] ^= 0x55
    edited[32768] ^= 0x33
    edited[-11] ^= 0x77
    from benchmarks.one.one_g02_translation_law_surprise_ir_compile import _programs
    _, program, _ = _programs(base, bytes(edited))
    got, stats = reconstruct_range_unverified(program, "edited", 30720, 4096)
    assert got == bytes(edited)[30720:34816]
    # Base + concat + only the in-range one-byte Surprise should be touched.
    assert stats.nodes_touched == 3
    assert stats.materialized_bytes <= 2 * 4096 + 2
    assert stats.work_bytes <= 3 * 4096 + 2


def test_nested_concat_is_fused_without_intermediate_materialization():
    left = b"abcd"
    right = b"EFGH"
    expected = left + right
    nodes = (
        Node("surprise", surprise=left, declared_length=4),
        Node("surprise", surprise=right, declared_length=4),
        Node("concat", refs=(Ref(0), Ref(1)), declared_length=8),
        Node("concat", refs=(Ref(2),), declared_length=8),
    )
    limits = Limits(max_nodes=16, max_output_bytes=64, max_work_bytes=64, max_depth=8)
    program = Program(nodes, {"x": _root(3, expected)}, limits)

    got, stats = reconstruct_range_unverified(program, "x", 0, 8)

    assert got == expected
    # The two Surprise leaves are real materialization (8 B total) and the outer concat
    # materializes the requested root (another 8 B). The nested concat is traversal only.
    assert stats.work_bytes == 16
    assert stats.materialized_bytes == 16
    assert stats.nodes_touched == 4
    assert stats.max_depth == 3


def test_range_is_explicitly_unverified_and_rejects_bad_requests():
    data = b"abcdef"
    p = Program((Node("surprise", surprise=data, declared_length=len(data)),), {"x": _root(0, data)})
    got, stats = reconstruct_range_unverified(p, "x", 1, 3)
    assert got == b"bcd"
    assert not stats.authenticated
    with pytest.raises(OneError):
        reconstruct_range_unverified(p, "x", 5, 2)
    with pytest.raises(OneError):
        reconstruct_range_unverified(p, "missing", 0, 1)
