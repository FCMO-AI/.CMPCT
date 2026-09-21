from __future__ import annotations

"""Thin Python owner for the package-local codec ABI.

The archive format depends on Zstd, but Python must not rediscover an ambient libzstd.  Packaging
places the existing cmpct_core cdylib beside this module; Rust owns Zstd and Python owns only caller
buffers plus the lifetime of opaque decoder handles.
"""

import ctypes
from pathlib import Path

_sz = ctypes.c_size_t
_u8p = ctypes.POINTER(ctypes.c_uint8)
_voidpp = ctypes.POINTER(ctypes.c_void_p)


def _library_path() -> Path:
    root = Path(__file__).resolve().parent
    candidates = sorted(
        p for pattern in ("cmpct_core*.so", "cmpct_core*.pyd", "cmpct_core*.dll", "cmpct_core*.dylib")
        for p in root.glob(pattern)
        if p.is_file()
    )
    if not candidates:
        raise RuntimeError("package-owned cmpct_core codec library is missing")
    return candidates[0]


_core = ctypes.CDLL(str(_library_path()))
_core.cmpct_codec_zstd_compress_bound.argtypes = [_sz]
_core.cmpct_codec_zstd_compress_bound.restype = _sz
_core.cmpct_codec_zstd_compress.argtypes = [ctypes.c_void_p, _sz, ctypes.c_int32, ctypes.c_void_p, _sz, ctypes.POINTER(_sz)]
_core.cmpct_codec_zstd_compress.restype = ctypes.c_int32
_core.cmpct_codec_zstd_compress_using_dict.argtypes = [ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.c_int32, ctypes.c_void_p, _sz, ctypes.POINTER(_sz)]
_core.cmpct_codec_zstd_compress_using_dict.restype = ctypes.c_int32
_core.cmpct_codec_zstd_decompress.argtypes = [ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.POINTER(_sz)]
_core.cmpct_codec_zstd_decompress.restype = ctypes.c_int32
_core.cmpct_codec_zstd_decompress_using_dict.argtypes = [ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.POINTER(_sz)]
_core.cmpct_codec_zstd_decompress_using_dict.restype = ctypes.c_int32
_core.cmpct_codec_zstd_dict_decoder_create.argtypes = [ctypes.c_void_p, _sz, _voidpp]
_core.cmpct_codec_zstd_dict_decoder_create.restype = ctypes.c_int32
_core.cmpct_codec_zstd_dict_decoder_decompress.argtypes = [ctypes.c_void_p, ctypes.c_void_p, _sz, ctypes.c_void_p, _sz, ctypes.POINTER(_sz)]
_core.cmpct_codec_zstd_dict_decoder_decompress.restype = ctypes.c_int32
_core.cmpct_codec_zstd_dict_decoder_free.argtypes = [ctypes.c_void_p]
_core.cmpct_codec_zstd_dict_decoder_free.restype = ctypes.c_int32


def _check(status: int, operation: str) -> None:
    if status == 0:
        return
    names = {-1: "null argument", -3: "malformed codec input", -6: "insufficient output/range", -127: "contained native panic"}
    raise RuntimeError(f"{operation}: {names.get(int(status), f'native status {int(status)}')}")


def _src(data: bytes):
    return ctypes.create_string_buffer(data) if data else None


def compress(data: bytes, level: int) -> bytes:
    if not data:
        return b""
    src = _src(data); cap = int(_core.cmpct_codec_zstd_compress_bound(len(data))); dst = ctypes.create_string_buffer(cap); out = _sz()
    _check(_core.cmpct_codec_zstd_compress(src, len(data), level, dst, cap, ctypes.byref(out)), "Zstd compress")
    return dst.raw[: out.value]


def compress_using_dict(data: bytes, dictionary: bytes, level: int) -> bytes:
    if not data:
        return b""
    src = _src(data); db = _src(dictionary); cap = int(_core.cmpct_codec_zstd_compress_bound(len(data))); dst = ctypes.create_string_buffer(cap); out = _sz()
    _check(_core.cmpct_codec_zstd_compress_using_dict(src, len(data), db, len(dictionary), level, dst, cap, ctypes.byref(out)), "Zstd dictionary compress")
    return dst.raw[: out.value]


def decompress(data: bytes, usize: int) -> bytes:
    if usize == 0:
        return b""
    src = _src(data); dst = ctypes.create_string_buffer(usize); out = _sz()
    _check(_core.cmpct_codec_zstd_decompress(src, len(data), dst, usize, ctypes.byref(out)), "Zstd decompress")
    if out.value != usize:
        raise IOError(f"Zstd size mismatch: {out.value} != {usize}")
    return dst.raw[: out.value]


class DictDecoder:
    """Load-once/use-many dictionary decoder; callers serialize access."""

    def __init__(self, dictionary: bytes):
        db = _src(dictionary); handle = ctypes.c_void_p()
        _check(_core.cmpct_codec_zstd_dict_decoder_create(db, len(dictionary), ctypes.byref(handle)), "Zstd dictionary decoder create")
        if not handle.value:
            raise MemoryError("native Zstd dictionary decoder returned no handle")
        self._handle = handle

    def decompress(self, data: bytes, usize: int) -> bytes:
        if usize == 0:
            return b""
        if not self._handle:
            raise RuntimeError("Zstd dictionary decoder is closed")
        src = _src(data); dst = ctypes.create_string_buffer(usize); out = _sz()
        _check(_core.cmpct_codec_zstd_dict_decoder_decompress(self._handle, src, len(data), dst, usize, ctypes.byref(out)), "Zstd dictionary decompress")
        if out.value != usize:
            raise IOError(f"Zstd dictionary size mismatch: {out.value} != {usize}")
        return dst.raw[: out.value]

    def close(self) -> None:
        if self._handle:
            handle, self._handle = self._handle, None
            _check(_core.cmpct_codec_zstd_dict_decoder_free(handle), "Zstd dictionary decoder free")
