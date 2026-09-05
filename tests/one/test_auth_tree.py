from __future__ import annotations

import pytest

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range


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
