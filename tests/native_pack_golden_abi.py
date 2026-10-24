"""Independent committed r24 S_PACK bytes through the real Rust C ABI.

Unlike tests/native_pack_abi.py, no Builder-generated archive enters this court.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
GOLDEN = ROOT / "tests/conformance/v24-pack.json"


def load_native():
    lib = ctypes.CDLL(str(LIBRARY))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    return lib


def read_native(lib, handle, index, offset, length):
    result = ctypes.create_string_buffer(max(length, 1))
    written = ctypes.c_size_t()
    status = lib.cmpct_entry_read_range(
        handle, index, offset, result, length, ctypes.byref(written)
    )
    return status, result.raw[:written.value]


def main():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    lib = load_native()
    with tempfile.TemporaryDirectory(prefix="cmpct-fixed-pack-native-") as td:
        for vec in manifest["vectors"]:
            wire = base64.b64decode(vec["archive_base64"], validate=True)
            assert hashlib.sha256(wire).hexdigest() == vec["archive_sha256"]
            archive = Path(td) / f"{vec['name']}.cmpct"
            archive.write_bytes(wire)
            handle = ctypes.c_void_p()
            status = lib.cmpct_open(str(archive).encode(), ctypes.byref(handle))
            assert status == 0, (vec["name"], status)
            try:
                count = lib.cmpct_entry_count(handle)
                assert count == len(vec["files"])
                seen = {}
                for index in range(count):
                    n = ctypes.c_size_t()
                    assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(n)) == 0
                    path = ctypes.create_string_buffer(n.value + 1)
                    assert lib.cmpct_entry_path(
                        handle, index, path, len(path), ctypes.byref(n)
                    ) == 0
                    name = path.value.decode("utf-8")
                    assert name in vec["files"] and name not in seen
                    seen[name] = index
                    expected = bytes.fromhex(vec["files"][name]["hex"])
                    status, actual = read_native(lib, handle, index, 0, len(expected))
                    assert status == 0, (vec["name"], name, status)
                    assert actual == expected
                    assert hashlib.sha256(actual).hexdigest() == vec["files"][name]["sha256"]
                assert set(seen) == set(vec["files"])
                for probe in vec["ranges"]:
                    want = bytes.fromhex(probe["hex"])
                    status, actual = read_native(
                        lib, handle, seen[probe["name"]], probe["offset"], probe["length"]
                    )
                    assert status == 0 and actual == want, (vec["name"], probe, status)
                status, actual = read_native(
                    lib, handle, seen["omega.bin"],
                    vec["files"]["omega.bin"]["size"] - 1, 2
                )
                assert status != 0 and not actual
            finally:
                lib.cmpct_close(handle)

            # Structural header-versus-authenticated-index disagreement MUST be
            # rejected for BOTH RAW and compressed physical PACKs. By contrast,
            # ordinary RAW selective reads intentionally do not hash unseen bytes.
            import struct
            encoded_index = struct.unpack_from("<Q", wire, 12)[0]
            physical_offset = 68 + encoded_index

            def require_rejection(raw_wire, tag):
                bad = Path(td) / f"{vec['name']}-{tag}.cmpct"
                bad.write_bytes(raw_wire)
                target_handle = ctypes.c_void_p()
                opened = lib.cmpct_open(str(bad).encode(), ctypes.byref(target_handle))
                if opened != 0:
                    return  # fail-closed structural validation may occur at open
                try:
                    failure_status, partial = read_native(
                        lib, target_handle, 0, 0,
                        vec["files"]["alpha-copy.txt"]["size"]
                    )
                    assert failure_status != 0 and not partial, (vec["name"], tag, failure_status)
                finally:
                    lib.cmpct_close(target_handle)

            malformed_size = bytearray(wire)
            # BHDR: magic(4), codec(1), flags(1), reserved(2), usize(8).
            malformed_size[physical_offset + 8] ^= 1
            require_rejection(malformed_size, "physical-size-mismatch")

            if vec["physical_codec"] == 1:
                # Zstd requests decode/authenticate the entire physical blob;
                # a strong physical SHA mismatch is therefore always detectable.
                bad_hash = bytearray(wire)
                bad_hash[physical_offset + 32] ^= 1
                require_rejection(bad_hash, "physical-zstd-sha-mismatch")



if __name__ == "__main__":
    main()
