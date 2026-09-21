from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

import cmpct.builder as builder_mod
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
VECTOR = ROOT / "tests/conformance/v24-zstd-dictionary.json"


def _load_lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]

    # Package-owned codec ABI: resolve symbols from the shipping cdylib through ctypes rather than
    # compiling codec_abi.rs into a Rust test crate. Symbol export/linkage is therefore evidence.
    lib.cmpct_codec_zstd_compress_bound.argtypes = [ctypes.c_size_t]
    lib.cmpct_codec_zstd_compress_bound.restype = ctypes.c_size_t
    lib.cmpct_codec_zstd_compress.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int32,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_codec_zstd_compress.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_compress_using_dict.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int32,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_codec_zstd_compress_using_dict.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_decompress_using_dict.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_codec_zstd_decompress_using_dict.restype = ctypes.c_int32
    return lib


def _open(lib, path: Path):
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(str(path).encode(), ctypes.byref(handle))
    assert status == 0, (path, status)
    return handle


def _entry_path(lib, handle, index: int) -> str:
    needed = ctypes.c_size_t()
    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(needed)) == 0
    buf = ctypes.create_string_buffer(needed.value + 1)
    assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(needed)) == 0
    return buf.value.decode()


def _read_range(lib, handle, offset: int, length: int):
    out = ctypes.create_string_buffer(length)
    got = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(handle, 0, offset, out, length, ctypes.byref(got))
    return status, got.value, out.raw[: got.value]


def _native_zc(lib, data: bytes, level: int) -> bytes:
    if not data:
        return b""
    capacity = lib.cmpct_codec_zstd_compress_bound(len(data))
    out = ctypes.create_string_buffer(capacity)
    out_len = ctypes.c_size_t()
    status = lib.cmpct_codec_zstd_compress(data, len(data), level, out, capacity, ctypes.byref(out_len))
    assert status == 0, status
    return out.raw[: out_len.value]


def _native_zcd(lib, data: bytes, dictionary: bytes, level: int) -> bytes:
    if not data:
        return b""
    capacity = lib.cmpct_codec_zstd_compress_bound(len(data))
    out = ctypes.create_string_buffer(capacity)
    out_len = ctypes.c_size_t()
    status = lib.cmpct_codec_zstd_compress_using_dict(
        data,
        len(data),
        dictionary,
        len(dictionary),
        level,
        out,
        capacity,
        ctypes.byref(out_len),
    )
    assert status == 0, status
    return out.raw[: out_len.value]


