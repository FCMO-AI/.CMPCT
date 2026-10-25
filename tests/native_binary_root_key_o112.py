"""Source-exact O112 scientific court: authenticated binary MessagePack root-key aliases.

Falsifies the narrower residual left explicitly untested by PR #316's string-only
Rust root key uniqueness guard. Green scientific execution can mean a product negative.
"""
from __future__ import annotations

import base64
import ctypes
import ctypes.util
import hashlib
import json
import struct
import tempfile
from pathlib import Path

import msgpack
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive, ValidationError

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/conformance/v24-direct-codecs.json"
NATIVE = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def sha(buf: bytes) -> bytes:
    return hashlib.sha256(buf).digest()


class Zstd:
    def __init__(self):
        libpath = ctypes.util.find_library("zstd")
        assert libpath is not None, "system libzstd not present"
        lib = self.lib = ctypes.CDLL(libpath)
        lib.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
        lib.ZSTD_compressBound.restype = ctypes.c_size_t
        lib.ZSTD_compress.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
            ctypes.c_size_t, ctypes.c_int,
        ]
        lib.ZSTD_compress.restype = ctypes.c_size_t
        lib.ZSTD_decompress.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
        ]
        lib.ZSTD_decompress.restype = ctypes.c_size_t
        lib.ZSTD_isError.argtypes = [ctypes.c_size_t]
        lib.ZSTD_isError.restype = ctypes.c_uint

    def compress(self, plain: bytes) -> bytes:
        lib = self.lib
        buf = ctypes.create_string_buffer(lib.ZSTD_compressBound(len(plain)))
        src = ctypes.create_string_buffer(plain, len(plain))
        n = lib.ZSTD_compress(buf, len(buf), src, len(plain), 12)
        assert not lib.ZSTD_isError(n)
        return buf.raw[:n]

    def decompress(self, compressed: bytes, size: int) -> bytes:
        lib = self.lib
        buf = ctypes.create_string_buffer(size)
        src = ctypes.create_string_buffer(compressed, len(compressed))
        n = lib.ZSTD_decompress(buf, len(buf), src, len(compressed))
        assert not lib.ZSTD_isError(n) and n == size
        return buf.raw[:n]


def native_lib():
    lib = ctypes.CDLL(str(NATIVE))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    return lib


def native_read(lib, filename: Path, expected_len: int | None) -> tuple[int, bytes]:
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(str(filename).encode(), ctypes.byref(handle))
    assert status == 0 and handle.value, ("native open refused", filename, status)
    try:
        count = lib.cmpct_entry_count(handle)
        if not count or expected_len is None:
            return count, b""
        assert count == 1, (filename, count)
        buf = ctypes.create_string_buffer(expected_len)
        received = ctypes.c_size_t()
        status = lib.cmpct_entry_read_range(
            handle, 0, 0, buf, expected_len, ctypes.byref(received)
        )
        assert status == 0 and received.value == expected_len, (filename, status)
        return count, buf.raw[:received.value]
    finally:
        lib.cmpct_close(handle)



BIN_KEY = b"O112-opaque-root-field"


def forge_authenticated_binary_key(original: bytes, zstd: Zstd, *, duplicate: bool):
    magic, version, flags, cs, us, data_span, original_index_hash = HDR.unpack_from(original)
    assert magic == b"CMPCT24\x00" and version == 24
    decoded = zstd.decompress(original[HDR.size:HDR.size + cs], us)
    assert sha(decoded) == original_index_hash
    index = msgpack.unpackb(decoded, raw=False)
    assert len(index["files"]) == 1
    packer = msgpack.Packer(use_bin_type=True)
    root = [packer.pack_map_header(len(index) + (2 if duplicate else 1))]
    for name, value in index.items():
        root += [packer.pack(name), packer.pack(value)]
    root += [packer.pack(BIN_KEY), packer.pack(b"one")]
    if duplicate:
        root += [packer.pack(BIN_KEY), packer.pack(b"two")]
    signed_index = b"".join(root)
    pairs = msgpack.unpackb(signed_index, raw=False, object_pairs_hook=lambda items: items)
    assert sum(k == BIN_KEY for k, _ in pairs) == (2 if duplicate else 1)
    # A normal dictionary may hide duplicate fields, but it is not the authority.
    assert msgpack.unpackb(signed_index, raw=False)[BIN_KEY] == (b"two" if duplicate else b"one")
    compressed = zstd.compress(signed_index)
    physical = original[HDR.size + cs:HDR.size + cs + data_span]
    assert len(physical) == data_span
    signed_hash = sha(signed_index)
    result = (
        HDR.pack(magic, version, flags, len(compressed), len(signed_index), data_span, signed_hash)
        + compressed + physical + compressed
        + FTR.pack(b"CMPTF24\x00", 0, 1, 0, 0,
                   len(compressed), len(signed_index), 0, signed_hash)
    )
    assert result[HDR.size + len(compressed):HDR.size + len(compressed) + data_span] == physical
    assert result[-FTR.size - len(compressed):-FTR.size] == compressed
    assert FTR.unpack_from(result, len(result) - FTR.size)[-1] == signed_hash
    assert sha(zstd.decompress(compressed, len(signed_index))) == signed_hash
    return result, sha(physical).hex()


