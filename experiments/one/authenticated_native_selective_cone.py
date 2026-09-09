"""End-to-end authenticated native selective open for ONE-G0.2 research.

The candidate reconstructs only the Merkle-leaf-aligned dependency cone and authenticates
that cone against the persisted generic AuthTree. It performs no reader discovery and no
whole-root reconstruction/hash. Unsupported native topology is reported explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
import time

from .auth_tree import AuthTree, verify_range
from .ir import OneError, Program
from .native_law_range_plan import (
    compile_native_law_range_plan,
    execute_native_law_range_plan,
)
from .selective_auth import (
    _expected_leaf_length,
    _leaf_selection,
    proof_from_leaf_payloads,
)


@dataclass(frozen=True)
class AuthenticatedNativeSelectiveStats:
    requested_bytes: int
    cone_start: int
    cone_bytes: int
    packed_source_bytes: int
    source_read_bytes: int
    source_plan_write_bytes: int
    sink_write_bytes: int
    proof_payload_bytes: int
    proof_hash_bytes: int
    auth_index_bytes: int
    plan_commands: int
    prepare_wall_ns: int
    prepare_cpu_ns: int
    execute_wall_ns: int
    execute_cpu_ns: int
    proof_prepare_wall_ns: int
    proof_prepare_cpu_ns: int
    verify_wall_ns: int
    verify_cpu_ns: int
    fallback: bool = False
    fallback_reason: str | None = None

    @property
    def proof_coordinate_objects(self) -> int:
        # RangeProof represents each sibling as one (level, index, digest) tuple.
        return self.proof_hash_bytes // 32

    @property
    def modeled_data_movement_bytes(self) -> int:
        # Charge source traffic twice when a source byte is packed: once for reading the
        # Program payload, once for writing it to the contiguous native source plan.
        # Proof payload/hash units use the same logical movement convention as incumbent.
        return (
            self.source_read_bytes
            + self.source_plan_write_bytes
            + self.sink_write_bytes
            + self.proof_payload_bytes
            + self.proof_hash_bytes
        )

    @property
    def peak_temporary_bytes(self) -> int:
        # The source plan now has one backing allocation with a zero-copy ctypes view.
        # Conservatively count source plan + reconstructed auth-leaf cone + proof payload.
        # Command objects are separately reported by count because their Python object
        # footprint is implementation-specific rather than stable wire/resource bytes.
        return self.packed_source_bytes + self.cone_bytes + self.proof_payload_bytes


def _clocked(fn):
    w0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    value = fn()
    return value, time.perf_counter_ns() - w0, time.process_time_ns() - c0


def reconstruct_authenticated_native_range(
    program: Program,
    root_name: str,
    tree: AuthTree,
    expected_auth_root: bytes,
    start: int,
    length: int,
) -> tuple[bytes, AuthenticatedNativeSelectiveStats]:
    if root_name not in program.roots:
        raise OneError(f"unknown root {root_name!r}")
    root = program.roots[root_name]
    if tree.total_len != root.length:
        raise ValueError("auth tree length does not match ONE root")
    if expected_auth_root != tree.root:
        raise ValueError("auth tree root does not match expected commitment")

    first, last = _leaf_selection(tree, start, length)
    cone_start = first * tree.leaf_bytes
    cone_end = min(tree.total_len, (last + 1) * tree.leaf_bytes)
    cone_length = cone_end - cone_start

    plan, prep_wall, prep_cpu = _clocked(
        lambda: compile_native_law_range_plan(
            program, root_name, cone_start, cone_length
        )
    )
    cone, exec_wall, exec_cpu = _clocked(
        lambda: execute_native_law_range_plan(plan)
    )

    def prepare_proof():
        payloads = []
        cursor = 0
        for index in range(first, last + 1):
            take = _expected_leaf_length(tree, index)
            payloads.append(cone[cursor : cursor + take])
            cursor += take
        if cursor != len(cone):
            raise OneError("native selective cone does not align to auth leaves")
        return proof_from_leaf_payloads(tree, start, length, payloads)

    proof, proof_wall, proof_cpu = _clocked(prepare_proof)
    value, verify_wall, verify_cpu = _clocked(
        lambda: verify_range(proof, expected_auth_root, start, length)
    )
    return value, AuthenticatedNativeSelectiveStats(
        requested_bytes=length,
        cone_start=cone_start,
        cone_bytes=cone_length,
        packed_source_bytes=plan.packed_source_bytes,
        source_read_bytes=plan.source_read_bytes,
        source_plan_write_bytes=plan.source_plan_write_bytes,
        sink_write_bytes=plan.sink_write_bytes,
        proof_payload_bytes=proof.touched_data_bytes,
        proof_hash_bytes=proof.touched_proof_bytes,
        auth_index_bytes=tree.stored_index_bytes,
        plan_commands=plan.command_count,
        prepare_wall_ns=prep_wall,
        prepare_cpu_ns=prep_cpu,
        execute_wall_ns=exec_wall,
        execute_cpu_ns=exec_cpu,
        proof_prepare_wall_ns=proof_wall,
        proof_prepare_cpu_ns=proof_cpu,
        verify_wall_ns=verify_wall,
        verify_cpu_ns=verify_cpu,
    )
