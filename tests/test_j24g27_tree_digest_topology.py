"""Source-bound regression for public tree_digest topology fidelity (J24G27).

These filesystem tests use independent host operations, not CMPCT Builder/Reader;
their scope is the public helper's evidence semantics only.
"""
import os
from pathlib import Path

import pytest

from cmpct.transactions import tree_digest


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
    assert tree_digest(linked) != tree_digest(copied)


def test_tree_digest_hardlink_is_not_content_copy(tmp_path: Path) -> None:
    copied = _new_tree(tmp_path, "copy")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "owner").write_bytes((copied / "owner").read_bytes())
    _hardlink_or_skip(linked / "owner", linked / "peer")
    assert tree_digest(linked) != tree_digest(copied)


def test_tree_digest_hardlinks_use_logical_owner_not_inode(tmp_path: Path) -> None:
    trees = []
    for i in range(2):
        d = tmp_path / str(i)
        d.mkdir()
        (d / "owner").write_bytes(b"shared content")
        _hardlink_or_skip(d / "owner", d / "peer")
        trees.append(d)
    assert tree_digest(trees[0]) == tree_digest(trees[1])


def test_tree_digest_symlink_target_is_not_dereferenced(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "owner").write_bytes(b"safe")
    _symlink_or_skip(tree / "peer", "owner")
    existing = tree_digest(tree)
    (tree / "peer").unlink()
    (tree / "peer").symlink_to("absent")
    assert tree_digest(tree) != existing
    # The target is absent: digesting only the lexical link is still defined.
    assert tree_digest(tree) == tree_digest(tree)


def test_tree_digest_regular_content_is_committed(tmp_path: Path) -> None:
    p = tmp_path / "content"
    p.write_bytes(b"A")
    old = tree_digest(tmp_path)
    p.write_bytes(b"B")
    assert tree_digest(tmp_path) != old


def test_tree_digest_empty_directory_is_a_distinct_entry(tmp_path: Path) -> None:
    old = tree_digest(tmp_path)
    (tmp_path / "empty").mkdir()
    assert tree_digest(tmp_path) != old


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"), reason="POSIX FIFO only")
def test_tree_digest_unsupported_special_kind_fails_closed(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(ValueError, match="unsupported filesystem entry"):
        tree_digest(tmp_path)


@pytest.mark.skipif(os.name != "posix", reason="byte pathname semantics are POSIX-only")
def test_tree_digest_non_utf8_filename(tmp_path: Path) -> None:
    byte_path = os.fsencode(tmp_path) + b"/bad-\xff"
    with open(byte_path, "wb") as f:
        f.write(b"exact")
    assert len(tree_digest(tmp_path)) == 64
