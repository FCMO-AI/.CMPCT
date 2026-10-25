"""O61-D2: independent native Windows false-remedy test for NTFS directory admission."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path

import pytest

from cmpct.ntfs_streams import refuse_unsupported_named_streams


@pytest.mark.skipif(os.name != "nt", reason="native Windows stream API required")
def test_regular_guard_refuses_empty_ntfs_directory(tmp_path: Path) -> None:
    directory = tmp_path / "plain-directory"
    directory.mkdir()
    assert list(directory.iterdir()) == []

    class StreamData(ctypes.Structure):
        _fields_ = [
            ("StreamSize", ctypes.c_int64),
            ("cStreamName", ctypes.c_wchar * 296),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.FindFirstStreamW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(StreamData), wintypes.DWORD
    ]
    kernel.FindFirstStreamW.restype = wintypes.HANDLE
    kernel.FindClose.argtypes = [wintypes.HANDLE]
    kernel.FindClose.restype = wintypes.BOOL
    data = StreamData()
    handle = kernel.FindFirstStreamW(str(directory), 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle is not None and handle != invalid:
        try:
            first = data.cStreamName
            print("O61D2_EMPTY_DIRECTORY_FIRST_STREAM=" + repr(first), flush=True)
            pytest.fail("O61-D2 prediction falsified: plain directory enumerated a data stream")
        finally:
            assert kernel.FindClose(handle), "Win32 stream handle leak"
    error = ctypes.get_last_error()
    print("O61D2_EMPTY_DIRECTORY_WIN32_ERROR=" + str(error), flush=True)
    assert error in (2, 38), ("unexpected native enumeration failure", error)

    with pytest.raises(OSError) as caught:
        refuse_unsupported_named_streams(directory)
    assert caught.value.errno in (2, 38), (
        "unexpected O57 regular-file guard failure on legitimate NTFS directory",
        repr(caught.value),
    )
    file = directory / "regular.bin"
    file.write_bytes(b"o61d2-regular-control")
    refuse_unsupported_named_streams(file)  # Existing original regular-source control.
    assert file.read_bytes() == b"o61d2-regular-control"
    print(
        "O61D2_FALSE_REMEDY_CONFIRMED=naive-O57-guard-refuses-plain-directory"
        " legitimate-file-control=accepted",
        flush=True,
    )
