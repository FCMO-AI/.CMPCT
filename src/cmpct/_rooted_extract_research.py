"""Experimental POSIX directory-capability extraction for exact r24 Reader inputs.

NOT the default CMPCT extractor or an established cross-platform security boundary.
This source is exercised against authentic Builder/Reader archives in the accompanying
science court. In particular, an opened directory inode can itself be *moved* by an
actor with rename permission; fd-relative traversal does not establish immutable
lexical containment under such an actor.
"""
from __future__ import annotations

import contextlib
import hashlib
import ntpath
import os
from pathlib import Path
import secrets
import stat

from .codec import K_DIR, K_FILE, K_HARDLINK, K_SYMLINK
from .path_policy import canonical_logical_path


def _require_posix() -> None:
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise NotImplementedError("experimental capability-root extraction requires POSIX no-follow directories")
    for fn in (os.open, os.mkdir, os.unlink, os.link, os.symlink, os.stat):
        if fn not in os.supports_dir_fd:
            raise NotImplementedError("experimental capability-root extraction requires dir_fd operations")


@contextlib.contextmanager
def _parent_fd(root_fd: int, parts: tuple[str, ...], *, create: bool = True):
    """Open all parent components relative to the already pinned root, never following links."""
    fd = os.dup(root_fd)
    try:
        for component in parts[:-1]:
            if create:
                try:
                    os.mkdir(component, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    finally:
        os.close(fd)


def _safe_symlink_target(raw: bytes) -> str:
    target = os.fsdecode(raw)
    normalized = target.replace("\\", "/")
    drive, _ = ntpath.splitdrive(normalized)
    if not target or normalized.startswith("/") or drive or any(c == ".." for c in normalized.split("/")):
        raise IOError("unsafe archived symlink target")
    return target


def extract_rooted_research(
    reader,
    destination: Path,
    *,
    max_member_bytes: int = 64 * 1024 * 1024,
    max_total_bytes: int = 512 * 1024 * 1024,
    before_member=None,
    after_parent_open=None,
) -> None:
    """Research-only exact extraction for bounded members on POSIX.

    Rejects non-POSIX platforms and over-budget logical files. Uses Reader.read()
    (full member materialization) and intentionally does *not* claim bounded RSS,
    sparse-hole fidelity, xattr/ownership restoration or race-proof lexical paths.
    Hooks are strictly for deterministic tests, not production API.
    """
    _require_posix()
    if max_member_bytes < 0 or max_total_bytes < 0:
        raise ValueError("negative extraction budget")
    rows = []
    by_name = {}
    seen = set()
    symlinks = set()
    total = 0
    for row in reader.files:
        key, parts = canonical_logical_path(row[0])
        if key in seen:
            raise IOError("duplicate canonical archive path")
        seen.add(key)
        rows.append((row, parts))
        by_name[key] = row
        if row[1] == K_SYMLINK:
            symlinks.add(key)
        if row[1] != K_DIR:
            size = int(row[4])
            if size < 0 or size > max_member_bytes:
                raise IOError("member exceeds rooted extraction budget")
            total += size
            if total > max_total_bytes:
                raise IOError("tree exceeds rooted extraction budget")
    for row, parts in rows:
        for i in range(1, len(parts)):
            if "/".join(parts[:i]) in symlinks:
                raise IOError("archive symlink used as parent path")
        if row[1] == K_HARDLINK:
            target_key, _ = canonical_logical_path(row[6][0])
            if target_key not in by_name or by_name[target_key][1] != K_FILE:
                raise IOError("hardlink has no regular owner")

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root_fd = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Directories are created before file materialization, but opened afresh
        # with O_NOFOLLOW on each use. No pathname resolved under a parent
        # directory may silently switch into a preexisting link.
        for row, parts in rows:
            if row[1] != K_DIR:
                continue
            with _parent_fd(root_fd, parts) as pfd:
                try:
                    os.mkdir(parts[-1], 0o700, dir_fd=pfd)
                except FileExistsError:
                    pass
                fd = os.open(parts[-1], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
                os.close(fd)

        # Extract regular owners before aliases regardless of archive ordering.
        for row, parts in rows:
            if row[1] in (K_DIR, K_HARDLINK, K_SYMLINK):
                continue
            if before_member:
                before_member(row[0])
            raw = reader.read(row[0])
            if len(raw) != row[4] or hashlib.sha256(raw).digest() != reader.file_sha256(row[0]):
                raise IOError("logical SHA mismatch before publication")
            with _parent_fd(root_fd, parts) as pfd:
                if after_parent_open:
                    after_parent_open(row[0])
                name = ".cmpct-rooted-" + secrets.token_hex(12)
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=pfd)
                published = False
                try:
                    view = memoryview(raw)
                    try:
                        while view:
                            n = os.write(fd, view)
                            if n <= 0:
                                raise IOError("short rooted write")
                            view = view[n:]
                    finally:
                        view.release()
                    os.fchmod(fd, row[2] & 0o7777)
                    try:
                        os.utime(fd, ns=(row[3], row[3]))
                    except OSError:
                        pass
                    os.close(fd)
                    fd = -1
                    os.replace(name, parts[-1], src_dir_fd=pfd, dst_dir_fd=pfd)
                    published = True
                finally:
                    if fd >= 0:
                        os.close(fd)
                    if not published:
                        try:
                            os.unlink(name, dir_fd=pfd)
                        except FileNotFoundError:
                            pass

        for row, parts in rows:
            if row[1] != K_HARDLINK:
                continue
            _, owner_parts = canonical_logical_path(row[6][0])
            with _parent_fd(root_fd, owner_parts, create=False) as opd:
                owner_fd = os.open(owner_parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=opd)
                try:
                    expected = os.fstat(owner_fd)
                    if not stat.S_ISREG(expected.st_mode):
                        raise IOError("hardlink owner is not a regular file")
                    with _parent_fd(root_fd, parts) as pfd:
                        try:
                            os.unlink(parts[-1], dir_fd=pfd)
                        except FileNotFoundError:
                            pass
                        os.link(owner_parts[-1], parts[-1], src_dir_fd=opd,
                                dst_dir_fd=pfd, follow_symlinks=False)
                        got = os.stat(parts[-1], dir_fd=pfd, follow_symlinks=False)
                        if (got.st_dev, got.st_ino) != (expected.st_dev, expected.st_ino):
                            os.unlink(parts[-1], dir_fd=pfd)
                            raise IOError("hardlink owner changed concurrently")
                finally:
                    os.close(owner_fd)

        for row, parts in rows:
            if row[1] != K_SYMLINK:
                continue
            raw = reader.read(row[0])
            if len(raw) != row[4] or hashlib.sha256(raw).digest() != reader.file_sha256(row[0]):
                raise IOError("symlink SHA mismatch")
            target = _safe_symlink_target(raw)
            with _parent_fd(root_fd, parts) as pfd:
                try:
                    os.unlink(parts[-1], dir_fd=pfd)
                except FileNotFoundError:
                    pass
                os.symlink(target, parts[-1], dir_fd=pfd)

        # Directory metadata is applied last through fd-only operations. This
        # court does not claim xattrs/ownership or symlink metadata restoration.
        for row, parts in reversed(rows):
            if row[1] != K_DIR:
                continue
            with _parent_fd(root_fd, parts, create=False) as pfd:
                dfd = os.open(parts[-1], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
                try:
                    os.fchmod(dfd, row[2] & 0o7777)
                    try:
                        os.utime(dfd, ns=(row[3], row[3]))
                    except OSError:
                        pass
                finally:
                    os.close(dfd)
    finally:
        os.close(root_fd)
