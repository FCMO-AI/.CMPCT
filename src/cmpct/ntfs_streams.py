"""Win32-only inventory guard for unrepresentable NTFS named data streams.

Revision 24 stores ordinary file bytes and physical hardlink relationships, but
has no representation for additional NTFS named $DATA streams. Never claim a
lossless successful archive when a stable regular source carries those bytes.
This is a source admission control, not an atomic filesystem snapshot.
"""
from __future__ import annotations

import os


def refuse_unsupported_named_streams(path: str | os.PathLike[str]) -> None:
    """Fail closed when an NTFS regular file carries a nondefault data stream.

    The check is a no-op on non-Windows platforms. On Windows, use the native
    directory/stream enumerator rather than ordinary stat/read or colon-name
    heuristics: named streams are not separate files in os.scandir().
    """
    if os.name != "nt":
        return

    import ctypes
    from ctypes import wintypes

    class FindStreamData(ctypes.Structure):
        _fields_ = [("StreamSize", ctypes.c_int64),
                    ("cStreamName", ctypes.c_wchar * 296)]

    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.FindFirstStreamW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(FindStreamData), wintypes.DWORD
    )
    api.FindFirstStreamW.restype = wintypes.HANDLE
    api.FindNextStreamW.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(FindStreamData)
    )
    api.FindNextStreamW.restype = wintypes.BOOL
    api.FindClose.argtypes = (wintypes.HANDLE,)
    api.FindClose.restype = wintypes.BOOL

    file_name = os.fspath(path)
    data = FindStreamData()
    handle = api.FindFirstStreamW(file_name, 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid:
        err = ctypes.get_last_error()
        raise OSError(err, f"cannot enumerate NTFS source streams: {file_name!r}")

    try:
        while True:
            # The one unnamed stream is already represented by the regular
            # K_FILE row. Every other stream name requires unsupported source
            # semantics and must not be silently omitted from a 'success'.
            if data.cStreamName != "::$DATA":
                raise OSError(f"unsupported NTFS named stream on source "
                              f"{file_name!r}: {data.cStreamName!r}; "
                              f"refusing lossy archive")
            if api.FindNextStreamW(handle, ctypes.byref(data)):
                continue
            err = ctypes.get_last_error()
            if err != 38:  # ERROR_HANDLE_EOF: normal stream enumeration end.
                raise OSError(err, f"NTFS stream enumeration failed: {file_name!r}")
            break
    finally:
        if not api.FindClose(handle):
            raise OSError(ctypes.get_last_error(),
                          f"NTFS stream enumeration cleanup failed: {file_name!r}")
