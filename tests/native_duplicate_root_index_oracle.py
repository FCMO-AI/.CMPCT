"""Research O0: identical authenticated r24 wire, conflicting native/Python tree.

A SUCCESSFUL scientific court reports a negative product finding. It does NOT
establish safe Reader behavior. This is a source-exact adversarial oracle.
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


def forge_authenticated_duplicate(original: bytes, zstd: Zstd, *, first_empty: bool):
    magic, ver, flags, ci, ui, span, expected = HDR.unpack_from(original)
    assert magic == b"CMPCT24\0" and ver == 24
    plain = zstd.decompress(original[HDR.size:HDR.size + ci], ui)
    assert sha(plain) == expected
    index = msgpack.unpackb(plain, raw=False)
    assert len(index["files"]) == 1
    packer = msgpack.Packer(use_bin_type=True)
    # Intentionally bypass dict serialization, which would silently deduplicate.
    pieces = [packer.pack_map_header(len(index) + 1)]
    for key, value in index.items():
        if key == "files" and first_empty:
            pieces.extend((packer.pack("files"), packer.pack([])))
        pieces.extend((packer.pack(key), packer.pack(value)))
        if key == "files" and not first_empty:
            pieces.extend((packer.pack("files"), packer.pack([])))
    ambiguous_plain = b"".join(pieces)
    assert ambiguous_plain != plain
    # Two "files" keys are intentional, and no index SHA mismatch is allowed.
    decoded_python = msgpack.unpackb(ambiguous_plain, raw=False)
    assert len(decoded_python["files"]) == (1 if first_empty else 0)
    encoded = zstd.compress(ambiguous_plain)
    logical = original[HDR.size + ci:HDR.size + ci + span]
    assert len(logical) == span
    digest = sha(ambiguous_plain)
    forged = (
        HDR.pack(magic, ver, flags, len(encoded), len(ambiguous_plain), span, digest)
        + encoded + logical + encoded
        + FTR.pack(b"CMPTF24\0", 0, 1, 0, 0, len(encoded), len(ambiguous_plain), 0, digest)
    )
    assert forged[HDR.size + len(encoded):HDR.size + len(encoded) + span] == logical
    assert forged[-FTR.size - len(encoded):-FTR.size] == encoded
    assert FTR.unpack_from(forged, len(forged) - FTR.size)[-1] == digest
    assert sha(zstd.decompress(encoded, len(ambiguous_plain))) == digest
    return forged


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


def main():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    zstd = Zstd()
    lib = native_lib()
    evidence = []
    with tempfile.TemporaryDirectory(prefix="cmpct-index-map-alias-o0-") as td:
        root = Path(td)
        for vector in manifest["vectors"]:
            orig = base64.b64decode(vector["archive_base64"], validate=True)
            assert sha(orig).hex() == vector["archive_sha256"]
            assert len(orig) == vector["archive_bytes"]
            expected_digest = vector["logical_sha256"]
            original_path = root / f"{vector['codec']}-unchanged.cmpct"
            original_path.write_bytes(orig)

            # Strict unchanged goldens prove the ABI is present and both readers
            # agree before the duplicate root key is introduced.
            with CMPCT(original_path) as python:
                assert len(python.files) == 1
                assert sha(python.read(vector["name"])).hex() == expected_digest
            native_count, native_data = native_read(lib, original_path, vector["logical_size"])
            assert native_count == 1 and sha(native_data).hex() == expected_digest
            evidence.append({"codec": vector["codec"], "case": "unaltered",
                             "python_count": 1, "native_count": 1, "agreement": True})

            for first_empty in (True, False):
                wire = forge_authenticated_duplicate(orig, zstd, first_empty=first_empty)
                path = root / f"{vector['codec']}-first-empty-{first_empty}.cmpct"
                path.write_bytes(wire)
                with CMPCT(path) as python:
                    python_count = len(python.files)
                    if python_count:
                        assert python_count == 1
                        assert sha(python.read(vector["name"])).hex() == expected_digest
                native_count, native_data = native_read(
                    lib, path, vector["logical_size"]
                )
                if native_count:
                    assert sha(native_data).hex() == expected_digest
                expected_python = 1 if first_empty else 0
                expected_native = 0 if first_empty else 1
                assert (python_count, native_count) == (
                    expected_python, expected_native
                ), (vector["codec"], first_empty, python_count, native_count)
                evidence.append({"codec": vector["codec"], "case":
                                 "first-empty" if first_empty else "last-empty",
                                 "wire_sha256": sha(wire).hex(),
                                 "python_count": python_count,
                                 "native_count": native_count,
                                 "agreement": False,
                                 "physical_data_unchanged": True,
                                 "both_indexes_authenticated": True})

    verdict = {
        "schema": "cmpct-dual-reader-authenticated-root-duplicate-o0-v1",
        "verdict": "PROVEN_DIVERGENT_LOGICAL_TREES_NOT_SAFE",
        "source": "independent committed revision-24 direct-codec goldens",
        "positive_same_wire": 3,
        "negative_same_wire": 6,
        "cases": evidence,
        "product_fix_or_release_credit": False,
    }
    dest = Path("duplicate-root-evidence")
    dest.mkdir(exist_ok=True)
    (dest / "verdict.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(f"DIVERGENCE_CONFIRMED {verdict['negative_same_wire']}/6; NOT A PRODUCT PASS")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
