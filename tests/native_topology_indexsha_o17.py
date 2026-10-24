#!/usr/bin/env python3
"""O17 prospective SAME-HANDLE composition court: terminal hardlink owner + index SHA + PACK.

Research only: neither an arbitrary-tree extractor nor a product authentication claim.
The O12 and O14 independent controls are also run, unchanged, by the O17 workflow.
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
from cmpct.codec import K_DIR, K_FILE, S_CDC
from cmpct.reader import CMPCT
from native_pack_batch_abi import batch, load_library, map_paths, open_native

CHUNK = 64 * 1024
SEED = 173104
# One real CDC representation, not an invented digest oracle.
CDC_BYTES = random.Random(SEED).randbytes(1_500_000)
RAW_BYTES = random.Random(SEED + 1).randbytes(86016)
FIXED_TIME = 1_700_000_000_000_000_000


def configure(lib):
    lib.cmpct_entry_logical_sha256.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p
    ]
    lib.cmpct_entry_logical_sha256.restype = ctypes.c_int
    lib.cmpct_entry_hardlink_owner.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_hardlink_owner.restype = ctypes.c_int
    lib.cmpct_entry_pack_owner.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_pack_owner.restype = ctypes.c_int


def logical_sha(lib, handle, index):
    digest = (ctypes.c_uint8 * 32)(*([0xA5] * 32))
    rc = lib.cmpct_entry_logical_sha256(handle, index, digest)
    return int(rc), bytes(digest)


def owner(lib, handle, index):
    result = ctypes.c_size_t(999_999_999)
    rc = lib.cmpct_entry_hardlink_owner(handle, index, ctypes.byref(result))
    return int(rc), int(result.value)


def streamed_digest(lib, handle, index, size):
    h = hashlib.sha256()
    bytes_read = 0
    for offset in range(0, size, CHUNK):
        want = min(CHUNK, size - offset)
        out = ctypes.create_string_buffer(want)
        got = ctypes.c_size_t(123456)
        rc = lib.cmpct_entry_read_range(handle, index, offset, out, want, ctypes.byref(got))
        assert rc == 0 and got.value == want, (index, offset, rc, got.value)
        h.update(out.raw[:got.value])
        bytes_read += got.value
    return h.digest(), bytes_read


def pack_control(lib, handle, paths, expected):
    by_owner = {}
    for name in sorted(expected):
        position = ctypes.c_size_t(777)
        rc = lib.cmpct_entry_pack_owner(handle, paths[name], ctypes.byref(position))
        if rc == 0:
            by_owner.setdefault(position.value, []).append(name)
        else:
            assert rc == -7, (name, rc)
    # Genuine Zstd S_PACK: fail, rather than claiming batching when not admitted.
    pack_names = max(by_owner.values(), key=len, default=[])
    assert len(pack_names) >= 2, ("no genuine shared Zstd physical owner", by_owner)
    batch_names = pack_names[:min(48, len(pack_names))]
    requests = [(paths[name], 0, len(expected[name])) for name in batch_names]
    status, contents, amount = batch(lib, handle, requests)
    concatenated = b"".join(expected[name] for name in batch_names)
    assert status == 0 and amount == len(concatenated), (status, amount)
    assert contents == concatenated, "batch reconstruction diverged"
    return {
        "shared_pack_members": len(pack_names),
        "batched_members_verified": len(batch_names),
        "verified_batch_output_bytes": amount,
        "distinct_zstd_owners": len(by_owner),
    }


def run(dest):
    lib = load_library()
    configure(lib)
    with tempfile.TemporaryDirectory(prefix="cmpct-o17-topology-sha-") as scratch:
        home = Path(scratch)
        source = home / "source"
        source.mkdir()
        (source / "directory").mkdir()
        (source / "a_owner.bin").write_bytes(CDC_BYTES)
        (source / "b_other.bin").write_bytes(b"b uniquely owns its hardlink" * 18)
        (source / "raw_direct.bin").write_bytes(RAW_BYTES)
        os.link(source / "a_owner.bin", source / "z_alias.bin")
        os.link(source / "b_other.bin", source / "y_alias_other.bin")
        (source / "sym").symlink_to("a_owner.bin")
        expected_pack = {}
        for i in range(128):
            name = f"p{i:03d}.txt"
            payload = (f"metadata type=owner identity={i % 11}; encoding=structured\n".encode() * 15)
            (source / name).write_bytes(payload)
            expected_pack[name] = payload
        for leaf in source.iterdir():
            if not leaf.is_symlink():
                os.utime(leaf, ns=(FIXED_TIME, FIXED_TIME))
        os.utime(source, ns=(FIXED_TIME, FIXED_TIME))
        assert os.stat(source / "a_owner.bin").st_ino == os.stat(source / "z_alias.bin").st_ino
        assert os.stat(source / "b_other.bin").st_ino == os.stat(source / "y_alias_other.bin").st_ino
        assert os.stat(source / "a_owner.bin").st_ino != os.stat(source / "b_other.bin").st_ino
        archive = home / "tree.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        archive_bytes = archive.read_bytes()
        with CMPCT(archive) as py_reader:
            rows = {r[0]: r for r in py_reader.files}
            assert rows["a_owner.bin"][1] == K_FILE
            assert rows["directory"][1] == K_DIR
            assert rows["a_owner.bin"][6][0] == S_CDC, rows["a_owner.bin"][6]
            assert rows["a_owner.bin"][5] == hashlib.sha256(CDC_BYTES).digest()
            assert rows["z_alias.bin"][1] == 3 and rows["z_alias.bin"][6] == ["a_owner.bin"]
            assert rows["y_alias_other.bin"][1] == 3 and rows["y_alias_other.bin"][6] == ["b_other.bin"]
            assert py_reader.read("z_alias.bin") == CDC_BYTES
            assert py_reader.read("y_alias_other.bin") == (source / "b_other.bin").read_bytes()
        handle = open_native(lib, archive)
        try:
            paths = map_paths(lib, handle)
            assert len(paths) == len(rows), (len(paths), len(rows))
            for link, target in (("z_alias.bin", "a_owner.bin"), ("y_alias_other.bin", "b_other.bin")):
                rc, ordinal = owner(lib, handle, paths[link])
                assert rc == 0 and ordinal == paths[target], (link, rc, ordinal, paths[target])
            digest_rc, digest = logical_sha(lib, handle, paths["a_owner.bin"])
            assert digest_rc == 0 and digest == hashlib.sha256(CDC_BYTES).digest()
            streamed, logical_count = streamed_digest(lib, handle, paths["a_owner.bin"], len(CDC_BYTES))
            assert streamed == digest and logical_count == len(CDC_BYTES)
            # Neither a hardlink nor direct RAW gains a fabricated index commitment.
            for name in ("z_alias.bin", "y_alias_other.bin", "raw_direct.bin", "sym", "directory"):
                rc, value = logical_sha(lib, handle, paths[name])
                assert (rc, value) == (-7, bytes(32)), (name, rc, value.hex())
            assert owner(lib, handle, paths["a_owner.bin"]) == (-7, 0)
            assert owner(lib, handle, lib.cmpct_entry_count(handle) + 3) == (-6, 0)
            assert logical_sha(lib, handle, lib.cmpct_entry_count(handle) + 3) == (-6, bytes(32))
            assert logical_sha(lib, None, paths["a_owner.bin"]) == (-1, bytes(32))
            assert owner(lib, None, paths["z_alias.bin"]) == (-1, 0)
            assert lib.cmpct_entry_logical_sha256(handle, paths["a_owner.bin"], None) == -1
            assert lib.cmpct_entry_hardlink_owner(handle, paths["z_alias.bin"], None) == -1
            pack = pack_control(lib, handle, paths, expected_pack)
        finally:
            lib.cmpct_close(handle)
        result = {
            "schema": "cmpct-native-topology-indexsha-o17-v1",
            "source_prs": {"hardlink_owner": 349, "logical_sha": 340, "pack_batch": 326},
            "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "complete_stored_bytes": len(archive_bytes),
            "logical_cdc_bytes_streamed": logical_count,
            "stream_buffer_ceiling": CHUNK,
            "logical_cdc_sha256": digest.hex(),
            "authenticated_index_sha_equals_streamed_sha": True,
            "terminal_owners_distinguished_in_same_handle": True,
            "negative_sha_and_owner_return_codes": "PASS",
            "pack": pack,
            "decision": "SOURCE_EXACT_NATIVE_METADATA_COMPOSITION_CANDIDATE_PASS",
            "product_credit": 0,
            "unmeasured": ["full-process memory", "matched ABBA", "portable safe extraction", "RAW complete logical integrity", "release promotion"],
        }
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_topology_indexsha_o17.py result.json")
    run(Path(sys.argv[1]))
