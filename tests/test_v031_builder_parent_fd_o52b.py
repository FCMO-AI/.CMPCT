"""O52b independent POSIX primitive: final O_NOFOLLOW does not guard ancestor traversal.

An already-held trusted directory fd and per-component O_NOFOLLOW can detect
an ancestor path changed to a symlink. This is not a CMPCT Builder patch.
"""
from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.name != "posix"
    or not hasattr(os, "O_NOFOLLOW")
    or not hasattr(os, "O_DIRECTORY")
    or os.open not in os.supports_dir_fd,
    reason="POSIX descriptor-relative O_NOFOLLOW/O_DIRECTORY challenge",
)
def test_final_only_nofollow_leaks_via_switched_parent_but_fd_walk_refuses(
    tmp_path: Path,
):
    src = tmp_path / "source"
    outer = tmp_path / "outside"
    src.mkdir()
    outer.mkdir()
    (src / "child").mkdir()

    trusted = b"INSIDE_ROOT_REFERENCE_BYTES"
    external = b"OUTSIDE_ROOT_REFERENCE_BYTES"
    (src / "child" / "data.bin").write_bytes(trusted)
    (outer / "data.bin").write_bytes(external)

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    regular_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(src / "child" / "data.bin", regular_flags), "rb") as stable:
        assert stable.read() == trusted
    print("O52B_STABLE_NOFOLLOW=INSIDE")

    root_fd = os.open(src, directory_flags)
    child_fd = -1
    try:
        # Pin the trusted child *before* the actor substitutes the namespace.
        child_fd = os.open("child", directory_flags, dir_fd=root_fd)
        (src / "child").rename(src / "renamed-original-child")
        os.symlink(outer, src / "child", target_is_directory=True)
        assert (src / "child").is_symlink()

        # Only the final name is protected. An ancestor symlink still resolves.
        with os.fdopen(os.open(src / "child" / "data.bin", regular_flags), "rb") as naive:
            got = naive.read()
            assert got == external, (got, external)
            assert got != trusted
        print("O52B_FINAL_ONLY_NOFOLLOW=OUTSIDE")

        # A directory-walking implementation checks every ancestor path.
        with pytest.raises(OSError) as exc:
            fd = os.open("child", directory_flags, dir_fd=root_fd)
            os.close(fd)
        assert exc.value.errno in (errno.ENOTDIR, errno.ELOOP), exc.value
        print("O52B_ANCHORED_ANCESTOR_REJECTION=YES errno=" + str(exc.value.errno))

        # Previously pinned source-tree child inode remains the original, not
        # the renamed source path's new alias to an untrusted directory.
        with os.fdopen(
            os.open("data.bin", regular_flags, dir_fd=child_fd), "rb"
        ) as pinned:
            got = pinned.read()
            assert got == trusted
            assert got != external
        print("O52B_PINNED_CHILD_FD=INSIDE")
    finally:
        if child_fd >= 0:
            os.close(child_fd)
        os.close(root_fd)
