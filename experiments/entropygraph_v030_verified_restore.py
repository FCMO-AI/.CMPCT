"""Verified-staging filesystem restoration for the CMPCT v0.30 release product.

The canonical r25 release streamer authenticates every reconstructed content-graph member before returning a
caller-owned staging tree.  The ordinary filesystem bridge deliberately remains defensive for callers that hand
it an arbitrary staging directory: it re-hashes every regular file before applying metadata and links.

The promoted extraction path has stronger provenance than that generic entry point.  Re-reading every file after
``release_reader_policy.extract_verified_into_staging`` duplicates a full content pass, especially hurting large
ML/model artifacts.  This helper keeps the filesystem bridge as the single grammar/metadata owner while replacing
only the already-proven digest pass with bounded shape checks.  It may be called *only* after the verified streamer
has returned successfully for the same archive/staging tree.

No archive grammar, digest, locality, resource limit, link rule, rollback rule, or publication rule changes here.
The authentication is moved from "stream then hash again" to "authenticated stream once, shape-check before
metadata", not removed.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import shutil

from experiments import entropygraph_v030_product_fs as FS


def restore_verified_manifest_tree(staging: Path, decoded: dict, *, safe_symlinks: bool = True) -> None:
    """Restore an r25 manifest after the release streamer authenticated the staging bytes.

    ``staging`` is unpublished and transaction-owned by the caller.  Regular-file content identity has already
    been checked against the authenticated graph by the release streamer; this function therefore checks only
    path/type/size before applying the exact existing FS metadata/link policy.
    """
    staging = Path(staging)
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(FS.INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

    # Preserve a cheap structural guard after authenticated streaming.  The generic FS entry point continues to
    # perform its independent digest pass for callers without verified-stream provenance.
    for row in entries:
        rel, kind = row[0], row[1]
        if kind != "f":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        size, _expected_digest = row[7]
        if not target.is_file() or target.is_symlink() or target.stat().st_size != int(size):
            raise RuntimeError(f"r25 extracted regular-file shape mismatch: {rel}")

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind == "d":
            target.mkdir(parents=True, exist_ok=True)
        elif kind == "l":
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = row[7]
            parsed = PurePosixPath(link_target)
            if safe_symlinks and (parsed.is_absolute() or ".." in parsed.parts):
                raise RuntimeError(f"unsafe r25 symlink target in {rel!r}")
            target.unlink(missing_ok=True)
            os.symlink(link_target, target)
        elif kind == "h":
            target.parent.mkdir(parents=True, exist_ok=True)
            owner = staging.joinpath(*PurePosixPath(row[7]).parts)
            if not owner.is_file() or owner.is_symlink():
                raise RuntimeError(f"r25 hardlink owner is not materialized: {row[7]}")
            target.unlink(missing_ok=True)
            os.link(owner, target)

    # Restore children before directory metadata so child creation cannot perturb directory mtimes.  These are
    # the exact operations owned by product_fs.restore_manifest_tree; only its redundant regular-file hash pass is
    # intentionally absent here.
    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        if kind == "d":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        follow = kind != "l"
        if follow:
            try:
                os.chmod(target, int(mode), follow_symlinks=False)
            except OSError:
                pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid), follow_symlinks=follow)
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=follow)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)), follow_symlinks=follow)
        except OSError:
            pass

    directories = sorted(
        (row for row in entries if row[1] == "d"),
        key=lambda item: item[0].count("/"),
        reverse=True,
    )
    for row in directories:
        rel, _kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        target = staging.joinpath(*PurePosixPath(rel).parts)
        try:
            os.chmod(target, int(mode))
        except OSError:
            pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid))
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=True)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)))
        except OSError:
            pass
