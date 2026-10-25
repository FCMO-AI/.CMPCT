"""Additive physical release-corpus identity: types, bytes, inode groups and xattrs.

This does not replace the historical r24 `tree_sha256` or certify a filesystem
snapshot. It is an independent before/after witness over a quiescent POSIX tree.
Physical inode numbers are used to *discover* groups, never serialized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import struct
from pathlib import Path

DOMAIN = b"CMPCT-r24-release-corpus-semantics-O42-v1\x00"
CHUNK = 1 << 20


def _put(digest, value: bytes) -> None:
    digest.update(struct.pack("<Q", len(value)))
    digest.update(value)


def _xattrs(path) -> tuple[tuple[bytes, bytes], ...]:
    # Unlike a best-effort archive metadata probe, a proof cannot silently skip
    # an unreadable namespace: it must fail rather than assert false equality.
    names = sorted((os.fsencode(key) for key in
                    os.listxattr(path, follow_symlinks=False)))
    return tuple((name, os.getxattr(path, name, follow_symlinks=False))
                 for name in names)


def semantic_release_tree_sha256(root: str | os.PathLike[str], *,
                                 max_entries: int = 1_000_000,
                                 max_depth: int = 256) -> str:
    """Hash the physical input contract without embedding root or inode numbers.

    Supported on POSIX where inode identity and non-following xattr access work.
    A check at two points detects end-state mutation, not transient ABA races.
    Unsupported types, metadata errors and unstable file reads fail closed.
    """
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("O42 physical release witness requires POSIX O_NOFOLLOW")
    if max_entries <= 0 or max_depth < 0:
        raise ValueError("invalid witness resource budget")
    path = os.fspath(root)
    if not stat.S_ISDIR(os.lstat(path).st_mode):
        raise ValueError("release input root must be a real directory")

    h = hashlib.sha256(DOMAIN)
    inode_groups: dict[tuple[int, int], int] = {}
    entry_count = 0

    def walk(directory, parts: tuple[bytes, ...], depth: int) -> None:
        nonlocal entry_count
        children = []
        with os.scandir(directory) as it:
            for item in it:
                if len(children) >= max_entries - entry_count:
                    raise ValueError("release witness entry budget exceeded")
                children.append(item)
        children.sort(key=lambda e: os.fsencode(e.name))
        for item in children:
            entry_count += 1
            name = os.fsencode(item.name)
            rel = parts + (name,)
            st = os.lstat(item.path)
            if not name or name in (b".", b"..") or st.st_ino == 0:
                raise ValueError("unsupported filesystem entry identity")
            # Components are length-delimited: a/b is not the same as a + b.
            h.update(struct.pack("<I", len(rel)))
            for segment in rel:
                _put(h, segment)
            h.update(struct.pack("<Iqqq", st.st_mode & 0o177777,
                                 st.st_mtime_ns, int(st.st_uid), int(st.st_gid)))
            attrs = _xattrs(item.path)
            h.update(struct.pack("<I", len(attrs)))
            for key, value in attrs:
                _put(h, key)
                _put(h, value)

            if stat.S_ISDIR(st.st_mode):
                if depth >= max_depth:
                    raise ValueError("release witness depth budget exceeded")
                h.update(b"D")
                walk(item.path, rel, depth + 1)
            elif stat.S_ISLNK(st.st_mode):
                h.update(b"L")
                _put(h, os.fsencode(os.readlink(item.path)))
            elif stat.S_ISREG(st.st_mode):
                h.update(b"F")
                key = (st.st_dev, st.st_ino)
                if key not in inode_groups:
                    inode_groups[key] = len(inode_groups)
                h.update(struct.pack("<Q", inode_groups[key]))
                # Never follow a late symlink replacement, and confirm the
                # observed physical file still matches its initial stat.
                fd = os.open(item.path, os.O_RDONLY | os.O_NOFOLLOW |
                             getattr(os, "O_CLOEXEC", 0))
                try:
                    pre = os.fstat(fd)
                    if (pre.st_dev, pre.st_ino, pre.st_mode, pre.st_mtime_ns) != (
                            st.st_dev, st.st_ino, st.st_mode, st.st_mtime_ns):
                        raise RuntimeError("release input changed before read")
                    contents = hashlib.sha256()
                    total = 0
                    while True:
                        block = os.read(fd, CHUNK)
                        if not block:
                            break
                        total += len(block)
                        contents.update(block)
                    post = os.fstat(fd)
                    if (post.st_dev, post.st_ino, post.st_mode, post.st_mtime_ns,
                            post.st_size) != (st.st_dev, st.st_ino, st.st_mode,
                                             st.st_mtime_ns, st.st_size) or total != st.st_size:
                        raise RuntimeError("release input changed during read")
                finally:
                    os.close(fd)
                fresh = os.lstat(item.path)
                if (fresh.st_dev, fresh.st_ino, fresh.st_mode, fresh.st_mtime_ns,
                        fresh.st_size) != (st.st_dev, st.st_ino, st.st_mode,
                                          st.st_mtime_ns, st.st_size):
                    raise RuntimeError("release input path changed during read")
                if _xattrs(item.path) != attrs:
                    raise RuntimeError("release input xattrs changed during read")
                h.update(struct.pack("<Q", total))
                h.update(contents.digest())
            else:
                raise ValueError("unsupported release input entry kind")
    walk(path, (), 0)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--record-json", type=Path)
    choice.add_argument("--check-json", type=Path)
    args = parser.parse_args()
    digest = semantic_release_tree_sha256(args.root)
    path = args.record_json or args.check_json
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("tree_sha256"), str):
        raise ValueError("historical release corpus manifest missing")
    if args.record_json:
        prev = manifest.get("semantic_tree_sha256")
        if prev is not None and prev != digest:
            raise RuntimeError("existing release semantic witness disagrees")
        manifest["semantic_tree_sha256"] = digest
        manifest["semantic_witness_schema"] = "cmpct-r24-o42-v1"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        print(json.dumps({"semantic_tree_sha256": digest, "phase": "record"}))
    else:
        if manifest.get("semantic_witness_schema") != "cmpct-r24-o42-v1":
            raise ValueError("release semantic witness version missing")
        if digest != manifest.get("semantic_tree_sha256"):
            raise RuntimeError("release input semantic tree changed during ABBA")
        print(json.dumps({"semantic_tree_sha256": digest, "phase": "verified"}))


if __name__ == "__main__":
    main()
