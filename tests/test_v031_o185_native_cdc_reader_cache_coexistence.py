"""O185: real native CDC cut/Builder r24/Reader bounded-cache composition.

This is an additional integrated product regression, not a replacement for
O166 ThreadSanitizer or O175 physical warm-scan/RSS economics.
Requires Linux/POSIX C compiler; other hosts remain a separate portability gate.
"""
from __future__ import annotations

import ctypes
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from cmpct import builder, codec, reader


@pytest.mark.skipif(sys.platform == "win32", reason="O185 POSIX C compilation court; Windows remains unmeasured")
def test_authentic_cdc_native_cuts_and_bounded_reader_reconstruct_same_r24_tree(
    tmp_path, monkeypatch,
):
    compiler = shutil.which("cc")
    if compiler is None:
        pytest.skip("C compiler unavailable; native core/hosted O185 court must still execute")

    # Compile the exact checked-in C, not a Python reimplementation of SplitMix64.
    source = Path(__file__).resolve().parents[1] / "native" / "cmpct_cdc.c"
    assert source.is_file()
    libpath = tmp_path / "libcmpct_o185_cdc.so"
    subprocess.run(
        [compiler, "-O2", "-std=c11", "-shared", "-fPIC", str(source), "-o", str(libpath)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    native = ctypes.CDLL(str(libpath))
    native.cmpct_cdc_cut.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    native.cmpct_cdc_cut.restype = ctypes.c_size_t
    monkeypatch.setattr(codec, "_cdc", native)

    # Nondictionary, deterministic incompressible input crosses both Builder's
    # 4*CHUNK admission and codec.cdc_chunks' max_size native dispatch threshold.
    data = b"".join(hashlib.sha256(i.to_bytes(4, "little")).digest() for i in range(70000))
    assert len(data) > codec.CDC_MAX
    assert len(data) > 4 * codec.CHUNK
    root = tmp_path / "input"
    root.mkdir()
    (root / "payload.bin").write_bytes(data)
    (root / "side.txt").write_bytes(b"bounded-cache/CDC coexistence\n" * 91)

    calls = []
    original_cdc_chunks = builder.cdc_chunks

    def audit_cdc_chunks(value, *args, **kwargs):
        parts = original_cdc_chunks(value, *args, **kwargs)
        calls.append((len(value), tuple(map(len, parts))))
        assert b"".join(parts) == value
        return parts

    monkeypatch.setattr(builder, "cdc_chunks", audit_cdc_chunks)
    archive = tmp_path / "integrated.cmpct"
    builder.Builder(root, workers=1).build(archive)

    # This assertion prevents a green test bought by silently skipping CDC.
    assert calls and any(input_size == len(data) and len(parts) > 1 for input_size, parts in calls)
    with reader.CMPCT(archive) as got:
        assert got.by["payload.bin"][6][0] == reader.S_CDC
        assert got.verify() == 2
        assert got.read_range("payload.bin", 123, 1061) == data[123:1184]
        assert got.read("payload.bin") == data
        assert got.read("side.txt") == b"bounded-cache/CDC coexistence\n" * 91
        assert got._cache_bytes <= got._DECODED_CACHE_MAX_BYTES
        assert len(got._cache_order) <= got._DECODED_CACHE_MAX_ENTRIES
        dest = tmp_path / "extracted"
        got.extractall(dest)
    assert (dest / "payload.bin").read_bytes() == data
    assert (dest / "side.txt").read_bytes() == b"bounded-cache/CDC coexistence\n" * 91
