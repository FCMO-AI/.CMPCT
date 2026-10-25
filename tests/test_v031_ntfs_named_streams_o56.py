"""O56 research: authentic Win32 NTFS named $DATA stream source completeness.

This is a falsifier, not a format change. Exact-product r24 Builder/Reader run
against stable source files; independent native Win32 API enumerates NTFS streams.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT


_STREAM = "cmpct_o56"
_DEFAULT = bytes((i * 13 + i // 17 + 3) & 255 for i in range(4096))
_NAMED = b"o56-named-stream-not-part-of-the-ordinary-file-" * 7 + b"\x00\xff"
_EVIDENCE = Path(os.environ.get("O56_EVIDENCE", "o56-observations.jsonl"))


class _WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_int64), ("cStreamName", ctypes.c_wchar * 296)]


def _streams(path: Path) -> dict[str, int]:
    """Use Windows' stream-enumeration API, not ordinary pathlib iteration."""
    assert os.name == "nt", "O56 requires genuine Windows named-stream semantics"
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.FindFirstStreamW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(_WIN32_FIND_STREAM_DATA), wintypes.DWORD,
    ]
    api.FindFirstStreamW.restype = wintypes.HANDLE
    api.FindNextStreamW.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_WIN32_FIND_STREAM_DATA),
    ]
    api.FindNextStreamW.restype = wintypes.BOOL
    api.FindClose.argtypes = [wintypes.HANDLE]
    api.FindClose.restype = wintypes.BOOL
    record = _WIN32_FIND_STREAM_DATA()
    handle = api.FindFirstStreamW(str(path), 0, ctypes.byref(record), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid:
        err = ctypes.get_last_error()
        raise OSError(err, f"FindFirstStreamW failed for {path}")
    found: dict[str, int] = {}
    try:
        while True:
            found[str(record.cStreamName)] = int(record.StreamSize)
            if api.FindNextStreamW(handle, ctypes.byref(record)):
                continue
            err = ctypes.get_last_error()
            if err != 38:  # ERROR_HANDLE_EOF means successful enumeration end.
                raise OSError(err, f"FindNextStreamW failed for {path}")
            break
    finally:
        if not api.FindClose(handle):
            raise OSError(ctypes.get_last_error(), "FindClose failed")
    assert "::$DATA" in found, found
    return found


def _record(payload: dict) -> None:
    _EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with _EVIDENCE.open("a", encoding="utf-8") as writer:
        writer.write(json.dumps(payload, sort_keys=True) + "\n")


@pytest.mark.parametrize("with_hardlink", [False, True])
def test_authentic_ntfs_named_stream_omitted_from_successful_r24(
    tmp_path: Path, with_hardlink: bool,
) -> None:
    """Original Builder accepts source but restored file lacks actual NTFS ADS."""
    assert os.name == "nt"
    root = tmp_path / "source"
    root.mkdir()
    original = root / "owner.bin"
    original.write_bytes(_DEFAULT)
    name = str(original) + ":" + _STREAM
    with open(name, "wb") as writer:
        writer.write(_NAMED)
    assert original.stat().st_size == len(_DEFAULT)
    with open(name, "rb") as reader:
        assert reader.read() == _NAMED
    if with_hardlink:
        alias = root / "alias.bin"
        os.link(original, alias)
        assert os.path.samefile(original, alias)
        with open(str(alias) + ":" + _STREAM, "rb") as reader:
            assert reader.read() == _NAMED
        assert (root / "alias.bin").stat().st_size == len(_DEFAULT)

    source_streams = _streams(original)
    assert source_streams[":" + _STREAM + ":$DATA"] == len(_NAMED), source_streams

    archive = tmp_path / "complete.cmpct"
    Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
    assert archive.exists()
    restored = tmp_path / "restored"
    with CMPCT(archive) as reader:
        assert reader.verify() >= 1
        assert reader.read("owner.bin") == _DEFAULT
        if with_hardlink:
            assert reader.read("alias.bin") == _DEFAULT
            assert sum(row[1] == K_HARDLINK for row in reader.index["files"]) == 1
        reader.extractall(restored, metadata=False)

    result = restored / "owner.bin"
    assert result.read_bytes() == _DEFAULT
    if with_hardlink:
        assert os.path.samefile(result, restored / "alias.bin")
    source_streams_after = _streams(original)
    restored_streams = _streams(result)
    assert source_streams_after == source_streams
    observation = {
        "kind": "hardlink_ads" if with_hardlink else "regular_ads",
        "source_streams": source_streams,
        "restored_streams": restored_streams,
        "ordinary_sha256": hashlib.sha256(_DEFAULT).hexdigest(),
        "named_sha256": hashlib.sha256(_NAMED).hexdigest(),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
        "result": ("silent_named_stream_loss" if
                   ":" + _STREAM + ":$DATA" not in restored_streams else
                   "named_stream_survived"),
    }
    _record(observation)
    assert ":" + _STREAM + ":$DATA" not in restored_streams, observation


def test_ordinary_ntfs_file_control_reconstructs_without_new_stream(tmp_path: Path) -> None:
    """Positive control: supported unnamed stream and structure remain exact."""
    assert os.name == "nt"
    root = tmp_path / "ordinary"
    root.mkdir()
    original = root / "control.bin"
    original.write_bytes(_DEFAULT)
    before = _streams(original)
    assert set(before) == {"::$DATA"}, before
    archive = tmp_path / "ordinary.cmpct"
    Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
    restored = tmp_path / "restored"
    with CMPCT(archive) as reader:
        assert reader.verify() >= 1
        assert reader.read("control.bin") == _DEFAULT
        reader.extractall(restored, metadata=False)
    assert (restored / "control.bin").read_bytes() == _DEFAULT
    after = _streams(restored / "control.bin")
    assert after == before, (before, after)
    _record({"kind": "ordinary_control", "result": "exact_regular",
             "streams": after, "archive_bytes": archive.stat().st_size})
