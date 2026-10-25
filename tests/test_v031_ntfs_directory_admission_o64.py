"""O64 product candidate: fail closed on unsupported NTFS directory named $DATA.

Native Windows oracle is independent of cmpct.ntfs_streams. These tests assert
supported directory and hardlink inputs remain exact, including source-root ADS.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.ntfs_streams import refuse_unsupported_named_streams
from cmpct.reader import CMPCT

WINDOWS = os.name == "nt"
PAYLOAD = bytes(((i * 37 + (i >> 5) * 13) & 255) for i in range(4096))
ADS = b"o64-directory-named-data-must-never-vanish" * 17


def _native_stream_names(path: Path) -> list[str]:
    """Independent genuine Win32 source oracle, not the new CMPCT helper."""
    assert WINDOWS
    class StreamData(ctypes.Structure):
        _fields_ = [
            ("StreamSize", ctypes.c_int64),
            ("cStreamName", ctypes.c_wchar * 296),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.FindFirstStreamW.argtypes = (
        wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.POINTER(StreamData), wintypes.DWORD
    )
    kernel.FindFirstStreamW.restype = wintypes.HANDLE
    kernel.FindNextStreamW.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(StreamData)
    )
    kernel.FindNextStreamW.restype = wintypes.BOOL
    kernel.FindClose.argtypes = (wintypes.HANDLE,)
    kernel.FindClose.restype = wintypes.BOOL
    data = StreamData()
    handle = kernel.FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    if handle is None or handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        if error == 38:  # A plain NTFS directory legitimately has no streams.
            return []
        raise OSError(error, "native source enumeration failed")
    names = []
    try:
        while True:
            names.append(data.cStreamName)
            if kernel.FindNextStreamW(handle, ctypes.byref(data)):
                continue
            error = ctypes.get_last_error()
            if error != 38:
                raise OSError(error, "native source enumeration ended abnormally")
            return names
    finally:
        assert kernel.FindClose(handle), "native source oracle leaked Find handle"


def _attach_ads(directory: Path, name: str) -> str:
    path = str(directory) + ":" + name
    with open(path, "wb") as writer:
        writer.write(ADS)
    with open(path, "rb") as reader:
        assert reader.read() == ADS
    assert ":" + name + ":$DATA" in _native_stream_names(directory)
    return path


@pytest.mark.skipif(not WINDOWS, reason="requires Windows NTFS directory ADS")
def test_nested_directory_ads_refuses_before_clobber(tmp_path: Path) -> None:
    root = tmp_path / "input"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (nested / "regular.bin").write_bytes(PAYLOAD)
    ads = _attach_ads(nested, "cmpct_o64_nested")
    previous = tmp_path / "previous.cmpct"
    previous.write_bytes(b"O64_SENTINEL_NOT_TO_BE_OVERWRITTEN")
    with pytest.raises(OSError, match="unsupported NTFS named stream"):
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(previous)
    assert previous.read_bytes() == b"O64_SENTINEL_NOT_TO_BE_OVERWRITTEN"
    assert (nested / "regular.bin").read_bytes() == PAYLOAD
    with open(ads, "rb") as source:
        assert source.read() == ADS
    print("O64_NESTED_ADS_REFUSED=1 source_bytes=" + str(len(ADS)), flush=True)


@pytest.mark.skipif(not WINDOWS, reason="requires Windows NTFS source-root ADS")
def test_source_root_directory_ads_refuses_before_publication(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "regular.bin").write_bytes(PAYLOAD)
    ads = _attach_ads(root, "cmpct_o64_root")
    fresh = tmp_path / "fresh.cmpct"
    with pytest.raises(OSError, match="unsupported NTFS named stream"):
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(fresh)
    assert not fresh.exists()
    with open(ads, "rb") as source:
        assert source.read() == ADS
    print("O64_ROOT_ADS_REFUSED=1", flush=True)


@pytest.mark.skipif(not WINDOWS, reason="requires Windows NTFS directory enumeration")
def test_plain_directories_admitted_with_physical_hardlinks(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    empty = root / "empty"
    nested.mkdir(parents=True)
    empty.mkdir()
    owner = nested / "owner.bin"
    alias = nested / "alias.bin"
    different = nested / "independent.bin"
    owner.write_bytes(PAYLOAD)
    os.link(owner, alias)
    different.write_bytes(PAYLOAD)
    assert os.path.samefile(owner, alias)
    assert not os.path.samefile(owner, different)
    for directory in (root, nested, empty):
        assert _native_stream_names(directory) == []
        refuse_unsupported_named_streams(directory, directory=True)
    digests = []
    for number in range(2):
        archive = tmp_path / f"stable-{number}.cmpct"
        Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
        digests.append(hashlib.sha256(archive.read_bytes()).hexdigest())
        restored = tmp_path / f"restored-{number}"
        with CMPCT(archive) as reader:
            assert reader.verify() >= 1
            assert reader.read("nested/owner.bin") == PAYLOAD
            reader.extractall(restored, metadata=False)
        assert (restored / "empty").is_dir()
        assert os.path.samefile(restored / "nested" / "owner.bin",
                                restored / "nested" / "alias.bin")
        assert not os.path.samefile(restored / "nested" / "owner.bin",
                                    restored / "nested" / "independent.bin")
        for leaf in ("owner.bin", "alias.bin", "independent.bin"):
            assert (restored / "nested" / leaf).read_bytes() == PAYLOAD
    assert digests[0] == digests[1]
    print("O64_SUPPORTED_TREE_EXACT=1 canonical_sha256=" + digests[0], flush=True)


@pytest.mark.skipif(not WINDOWS, reason="requires genuine Windows FindFirstStreamW errors")
def test_nonexistent_directory_enumeration_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "not-a-directory"
    assert not missing.exists()
    with pytest.raises(OSError):
        refuse_unsupported_named_streams(missing, directory=True)


@pytest.mark.skipif(WINDOWS, reason="non-Windows no-op contract")
def test_nonwindows_directory_guard_is_noop(tmp_path: Path) -> None:
    root = tmp_path / "normal"
    root.mkdir()
    refuse_unsupported_named_streams(root, directory=True)
    refuse_unsupported_named_streams(root / "does-not-exist", directory=True)
