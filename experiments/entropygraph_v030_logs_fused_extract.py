"""One-session extraction implementation for canonical logs-inverse archives.

The promoted release path historically decoded the authenticated filesystem manifest once for caller-budget/symlink
policy, opened the archive again for V2 extraction, materialized the internal manifest, read/decoded it again, and
then re-read every extracted regular file to SHA-256 it during filesystem restoration. The logs Archive already
SHA-256 verifies every restored logical member. This implementation keeps one authenticated Archive session,
proves its declared regular identities exactly equal the filesystem manifest, restores each value once, and
therefore avoids the second on-disk identity pass. Archive bytes, public selector, locality policy, and release
credit are unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product_base as BASE


def _restore_filesystem_metadata(staging: Path, decoded: dict, *, safe_symlinks: bool) -> None:
    """Apply FS manifest structure/metadata after content identity was proven in the same Archive session.

    Regular-file existence/size is not re-stat'ed here. ``extract`` writes every graph regular only after proving
    that graph ``(size, SHA-256)`` identities exactly equal the authenticated filesystem manifest, and it checks
    each write's returned byte count. Re-reading filesystem shape immediately afterwards therefore adds syscalls
    without adding a new integrity fact. Metadata operations below still fail naturally if publication state is
    unexpectedly missing.
    """
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(FS.INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

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


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = BASE.POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    dst = Path(dst)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    dst.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="cmpct-v030-logs-fused-extract-", dir=dst.parent))
    stage = temp_root / "tree"
    installed = False
    try:
        with LOGS.Archive(archive) as reader:
            paths = reader._paths()
            try:
                manifest_index = paths.index(FS.FILESYSTEM_MANIFEST)
            except ValueError as exc:
                raise RuntimeError("logs canonical profile is missing filesystem manifest") from exc

            member_cache: dict[int, tuple[bytes, int]] = {}
            pack_cache: dict[int, bytes] = {}
            active: set[int] = set()
            manifest_raw, _ = reader._restore_session(
                manifest_index,
                member_cache=member_cache,
                pack_cache=pack_cache,
                active=active,
            )
            decoded = FS.decode_manifest(
                manifest_raw,
                max_path_bytes=LOGS.MAX_PATH_BYTES,
                max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
            )
            graph_regular = {
                str(row[5]): (int(row[2]), bytes(row[3]))
                for row in reader.files
                if str(row[5]) != FS.FILESYSTEM_MANIFEST
            }
            if graph_regular != decoded["regular"]:
                raise RuntimeError("logs fused extraction filesystem/content identity mismatch")
            user_bytes = sum(size for size, _digest in decoded["regular"].values())
            if user_bytes > max_output_bytes:
                raise RuntimeError("logs extraction exceeds caller output budget")
            if safe_symlinks:
                for row in decoded["manifest"]["entries"]:
                    if row[1] != "l":
                        continue
                    parsed = PurePosixPath(row[7])
                    if parsed.is_absolute() or ".." in parsed.parts:
                        raise RuntimeError(f"unsafe r25 symlink target in {row[0]!r}")

            stage.mkdir(parents=True, exist_ok=True)
            prepared_parents: set[Path] = {stage}
            for index, row in enumerate(reader.files):
                rel = str(row[5])
                if rel == FS.FILESYSTEM_MANIFEST:
                    continue
                target = stage.joinpath(*PurePosixPath(rel).parts)
                parent = target.parent
                if parent not in prepared_parents:
                    parent.mkdir(parents=True, exist_ok=True)
                    prepared_parents.add(parent)
                value, _context = reader._restore_session(
                    index,
                    member_cache=member_cache,
                    pack_cache=pack_cache,
                    active=active,
                )
                written = target.write_bytes(value)
                if written != len(value):
                    raise OSError(f"short logs extraction write for {rel!r}: {written} != {len(value)}")

        _restore_filesystem_metadata(stage, decoded, safe_symlinks=safe_symlinks)
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        os.replace(stage, dst)
        installed = True
    finally:
        if not installed and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(temp_root, ignore_errors=True)
