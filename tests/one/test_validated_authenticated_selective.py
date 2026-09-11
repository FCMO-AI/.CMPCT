from __future__ import annotations

import pytest

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.range_vm import RangeEvaluator
from experiments.one.selective_auth import reconstruct_validated_authenticated_range
from experiments.one.validated_program import validate_program_snapshot


@pytest.mark.parametrize("family", ["add8", "xor", "add8_crack", "xor_crack"])
def test_shared_open_generic_and_native_authenticated_ranges_match(family):
    n = 128 * 1024
    program = _case(n, family)
    current, _ = RangeEvaluator(program).reconstruct("current", 0, n)
    tree = build_auth_tree(current, 4096)
    validated = validate_program_snapshot(program)

    for start, length in [(0, 1), (17, 913), (4090, 31), (n // 2 - 37, 127), (n - 4096, 4096)]:
        generic, generic_stats = reconstruct_validated_authenticated_range(
            validated, "current", tree, tree.root, start, length
        )
        native, native_stats = reconstruct_validated_authenticated_native_range(
            validated, "current", tree, tree.root, start, length
        )
        expected = current[start:start + length]
        assert generic == native == expected
        assert generic_stats.cone_start == native_stats.cone_start
        assert generic_stats.cone_bytes == native_stats.cone_bytes
        assert generic_stats.proof_payload_bytes == native_stats.proof_payload_bytes
        assert generic_stats.proof_hash_bytes == native_stats.proof_hash_bytes


def test_shared_open_native_rejects_wrong_auth_commitment_before_range_result():
    n = 32 * 1024
    program = _case(n, "xor")
    current, _ = RangeEvaluator(program).reconstruct("current", 0, n)
    tree = build_auth_tree(current, 4096)
    validated = validate_program_snapshot(program)
    wrong = bytes([tree.root[0] ^ 1]) + tree.root[1:]

    with pytest.raises(ValueError, match="expected commitment"):
        reconstruct_validated_authenticated_native_range(
            validated, "current", tree, wrong, 123, 4096
        )


def test_shared_open_generic_rejects_wrong_auth_commitment_before_range_result():
    n = 32 * 1024
    program = _case(n, "add8")
    current, _ = RangeEvaluator(program).reconstruct("current", 0, n)
    tree = build_auth_tree(current, 4096)
    validated = validate_program_snapshot(program)
    wrong = bytes([tree.root[0] ^ 1]) + tree.root[1:]

    with pytest.raises(ValueError, match="expected commitment"):
        reconstruct_validated_authenticated_range(
            validated, "current", tree, wrong, 123, 4096
        )
