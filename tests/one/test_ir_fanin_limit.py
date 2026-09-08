from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root


def _root(node: int, length: int, payload: bytes) -> Root:
    return Root(Ref(node), length, sha256(payload).hexdigest())


def test_ir_rejects_concat_fanin_above_declared_reader_envelope():
    limits = Limits(max_nodes=4)
    nodes = (
        Node("surprise", surprise=b"a"),
        Node("concat", refs=(Ref(0), Ref(0), Ref(0), Ref(0), Ref(0)), declared_length=5),
    )
    program = Program(nodes, {"current": _root(1, 5, b"aaaaa")}, limits)

    with pytest.raises(OneError, match="node reference count exceeds declared limit"):
        program.validate_shape()


def test_ir_allows_fanin_exactly_at_declared_reader_envelope():
    limits = Limits(max_nodes=4)
    nodes = (
        Node("surprise", surprise=b"a"),
        Node("concat", refs=(Ref(0), Ref(0), Ref(0), Ref(0)), declared_length=4),
    )
    program = Program(nodes, {"current": _root(1, 4, b"aaaa")}, limits)

    program.validate_shape()
