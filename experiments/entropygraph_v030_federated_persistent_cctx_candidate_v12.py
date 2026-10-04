from __future__ import annotations

"""C25EG12: exact EG11 creation with one reusable libzstd compression context.

Research-only. The frozen EG08 stopping oracle showed that deleting ladder calls with
shallow size predicates is unsafe. EG12 therefore removes no proof: it changes only the
lifetime of libzstd's compression context. Every call keeps the same source bytes and
compression level and must remain byte-identical to the inherited ZSTD_compress path.
"""

from contextlib import contextmanager
import ctypes
from pathlib import Path

from experiments import entropygraph_v030_federated_raw_incumbent_fusion_candidate_v11 as EG11

V25 = EG11.V25
E5 = EG11.E5
MAGIC = EG11.MAGIC
TAIL_MAGIC = EG11.TAIL_MAGIC
PH = EG11.PH

_STATS: dict[str, int] = {}

# Use the exact libzstd instance already loaded by the inherited research engine.
_z = V25.z
_sz = V25.sz
_z.ZSTD_createCCtx.argtypes = []
_z.ZSTD_createCCtx.restype = ctypes.c_void_p
_z.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
_z.ZSTD_freeCCtx.restype = _sz
_z.ZSTD_compressCCtx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    _sz,
    ctypes.c_void_p,
    _sz,
    ctypes.c_int,
]
_z.ZSTD_compressCCtx.restype = _sz
_z.ZSTD_isError.argtypes = [_sz]
_z.ZSTD_isError.restype = ctypes.c_uint
_z.ZSTD_getErrorName.argtypes = [_sz]
_z.ZSTD_getErrorName.restype = ctypes.c_char_p


class _PersistentCompressor:
    def __init__(self) -> None:
        self._ctx = _z.ZSTD_createCCtx()
        if not self._ctx:
            raise MemoryError("ZSTD_createCCtx returned null")
        self.calls = 0
        self.input_bytes = 0
        self.output_bytes = 0

    def close(self) -> None:
        if self._ctx:
            _z.ZSTD_freeCCtx(self._ctx)
            self._ctx = None

    def compress(self, data: bytes, level: int = 19) -> bytes:
        # Preserve the inherited empty-input special case exactly.
        if not data:
            return b""
        src = ctypes.create_string_buffer(data)
        cap = int(_z.ZSTD_compressBound(len(data)))
        dst = ctypes.create_string_buffer(cap)
        n = int(_z.ZSTD_compressCCtx(self._ctx, dst, cap, src, len(data), int(level)))
        if _z.ZSTD_isError(n):
            name = _z.ZSTD_getErrorName(n)
            raise RuntimeError(f"ZSTD_compressCCtx failed: {(name or b'unknown').decode(errors='replace')}")
        self.calls += 1
        self.input_bytes += len(data)
        self.output_bytes += n
        return dst.raw[:n]


@contextmanager
def _persistent_zc():
    old = V25.zc
    compressor = _PersistentCompressor()
    V25.zc = compressor.compress
    try:
        yield compressor
    finally:
        V25.zc = old
        compressor.close()


def _treehash(root: Path) -> str:
    return EG11._treehash(root)


def extract(archive: Path, destination: Path) -> None:
    EG11.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return EG11.strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    return EG11.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    _STATS.clear()
    with _persistent_zc() as compressor:
        result = dict(EG11.build(source, archive))
        _STATS.update(
            {
                "compress_calls": int(compressor.calls),
                "compress_input_bytes": int(compressor.input_bytes),
                "compress_output_bytes": int(compressor.output_bytes),
            }
        )
    result["profile"] = "federated-eg12-persistent-cctx"
    result["persistent_cctx"] = dict(_STATS)
    return result
