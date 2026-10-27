#!/usr/bin/env python3
"""DIAGNOSTIC ONLY: run Python reference code with ambient Zstd and vendored MessagePack.

This deliberately substitutes the package-owned pinned runtime. Never cite its results
as release parity or a shipping-runtime measurement. It does not modify installed code.
Use only when the real package cannot be built offline; the genuine gate remains due.
"""
import ctypes as C
import os
from pathlib import Path
import runpy
import sys
import types


def install():
    sys.path.insert(0, os.environ.get("CMPCT_DIAGNOSTIC_SOURCE",
                                    str(Path(__file__).resolve().parents[1] / "src")))
    # Reuse an already installed dependency; no download or installation is performed.
    try:
        import msgpack
    except ImportError:
        from pip._vendor import msgpack
        sys.modules["msgpack"] = msgpack
    z = C.CDLL("libzstd.so.1")
    sz, ptr = C.c_size_t, C.c_void_p
    signatures = [
        ("ZSTD_compressBound", [sz], sz), ("ZSTD_isError", [sz], C.c_uint),
        ("ZSTD_versionString", [], C.c_char_p),
        ("ZSTD_compress", [ptr, sz, ptr, sz, C.c_int], sz),
        ("ZSTD_decompress", [ptr, sz, ptr, sz], sz),
        ("ZSTD_createCCtx", [], ptr), ("ZSTD_freeCCtx", [ptr], sz),
        ("ZSTD_createDCtx", [], ptr), ("ZSTD_freeDCtx", [ptr], sz),
        ("ZSTD_compress_usingDict", [ptr, ptr, sz, ptr, sz, ptr, sz, C.c_int], sz),
        ("ZSTD_decompress_usingDict", [ptr, ptr, sz, ptr, sz, ptr, sz], sz),
    ]
    for name, args, result in signatures:
        function = getattr(z, name)
        function.argtypes, function.restype = args, result

    def check(n):
        if z.ZSTD_isError(n):
            raise RuntimeError("diagnostic Zstd failure")
        return n

    def compress(raw, level):
        if not raw:
            return b""
        out = C.create_string_buffer(z.ZSTD_compressBound(len(raw)))
        n = check(z.ZSTD_compress(out, len(out), raw, len(raw), level))
        return out.raw[:n]

    def decompress(raw, size):
        if not size:
            return b""
        out = C.create_string_buffer(size)
        n = check(z.ZSTD_decompress(out, size, raw, len(raw)))
        if n != size:
            raise IOError("diagnostic decoded size mismatch")
        return out.raw[:n]

    def compress_using_dict(raw, dictionary, level):
        if not raw:
            return b""
        out = C.create_string_buffer(z.ZSTD_compressBound(len(raw)))
        context = z.ZSTD_createCCtx()
        if not context:
            raise MemoryError("diagnostic compression context")
        try:
            n = check(z.ZSTD_compress_usingDict(context, out, len(out), raw, len(raw),
                                               dictionary, len(dictionary), level))
            return out.raw[:n]
        finally:
            z.ZSTD_freeCCtx(context)

    class DictDecoder:
        def __init__(self, dictionary):
            self.dictionary, self.context = dictionary, z.ZSTD_createDCtx()
            if not self.context:
                raise MemoryError("diagnostic dictionary context")

        def decompress(self, raw, size):
            if not self.context:
                raise RuntimeError("diagnostic decoder is closed")
            out = C.create_string_buffer(size)
            n = check(z.ZSTD_decompress_usingDict(self.context, out, size, raw, len(raw),
                                                 self.dictionary, len(self.dictionary)))
            if n != size:
                raise IOError("diagnostic dictionary decoded size mismatch")
            return out.raw[:n]

        def close(self):
            if self.context:
                z.ZSTD_freeDCtx(self.context)
                self.context = None

    module = types.ModuleType("cmpct.native_codec")
    module.compress, module.decompress = compress, decompress
    module.compress_using_dict, module.DictDecoder = compress_using_dict, DictDecoder
    runtime = {"status": "DIAGNOSTIC_SUBSTITUTED_BACKEND_NOT_RELEASE_EVIDENCE",
               "zstd": z.ZSTD_versionString().decode(), "msgpack": str(msgpack.version)}
    module.diagnostic_runtime = runtime
    sys.modules["cmpct.native_codec"] = module
    return runtime


if __name__ == "__main__":
    print("DIAGNÓSTICO: runtime sustituido; no acredita el paquete ni una promoción.", file=sys.stderr)
    install()
    if sys.argv[1:2] == ["--test"]:
        import unittest
        sys.argv.pop(1)
        unittest.main(module=None)
    elif sys.argv[1:2] == ["--script"]:
        sys.argv = sys.argv[2:]
        runpy.run_path(sys.argv[0], run_name="__main__")
    else:
        runpy.run_module("cmpct", run_name="__main__")
