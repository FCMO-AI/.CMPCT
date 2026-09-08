from __future__ import annotations

import pytest

from experiments.one.auth_tree import build_auth_tree
from experiments.one.native_auth_tree import build_auth_tree_native


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


def test_native_auth_tree_rejects_invalid_leaf() -> None:
    for leaf in (0,-1,1<<32):
        with pytest.raises(ValueError):
            build_auth_tree_native(b"abc",leaf)


def test_native_auth_tree_rejects_non_bytes() -> None:
    with pytest.raises(TypeError):
        build_auth_tree_native(bytearray(b"abc"),80)  # type: ignore[arg-type]
