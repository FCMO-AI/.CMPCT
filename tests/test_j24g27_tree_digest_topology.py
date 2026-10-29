"""Source-bound regression for opt-in tree topology digest fidelity (J24G27b).

These filesystem tests use independent host operations, not CMPCT Builder/Reader;
their scope is the public helper's evidence semantics only.
"""
import os
from pathlib import Path

import pytest

from cmpct.transactions import tree_digest, tree_topology_digest
from cmpct import core as public_facade


def _new_tree(root: Path, variant: str) -> Path:
    tree = root / variant
    tree.mkdir()
    (tree / "owner").write_bytes(b"same bytes, different filesystem semantics")
    peer = tree / "peer"
    if variant == "copy":
        peer.write_bytes((tree / "owner").read_bytes())
    elif variant == "hardlink":
        os.link(tree / "owner", peer)
    elif variant == "symlink":
        peer.symlink_to("owner")
    elif variant == "dangling":
        peer.symlink_to("absent")
    elif variant == "directory":
        peer.mkdir()
    else:
        raise AssertionError(variant)
    return tree


def _symlink_or_skip(path: Path, target: str) -> None:
    try:
        path.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem does not allow symlinks: {exc}")


def _hardlink_or_skip(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem does not allow hardlinks: {exc}")


def test_tree_digest_symlink_is_not_content_copy(tmp_path: Path) -> None:
    copied = _new_tree(tmp_path, "copy")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "owner").write_bytes((copied / "owner").read_bytes())
    _symlink_or_skip(linked / "peer", "owner")
    assert tree_topology_digest(linked) != tree_topology_digest(copied)


def test_tree_digest_hardlink_is_not_content_copy(tmp_path: Path) -> None:
    copied = _new_tree(tmp_path, "copy")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "owner").write_bytes((copied / "owner").read_bytes())
    _hardlink_or_skip(linked / "owner", linked / "peer")
    assert tree_topology_digest(linked) != tree_topology_digest(copied)


def test_tree_digest_hardlinks_use_logical_owner_not_inode(tmp_path: Path) -> None:
    trees = []
    for i in range(2):
        d = tmp_path / str(i)
        d.mkdir()
        (d / "owner").write_bytes(b"shared content")
        _hardlink_or_skip(d / "owner", d / "peer")
        trees.append(d)
    assert tree_topology_digest(trees[0]) == tree_topology_digest(trees[1])


def test_tree_digest_symlink_target_is_not_dereferenced(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "owner").write_bytes(b"safe")
    _symlink_or_skip(tree / "peer", "owner")
    existing = tree_topology_digest(tree)
    (tree / "peer").unlink()
    (tree / "peer").symlink_to("absent")
    assert tree_topology_digest(tree) != existing
    # The target is absent: digesting only the lexical link is still defined.
    assert tree_topology_digest(tree) == tree_topology_digest(tree)


def test_tree_digest_regular_content_is_committed(tmp_path: Path) -> None:
    p = tmp_path / "content"
    p.write_bytes(b"A")
    old = tree_topology_digest(tmp_path)
    p.write_bytes(b"B")
    assert tree_topology_digest(tmp_path) != old


def test_tree_digest_empty_directory_is_a_distinct_entry(tmp_path: Path) -> None:
    old = tree_topology_digest(tmp_path)
    (tmp_path / "empty").mkdir()
    assert tree_topology_digest(tmp_path) != old


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"), reason="POSIX FIFO only")
def test_tree_digest_unsupported_special_kind_fails_closed(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(ValueError, match="unsupported filesystem entry"):
        tree_topology_digest(tmp_path)


@pytest.mark.skipif(os.name != "posix", reason="byte pathname semantics are POSIX-only")
def test_tree_digest_non_utf8_filename(tmp_path: Path) -> None:
    byte_path = os.fsencode(tmp_path) + b"/bad-\xff"
    with open(byte_path, "wb") as f:
        f.write(b"exact")
    assert len(tree_topology_digest(tmp_path)) == 64


def _four_path_partitions(prefix=(0,)):
    """All 15 set partitions of four named entries (restricted-growth strings)."""
    if len(prefix) == 4:
        yield prefix
        return
    for nxt in range(max(prefix) + 2):
        yield from _four_path_partitions(prefix + (nxt,))


def test_tree_digest_exhaustive_four_path_hardlink_partition_court(tmp_path: Path) -> None:
    """Independent oracle: os.path.samefile equivalence, not the digest's inode map."""
    seen = {}
    count = 0
    for model in _four_path_partitions():
        for replica in range(2):
            root = tmp_path / f"{count:02d}-{replica}"
            root.mkdir()
            owners = {}
            paths = []
            for name, group in zip("abcd", model):
                p = root / name
                if group in owners:
                    _hardlink_or_skip(owners[group], p)
                else:
                    p.write_bytes(b"same bytes in each independent file class")
                    owners[group] = p
                paths.append(p)
            independent_equivalence = tuple(
                tuple(os.path.samefile(a, b) for b in paths) for a in paths
            )
            observed = tree_topology_digest(root)
            if independent_equivalence in seen:
                assert seen[independent_equivalence] == observed
            else:
                seen[independent_equivalence] = observed
        count += 1
    assert count == 15
    assert len(seen) == len(set(seen.values())) == 15


def test_legacy_digest_golden_and_facade_contract(tmp_path: Path) -> None:
    """Published v1 hash stays byte-identical, despite its known topology collision."""
    (tmp_path / "owner").write_bytes(b"same bytes independent of topology")
    (tmp_path / "peer").write_bytes(b"same bytes independent of topology")
    expected = "4a0ec1aaba71d5c2abd6cb9c8d6b54e7601c582b35a1c4f98c0d3bd67ba85b24"
    assert tree_digest(tmp_path) == expected
    assert public_facade.tree_digest(tmp_path) == expected
    assert public_facade.tree_topology_digest is tree_topology_digest
    assert tree_topology_digest(tmp_path) != expected


def test_legacy_collision_is_explicitly_not_topology_proof(tmp_path: Path) -> None:
    original = tmp_path / "copy"
    original.mkdir()
    (original / "owner").write_bytes(b"same bytes independent of topology")
    (original / "peer").write_bytes(b"same bytes independent of topology")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "owner").write_bytes(b"same bytes independent of topology")
    _symlink_or_skip(linked / "peer", "owner")
    assert tree_digest(linked) == tree_digest(original)
    assert tree_topology_digest(linked) != tree_topology_digest(original)
