"""Explicit POSIX xattr provider, with a bounded native Darwin fallback.

CPython on macOS may expose no os.{list,get,set}xattr even when libSystem does.
Keep Python's native interface as the first choice (and test injection seam);
use Apple's syscall ABI *only* on Darwin when that interface is absent.

No silent truncation: a changing list/value is retried briefly, then raises.
This module does not claim an atomic source filesystem snapshot.
"""
from __future__ import annotations

import ctypes
import errno
import functools
import os
import sys

_DARWIN = sys.platform == "darwin"
_NOFOLLOW = 0x0001  # <sys/xattr.h> XATTR_NOFOLLOW on Darwin.
_MAX_NAME_BYTES = 4 * 1024 * 1024
_MAX_VALUE_BYTES = 64 * 1024 * 1024
_MAX_ATTEMPTS = 3


def can_list() -> bool:
    return hasattr(os, "listxattr") or _DARWIN


def can_set() -> bool:
    if hasattr(os, "setxattr"):
        return True
    if not _DARWIN:
        return False
    try:
        # Strict Reader must reject unavailable destination capability *before*
        # creating output, not discover a missing native ABI during late restore.
        _darwin_api()
    except OSError:
        return False
    return True


@functools.lru_cache(maxsize=1)
def _darwin_api():
    if not _DARWIN:
        raise OSError(errno.ENOSYS, "Darwin xattr bridge unavailable")
    # libSystem is linked into the process; errno is copied by ctypes.
    library = ctypes.CDLL(None, use_errno=True)
    try:
        listing = library.listxattr
        getter = library.getxattr
        setter = library.setxattr
    except AttributeError as exc:
        # We promised the Darwin provider; a missing libSystem symbol is not
        # proof that the SOURCE filesystem lacks xattrs. O65 must fail closed
        # rather than interpret ENOSYS as a legitimate empty metadata table.
        raise OSError(errno.EIO, "Darwin native xattr entrypoint missing") from exc

    listing.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    listing.restype = ctypes.c_ssize_t
    getter.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int,
    ]
    getter.restype = ctypes.c_ssize_t
    setter.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int,
    ]
    setter.restype = ctypes.c_int
    return listing, getter, setter


def _path_bytes(path):
    result = os.fsencode(path)
    if b"\x00" in result:
        raise ValueError("NUL in xattr path")
    return result


def _name_bytes(name):
    # Darwin names are UTF-8 (not arbitrary filesystem-encoded byte strings).
    # Reject malformed names rather than lossy roundtrip through MessagePack.
    if isinstance(name, bytes):
        name.decode("utf-8", "strict")
        result = name
    else:
        result = name.encode("utf-8", "strict")
    if not result or b"\x00" in result:
        raise ValueError("empty/NUL xattr name")
    return result


def _checked(result, path):
    if result < 0:
        error = ctypes.get_errno() or errno.EIO
        raise OSError(error, os.strerror(error), os.fspath(path))
    return int(result)


def _bounded_copy(path, probe, read, limit):
    # Darwin's size-probe and read are separate syscalls: source can mutate.
    # ERANGE is evidence of a race, not evidence of absent attributes.
    for attempt in range(_MAX_ATTEMPTS):
        needed = _checked(probe(), path)
        if needed > limit:
            raise OSError(errno.E2BIG, "xattr exceeds bounded provider limit", os.fspath(path))
        buf = ctypes.create_string_buffer(max(needed, 1))
        try:
            got = _checked(read(buf, needed), path)
        except OSError as exc:
            if exc.errno == errno.ERANGE and attempt + 1 < _MAX_ATTEMPTS:
                continue
            raise
        if got > needed:
            raise OSError(errno.EIO, "xattr size changed across native read", os.fspath(path))
        return buf.raw[:got]
    raise OSError(errno.ERANGE, "xattr changed during bounded read", os.fspath(path))


def listxattr(path, *, follow_symlinks=False):
    if hasattr(os, "listxattr"):
        return os.listxattr(path, follow_symlinks=follow_symlinks)
    listing, _, _ = _darwin_api()
    encoded = _path_bytes(path)
    options = 0 if follow_symlinks else _NOFOLLOW
    raw = _bounded_copy(
        path,
        lambda: listing(encoded, None, 0, options),
        lambda buf, size: listing(encoded, buf, size, options),
        _MAX_NAME_BYTES,
    )
    if not raw:
        return []
    if not raw.endswith(b"\x00"):
        raise OSError(errno.EIO, "unterminated native xattr name list", os.fspath(path))
    names = raw[:-1].split(b"\x00")
    if any(not name for name in names) or len(names) != len(set(names)):
        raise OSError(errno.EIO, "ambiguous native xattr name list", os.fspath(path))
    return [name.decode("utf-8", "strict") for name in names]


def getxattr(path, name, *, follow_symlinks=False):
    if hasattr(os, "getxattr"):
        return os.getxattr(path, name, follow_symlinks=follow_symlinks)
    _, getter, _ = _darwin_api()
    encoded = _path_bytes(path)
    key = _name_bytes(name)
    options = 0 if follow_symlinks else _NOFOLLOW
    return _bounded_copy(
        path,
        lambda: getter(encoded, key, None, 0, 0, options),
        lambda buf, size: getter(encoded, key, buf, size, 0, options),
        _MAX_VALUE_BYTES,
    )


def setxattr(path, name, value, *, follow_symlinks=False):
    if hasattr(os, "setxattr"):
        return os.setxattr(path, name, value, follow_symlinks=follow_symlinks)
    _, _, setter = _darwin_api()
    raw = bytes(value)
    if len(raw) > _MAX_VALUE_BYTES:
        raise OSError(errno.E2BIG, "xattr exceeds bounded provider limit", os.fspath(path))
    encoded = _path_bytes(path)
    key = _name_bytes(name)
    options = 0 if follow_symlinks else _NOFOLLOW
    # Keep the buffer alive across the synchronous syscall; size excludes NUL.
    buf = ctypes.create_string_buffer(raw, len(raw) + 1)
    _checked(setter(encoded, key, buf, len(raw), 0, options), path)
