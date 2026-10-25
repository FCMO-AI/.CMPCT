"""O61-D source-exact falsifier: stable NTFS *directory* named-stream loss.

A green test here means an actual product defect was reproduced, not that the
Builder is fit for release. See the prospective O61-D preregistration.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT

_WIN = os.name == "nt"
_STREAM_NAME = "cmpct_o61d"
_STREAM_PAYLOAD = (b"o61d-stable-directory-named-stream-not-a-child-file\x00" * 13)
_NORMAL = bytes(((n * 29 + 17) & 255) for n in range(4096))


def _named_streams_windows(path: Path) -> list[str]:
    """Separate Win32 source oracle; do not call CMPCT's admission helper."""
    assert _WIN
    class StreamData(ctypes.Structure):
        _fields_ = [
            ("StreamSize", ctypes.c_int64),
            ("cStreamName", ctypes.c_wchar * 296),
        ]
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.FindFirstStreamW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(StreamData), wintypes.DWORD
    ]
    api.FindFirstStreamW.restype = wintypes.HANDLE
    api.FindNextStreamW.argtypes = [wintypes.HANDLE, ctypes.POINTER(StreamData)]
    api.FindNextStreamW.restype = wintypes.BOOL
    api.FindClose.argtypes = [wintypes.HANDLE]
    api.FindClose.restype = wintypes.BOOL
    d = StreamData()
    handle = api.FindFirstStreamW(str(path), 0, ctypes.byref(d), 0)
    if handle is None or handle == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "Win32 directory stream enumeration unsupported")
    names = []
    try:
        while True:
            names.append(d.cStreamName)
            if api.FindNextStreamW(handle, ctypes.byref(d)):
                continue
            last = ctypes.get_last_error()
            if last != 38:
                raise OSError(last, "Win32 directory stream enumeration incomplete")
            return names
    finally:
        if not api.FindClose(handle):
            raise OSError(ctypes.get_last_error(), "Win32 stream enumerator close failed")


@pytest.mark.skipif(not _WIN, reason="requires native Windows NTFS directory streams")
def test_nested_directory_named_stream_is_silently_lost_on_o57(tmp_path: Path) -> None:
    src = tmp_path / "input"
    nested = src / "nested"
    nested.mkdir(parents=True)
    (nested / "ordinary.bin").write_bytes(_NORMAL)
    stream = str(nested) + ":" + _STREAM_NAME
    with open(stream, "wb") as dst:
        dst.write(_STREAM_PAYLOAD)
    with open(stream, "rb") as original:
        assert original.read() == _STREAM_PAYLOAD
    observed = _named_streams_windows(nested)
    assert ":" + _STREAM_NAME + ":$DATA" in observed, observed
    assert [x.name for x in nested.iterdir()] == ["ordinary.bin"], (
        "named stream must not masquerade as scanned ordinary file"
    )
    original_hash = hashlib.sha256(_STREAM_PAYLOAD).hexdigest()

    output = tmp_path / "actual-o57.cmpct"
    result = Builder(
        src, workers=1, reproducible=True, reproducible_epoch_ns=0
    ).build(output)
    assert output.is_file() and result["bytes"] == output.stat().st_size
    restored = tmp_path / "restored"
    with CMPCT(output) as reader:
        assert reader.verify() >= 1
        assert reader.read("nested/ordinary.bin") == _NORMAL
        reader.extractall(restored, metadata=False)
    assert (restored / "nested" / "ordinary.bin").read_bytes() == _NORMAL
    assert (restored / "nested").is_dir()
    with pytest.raises(OSError):
        with open(str(restored / "nested") + ":" + _STREAM_NAME, "rb") as stream_reader:
            stream_reader.read()
    assert _named_streams_windows(nested) == observed
    with open(stream, "rb") as original:
        assert hashlib.sha256(original.read()).hexdigest() == original_hash
    print(
        "O61D_DEFECT_CONFIRMED=directory-stream-omitted "
        "source_bytes=" + str(len(_STREAM_PAYLOAD)) +
        " restored_stream=missing archive_sha256=" +
        hashlib.sha256(output.read_bytes()).hexdigest(),
        flush=True,
    )


@pytest.mark.skipif(not _WIN, reason="requires Windows NTFS control")
def test_stable_directory_without_named_stream_round_trips(tmp_path: Path) -> None:
    src = tmp_path / "input"
    nested = src / "nested"
    nested.mkdir(parents=True)
    (nested / "ordinary.bin").write_bytes(_NORMAL)
    output = tmp_path / "ordinary.cmpct"
    Builder(src, workers=1, reproducible=True, reproducible_epoch_ns=0).build(output)
    with CMPCT(output) as reader:
        assert reader.verify() >= 1
        assert reader.read("nested/ordinary.bin") == _NORMAL
        target = tmp_path / "extracted"
        reader.extractall(target, metadata=False)
    assert (target / "nested" / "ordinary.bin").read_bytes() == _NORMAL
    print("O61D_STABLE_CONTROL=exact", flush=True)
