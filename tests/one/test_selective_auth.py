from __future__ import annotations

import hashlib

import pytest

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range
from experiments.one.ir import Node, Program, Ref, Root
from experiments.one.selective_auth import (
    proof_from_leaf_payloads,
    reconstruct_authenticated_range,
)


def _program(data: bytes) -> Program:
    digest = hashlib.sha256(data).hexdigest()
    return Program(
        nodes=(Node("surprise", surprise=data),),
        roots={"root": Root(Ref(0), len(data), digest)},
    )


@pytest.mark.parametrize("size", [1, 1025, 8193, 65537])
@pytest.mark.parametrize("leaf_bytes", [256, 1024, 4096])
def test_proof_from_reconstructed_leaves_matches_full_data_proof(size, leaf_bytes):
    data = bytes((i * 131 + 17) & 255 for i in range(size))
    tree = build_auth_tree(data, leaf_bytes)
    start = min(size - 1, size // 3)
    length = min(3000, size - start)
    full = prove_range(data, tree, start, length)
    rebuilt = proof_from_leaf_payloads(tree, start, length, full.leaf_payloads)
    assert rebuilt == full
    assert verify_range(rebuilt, tree.root, start, length) == data[start:start+length]


def test_proof_from_reconstructed_leaves_rejects_wrong_geometry():
    data = bytes(range(256)) * 40
    tree = build_auth_tree(data, 1024)
    full = prove_range(data, tree, 900, 3000)

    with pytest.raises(ValueError, match="number"):
        proof_from_leaf_payloads(tree, 900, 3000, full.leaf_payloads[:-1])

    bad = list(full.leaf_payloads)
    bad[-1] = bad[-1][:-1]
    with pytest.raises(ValueError, match="wrong length"):
        proof_from_leaf_payloads(tree, 900, 3000, bad)


def test_authenticated_selective_reconstruction_roundtrips_without_full_root_input():
    data = bytes((i * 29 + 11) & 255 for i in range(128 * 1024 + 333))
    program = _program(data)
    tree = build_auth_tree(data, 4096)
    start = 47_123
    length = 913

    value, stats = reconstruct_authenticated_range(
        program, "root", tree, tree.root, start, length
    )
    assert value == data[start:start+length]
    assert stats.cone_bytes <= 2 * tree.leaf_bytes
    assert stats.proof_payload_bytes == stats.cone_bytes
    assert stats.cone_bytes < len(data)
    assert stats.moved_bytes < len(data)


def test_authenticated_selective_reconstruction_rejects_tampered_cone():
    data = bytes((i * 17 + 3) & 255 for i in range(32 * 1024))
    program = _program(data)
    tree = build_auth_tree(data, 1024)

    changed = bytearray(data)
    changed[4100] ^= 1
    bad_program = _program(bytes(changed))
    with pytest.raises(ValueError, match="authentication"):
        reconstruct_authenticated_range(
            bad_program, "root", tree, tree.root, 4096, 64
        )


def test_authenticated_selective_reconstruction_rejects_wrong_commitment():
    data = b"x" * 8192
    program = _program(data)
    tree = build_auth_tree(data, 1024)
    bad_root = bytes([tree.root[0] ^ 1]) + tree.root[1:]
    with pytest.raises(ValueError, match="expected commitment"):
        reconstruct_authenticated_range(program, "root", tree, bad_root, 1, 1)
