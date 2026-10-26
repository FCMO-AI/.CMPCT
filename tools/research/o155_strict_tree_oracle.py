#!/usr/bin/env python3
"""O155: static exact filesystem-kind/link-topology witness (research, not a snapshot).

Scope: entry raw path bytes, file/symlink/directory type, POSIX mode, regular
file bytes, raw symlink targets and *in-tree* hardlink equivalence classes.
NOT covered: uid/gid, ACL, xattrs, time, sparse physical layout, alternate
streams or hostile concurrent mutation. Never mistake this for release proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


class UnsupportedTreeEntry(ValueError):
    """A special filesystem object is outside this strict witness's scope."""


def _file_hash(path: bytes, initial: os.stat_result, cache: dict) -> str:
    key = (initial.st_dev, initial.st_ino)
    if key in cache:
        return cache[key]
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size) != (
            initial.st_dev, initial.st_ino, initial.st_size
        ) or not stat.S_ISREG(before.st_mode):
            raise OSError("file changed between lstat and open")
        digest = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        after = os.fstat(fd)
        if (
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        ):
            raise OSError("file changed while hashing")
        cache[key] = digest.hexdigest()
        return cache[key]
    finally:
        os.close(fd)


def strict_manifest(root: os.PathLike | str | bytes) -> dict:
    """Canonical, inode-number-free witness for a *quiescent* POSIX tree.

    File and directory traversal cannot guarantee an atomic snapshot against
    malicious renames; use isolated/stable trees or filesystem snapshots.
    """
    root_raw = os.fsencode(root)
    root_stat = os.lstat(root_raw)
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("root must be a real directory, not a symlink")
    rows: list[dict] = []
    owner: dict[tuple[int, int], list[str]] = {}
    file_cache: dict = {}
    seen_dirs = {(root_stat.st_dev, root_stat.st_ino)}
    stack: list[tuple[bytes, bytes]] = [(root_raw, b"")]

    while stack:
        directory, relative_parent = stack.pop()
        with os.scandir(directory) as listing:
            entries = sorted(list(listing), key=lambda e: e.name)
        for entry in entries:
            name = entry.name
            if not isinstance(name, bytes):
                raise AssertionError("bytes scandir contract broken")
            relative = relative_parent + (b"/" if relative_parent else b"") + name
            physical = os.path.join(directory, name)
            info = os.lstat(physical)
            kind_mode = info.st_mode
            record: dict = {
                "path_hex": relative.hex(),
                "mode": stat.S_IMODE(kind_mode),
            }
            if stat.S_ISLNK(kind_mode):
                record["type"] = "symlink"
                record["target_hex"] = os.readlink(physical).hex()
            elif stat.S_ISREG(kind_mode):
                record["type"] = "file"
                record["length"] = info.st_size
                record["sha256"] = _file_hash(physical, info, file_cache)
            elif stat.S_ISDIR(kind_mode):
                record["type"] = "directory"
                inode = (info.st_dev, info.st_ino)
                if inode in seen_dirs:
                    raise ValueError("revisited directory inode; concurrent rename or cycle")
                seen_dirs.add(inode)
                stack.append((physical, relative))
            else:
                raise UnsupportedTreeEntry(
                    f"unsupported filesystem entry at raw path {relative.hex()}"
                )
            if record["type"] in ("file", "symlink"):
                owner.setdefault((info.st_dev, info.st_ino), []).append(relative.hex())
            rows.append(record)

    rows.sort(key=lambda row: bytes.fromhex(row["path_hex"]))
    hardlink_classes = sorted(
        (sorted(paths) for paths in owner.values() if len(paths) > 1),
        key=lambda group: tuple(bytes.fromhex(p) for p in group),
    )
    return {
        "schema": "cmpct-o155-static-posix-tree-witness-v1",
        "scope": "raw paths+types+modes+file bytes+symlink targets+in-tree hardlink partition",
        "root_mode": stat.S_IMODE(root_stat.st_mode),
        "entries": rows,
        "hardlink_classes": hardlink_classes,
    }


def strict_digest(root: os.PathLike | str | bytes) -> tuple[str, dict]:
    manifest = strict_manifest(root)
    encoding = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoding).hexdigest(), manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--manifest", action="store_true", help="include full canonical manifest")
    args = parser.parse_args()
    digest, manifest = strict_digest(args.root)
    summary = {
        "digest": digest,
        "entries": len(manifest["entries"]),
        "hardlink_classes": len(manifest["hardlink_classes"]),
        "scope": manifest["scope"],
    }
    if args.manifest:
        summary["manifest"] = manifest
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