def _codec_abi_exact_dictionary_gate(lib) -> None:
    payload = b"structured-record\0" * 8192 + bytes(range(64)) * 128
    seed = b"alpha beta gamma delta structured-record\0"
    dictionary = (seed * ((4096 + len(seed) - 1) // len(seed)))[:4096]

    compressed = _native_zcd(lib, payload, dictionary, 9)
    assert len(compressed) == 104
    assert hashlib.sha256(compressed).hexdigest() == "0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6"

    decoded = ctypes.create_string_buffer(len(payload))
    decoded_len = ctypes.c_size_t()
    status = lib.cmpct_codec_zstd_decompress_using_dict(
        compressed,
        len(compressed),
        dictionary,
        len(dictionary),
        decoded,
        len(decoded),
        ctypes.byref(decoded_len),
    )
    assert status == 0, status
    assert decoded_len.value == len(payload)
    assert decoded.raw[: decoded_len.value] == payload

    # Caller-buffer semantics must fail closed rather than allocating or partially succeeding.
    too_small = ctypes.create_string_buffer(103)
    too_small_len = ctypes.c_size_t(12345)
    status = lib.cmpct_codec_zstd_compress_using_dict(
        payload,
        len(payload),
        dictionary,
        len(dictionary),
        9,
        too_small,
        len(too_small),
        ctypes.byref(too_small_len),
    )
    assert status == -6, status
    assert too_small_len.value == 0


def _archive_identity_gate(lib, root: Path) -> None:
    """Prove transparent writer substitution before changing shipping Python ownership."""
    src = root / "identity-src"
    src.mkdir()
    common = ("timestamp=2026-09-21 level=INFO component=cmpct message=structured record\n" * 1024).encode()
    for i in range(6):
        (src / f"log-{i}.txt").write_bytes(common + (f"record={i}\n" * 2048).encode())
    # A non-text member keeps ordinary Zstd in the same archive while the text family exercises the
    # dictionary path when the builder's generic dictionary admission selects it.
    (src / "payload.bin").write_bytes((bytes(range(251)) * 2048) + b"cmpct-tail")

    ambient = root / "ambient.cmpct"
    native = root / "native-codec.cmpct"
    builder_mod.Builder(src, workers=1, reproducible=True).build(ambient)

    old_zc, old_zcd = builder_mod.zc, builder_mod.zcd
    try:
        builder_mod.zc = lambda data, level: _native_zc(lib, data, level)
        builder_mod.zcd = lambda data, dictionary, level: _native_zcd(lib, data, dictionary, level)
        builder_mod.Builder(src, workers=1, reproducible=True).build(native)
    finally:
        builder_mod.zc, builder_mod.zcd = old_zc, old_zcd

    ambient_bytes = ambient.read_bytes()
    native_bytes = native.read_bytes()
    assert native_bytes == ambient_bytes, (
        len(ambient_bytes),
        len(native_bytes),
        hashlib.sha256(ambient_bytes).hexdigest(),
        hashlib.sha256(native_bytes).hexdigest(),
    )


def main() -> None:
    vector = json.loads(VECTOR.read_text())["vector"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    lib = _load_lib()
    _codec_abi_exact_dictionary_gate(lib)

    with tempfile.TemporaryDirectory(prefix="cmpct-native-dictionary-") as td:
        root = Path(td)
        _archive_identity_gate(lib, root)
        archive = root / "dictionary.cmpct"
        archive.write_bytes(archive_bytes)

        handle = _open(lib, archive)
        try:
            assert lib.cmpct_entry_count(handle) == 1
            assert _entry_path(lib, handle, 0) == vector["name"]
            want = bytes.fromhex(vector["range"]["hex"])
            status, got_n, got = _read_range(
                lib,
                handle,
                vector["range"]["offset"],
                vector["range"]["length"],
            )
            assert status == 0, status
            assert got_n == len(want)
            assert got == want

            # Full reads additionally prove exact decode length/content, not merely a fortunate slice.
            status, got_n, got = _read_range(lib, handle, 0, vector["logical_size"])
            assert status == 0, status
            assert got_n == vector["logical_size"]
            with CMPCT(archive) as ar:
                assert got == ar.read(vector["name"])
                dict_index = ar.index["dict_blob"]
                member_index = ar.by[vector["name"]][6][1]
                dict_pos = ar.record_base + ar.blobs[dict_index][0]
                member_pos = ar.record_base + ar.blobs[member_index][0]
        finally:
            lib.cmpct_close(handle)

        # Dictionary bytes are an authenticated dependency of codec 3. Corrupting only the dictionary
        # payload must fail the member read even though the primary index/member frame still authenticate.
        corrupt_dict = bytearray(archive_bytes)
        corrupt_dict[dict_pos + 64 + 17] ^= 1
        corrupt_dict_path = root / "dictionary-corrupt-payload.cmpct"
        corrupt_dict_path.write_bytes(corrupt_dict)
        handle = _open(lib, corrupt_dict_path)
        try:
            status, got_n, _ = _read_range(lib, handle, 0, 32)
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)

        # Mutating only the member's physical SHA leaves the Zstd-with-dictionary stream decodable;
        # returning bytes would therefore expose a missing strong-integrity check in the native path.
        corrupt_member = bytearray(archive_bytes)
        corrupt_member[member_pos + 32] ^= 1
        corrupt_member_path = root / "dictionary-member-corrupt-hash.cmpct"
        corrupt_member_path.write_bytes(corrupt_member)
        handle = _open(lib, corrupt_member_path)
        try:
            status, got_n, _ = _read_range(lib, handle, 0, 32)
            assert status == -3, status
            assert got_n == 0
        finally:
            lib.cmpct_close(handle)


if __name__ == "__main__":
    main()
