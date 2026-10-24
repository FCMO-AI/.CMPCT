#!/usr/bin/env python3
"""O12 source-exact native ABI court: signed-index logical SHA for bounded streaming.

This is a scoped library-capability test, not a secure filesystem extractor.
All digests are independently computed with Python hashlib over reconstructed
bytes. The negative mutates a real RAW payload *after* cmpct_open.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.codec import CODEC_RAW, K_FILE, K_DIR, S_BLOB
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_batch_abi import load_library, open_native, map_paths

CHUNK = 64 * 1024


def query(lib, handle, index):
    # C buffers must have 32 writable bytes; initialize to a sentinel so an
    # accidentally partial or uninitialized failure result is observable.
    buf = (ctypes.c_uint8 * 32)(*([0xA5] * 32))
    status = lib.cmpct_entry_logical_sha256(handle, index, buf)
    return status, bytes(buf)


def streamed(lib, handle, index, size):
    digest = hashlib.sha256()
    reconstructed = bytearray()
    for pos in range(0, size, CHUNK):
        wanted = min(CHUNK, size - pos)
        buf = (ctypes.c_uint8 * wanted)()
        n = ctypes.c_size_t(897321)
        rc = lib.cmpct_entry_read_range(
            handle, index, pos, buf, wanted, ctypes.byref(n)
        )
        assert rc == 0 and n.value == wanted, (index, pos, rc, n.value)
        chunk = bytes(buf)
        digest.update(chunk)
        reconstructed.extend(chunk)
    return digest.digest(), bytes(reconstructed)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_authenticated_sha_o12.py RESULT.json")
    lib = load_library()
    lib.cmpct_entry_logical_sha256.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p
    ]
    lib.cmpct_entry_logical_sha256.restype = ctypes.c_int
    with tempfile.TemporaryDirectory(prefix="cmpct-native-sha-o12-") as temp:
        base = Path(temp)
        root = base / "input"
        root.mkdir()
        (root / "directory").mkdir()
        raw = random.Random(834123).randbytes(86016)
        txt = ((b"typed object=source; owner=index; read=bounded; trust=signed;\n" * 1400)
               + b"tail:known")
        (root / "raw.bin").write_bytes(raw)
        (root / "directory" / "config.txt").write_bytes(txt)
        output = base / "corpus.cmpct"
        Builder(root, workers=1, reproducible=True).build(output)
        original = output.read_bytes()
        source_hashes = {
            "raw.bin": hashlib.sha256(raw).digest(),
            "directory/config.txt": hashlib.sha256(txt).digest(),
        }
        with CMPCT(output) as reference:
            rows = {row[0]: row for row in reference.files}
            assert rows["raw.bin"][1] == K_FILE
            assert rows["directory"][1] == K_DIR
            raw_store = rows["raw.bin"][6]
            assert raw_store[0] == S_BLOB, ("RAW control must be direct", raw_store)
            assert int(reference.blobs[int(raw_store[1])][3]) == CODEC_RAW, (
                "RAW control must not be reencoded", reference.blobs[int(raw_store[1])]
            )
            for name, expected in [("raw.bin", raw), ("directory/config.txt", txt)]:
                assert reference.read(name) == expected
                assert rows[name][5] == hashlib.sha256(expected).digest(), name
        # The archive source is signed and immutable during the positive court.
        handle = open_native(lib, output)
        cases = {}
        try:
            paths = map_paths(lib, handle)
            for name, expected in [("raw.bin", raw), ("directory/config.txt", txt)]:
                st, indexed = query(lib, handle, paths[name])
                assert st == 0 and indexed == source_hashes[name], (name, st)
                streamed_sha, reconstructed = streamed(
                    lib, handle, paths[name], len(expected)
                )
                assert reconstructed == expected
                assert streamed_sha == indexed == hashlib.sha256(reconstructed).digest()
                cases[name] = {
                    "bytes": len(expected), "status": st,
                    "source_sha256": indexed.hex(),
                    "chunk_size": CHUNK,
                }
            # All failures zero the entire caller output, not merely its prefix.
            for name, h, index, code in [
                ("nonfile", handle, paths["directory"], -7),
                ("out_of_range", handle, lib.cmpct_entry_count(handle) + 8, -6),
                ("null_archive", None, paths["raw.bin"], -1),
            ]:
                status, digest = query(lib, h, index)
                assert (status, digest) == (code, bytes(32)), (name, status, digest)
            assert lib.cmpct_entry_logical_sha256(
                handle, paths["raw.bin"], None
            ) == -1

            # Choose a genuine physical RAW byte sequence by exact-content
            # search, then change a different byte inside the same source.
            # Not a corruption of the signed index or metadata.
            pos = original.find(raw[:64])
            assert pos > 68 and original.find(raw[:64], pos + 1) == -1, (
                "fixture must retain the actual RAW payload", pos
            )
            off = pos + 193
            assert original[off] == raw[193]
            with output.open("r+b") as fd:
                fd.seek(off)
                fd.write(bytes([original[off] ^ 1]))
                fd.flush()
                os.fsync(fd.fileno())
            # The immutable authenticated-index commitment remains the same.
            st, still_expected = query(lib, handle, paths["raw.bin"])
            assert st == 0 and still_expected == source_hashes["raw.bin"]
            changed_sha, changed = streamed(lib, handle, paths["raw.bin"], len(raw))
            assert changed != raw and changed_sha != still_expected, (
                "MUTATED_RAW_MUST_NOT_PASS_STREAM_SHA", changed_sha.hex()
            )
            assert changed[193] == (raw[193] ^ 1)
            # Restore the physical bytes to demonstrate that the mismatch
            # follows the source mutation, not a nondeterministic ABI result.
            with output.open("r+b") as fd:
                fd.seek(off)
                fd.write(bytes([original[off]]))
                fd.flush()
                os.fsync(fd.fileno())
            assert output.read_bytes() == original
            restored_sha, restored = streamed(lib, handle, paths["raw.bin"], len(raw))
            assert restored == raw and restored_sha == still_expected
        finally:
            lib.cmpct_close(handle)

    result = {
        "schema": "cmpct-native-authenticated-stream-sha-o12-v1",
        "source_head_binding": "verified by workflow checkout EVIDENCE_HEAD",
        "archive_sha256": hashlib.sha256(original).hexdigest(),
        "cases": cases,
        "controls": {
            "real_direct_raw_codec": True,
            "native_index_hash_matches_originals": True,
            "native_bounded_stream_output_hashes_match": True,
            "directory_invalid_index_and_null_fail_zero": True,
            "mutated_RAW_payload_ranged_reads_must_mismatch_signed_SHA": True,
            "restored_source_accepts_again": True,
        },
        "decision": "NARROW_ABI_CAPABILITY_POSITIVE_NOT_PRODUCT_EXTRACTOR",
    }
    dest = Path(sys.argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
