"""Authenticated selective reconstruction for experimental ONE programs.

This module composes the existing cone-only RangeEvaluator with the generic AuthTree.
It deliberately reconstructs only the Merkle-leaf-aligned dependency cone needed by
the request. Sibling hashes come from the persisted auth index; no whole-root bytes
are available to proof construction at open time.

Research-only: this does not change the canonical ONE wire format.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .auth_tree import AuthTree, RangeProof, verify_range
from .ir import OneError, Program
from .range_vm import RangeEvaluator
from .validated_program import ValidatedProgram


@dataclass(frozen=True)
class AuthenticatedSelectiveStats:
    requested_bytes: int
    cone_start: int
    cone_bytes: int
    proof_payload_bytes: int
    proof_hash_bytes: int
    auth_index_bytes: int
    range_materialized_bytes: int
    range_work_bytes: int
    nodes_touched: int
    max_depth: int

    @property
    def moved_bytes(self) -> int:
        return self.proof_payload_bytes + self.proof_hash_bytes


def _leaf_selection(tree: AuthTree, start: int, length: int) -> tuple[int, int]:
    if type(start) is not int or type(length) is not int or start < 0 or length < 0:
        raise ValueError("range start/length must be non-negative integers")
    if start + length > tree.total_len:
        raise ValueError("invalid proof range")
    if length == 0:
        first = min(start // tree.leaf_bytes, tree.leaf_count - 1)
        return first, first
    first = start // tree.leaf_bytes
    last = (start + length - 1) // tree.leaf_bytes
    return first, last


def _expected_leaf_length(tree: AuthTree, index: int) -> int:
    if index < 0 or index >= tree.leaf_count:
        raise ValueError("leaf index outside auth tree")
    start = index * tree.leaf_bytes
    return max(0, min(tree.total_len, start + tree.leaf_bytes) - start)


def proof_from_leaf_payloads(
    tree: AuthTree,
    start: int,
    length: int,
    leaf_payloads: Iterable[bytes],
) -> RangeProof:
    """Build a range proof without access to the complete logical root.

    ``leaf_payloads`` must contain exactly the selected Merkle leaves in ascending
    order. This function reads only sibling digests from the persisted ``AuthTree``.
    """
    first, last = _leaf_selection(tree, start, length)
    payloads = tuple(leaf_payloads)
    expected_count = last - first + 1
    if len(payloads) != expected_count:
        raise ValueError("wrong number of reconstructed auth leaves")
    for off, payload in enumerate(payloads):
        if not isinstance(payload, bytes):
            raise ValueError("auth leaf payload must be bytes")
        expected = _expected_leaf_length(tree, first + off)
        if len(payload) != expected:
            raise ValueError("reconstructed auth leaf has wrong length")

    selected = set(range(first, last + 1))
    siblings: list[tuple[int, int, bytes]] = []
    current = selected
    for level_no, level in enumerate(tree.levels[:-1]):
        needed: set[int] = set()
        for idx in current:
            sibling = idx ^ 1
            if sibling < len(level) and sibling not in current:
                needed.add(sibling)
        for idx in sorted(needed):
            siblings.append((level_no, idx, level[idx]))
        current = {idx // 2 for idx in current}
    return RangeProof(tree.total_len, tree.leaf_bytes, first, payloads, tuple(siblings))


def _reconstruct_authenticated_with_evaluator(
    evaluator: RangeEvaluator,
    root_name: str,
    tree: AuthTree,
    expected_auth_root: bytes,
    start: int,
    length: int,
) -> tuple[bytes, AuthenticatedSelectiveStats]:
    program = evaluator.program
    if root_name not in program.roots:
        raise OneError(f"unknown root {root_name!r}")
    root = program.roots[root_name]
    if tree.total_len != root.length:
        raise ValueError("auth tree length does not match ONE root")
    if expected_auth_root != tree.root:
        # Fail before reconstruction if the supplied sidecar is not the committed one.
        raise ValueError("auth tree root does not match expected commitment")

    first, last = _leaf_selection(tree, start, length)
    cone_start = first * tree.leaf_bytes
    cone_end = min(tree.total_len, (last + 1) * tree.leaf_bytes)
    cone_length = cone_end - cone_start

    cone, range_stats = evaluator.reconstruct(root_name, cone_start, cone_length)
    payloads = []
    cursor = 0
    for index in range(first, last + 1):
        take = _expected_leaf_length(tree, index)
        payloads.append(cone[cursor : cursor + take])
        cursor += take
    if cursor != len(cone):
        raise OneError("selective cone does not align to auth leaves")

    proof = proof_from_leaf_payloads(tree, start, length, payloads)
    value = verify_range(proof, expected_auth_root, start, length)
    stats = AuthenticatedSelectiveStats(
        requested_bytes=length,
        cone_start=cone_start,
        cone_bytes=cone_length,
        proof_payload_bytes=proof.touched_data_bytes,
        proof_hash_bytes=proof.touched_proof_bytes,
        auth_index_bytes=tree.stored_index_bytes,
        range_materialized_bytes=range_stats.materialized_bytes,
        range_work_bytes=range_stats.work_bytes,
        nodes_touched=range_stats.nodes_touched,
        max_depth=range_stats.max_depth,
    )
    return value, stats


def reconstruct_authenticated_range(
    program: Program,
    root_name: str,
    tree: AuthTree,
    expected_auth_root: bytes,
    start: int,
    length: int,
) -> tuple[bytes, AuthenticatedSelectiveStats]:
    """Reconstruct/authenticate one interval from a raw Program.

    This API preserves the inherited fail-closed contract: it performs a complete Program
    preflight through ``RangeEvaluator(program)`` before serving the range.
    """
    return _reconstruct_authenticated_with_evaluator(
        RangeEvaluator(program), root_name, tree, expected_auth_root, start, length
    )


def reconstruct_validated_authenticated_range(
    validated: ValidatedProgram,
    root_name: str,
    tree: AuthTree,
    expected_auth_root: bytes,
    start: int,
    length: int,
) -> tuple[bytes, AuthenticatedSelectiveStats]:
    """Serve a repeated authenticated range after one sealed full-Program open."""
    if not isinstance(validated, ValidatedProgram):
        raise TypeError("validated must be ValidatedProgram")
    return _reconstruct_authenticated_with_evaluator(
        RangeEvaluator.from_validated(validated),
        root_name,
        tree,
        expected_auth_root,
        start,
        length,
    )
