from __future__ import annotations

import os
from pathlib import Path

import pytest

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product_base as BASE


def _source(root: Path) -> None:
    root.mkdir()
    (root / "nested").mkdir()
    owner = root / "nested" / "owner.log"
    owner.write_bytes((b"canonical-tree-owner\n" * 4096) + b"tail")
    alias = root / "nested" / "owner-hardlink.log"
    try:
        os.link(owner, alias)
    except OSError:
        pytest.skip("filesystem does not support hardlinks")
    link = root / "owner-link"
    try:
        link.symlink_to("nested/owner.log")
    except (OSError, NotImplementedError):
        pytest.skip("filesystem does not support symlinks")


def test_logs_profile_strong_verify_exports_canonical_user_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _source(source)
    archive = tmp_path / "logs.cmpct"

    LOGS.build(source, archive)
    verified = LOGS.strong_verify(archive)
    expected = BASE.treehash(source)

    assert verified["ok"] is True
    assert verified["tree_sha256"] == expected
    assert verified["user_tree_sha256"] == expected
    assert verified["canonical_user_tree_sha256"] == expected

    restored = tmp_path / "restored"
    LOGS.extract(archive, restored)
    assert BASE.treehash(restored) == expected


def test_logs_recovery_routes_preserve_canonical_user_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _source(source)
    archive = tmp_path / "logs.cmpct"
    LOGS.build(source, archive)
    expected = BASE.treehash(source)

    recovery = LOGS.recovery_probe(archive)
    assert recovery["primary_damage"]["tree_sha256"] == expected
    assert recovery["tail_damage"]["tree_sha256"] == expected
    assert recovery["both_failed_closed"] is True
