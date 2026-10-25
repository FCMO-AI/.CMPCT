"""Copy a quiescent corpus without erasing its within-tree hardlink topology.

Research-only helper: do not mutate frozen benchmark inputs or comparisons.
This is *not* an atomic snapshot or a secure copier of an attacker-controlled tree.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


def copytree_with_hardlinks(source: Path, destination: Path) -> Path:
    """Copy contents, relative symlinks, metadata and within-tree regular hardlinks.

    The first source path for an inode is copied conventionally; later paths link to
    that *destination* file. An unrepresentable hardlink fails closed instead of
    becoming an independent copy. Equal bytes on different source inodes stay
    independent; hardlinks outside the source subtree are never followed.
    """
    source = Path(source)
    destination = Path(destination)
    if not stat.S_ISDIR(source.lstat().st_mode):
        raise ValueError("source must be a real directory")

    # Shared across every recursive directory visited by this one copytree call.
    first_destination: dict[tuple[int, int], Path] = {}

    def copy_file(src: str, dst: str) -> str:
        before = os.stat(src, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("only regular file payloads are supported")
        inode = (before.st_dev, before.st_ino)
        first = first_destination.get(inode)
        if first is None:
            shutil.copy2(src, dst, follow_symlinks=False)
            after = os.stat(src, follow_symlinks=False)
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns
            ):
                raise RuntimeError("source changed during corpus copy")
            first_destination[inode] = Path(dst)
        else:
            # Never silently use copy2 as a fallback: that erases the exact topology.
            os.link(first, dst, follow_symlinks=False)
        return str(dst)

    shutil.copytree(source, destination, copy_function=copy_file, symlinks=True)
    return destination
