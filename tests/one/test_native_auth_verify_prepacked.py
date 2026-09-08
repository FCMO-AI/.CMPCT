from dataclasses import replace

import pytest

from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval
from experiments.one.native_auth_verify_prepacked import prepare_native_range_proof, verify_range_native_prepacked


def _flip(data: bytes) -> bytes:
    return bytes([data[0] ^ 1]) + data[1:]


def test_prepacked_native_verifier_matches_exact_requested_bytes():
    data=bytes((i * 37 + 11) & 0xFF for i in range(1 << 16))
    for leaf in (80,96,112,192):
        tree=build_auth_tree_native(data,leaf)
        for start,length in ((0,4096),(12345,4096),(len(data)-4096,4096),(8192,16384)):
            proof=prove_range_packed_interval(data,tree,start,length)
            prepared=prepare_native_range_proof(proof,tree.root)
            assert verify_range_native_prepacked(prepared,start,length) == data[start:start+length]


def test_prepacked_native_verifier_rejects_tampered_payload_sibling_and_root():
    data=bytes((i * 17 + 5) & 0xFF for i in range(1 << 16))
    tree=build_auth_tree_native(data,96)
    start,length=12345,4096
    proof=prove_range_packed_interval(data,tree,start,length)

    payloads=list(proof.leaf_payloads)
    payloads[0]=_flip(payloads[0])
    bad_payload=prepare_native_range_proof(replace(proof,leaf_payloads=tuple(payloads)),tree.root)
    with pytest.raises(ValueError):
        verify_range_native_prepacked(bad_payload,start,length)

    siblings=list(proof.siblings)
    assert siblings
    level,index,digest=siblings[0]
    siblings[0]=(level,index,_flip(digest))
    bad_sibling=prepare_native_range_proof(replace(proof,siblings=tuple(siblings)),tree.root)
    with pytest.raises(ValueError):
        verify_range_native_prepacked(bad_sibling,start,length)

    bad_root=prepare_native_range_proof(proof,_flip(tree.root))
    with pytest.raises(ValueError):
        verify_range_native_prepacked(bad_root,start,length)


def test_prepacked_native_verifier_rejects_bad_request_bounds():
    data=b"x" * 8192
    tree=build_auth_tree_native(data,192)
    proof=prove_range_packed_interval(data,tree,0,4096)
    prepared=prepare_native_range_proof(proof,tree.root)
    with pytest.raises(ValueError):
        verify_range_native_prepacked(prepared,-1,1)
    with pytest.raises(ValueError):
        verify_range_native_prepacked(prepared,len(data),1)
