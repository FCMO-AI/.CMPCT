"""Research-only fresh-root extraction for a CMPCT reader (Linux).

The caller must supply a previously absent directory. Extraction occurs in a
private sibling; a single RENAME_NOREPLACE publishes the fully reconstructed
root. This is an opt-in experiment, not the default extractor or a format change.

Boundary: Linux renameat2 + procfs, same filesystem, stable parent namespace,
cooperative/no hostile same-UID actors. NOT atomic merging, public-path ownership
under concurrent parent rename, crash/power-loss durability, portable extraction,
or a complete security sandbox.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import secrets
import shutil
import time

_O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_RENAME_NOREPLACE = 1
_LIBC = ctypes.CDLL(None, use_errno=True)
_RENAMEAT2 = getattr(_LIBC, "renameat2", None)
if _RENAMEAT2 is not None:
    _RENAMEAT2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    _RENAMEAT2.restype = ctypes.c_int


def _parent_dir_fd(dest: Path) -> tuple[int, str]:
    """Anchor each existing ancestor without following symlinks."""
    if not _O_DIRECTORY or not _O_NOFOLLOW:
        raise NotImplementedError("no-follow directory descriptors required")
    absolute = os.path.abspath(os.fspath(dest))  # lexical, never realpath()
    components = Path(absolute).parts
    leaf = components[-1]
    if leaf in ("", ".", "..", "/"):
        raise ValueError("destination must name a new directory")
    fd = os.open("/", os.O_RDONLY | _O_DIRECTORY)
    try:
        for part in components[1:-1]:
            nxt = os.open(part, os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd, leaf
    except BaseException:
        os.close(fd)
        raise


def _publish(source_fd: int, src: str, parent_fd: int, dst: str) -> None:
    if _RENAMEAT2 is None:
        raise NotImplementedError("atomic no-clobber publication requires renameat2")
    rc = _RENAMEAT2(source_fd, os.fsencode(src), parent_fd, os.fsencode(dst), _RENAME_NOREPLACE)
    if rc:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err), dst)


def _cleanup_private_stage(path: str) -> None:
    """Make archived mode-000 directories removable, never following symlinks."""
    for root, directories, _files in os.walk(path, topdown=True, followlinks=False):
        for directory in directories:
            child = os.path.join(root, directory)
            if not os.path.islink(child):
                os.chmod(child, 0o700, follow_symlinks=False)
    shutil.rmtree(path)


def extract_new_root(reader, dest: Path, *, metadata=True, max_bytes=None,
                     stage_hook=None) -> dict:
    """Reconstruct privately, then atomically publish at a previously absent root.

    stage_hook is a research-only fault/race injection seam; do not use it with
    untrusted callers. The original Reader remains responsible for archive
    decoding, logical pathname validation, and member-integrity checks.
    """
    if _RENAMEAT2 is None or not os.path.exists("/proc/self/fd"):
        raise NotImplementedError("requires Linux renameat2 and procfs")
    started = time.perf_counter_ns()
    parent_fd, leaf = _parent_dir_fd(Path(dest))
    stage_name = ".cmpct-stage-" + secrets.token_hex(12)
    stage_exists = False
    stage_fd = -1
    try:
        if leaf.startswith(".cmpct-stage-"):
            raise ValueError("destination uses reserved staging name")
        os.mkdir(stage_name, mode=0o700, dir_fd=parent_fd)
        stage_exists = True
        stage_fd = os.open(stage_name, os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW, dir_fd=parent_fd)
        os.mkdir("root", mode=0o777, dir_fd=stage_fd)
        staging_root = Path(f"/proc/self/fd/{stage_fd}/root")
        reader.extractall(staging_root, metadata=metadata, max_bytes=max_bytes, safe_symlinks=True)
        if stage_hook is not None:
            stage_hook(staging_root, Path(dest))
        _publish(stage_fd, "root", parent_fd, leaf)
        # The publication is already successful; wrapper-cleanup failure cannot
        # turn an acknowledged commit into a reported abort.
        stage_exists = False
        warning = None
        try:
            os.rmdir(stage_name, dir_fd=parent_fd)
        except OSError as exc:
            warning = f"{exc.__class__.__name__}: {exc.strerror}"
        return {"published": True, "elapsed_ns": time.perf_counter_ns() - started,
                "cleanup_warning": warning}
    finally:
        if stage_fd >= 0:
            os.close(stage_fd)
        if stage_exists:
            try:
                _cleanup_private_stage(f"/proc/self/fd/{parent_fd}/{stage_name}")
            except FileNotFoundError:
                pass
        os.close(parent_fd)
