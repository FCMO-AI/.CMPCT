"""O67: source-exact physical alias fidelity for *hardlinked symlink inodes*.

Deliberately distinguishes true hardlinks to a symlink inode from independently
created symlinks whose targets are textually identical.
"""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


VARIANT = os.environ.get("CMPCT_O67_VARIANT", "")
assert VARIANT in {"baseline", "candidate"}, (
    "O67 requires an explicit baseline/candidate binding; no silent defaults"
)


def _link_symlink_inode(src: Path, dest: Path) -> None:
    if os.name == "nt":
        pytest.skip("POSIX hardlink-to-symlink-inode semantic fixture")
    os.symlink("payload.bin", src)
    try:
        os.link(src, dest, follow_symlinks=False)
    except (OSError, NotImplementedError, ValueError) as exc:
        pytest.skip(f"host filesystem does not permit hardlinking symlink inode: {exc}")
    sa, sb = os.lstat(src), os.lstat(dest)
    assert stat.S_ISLNK(sa.st_mode) and stat.S_ISLNK(sb.st_mode), (
        "precondition failed: both names must remain symbolic links"
    )
    assert (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino), (
        "precondition failed: second name did not hardlink original symlink inode"
    )
    assert sa.st_nlink >= 2 and sb.st_nlink >= 2, "no physical alias link count"


def _create(root: Path, out: Path) -> None:
    Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(out)


def test_hardlinked_symlink_inode_source_completeness(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "payload.bin").write_bytes(b"strictly-ordinary-target")
    _link_symlink_inode(root / "aaa-symlink", root / "zzz-symlink")
    out = tmp_path / "physical.cmpct"

    if VARIANT == "candidate":
        sentinel = b"EXISTING-ARCHIVE-MUST-NOT-BE-CLOBBERED"
        out.write_bytes(sentinel)
        with pytest.raises(OSError, match="hardlinked symlink"):
            _create(root, out)
        assert out.read_bytes() == sentinel
        return

    # Original Builder is expected to create a self-consistent but physically
    # incomplete archive. A different outcome falsifies the preregistered defect.
    _create(root, out)
    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        assert reader.read("aaa-symlink") == b"payload.bin"
        assert reader.read("zzz-symlink") == b"payload.bin"
        dest = tmp_path / "extracted"
        reader.extractall(dest, metadata=False)
    a, b = dest / "aaa-symlink", dest / "zzz-symlink"
    sa, sb = os.lstat(a), os.lstat(b)
    assert stat.S_ISLNK(sa.st_mode) and stat.S_ISLNK(sb.st_mode)
    assert os.readlink(a) == os.readlink(b) == "payload.bin"
    assert (sa.st_dev, sa.st_ino) != (sb.st_dev, sb.st_ino), (
        "baseline did preserve symlink inode alias; O67 defect is falsified"
    )
    print("O67_BASELINE_SILENT_SYMLINK_INODE_ALIAS_LOSS=CONFIRMED")


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink creation and inode semantics")
def test_independent_equal_target_symlinks_must_remain_distinct(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "payload.bin").write_bytes(b"same-target-control")
    os.symlink("payload.bin", root / "left")
    os.symlink("payload.bin", root / "right")
    source_a, source_b = os.lstat(root / "left"), os.lstat(root / "right")
    assert source_a.st_ino != source_b.st_ino, "control requires independent symlink objects"
    out = tmp_path / "independent.cmpct"
    _create(root, out)
    with CMPCT(out) as reader:
        reader.verify()
        dest = tmp_path / "out"
        reader.extractall(dest, metadata=False)
    a, b = dest / "left", dest / "right"
    assert os.readlink(a) == os.readlink(b) == "payload.bin"
    assert os.lstat(a).st_ino != os.lstat(b).st_ino



@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink-inode external-link control")
def test_single_selected_symlink_alias_with_external_hardlink_is_valid(tmp_path):
    """Global nlink>1 is not proof that the selected source contains an alias pair."""
    root = tmp_path / "source"
    root.mkdir()
    (root / "payload.bin").write_bytes(b"one-name-in-scope-is-representable")
    os.symlink("payload.bin", root / "selected")
    try:
        os.link(root / "selected", tmp_path / "outside-root-alias", follow_symlinks=False)
    except (OSError, NotImplementedError, ValueError) as exc:
        pytest.skip(f"hardlinking a symlink inode is unsupported on host: {exc}")
    inside, outside = os.lstat(root / "selected"), os.lstat(tmp_path / "outside-root-alias")
    assert stat.S_ISLNK(inside.st_mode) and stat.S_ISLNK(outside.st_mode)
    assert (inside.st_dev, inside.st_ino) == (outside.st_dev, outside.st_ino)
    assert inside.st_nlink >= 2
    # There is exactly one selected symlink: rejection solely from st_nlink
    # would be a false-positive loss of valid archive coverage.
    archive = tmp_path / "single-alias.cmpct"
    _create(root, archive)
    with CMPCT(archive) as reader:
        assert reader.verify() >= 1
        dest = tmp_path / "restored"
        reader.extractall(dest, metadata=False)
    assert os.readlink(dest / "selected") == "payload.bin"
    assert (dest / "payload.bin").read_bytes() == b"one-name-in-scope-is-representable"

def test_regular_file_hardlinks_remain_one_inode(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    data = b"physical-hardlink-owner" * 113
    (root / "a.bin").write_bytes(data)
    try:
        os.link(root / "a.bin", root / "b.bin")
    except OSError as exc:
        pytest.skip(f"host does not support regular hardlinks: {exc}")
    s1, s2 = os.stat(root / "a.bin"), os.stat(root / "b.bin")
    assert (s1.st_dev, s1.st_ino) == (s2.st_dev, s2.st_ino)
    out = tmp_path / "file-hardlinks.cmpct"
    _create(root, out)
    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        dest = tmp_path / "restored"
        reader.extractall(dest, metadata=False)
    assert (dest / "a.bin").read_bytes() == data
    assert (dest / "b.bin").read_bytes() == data
    d1, d2 = os.stat(dest / "a.bin"), os.stat(dest / "b.bin")
    assert (d1.st_dev, d1.st_ino) == (d2.st_dev, d2.st_ino)


def test_supported_tree_reproducibility_and_exact_content(tmp_path):
    root = tmp_path / "source"
    (root / "dir").mkdir(parents=True)
    data = bytes((i * 37 + 11) % 256 for i in range(2000))
    (root / "dir" / "data.bin").write_bytes(data)
    (root / "empty").write_bytes(b"")
    hashes = []
    for n in range(2):
        out = tmp_path / f"repro-{n}.cmpct"
        _create(root, out)
        hashes.append(hashlib.sha256(out.read_bytes()).hexdigest())
        with CMPCT(out) as reader:
            assert reader.verify() >= 1
            assert reader.read("dir/data.bin") == data
            assert reader.read("empty") == b""
            dest = tmp_path / f"extract-{n}"
            reader.extractall(dest, metadata=False)
        assert (dest / "dir" / "data.bin").read_bytes() == data
        assert (dest / "empty").read_bytes() == b""
    assert hashes[0] == hashes[1]
    print("O67_SUPPORTED_TREE_SHA256=" + hashes[0])
