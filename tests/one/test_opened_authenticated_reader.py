from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.auth_tree import build_auth_tree
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.opened_authenticated_reader import open_authenticated_reader


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref=ref, length=len(value), sha256=sha256(value).hexdigest())


def _program(n: int = 16384) -> tuple[Program, bytes]:
    previous = bytes((i * 29 + 7) & 255 for i in range(n))
    delta = bytes([37]) * n
    current = bytes((b + 37) & 255 for b in previous)
    nodes = (
        Node("surprise", surprise=previous, declared_length=n),
        Node("fill", count=n, value=37, declared_length=n),
        Node("add8", refs=(Ref(0), Ref(1)), declared_length=n),
    )
    roots = {
        "previous": _root(Ref(0), previous),
        "current": _root(Ref(2), current),
    }
    return Program(nodes, roots, Limits()), current


def test_opened_reader_reuses_sealed_validation_and_authenticates_ranges() -> None:
    program, current = _program()
    tree = build_auth_tree(current, 4096)
    reader = open_authenticated_reader(program, "current", tree, tree.root)

    for start, length in ((0, 64), (4096, 1024), (7777, 333), (len(current) - 257, 257)):
        value, stats = reader.read(start, length)
        assert value == current[start : start + length]
        assert stats.requested_bytes == length
        assert stats.auth_index_bytes == tree.stored_index_bytes


def test_opened_reader_snapshot_is_not_affected_by_caller_root_mutation() -> None:
    program, current = _program()
    tree = build_auth_tree(current, 4096)
    reader = open_authenticated_reader(program, "current", tree, tree.root)

    # Program is frozen but its research root Mapping may be caller-owned. The open path must
    # have snapshotted it before granting reusable validation authority.
    program.roots["current"] = Root(Ref(0), len(current), sha256(current).hexdigest())
    value, _ = reader.read(5000, 500)
    assert value == current[5000:5500]


def test_opened_reader_rejects_wrong_commitment_at_open() -> None:
    program, current = _program()
    tree = build_auth_tree(current, 4096)
    wrong = bytes([tree.root[0] ^ 1]) + tree.root[1:]
    with pytest.raises(OneError, match="does not match expected root"):
        open_authenticated_reader(program, "current", tree, wrong)


def test_opened_reader_rejects_tree_for_wrong_root_length() -> None:
    program, current = _program()
    short_tree = build_auth_tree(current[:-1], 4096)
    with pytest.raises(OneError, match="tree length"):
        open_authenticated_reader(program, "current", short_tree, short_tree.root)


def test_opened_reader_rejects_unknown_root() -> None:
    program, current = _program()
    tree = build_auth_tree(current, 4096)
    with pytest.raises(OneError, match="unknown root"):
        open_authenticated_reader(program, "missing", tree, tree.root)
