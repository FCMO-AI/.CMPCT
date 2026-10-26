"""Win32 leaf-handle timestamp restoration when Python lacks no-follow utime.

The built-in os.utime(..., follow_symlinks=False) raises NotImplementedError on
supported Windows Python builds. Avoid falling back to pathname-following utime:
CreateFileW opens the *leaf* reparse point itself and a handle attributes check
rejects it before writing. This is not an ancestor-directory race defense.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


_UNIX_TO_WIN_100NS = 116_444_736_000_000_000
_FILE_WRITE_ATTRIBUTES = 0x00000100
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_SHARE_ALL = 0x00000007
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_ATTRIBUTE_DIRECTORY = 0x00000010


class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", _FILETIME),
        ("ftLastAccessTime", _FILETIME),
        ("ftLastWriteTime", _FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


def _filetime_from_unix_ns(mtime_ns: int) -> _FILETIME:
    """Convert the authenticated Unix mtime into the Windows 100-ns epoch."""
    ticks = int(mtime_ns) // 100 + _UNIX_TO_WIN_100NS
    if not 0 <= ticks < (1 << 64):
        raise OverflowError("mtime is outside FILETIME range")
    return _FILETIME(ticks & 0xFFFFFFFF, ticks >> 32)


def restore_win32_leaf_mtime(path: os.PathLike[str] | str, mtime_ns: int, *, directory: bool) -> None:
    """Write one leaf's mtime through a non-following Win32 file handle.

    On an unsupported/non-Windows host, fail rather than silently follow a
    pathname. Reparse points (symlinks/junctions) and type changes fail
    closed. Parent paths are still resolved by Windows and are NOT race-safe.
    """
    if os.name != "nt":
        raise NotImplementedError("Win32 mtime restoration is Windows-only")

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.SetFileTime.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME), ctypes.POINTER(_FILETIME),
    ]
    kernel.SetFileTime.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL

    handle = kernel.CreateFileW(
        os.fspath(path), _FILE_WRITE_ATTRIBUTES | _FILE_READ_ATTRIBUTES,
        _FILE_SHARE_ALL, None, _OPEN_EXISTING,
        _FILE_FLAG_OPEN_REPARSE_POINT | _FILE_FLAG_BACKUP_SEMANTICS, None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = _BY_HANDLE_FILE_INFORMATION()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        attributes = int(info.dwFileAttributes)
        if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise OSError("cannot restore timestamp through a Win32 reparse point")
        if bool(attributes & _FILE_ATTRIBUTE_DIRECTORY) != bool(directory):
            raise OSError("Win32 mtime destination changed file type")
        stamp = _filetime_from_unix_ns(mtime_ns)
        if not kernel.SetFileTime(handle, None, None, ctypes.byref(stamp)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(handle)
