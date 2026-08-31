"""Authenticated filesystem-semantics bridge for CMPCT revision-25 graph profiles.

G0-G4 and PrefixGraph were deliberately developed as content graphs: their tree identity binds path + bytes,
not the richer filesystem contract that canonical revision 24 preserves. Promotion therefore needs one small,
reader-visible bridge rather than teaching every graph mechanism about modes, ownership, links and xattrs.

The bridge stores a deterministic MessagePack manifest at one reserved logical path. That manifest is itself an
ordinary graph member, so its bytes participate in the selected profile's authentication, recovery and complete-
artifact size. Regular-file content stays owned by the graph; directories, symlinks, hardlink relationships and
portable metadata stay owned here.

Sparse and special files intentionally decline revision-25 admission for now. Canonical product code then emits
the already-supported revision-24 representation instead of flattening a sparse hole or inventing device-file
semantics. This is a compatibility fallback, not a feature loss.

Footnote: keeping this logic outside the graph encoder is deliberate. Encoder similarity/Geometry heuristics may
change aggressively; a reader only needs this bounded manifest grammar and the selected content decoder.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat

import msgpack

from cmpct.path_policy import canonical_logical_path

INTERNAL_ROOT = ".__cmpct_r25_internal__"
FILESYSTEM_MANIFEST = f"{INTERNAL_ROOT}/filesystem-v1.msgpack"
FILESYSTEM_MANIFEST_VERSION = 1
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_MANIFEST_ENTRIES = 65_536
SIGNED_MTIME_MIN = -(1 << 63)
SIGNED_MTIME_MAX = (1 << 63) - 1
UID_GID_MAX = (1 << 32) - 1


class ProfileNotEligible(RuntimeError):
    """Filesystem semantics require canonical revision-24 fallback."""


def safe_relpath(rel: str, *, max_path_bytes: int) -> PurePosixPath:
    """Apply the shared CMPCT lexical policy plus the r25 reserved-namespace rule."""
    if not isinstance(rel, str) or "\\" in rel:
        # Footnote: the shared path policy treats backslash as an archive separator. The r25 manifest writes one
        # normalized slash spelling only, so accepting the alternate spelling would create two grammar forms for
        # one destination path without adding capability.
        raise ProfileNotEligible("r25 path syntax is not canonical")
    try:
        key, parts = canonical_logical_path(rel, max_path_bytes=max_path_bytes)
    except (ValueError, UnicodeError) as exc:
        raise ProfileNotEligible("r25 path syntax is not portable") from exc
    if key != rel:
        raise ProfileNotEligible("r25 path is not in canonical slash form")
    if rel == INTERNAL_ROOT or rel.startswith(INTERNAL_ROOT + "/"):
        raise ProfileNotEligible("source tree collides with the reserved r25 manifest namespace")
    return PurePosixPath(*parts)


def _xattrs(path: Path) -> list[list]:
    values: list[list] = []
    if not hasattr(os, "listxattr"):
        return values
    try:
        names = sorted(os.listxattr(path, follow_symlinks=False))
    except OSError:
        return values
    for name in names:
        try:
            value = os.getxattr(path, name, follow_symlinks=False)
        except OSError:
            continue
        values.append([str(name), bytes(value)])
    return values


def _metadata_fields(path: Path, st: os.stat_result) -> list:
    mtime_ns = int(st.st_mtime_ns)
    uid = int(getattr(st, "st_uid", 0))
    gid = int(getattr(st, "st_gid", 0))
    if not SIGNED_MTIME_MIN <= mtime_ns <= SIGNED_MTIME_MAX:
        raise ProfileNotEligible("r25 filesystem mtime exceeds signed i64 domain")
    if not 0 <= uid <= UID_GID_MAX or not 0 <= gid <= UID_GID_MAX:
        raise ProfileNotEligible("r25 filesystem uid/gid exceeds portable u32 domain")
    return [
        stat.S_IMODE(st.st_mode),
        mtime_ns,
        uid,
        gid,
        _xattrs(path),
    ]


def _is_sparse(st: os.stat_result) -> bool:
    blocks = getattr(st, "st_blocks", None)
    return bool(st.st_size and isinstance(blocks, int) and blocks * 512 < st.st_size)


def capture_filesystem_manifest(
    root: Path,
    *,
    max_path_bytes: int,
    max_profile_files: int,
    max_profile_logical_bytes: int,
    max_entries: int = DEFAULT_MAX_MANIFEST_ENTRIES,
) -> tuple[bytes, list[tuple[Path, str]], dict]:
    """Return manifest bytes, graph-owned regular sources and exact admission statistics."""
    root = Path(root)
    if not root.is_dir():
        raise ProfileNotEligible("r25 source must be a directory tree")
    if not isinstance(max_entries, int) or isinstance(max_entries, bool) or max_entries < 1:
        raise ValueError("max_entries must be a positive integer")

    entries: list[list] = []
    regular_sources: list[tuple[Path, str]] = []
    inode_first: dict[tuple[int, int], str] = {}
    logical_bytes = 0

    def reserve_entry() -> None:
        if len(entries) >= max_entries:
            raise ProfileNotEligible("r25 filesystem manifest entry count exceeds reader policy")

    def walk(abs_dir: Path, prefix: str = "") -> None:
        nonlocal logical_bytes
        with os.scandir(abs_dir) as iterator:
            children = sorted(iterator, key=lambda item: item.name)
        for child in children:
            reserve_entry()
            rel = f"{prefix}/{child.name}" if prefix else child.name
            safe_relpath(rel, max_path_bytes=max_path_bytes)
            path = Path(child.path)
            st = child.stat(follow_symlinks=False)
            fields = _metadata_fields(path, st)

            if stat.S_ISDIR(st.st_mode):
                entries.append([rel, "d", *fields, None])
                walk(path, rel)
                continue
            if stat.S_ISLNK(st.st_mode):
                target = os.readlink(path)
                if "\x00" in target:
                    raise ProfileNotEligible("symlink target contains NUL")
                entries.append([rel, "l", *fields, target])
                continue
            if not stat.S_ISREG(st.st_mode):
                raise ProfileNotEligible(f"r25 does not yet canonicalize special file: {rel}")
            if _is_sparse(st):
                raise ProfileNotEligible(f"r25 defers sparse file to r24: {rel}")

            inode = (int(getattr(st, "st_dev", 0)), int(getattr(st, "st_ino", 0)))
            if st.st_nlink > 1 and inode[1] and inode in inode_first:
                # Hardlink aliases point directly to the first deterministic regular-file owner. This prevents
                # both link chains and cycles and makes read/extract dependency depth exactly one.
                entries.append([rel, "h", *fields, inode_first[inode]])
                continue

            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while True:
                    block = stream.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
            if st.st_nlink > 1 and inode[1]:
                inode_first[inode] = rel
            entries.append([rel, "f", *fields, [int(st.st_size), digest.digest()]])
            regular_sources.append((path, rel))
            logical_bytes += int(st.st_size)
            if logical_bytes > max_profile_logical_bytes:
                raise ProfileNotEligible("r25 logical bytes exceed reader policy")
            if len(regular_sources) > max_profile_files:
                raise ProfileNotEligible("r25 regular-file count exceeds reader policy")

    walk(root)
    manifest = {
        "v": FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    try:
        raw = msgpack.packb(manifest, use_bin_type=True)
    except (UnicodeEncodeError, TypeError, ValueError) as exc:
        # Footnote: Python can represent POSIX names through surrogate escapes that MessagePack text cannot encode
        # portably. Falling back to r24 preserves those bytes instead of lossy-normalizing a path or xattr name.
        raise ProfileNotEligible("r25 filesystem metadata is not portable MessagePack text") from exc
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ProfileNotEligible("r25 filesystem manifest exceeds bounded decode unit")
    return raw, regular_sources, {
        "entries": len(entries),
        "regular_graph_members": len(regular_sources),
        "logical_regular_bytes": logical_bytes,
        "manifest_bytes": len(raw),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target, follow_symlinks=False)
    except OSError:
        # Footnote: staging is creation-time machinery. A cross-device copy is slower but does not change the
        # selected bytes or reader semantics, so it is preferable to adding a second source-tree parser.
        shutil.copyfile(source, target)


def prepare_profile_tree(
    root: Path,
    staging_root: Path,
    *,
    max_path_bytes: int,
    max_profile_files: int,
    max_profile_logical_bytes: int,
    max_entries: int = DEFAULT_MAX_MANIFEST_ENTRIES,
) -> dict:
    raw, regular_sources, stats = capture_filesystem_manifest(
        root,
        max_path_bytes=max_path_bytes,
        max_profile_files=max_profile_files,
        max_profile_logical_bytes=max_profile_logical_bytes,
        max_entries=max_entries,
    )
    staging_root.mkdir(parents=True, exist_ok=True)
    for source, rel in regular_sources:
        _link_or_copy(source, staging_root.joinpath(*PurePosixPath(rel).parts))
    manifest_path = staging_root.joinpath(*PurePosixPath(FILESYSTEM_MANIFEST).parts)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(raw)
    return {"manifest_raw": raw, "manifest": msgpack.unpackb(raw, raw=False), **stats}


def decode_manifest(raw: bytes, *, max_path_bytes: int, max_entries: int) -> dict:
    if not isinstance(raw, bytes) or len(raw) > MAX_MANIFEST_BYTES:
        raise RuntimeError("r25 filesystem manifest exceeds policy")
    try:
        manifest = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=max_entries * 8 + 1024,
            max_map_len=32,
            max_str_len=max_path_bytes,
            max_bin_len=MAX_MANIFEST_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded r25 filesystem manifest") from exc
    if not isinstance(manifest, dict) or manifest.get("v") != FILESYSTEM_MANIFEST_VERSION:
        raise RuntimeError("unsupported r25 filesystem manifest version")
    if manifest.get("profile") != "cmpct-r25-filesystem-manifest-v1":
        raise RuntimeError("unsupported r25 filesystem manifest profile")
    if manifest.get("internal_path") != FILESYSTEM_MANIFEST:
        raise RuntimeError("r25 filesystem manifest internal-path mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) > max_entries:
        raise RuntimeError("r25 filesystem manifest entry-count declaration")

    seen: set[str] = set()
    regular: dict[str, tuple[int, bytes]] = {}
    hardlinks: dict[str, str] = {}
    for row in entries:
        if not isinstance(row, list) or len(row) != 8:
            raise RuntimeError("malformed r25 filesystem manifest entry")
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        try:
            safe_relpath(rel, max_path_bytes=max_path_bytes)
        except ProfileNotEligible as exc:
            raise RuntimeError("unsafe r25 filesystem manifest path") from exc
        if rel in seen:
            raise RuntimeError("duplicate r25 filesystem manifest path")
        if kind not in ("f", "d", "l", "h"):
            raise RuntimeError("unknown r25 filesystem manifest entry kind")
        if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
            raise RuntimeError("r25 filesystem mode declaration")
        if (
            not isinstance(mtime_ns, int)
            or isinstance(mtime_ns, bool)
            or not SIGNED_MTIME_MIN <= mtime_ns <= SIGNED_MTIME_MAX
        ):
            raise RuntimeError("r25 filesystem mtime declaration")
        for value, label in ((uid, "uid"), (gid, "gid")):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= UID_GID_MAX
            ):
                raise RuntimeError(f"r25 filesystem {label} declaration")
        if not isinstance(xattrs, list):
            raise RuntimeError("r25 filesystem xattr declaration")
        for item in xattrs:
            if (
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], bytes)
            ):
                raise RuntimeError("r25 filesystem xattr item")

        if kind == "f":
            if (
                not isinstance(extra, list)
                or len(extra) != 2
                or not isinstance(extra[0], int)
                or isinstance(extra[0], bool)
                or extra[0] < 0
                or not isinstance(extra[1], bytes)
                or len(extra[1]) != 32
            ):
                raise RuntimeError("r25 regular-file identity declaration")
            regular[rel] = (int(extra[0]), bytes(extra[1]))
        elif kind == "d":
            if extra is not None:
                raise RuntimeError("r25 directory carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("r25 symlink target declaration")
        else:
            if not isinstance(extra, str) or extra not in regular:
                # The target must be an already-declared *regular owner*, not merely any earlier path. This
                # removes hardlink chains/cycles and keeps read_member dependency depth bounded at one.
                raise RuntimeError("r25 hardlink target must be an earlier regular-file owner")
            hardlinks[rel] = extra
        seen.add(rel)

    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def entry_map(decoded: dict) -> dict[str, list]:
    return {row[0]: row for row in decoded["manifest"]["entries"]}


def _apply_xattrs(path: Path, items: list[list], *, follow_symlinks: bool) -> None:
    if not hasattr(os, "setxattr"):
        return
    for name, value in items:
        try:
            os.setxattr(path, name, value, follow_symlinks=follow_symlinks)
        except OSError:
            pass


def _unsafe_symlink_target(target: str) -> bool:
    """Reject any target that can escape/root under either POSIX or Windows lexical semantics."""
    posix = PurePosixPath(target)
    windows = PureWindowsPath(target)
    return (
        posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or ".." in posix.parts
        or ".." in windows.parts
    )


def restore_manifest_tree(staging: Path, decoded: dict, *, safe_symlinks: bool = True) -> None:
    """Turn graph-owned regular files into the authenticated user-visible filesystem tree."""
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind != "f":
            continue
        size, expected = row[7]
        if not target.is_file() or target.is_symlink() or target.stat().st_size != int(size):
            raise RuntimeError(f"r25 extracted regular-file shape mismatch: {rel}")
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
        if digest.digest() != bytes(expected):
            raise RuntimeError(f"r25 extracted regular-file identity mismatch: {rel}")

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind == "d":
            target.mkdir(parents=True, exist_ok=True)
        elif kind == "l":
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = row[7]
            if safe_symlinks and _unsafe_symlink_target(link_target):
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

    # Restore children before directory metadata so child creation cannot perturb directory mtimes.
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
        _apply_xattrs(target, xattrs, follow_symlinks=follow)
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
        _apply_xattrs(target, xattrs, follow_symlinks=True)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)))
        except OSError:
            pass
