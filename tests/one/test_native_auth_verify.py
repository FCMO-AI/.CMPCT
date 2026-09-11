from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range
from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval
from experiments.one.native_auth_verify import verify_range_native


def _data(n: int) -> bytes:
    return bytes(((i * 37 + i // 7) & 0xFF) for i in range(n))


@pytest.mark.parametrize("leaf", [80, 96, 112, 192])
@pytest.mark.parametrize("start,length", [(0,4096),(3072,4096),(8192,0),(65536-4096,4096)])
def test_native_verifier_matches_reference(leaf: int, start: int, length: int) -> None:
    data=_data(65536)
    tree=build_auth_tree_native(data,leaf)
    proof=prove_range_packed_interval(data,tree,start,length)
    expected=data[start:start+length]
    assert verify_range_native(proof,tree.root,start,length) == expected
    assert verify_range(proof,tree.root,start,length) == expected


def test_native_verifier_matches_independent_reference_proof() -> None:
    data=_data(32768); leaf=112; start=5000; length=7000
    ref=build_auth_tree(data,leaf)
    proof=prove_range(data,ref,start,length)
    assert verify_range_native(proof,ref.root,start,length) == data[start:start+length]


def test_tampered_payload_fails() -> None:
    data=_data(65536); tree=build_auth_tree_native(data,96); proof=prove_range_packed_interval(data,tree,30000,4096)
    payloads=list(proof.leaf_payloads); payloads[0]=bytes([payloads[0][0]^1])+payloads[0][1:]
    with pytest.raises(ValueError):
        verify_range_native(replace(proof,leaf_payloads=tuple(payloads)),tree.root,30000,4096)


def test_tampered_sibling_fails() -> None:
    data=_data(65536); tree=build_auth_tree_native(data,80); proof=prove_range_packed_interval(data,tree,0,4096)
    assert proof.siblings
    siblings=list(proof.siblings); level,index,digest=siblings[0]
    siblings[0]=(level,index,bytes([digest[0]^1])+digest[1:])
    with pytest.raises(ValueError):
        verify_range_native(replace(proof,siblings=tuple(siblings)),tree.root,0,4096)


def test_tampered_root_fails() -> None:
    data=_data(65536); tree=build_auth_tree_native(data,192); proof=prove_range_packed_interval(data,tree,10000,4096)
    bad=bytes([tree.root[0]^1])+tree.root[1:]
    with pytest.raises(ValueError):
        verify_range_native(proof,bad,10000,4096)


def test_malformed_sibling_coordinate_fails_closed() -> None:
    data=_data(65536); tree=build_auth_tree_native(data,80); proof=prove_range_packed_interval(data,tree,0,4096)
    siblings=list(proof.siblings); level,index,digest=siblings[0]; siblings[0]=(level,index+3,digest)
    with pytest.raises(ValueError):
        verify_range_native(replace(proof,siblings=tuple(siblings)),tree.root,0,4096)


def test_invalid_request_fails_closed() -> None:
    data=_data(8192); tree=build_auth_tree_native(data,96); proof=prove_range_packed_interval(data,tree,0,4096)
    with pytest.raises(ValueError):
        verify_range_native(proof,tree.root,-1,10)
    with pytest.raises(ValueError):
        verify_range_native(proof,tree.root,0,len(data)+1)
