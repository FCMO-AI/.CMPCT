from __future__ import annotations

import hashlib
import math
import struct

import pytest

from benchmarks.one.one_g02_shared_auth_family_creation_ab import _basis_sha_input_bytes
from experiments.one.auth_tree import (
    LEAF_DOMAIN,
    PARENT_DOMAIN,
    ROOT_DOMAIN,
    build_auth_tree,
    prove_range,
    verify_range,
)


@pytest.mark.parametrize("size", [0, 1, 1023, 1024, 1025, 8193, 65537])
@pytest.mark.parametrize("leaf", [256, 1024, 4096])
def test_authenticated_ranges_roundtrip(size, leaf):
    data = bytes((i * 131 + 17) & 255 for i in range(size))
    tree = build_auth_tree(data, leaf)
    probes = [(0, 0)]
    if size:
        probes += [(0, min(size, 17)), (size//2, min(4096, size-size//2)), (max(0,size-33), min(33,size))]
    for start, length in probes:
        proof = prove_range(data, tree, start, length)
        assert verify_range(proof, tree.root, start, length) == data[start:start+length]


def test_tampered_payload_and_proof_fail_closed():
    data = bytes(range(256)) * 100
    tree = build_auth_tree(data, 1024)
    proof = prove_range(data, tree, 7000, 4096)
    payloads = list(proof.leaf_payloads)
    payloads[0] = bytes([payloads[0][0] ^ 1]) + payloads[0][1:]
    bad = type(proof)(proof.total_len, proof.leaf_bytes, proof.first_leaf, tuple(payloads), proof.siblings)
    with pytest.raises(ValueError, match="authentication"):
        verify_range(bad, tree.root, 7000, 4096)
    if proof.siblings:
        siblings = list(proof.siblings)
        level, idx, digest = siblings[0]
        siblings[0] = (level, idx, bytes([digest[0] ^ 1]) + digest[1:])
        bad = type(proof)(proof.total_len, proof.leaf_bytes, proof.first_leaf, proof.leaf_payloads, tuple(siblings))
        with pytest.raises(ValueError, match="authentication"):
            verify_range(bad, tree.root, 7000, 4096)


def test_root_commits_leaf_geometry_and_length():
    data = b"x" * 10000
    assert build_auth_tree(data, 1024).root != build_auth_tree(data, 2048).root
    assert build_auth_tree(data, 1024).root != build_auth_tree(data + b"x", 1024).root


def test_auth_domains_are_exact_semantic_bytes():
    assert LEAF_DOMAIN == b"ONE-L\x00"
    assert PARENT_DOMAIN == b"ONE-P\x00"
    assert ROOT_DOMAIN == b"ONE-R\x00"

    data = b"abc"
    leaf_bytes = 80
    leaf = hashlib.sha256(LEAF_DOMAIN + struct.pack("<QQ", 0, len(data)) + data).digest()
    expected = hashlib.sha256(ROOT_DOMAIN + struct.pack("<QI", len(data), leaf_bytes) + leaf).digest()
    assert build_auth_tree(data, leaf_bytes).root == expected


def test_shared_family_basis_sha_accounting_matches_auth_tree_grammar():
    size = 65_536
    leaf_bytes = 80
    leaves = math.ceil(size / leaf_bytes)
    width = leaves
    parents = 0
    while width > 1:
        width = math.ceil(width / 2)
        parents += width
    expected = (
        size
        + leaves * (len(LEAF_DOMAIN) + 16)
        + parents * (len(PARENT_DOMAIN) + 4 + 64)
        + len(ROOT_DOMAIN) + 8 + 4 + 32
    )
    assert _basis_sha_input_bytes(size) == expected
