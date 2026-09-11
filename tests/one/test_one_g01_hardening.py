from __future__ import annotations

from hashlib import sha256

import pytest

from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.vm import evaluate


def _root(ref: Ref, value: bytes) -> Root:
    return Root(ref, len(value), sha256(value).hexdigest())


def test_dependency_depth_cannot_be_hidden_by_a_warm_cache() -> None:
    # Root insertion order deliberately evaluates node 1 first, warming node 0. The
    # deeper chain then reaches that same cached leaf at dependency depth 3. Validity
    # must not depend on cache/evaluation order, so static preflight rejects it.
    p = Program(
        nodes=(
            Node("surprise", surprise=b"x", declared_length=1),
            Node("concat", refs=(Ref(0),), declared_length=1),
            Node("concat", refs=(Ref(0),), declared_length=1),
            Node("concat", refs=(Ref(2),), declared_length=1),
        ),
        roots={"shallow": _root(Ref(1), b"x"), "too-deep": _root(Ref(3), b"x")},
        limits=Limits(max_nodes=8, max_output_bytes=32, max_work_bytes=128, max_depth=2),
    )
    with pytest.raises(OneError, match="dependency depth"):
        evaluate(p)


def test_unreachable_cycle_is_invalid_stored_program() -> None:
    p = Program(
        nodes=(
            Node("surprise", surprise=b"ok", declared_length=2),
            Node("concat", refs=(Ref(2),), declared_length=0),
            Node("concat", refs=(Ref(1),), declared_length=0),
        ),
        roots={"ok": _root(Ref(0), b"ok")},
        limits=Limits(max_nodes=8, max_output_bytes=32, max_work_bytes=128, max_depth=8),
    )
    with pytest.raises(OneError, match="cycle"):
        evaluate(p)


def test_malformed_python_types_fail_as_one_errors_not_host_exceptions() -> None:
    malformed = Program(
        nodes=(Node("fill", value=0, count="4"),),  # type: ignore[arg-type]
        roots={"x": _root(Ref(0), b"\0" * 4)},
    )
    with pytest.raises(OneError, match="count/value"):
        evaluate(malformed)


def test_sha_text_with_whitespace_cannot_shrink_integrity_field() -> None:
    # bytes.fromhex ignores ASCII spaces. G0.1 requires both 64 textual hex digits and
    # exactly 32 decoded digest bytes so this cannot become a shorter wire field.
    p = Program(
        nodes=(Node("surprise", surprise=b"x"),),
        roots={"x": Root(Ref(0), 1, "00" * 31 + "  ")},
    )
    with pytest.raises(OneError, match="exactly 32 bytes"):
        evaluate(p)


def test_bool_is_not_an_integer_in_resource_semantics() -> None:
    p = Program(
        nodes=(Node("surprise", surprise=b"x"),),
        roots={"x": _root(Ref(0), b"x")},
        limits=Limits(max_nodes=True),  # type: ignore[arg-type]
    )
    with pytest.raises(OneError, match="invalid limit"):
        evaluate(p)
