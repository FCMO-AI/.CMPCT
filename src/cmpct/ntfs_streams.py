"""Win32-only inventory guard for unrepresentable NTFS named data streams.

Revision 24 stores ordinary file bytes and physical hardlink relationships, but
has no representation for additional NTFS named $DATA streams. Never claim a
lossless successful archive when a stable regular source carries those bytes.
This is a source admission control, not an atomic filesystem snapshot.
"""
from __future__ import annotations

import os


def refuse_unsupported_named_streams(
    path: str | os.PathLike[str], *, directory: bool = False
) -> None:
    """Refuse NTFS named $DATA streams that revision 24 cannot reconstruct.

    Regular-file admission (the backward-compatible default) expects the
    ordinary unnamed ::$DATA stream. A *directory* normally has no unnamed
    data stream: an empty FindFirstStreamW enumeration (ERROR_HANDLE_EOF) is
    valid there, but a named stream must fail closed. Both modes are no-ops
    on non-Windows. This is a static inventory check, not a race-proof snapshot.
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
        # O61-D2 confirmed that empty NTFS *directories* produce EOF before
        # the first stream; regular files must still have their default stream.
        if directory and err == 38:  # ERROR_HANDLE_EOF
            return
        raise OSError(err, f"cannot enumerate NTFS source streams: {file_name!r}")

    try:
        while True:
            # K_FILE represents only its unnamed stream. K_DIR represents no
            # stream at all. Never silently publish a complete-looking r24
            # archive after discovering any directory stream (or named file stream).
            if directory or data.cStreamName != "::$DATA":
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
