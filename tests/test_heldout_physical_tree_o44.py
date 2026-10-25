"""Evidence for the non-frozen hardlink-preserving copier and its control."""

import os
import shutil
import stat
from pathlib import Path

import pytest

from benchmarks.heldout_physical_tree import copytree_with_hardlinks


def _partition(root: Path):
    """Root-independent equivalence classes; never compare absolute inode IDs."""
    groups = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.is_symlink():
            st = p.stat()
            groups.setdefault((st.st_dev, st.st_ino), []).append(p.relative_to(root).as_posix())
    return sorted(tuple(v) for v in groups.values())


def _snapshot(root: Path):
    result = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        m = p.lstat().st_mode
        if stat.S_ISLNK(m):
            result[rel] = ("symlink", os.readlink(p))
        elif stat.S_ISDIR(m):
            result[rel] = ("dir", stat.S_IMODE(m))
        elif stat.S_ISREG(m):
            result[rel] = ("file", p.read_bytes(), stat.S_IMODE(m))
        else:
            result[rel] = ("unsupported",)
    return result


def _build(root: Path):
    (root / "nested").mkdir(parents=True)
    payload = b"ABC" * 300
    (root / "nested" / "owner.dat").write_bytes(payload)
    os.link(root / "nested" / "owner.dat", root / "alias.dat")
    os.link(root / "nested" / "owner.dat", root / "alias2.dat")
    (root / "copy.dat").write_bytes(payload)
    (root / "other.dat").write_bytes(b"xyz")
    (root / "nested" / "empty").mkdir()
    os.symlink("nested/owner.dat", root / "symlink.dat")


def test_copytree_control_loses_hardlink_equivalence(tmp_path):
    source = tmp_path / "source"; source.mkdir(); _build(source)
    legacy = tmp_path / "legacy"; shutil.copytree(source, legacy, symlinks=True)
    assert _snapshot(source) == _snapshot(legacy)
    assert _partition(source) != _partition(legacy)
    assert len(_partition(source)) == 3
    assert len(_partition(legacy)) == 5


def test_copytree_with_hardlinks_preserves_topology_and_logical_semantics(tmp_path):
    source = tmp_path / "source"; source.mkdir(); _build(source)
    candidate = tmp_path / "candidate"; copytree_with_hardlinks(source, candidate)
    assert _snapshot(source) == _snapshot(candidate)
    assert _partition(source) == _partition(candidate)
    assert (candidate / "alias.dat").stat().st_ino == (candidate / "nested" / "owner.dat").stat().st_ino
    assert (candidate / "copy.dat").stat().st_ino != (candidate / "nested" / "owner.dat").stat().st_ino
    assert (candidate / "symlink.dat").is_symlink()


def test_copytree_refuses_symlink_root(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    src = tmp_path / "link"; src.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="real directory"):
        copytree_with_hardlinks(src, tmp_path / "candidate")


def test_copytree_independent_source_inode_outside_tree_not_relinked_to_external(tmp_path):
    outside = tmp_path / "outside.dat"; outside.write_bytes(b"abc")
    root = tmp_path / "root"; root.mkdir(); os.link(outside, root / "inside.dat")
    dst = tmp_path / "candidate"; copytree_with_hardlinks(root, dst)
    assert (dst / "inside.dat").read_bytes() == b"abc"
    assert (dst / "inside.dat").stat().st_ino != outside.stat().st_ino
    assert outside.stat().st_nlink == 2


def test_heldout_combined_realistic_synthetic_corpus_without_frozen_changes(tmp_path):
    from benchmarks.heldout_combined_topology_o44 import assess, build_nonfrozen_combined
    corpora = tmp_path / "corpora"; corpora.mkdir()
    for name in ("tiny", "source", "media", "dedup_links", "nested", "binary"):
        (corpora / name).mkdir()
    d = corpora / "dedup_links"
    (d / "real.dat").write_bytes(b"proof")
    os.link(d / "real.dat", d / "hardlink.dat")
    (d / "copy.dat").write_bytes(b"proof")
    os.symlink("real.dat", d / "symlink.dat")
    for name in ("pattern32m.bin", "random16m.bin"):
        (corpora / "binary" / name).write_bytes(b"exact-" + name.encode())
    original = corpora / "combined"; original.mkdir()
    for name in ("tiny", "source", "media", "dedup_links", "nested"):
        shutil.copytree(corpora / name, original / name, symlinks=True)
    for name in ("pattern32m.bin", "random16m.bin"):
        shutil.copy2(corpora / "binary" / name, original / name)
    heldout = tmp_path / "heldout"
    build_nonfrozen_combined(corpora, heldout)
    outcome = assess(corpora, heldout)
    assert outcome["verdict"] == "PASS"
    assert outcome["source_hardlink_pair"]
    assert not outcome["historical_combined_hardlink_pair"]
    assert outcome["heldout_combined_hardlink_pair"]
    assert outcome["typed_member_snapshots_equal"]
    assert outcome["heldout_partition_matches_sources"]
    assert outcome["legacy_unique_inode_charged_bytes"] - outcome["heldout_unique_inode_charged_bytes"] == len(b"proof")


def test_hardlink_failure_does_not_silently_make_an_independent_copy(tmp_path, monkeypatch):
    from benchmarks import heldout_physical_tree as module
    src = tmp_path / "src"; src.mkdir()
    (src / "first").write_bytes(b"payload")
    os.link(src / "first", src / "second")
    def denied(*_args, **_kwargs):
        raise OSError("simulated hardlink unavailable")
    monkeypatch.setattr(module.os, "link", denied)
    dst = tmp_path / "dst"
    with pytest.raises((OSError, shutil.Error), match="simulated hardlink unavailable"):
        module.copytree_with_hardlinks(src, dst)
    # Partial failure is not a successful corpus; no silent independent copy.
    assert len(list(dst.glob("*"))) == 1