def python_observation(path: Path, name: str, digest: str):
    try:
        with CMPCT(path) as handle:
            count = len(handle.files)
            data = handle.read(name)
        return {"accepted": True, "members": count,
                "payload_valid": sha(data).hex() == digest}
    except (IOError, ValueError, KeyError, TypeError) as exc:
        return {"accepted": False, "error_type": type(exc).__name__,
                "error": str(exc)[:240]}


def preflight_observation(path: Path):
    try:
        preflight_archive(path)
        return {"accepted": True}
    except (IOError, ValueError, ValidationError, TypeError) as exc:
        return {"accepted": False, "error_type": type(exc).__name__,
                "error": str(exc)[:240]}


def native_observation(lib, path: Path, logical_size: int, digest: str):
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(str(path).encode(), ctypes.byref(handle))
    if status != 0 or not handle.value:
        if handle.value:
            lib.cmpct_close(handle)
        return {"accepted": False, "status": int(status)}
    try:
        count = lib.cmpct_entry_count(handle)
        if count != 1:
            return {"accepted": True, "members": count, "status": int(status),
                    "payload_valid": False}
        data = ctypes.create_string_buffer(logical_size)
        length = ctypes.c_size_t()
        rs = lib.cmpct_entry_read_range(
            handle, 0, 0, data, logical_size, ctypes.byref(length)
        )
        return {"accepted": True, "members": count, "status": int(status),
                "read_status": int(rs),
                "payload_valid": rs == 0 and length.value == logical_size and
                sha(data.raw[:length.value]).hex() == digest}
    finally:
        lib.cmpct_close(handle)


def main():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    zstd, native = Zstd(), native_lib()
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o112-") as tmp:
        work = Path(tmp)
        for item in manifest["vectors"]:
            original = base64.b64decode(item["archive_base64"], validate=True)
            assert sha(original).hex() == item["archive_sha256"]
            assert len(original) == item["archive_bytes"]
            expected_sha = item["logical_sha256"]
            original_path = work / f"{item['codec']}-original.cmpct"
            original_path.write_bytes(original)
            golden_python = python_observation(original_path, item["name"], expected_sha)
            golden_native = native_observation(native, original_path, item["logical_size"], expected_sha)
            assert golden_python.get("accepted") and golden_python.get("payload_valid")
            assert golden_native.get("accepted") and golden_native.get("payload_valid")
            outcomes.append({"codec": item["codec"], "case": "unaltered",
                             "sha256": sha(original).hex(),
                             "python": golden_python, "native": golden_native})

            for duplicated in (False, True):
                wire, physical_sha = forge_authenticated_binary_key(original, zstd, duplicate=duplicated)
                path = work / f"{item['codec']}-bin-duplicate-{duplicated}.cmpct"
                path.write_bytes(wire)
                py = python_observation(path, item["name"], expected_sha)
                pre = preflight_observation(path)
                rust = native_observation(native, path, item["logical_size"], expected_sha)
                outcomes.append({
                    "codec": item["codec"],
                    "case": "duplicated-bin-key" if duplicated else "one-bin-key-control",
                    "wire_sha256": sha(wire).hex(),
                    "original_sha256": sha(original).hex(),
                    "physical_payload_sha256": physical_sha,
                    "index_copies_authenticated": True,
                    "python": py, "preflight": pre, "native": rust,
                })

    controls = [o for o in outcomes if o["case"] == "one-bin-key-control"]
    adversaries = [o for o in outcomes if o["case"] == "duplicated-bin-key"]
    valid_controls = all(o["python"].get("accepted") and o["python"].get("payload_valid") and
                         o["preflight"].get("accepted") and
                         o["native"].get("accepted") and o["native"].get("payload_valid") for o in controls)
    divergences = sum(not o["python"].get("accepted") and
                      not o["preflight"].get("accepted") and
                      o["native"].get("accepted") and
                      o["native"].get("payload_valid") for o in adversaries)
    both_refuse = all(not o["python"].get("accepted") and
                      not o["preflight"].get("accepted") and
                      not o["native"].get("accepted") for o in adversaries)
    if not valid_controls:
        verdict = "CONTROL_INVALID"
    elif divergences == len(adversaries) == 3:
        verdict = "NONSTRING_ROOT_DUPLICATE_GAP_CONFIRMED"
    elif both_refuse:
        verdict = "GAP_FALSIFIED_BOTH_REFUSE"
    else:
        verdict = "MIXED_OR_UNEXPLAINED"
    record = {"schema": "cmpct-o112-same-wire-bin-map-duplicate-v1",
              "product_source": "PR316 exact-head installed Reader + Rust ABI",
              "golden_count": 3, "unique_bin_control_count": len(controls),
              "duplicate_bin_count": len(adversaries), "divergence_count": divergences,
              "verdict": verdict, "release_credit": False,
              "observations": outcomes}
    artifact = Path("o112-evidence")
    artifact.mkdir(exist_ok=True)
    (artifact / "result.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print("O112_VERDICT=" + verdict + " 3 golden/3 unique-bin/3 duplicate-bin")
    print(json.dumps(record, sort_keys=True))
    if verdict not in ("NONSTRING_ROOT_DUPLICATE_GAP_CONFIRMED", "GAP_FALSIFIED_BOTH_REFUSE"):
        raise AssertionError("O112 court inconclusive; see durable raw evidence")


if __name__ == "__main__":
    main()
