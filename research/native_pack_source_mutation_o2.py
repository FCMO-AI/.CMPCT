#!/usr/bin/env python3
"""Hostile same-open-handle PACK source-freshness court: unchanged r24/Rust ABI.

Scientific follow-up to native S_PACK amplification O1, not a proposed cache.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_golden_abi import load_native, read_native  # original owner API binding

GOLDEN = ROOT / "tests/conformance/v24-pack.json"
HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")


def open_native(lib, path: Path):
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(os.fsencode(path), ctypes.byref(handle))
    assert status == 0, (path, "native open", status)
    return handle


def index_of(lib, handle, wanted):
    count = lib.cmpct_entry_count(handle)
    for i in range(count):
        n = ctypes.c_size_t()
        assert lib.cmpct_entry_path(handle, i, None, 0, ctypes.byref(n)) == 0
        buf = ctypes.create_string_buffer(n.value + 1)
        assert lib.cmpct_entry_path(handle, i, buf, len(buf), ctypes.byref(n)) == 0
        if buf.value.decode() == wanted:
            return i
    raise AssertionError(("missing exact native path", wanted))


def edit_byte(path: Path, at: int, before: int, after: int, inode):
    assert before != after
    with path.open("r+b", buffering=0) as f:
        assert (os.fstat(f.fileno()).st_dev, os.fstat(f.fileno()).st_ino) == inode
        f.seek(at)
        assert f.read(1) == bytes([before]), ("unexpected physical byte", at)
        f.seek(at)
        assert f.write(bytes([after])) == 1
        os.fsync(f.fileno())
    assert (path.stat().st_dev, path.stat().st_ino) == inode


def check_fixed_source(lib, vector, home):
    wire = base64.b64decode(vector["archive_base64"], validate=True)
    assert hashlib.sha256(wire).hexdigest() == vector["archive_sha256"]
    path = home / (vector["name"] + "-same-open.cmpct")
    path.write_bytes(wire)
    st = path.stat()
    inode = (st.st_dev, st.st_ino)
    original_size = st.st_size
    header = HDR.unpack_from(wire)
    assert header[0] == b"CMPCT24\x00" and header[1] == 24
    physical_off = HDR.size + header[3]
    fields = BHDR.unpack_from(wire, physical_off)
    assert fields[0] == b"CMA4"
    assert fields[1] == vector["physical_codec"]
    assert fields[4] == vector["packed_blob_uncompressed_bytes"]
    assert fields[5] == vector["packed_blob_compressed_bytes"]
    payload_start = physical_off + BHDR.size + fields[6]
    payload_end = payload_start + fields[5]
    assert payload_end <= len(wire)
    assert fields[8].hex() == vector["packed_blob_sha256"]
    expected = bytes.fromhex(vector["files"]["alpha.txt"]["hex"])
    result = {"name": vector["name"], "physical_codec": vector["physical_codec"],
              "same_open_handle": True, "source_sha256": vector["archive_sha256"],
              "source_size": original_size, "source_identity": "st_dev/st_ino/size",
              "cases": []}
    handle = open_native(lib, path)
    member = index_of(lib, handle, "alpha.txt")
    try:
        status, data = read_native(lib, handle, member, 0, len(expected))
        assert status == 0 and data == expected
        result["cases"].append({"case": "original", "status": status, "exact": True})

        if fields[1] == 1:
            # The stored physical digest is intentionally altered while both
            # authenticated index copies and actual Zstd payload remain unchanged.
            at = physical_off + 32
            original = wire[at]
            edit_byte(path, at, original, original ^ 1, inode)
            corrupt = path.read_bytes()
            assert len(corrupt) == len(wire) and corrupt[:at] == wire[:at]
            assert corrupt[at + 1:] == wire[at + 1:]
            bad_status, bad_bytes = read_native(lib, handle, member, 0, len(expected))
            assert bad_status != 0 and not bad_bytes, (
                "same-open native accepted modified strong physical SHA", bad_status, bad_bytes
            )
            result["cases"].append(
                {"case": "zstd-physical-sha-bitflip-after-open", "status": bad_status,
                 "must_refuse": True, "returned_bytes": 0}
            )
            edit_byte(path, at, original ^ 1, original, inode)
            status, data = read_native(lib, handle, member, 0, len(expected))
            assert status == 0 and data == expected
            result["cases"].append({"case": "restored-strong-hash", "status": status, "exact": True})

            # Independently corrupt the stored Zstd payload, leaving all hash and
            # index fields pristine and preserving the whole archive length.
            at = payload_start + max(1, fields[5] // 2)
            assert payload_start <= at < payload_end
            original = wire[at]
            edit_byte(path, at, original, original ^ 1, inode)
            bad_status, bad_bytes = read_native(lib, handle, member, 0, len(expected))
            assert bad_status != 0 and not bad_bytes, (
                "same-open native accepted physical Zstd payload mutation", bad_status, bad_bytes
            )
            result["cases"].append(
                {"case": "zstd-compressed-payload-bitflip-after-open", "status": bad_status,
                 "must_refuse": True, "returned_bytes": 0}
            )
            edit_byte(path, at, original ^ 1, original, inode)
            status, data = read_native(lib, handle, member, 0, len(expected))
            assert status == 0 and data == expected
            result["cases"].append({"case": "restored-zstd-payload", "status": status, "exact": True})
        else:
            # Deliberate semantic contrast: RAW selective-range is not a full
            # physical SHA gate. A requested mutated byte must be read fresh.
            offset = wire[payload_start:payload_end].find(expected)
            assert offset >= 0 and wire[payload_start:payload_end].count(expected) == 1
            at = payload_start + offset
            original = wire[at]
            edit_byte(path, at, original, original ^ 1, inode)
            status, data = read_native(lib, handle, member, 0, len(expected))
            assert status == 0 and data == bytes([original ^ 1]) + expected[1:]
            result["cases"].append(
                {"case": "raw-requested-byte-mutated-after-open",
                 "status": status, "saw_new_in_place_byte": True,
                 "strong_sha_for_unseen_raw_bytes": "NOT_CLAIMED"}
            )
            edit_byte(path, at, original ^ 1, original, inode)
            status, data = read_native(lib, handle, member, 0, len(expected))
            assert status == 0 and data == expected
            result["cases"].append({"case": "restored-raw-requested-byte", "status": status, "exact": True})

        assert path.stat().st_size == original_size
        assert (path.stat().st_dev, path.stat().st_ino) == inode
        assert hashlib.sha256(path.read_bytes()).hexdigest() == vector["archive_sha256"]
        result["fully_restored_original_archive_sha256"] = True
        result["no_inode_rebinding"] = True
        return result
    finally:
        lib.cmpct_close(handle)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python research/native_pack_source_mutation_o2.py RESULT.json")
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    lib = load_native()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-pack-fresh-o2-") as td:
        records = [check_fixed_source(lib, x, Path(td)) for x in manifest["vectors"]]
    assert {x["physical_codec"] for x in records} == {0, 1}
    result = {
        "schema": "cmpct-native-pack-same-handle-source-mutation-o2-v1",
        "source_fingerprint": os.environ.get("EVIDENCE_HEAD", "LOCAL_UNBOUND"),
        "purpose": "Native PACK source freshness and unsafe cross-call cache falsifier",
        "scope": "Independent fixed revision-24 RAW/Zstd golden; same opened handle;",
        "not_a_cache_or_release": True, "results": records
    }
    path = Path(sys.argv[1])
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("SOURCE_MUTATION_O2_PASS native Zstd refuses 2/2 in-place corruptions on SAME open handle")
    print("SOURCE_MUTATION_O2_PASS native RAW selectively sees requested byte mutation")
    print("SOURCE_MUTATION_O2_PASS both golden archives restored bit-for-bit", path)
    print("SOURCE_MUTATION_O2_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
