"""Independent, opt-in filesystem-semantics oracle for CMPCT evidence.

Version 1 commits to relative raw filesystem names, entry type, file bytes,
symlink-target bytes and within-tree hardlink equivalence. It deliberately does
NOT certify permissions, ACLs, xattrs, mtime, sparse physical layout, device
nodes, directory ownership, snapshot isolation or absence of concurrent races.

This is a correctness/evidence instrument, not an r24 archive-format change.
"""

from __future__ import annotations

import hashlib
import os
import stat
import struct
from pathlib import Path

_DOMAIN = b"CMPCT-fs-semantics-v1\x00"
_BUFFER = 1 << 20


class UnsupportedFilesystemEntry(ValueError):
    """Fail closed rather than making unsupported physical types equal."""


def semantic_tree_digest_v1(
    root: str | os.PathLike[str],
    *,
    max_entries: int = 1_000_000,
    max_depth: int = 256,
    max_path_bytes: int = 1 << 20,
) -> str:
    """Return a source-root-independent SHA256 of the documented tree semantics.

    Hardlink identities are canonical ordinal groups, never raw ``st_ino`` or
    ``st_dev`` numbers. A hardlink to an out-of-tree path has no in-tree alias,
    and is intentionally indistinguishable from a singleton regular file.

    This checks inode identity around file reads but is NOT a filesystem
    snapshot, a safe concurrent mutation boundary or a physical containment
    mechanism. Supply a quiescent tree for authoritative reconstruction proof.
    """
    if max_entries < 0 or max_depth < 0 or max_path_bytes <= 0:
        raise ValueError("filesystem oracle bounds must be nonnegative")
    path = os.fspath(root)
    root_st = os.lstat(path)
    if not stat.S_ISDIR(root_st.st_mode):
        raise ValueError("oracle root must be a real directory, not a symlink")

    digest = hashlib.sha256(_DOMAIN)
    groups: dict[tuple[int, int], int] = {}
    next_group = 0
    entries = 0

    def append_path(parts: tuple[bytes, ...]) -> None:
        nonlocal entries
        entries += 1
        if entries > max_entries:
            raise ValueError("filesystem oracle entry budget exceeded")
        if sum(len(name) for name in parts) > max_path_bytes:
            raise ValueError("filesystem oracle relative-name byte budget exceeded")
        digest.update(struct.pack("<I", len(parts)))
        for name in parts:
            digest.update(struct.pack("<I", len(name)))
            digest.update(name)

    def scan(directory: str | bytes, parts: tuple[bytes, ...], depth: int) -> None:
        nonlocal next_group
        # Sorting each directory by filesystem bytes makes traversal independent
        # of readdir order while retaining POSIX non-UTF-8 spelling exactly.
        with os.scandir(directory) as it:
            children = sorted(it, key=lambda item: os.fsencode(item.name))
        for item in children:
            name = os.fsencode(item.name)
            if not name or name in (b".", b".."):
                raise ValueError("invalid filesystem entry name")
            rel = parts + (name,)
            st = item.stat(follow_symlinks=False)
            if stat.S_ISDIR(st.st_mode):
                if depth >= max_depth:
                    raise ValueError("filesystem oracle depth budget exceeded")
                digest.update(b"D")
                append_path(rel)
                scan(item.path, rel, depth + 1)
            elif stat.S_ISLNK(st.st_mode):
                # lstat-first branch order is critical: is_file/is_dir follow
                # symlinks and cause the exact false equivalence this court tests.
                target = os.readlink(item.path)
                target_bytes = os.fsencode(target)
                digest.update(b"L")
                append_path(rel)
                digest.update(struct.pack("<Q", len(target_bytes)))
                digest.update(target_bytes)
            elif stat.S_ISREG(st.st_mode):
                flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
                flags |= getattr(os, "O_NOFOLLOW", 0)
                flags |= getattr(os, "O_CLOEXEC", 0)
                fd = os.open(item.path, flags)
                try:
                    before = os.fstat(fd)
                    if (not stat.S_ISREG(before.st_mode) or
                        (before.st_dev, before.st_ino) != (st.st_dev, st.st_ino)):
                        raise ValueError("file changed identity before read")
                    content = hashlib.sha256()
                    total = 0
                    while True:
                        block = os.read(fd, _BUFFER)
                        if not block:
                            break
                        total += len(block)
                        content.update(block)
                    after = os.fstat(fd)
                    if ((after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
                            or total != before.st_size or total != after.st_size):
                        raise ValueError("file changed identity or size during read")
                finally:
                    os.close(fd)
                # Some platforms/filesystems do not expose usable file IDs.
                # A zero-valued inode could conflate all independent files, so
                # fail closed instead of claiming hardlink fidelity.
                if not st.st_ino:
                    raise UnsupportedFilesystemEntry(
                        "filesystem does not expose stable hardlink identifiers"
                    )
                key = (st.st_dev, st.st_ino)
                if key not in groups:
                    groups[key] = next_group
                    next_group += 1
                digest.update(b"F")
                append_path(rel)
                digest.update(struct.pack("<Q", groups[key]))
                digest.update(struct.pack("<Q", total))
                digest.update(content.digest())
            else:
                raise UnsupportedFilesystemEntry(
                    "oracle cannot certify special filesystem entries"
                )

    scan(path, (), 0)
    return digest.hexdigest()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--max-entries", type=int, default=1_000_000)
    parser.add_argument("--max-depth", type=int, default=256)
    args = parser.parse_args()
    print(semantic_tree_digest_v1(args.root, max_entries=args.max_entries,
                                  max_depth=args.max_depth))
