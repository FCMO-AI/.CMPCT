from __future__ import annotations

import pytest

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range
from experiments.one.native_auth_tree import NativeAuthTree, build_auth_tree_native, prove_range_packed


@pytest.mark.parametrize("size", [0, 1, 79, 80, 81, 191, 192, 193, 4097, 65536])
@pytest.mark.parametrize("leaf", [80, 96, 112, 192])
def test_native_auth_tree_matches_reference(size: int, leaf: int) -> None:
    data=bytes(((i*131 + size*17) ^ (i>>3)) & 0xFF for i in range(size))
    ref=build_auth_tree(data,leaf)
    got=build_auth_tree_native(data,leaf)
    assert got.root == ref.root
    assert got.levels() == ref.levels
    assert got.node_count == sum(len(level) for level in ref.levels)
    assert got.stored_index_bytes == ref.stored_index_bytes


@pytest.mark.parametrize("leaf", [80, 96, 112, 192])
def test_packed_range_proof_matches_reference_exactly(leaf: int) -> None:
    data=bytes(((i*73) ^ (i>>5) ^ 0xA7) & 0xFF for i in range(65536))
    ref=build_auth_tree(data,leaf)
    native=build_auth_tree_native(data,leaf)
    ranges=[(0,0),(0,1),(1,79),(4093,4096),(32768,4096),(65535,1)]
    for start,length in ranges:
        expected=prove_range(data,ref,start,length)
        got=prove_range_packed(data,native,start,length)
        assert got == expected
        assert verify_range(got,native.root,start,length) == data[start:start+length]
        assert got.touched_proof_bytes == 32*len(got.siblings)


def test_packed_proof_does_not_require_full_level_materialization(monkeypatch: pytest.MonkeyPatch) -> None:
    data=bytes((i*29) & 0xFF for i in range(65536))
    native=build_auth_tree_native(data,96)
    def forbidden_levels():
        raise AssertionError("packed selective proof must not expand the full tree")
    monkeypatch.setattr(type(native),"levels",lambda self: forbidden_levels())
    proof=prove_range_packed(data,native,8192,4096)
    assert verify_range(proof,native.root,8192,4096) == data[8192:12288]


def test_packed_proof_reads_exactly_one_digest_per_sibling(monkeypatch: pytest.MonkeyPatch) -> None:
    data=bytes((i*47 + 11) & 0xFF for i in range(65536))
    native=build_auth_tree_native(data,112)
    original=NativeAuthTree.digest_at
    calls=[]
    def counted(self: NativeAuthTree, level: int, index: int) -> bytes:
        calls.append((level,index))
        return original(self,level,index)
    monkeypatch.setattr(NativeAuthTree,"digest_at",counted)
    proof=prove_range_packed(data,native,12288,4096)
    assert len(calls) == len(proof.siblings)
    assert calls == [(level,index) for level,index,_ in proof.siblings]
    assert 32*len(calls) == proof.touched_proof_bytes


def test_packed_proof_rejects_invalid_ranges() -> None:
    data=b"abcdef"
    native=build_auth_tree_native(data,80)
    for start,length in [(-1,1),(0,-1),(6,1),(7,0)]:
        with pytest.raises(ValueError):
            prove_range_packed(data,native,start,length)


def test_native_auth_tree_rejects_invalid_leaf() -> None:
    for leaf in (0,-1,1<<32):
        with pytest.raises(ValueError):
            build_auth_tree_native(b"abc",leaf)


def test_native_auth_tree_rejects_non_bytes() -> None:
    with pytest.raises(TypeError):
        build_auth_tree_native(bytearray(b"abc"),80)  # type: ignore[arg-type]
