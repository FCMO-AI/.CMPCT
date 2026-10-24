#!/usr/bin/env python3
"""O14: actual Builder native hardlink ordinal + separately signed hostile-index court.

Prediction fixed before implementation in NATIVE_HARDLINK_OWNER_ORDINAL_O14_PREREG.md.
No native Rust internals are imported; the test creates and reauthenticates r24 wire itself.
"""
from __future__ import annotations

import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time

import msgpack

from cmpct.builder import Builder
from cmpct.codec import HDR, FTR, MAGIC, FMAGIC, VERSION, sha, zc, zd
from cmpct.reader import CMPCT
from native_pack_batch_abi import load_library, open_native, map_paths

FIXED_TIME = 1_700_000_000_000_000_000
A = b"alpha distinct from bravo native hardlink O14|" * 20
B = b"bravo distinct from alpha native hardlink O14|" * 20
assert len(A) == len(B) and A != B


def wire_parts(blob: bytes):
    magic, version, flags, clen, ulen, data_size, digest = HDR.unpack_from(blob)
    assert magic == MAGIC and version == VERSION
    encoded = blob[HDR.size: HDR.size + clen]
    index_raw = zd(encoded, ulen)
    assert len(index_raw) == ulen and sha(index_raw) == digest
    index = msgpack.unpackb(index_raw, raw=False)
    records = blob[HDR.size + clen: HDR.size + clen + data_size]
    footer = FTR.unpack_from(blob, len(blob) - FTR.size)
    assert footer[0] == FMAGIC and footer[1] == 0 and footer[2] == 1
    assert blob[HDR.size + clen + data_size: -FTR.size] == encoded
    assert footer[5] == clen and footer[6] == ulen and footer[8] == digest
    return index, records, flags


def rebuild(blob: bytes, transform):
    index, records, flags = wire_parts(blob)
    index = copy.deepcopy(index)
    transform(index)
    raw = msgpack.packb(index, use_bin_type=True)
    encoded = zc(raw, 12)
    h = sha(raw)
    head = HDR.pack(MAGIC, VERSION, flags, len(encoded), len(raw), len(records), h)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(raw), 0, h)
    rebuilt = head + encoded + records + encoded + footer
    check_index, check_records, check_flags = wire_parts(rebuilt)
    assert check_index == index and check_records == records and check_flags == flags
    return rebuilt


def setup(lib):
    lib.cmpct_entry_hardlink_owner.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_hardlink_owner.restype = ctypes.c_int


def owner(lib, handle, ix):
    v = ctypes.c_size_t(999_999_999)
    rc = lib.cmpct_entry_hardlink_owner(handle, ix, ctypes.byref(v))
    return int(rc), int(v.value)


def make_archive(home: Path, owner_name: str):
    source = home / ("source-" + owner_name[0])
    source.mkdir()
    for name, data in (("a.bin", A), ("b.bin", B)):
        (source / name).write_bytes(data)
        (source / name).chmod(0o644)
    (source / "directory").mkdir()
    (source / "symlink").symlink_to("a.bin")
    os.link(source / owner_name, source / "z_alias.bin")
    for name in ("a.bin", "b.bin"):
        os.utime(source / name, ns=(FIXED_TIME, FIXED_TIME))
    os.utime(source, ns=(FIXED_TIME, FIXED_TIME))
    aa, bb, alias = [os.stat(source / x) for x in ("a.bin", "b.bin", "z_alias.bin")]
    assert aa.st_ino != bb.st_ino
    assert alias.st_ino == (aa.st_ino if owner_name == "a.bin" else bb.st_ino)
    dest = home / ("hardlink-" + owner_name[0] + ".cmpct")
    Builder(source, workers=1, reproducible=True).build(dest)
    with CMPCT(dest) as reader:
        rows = {r[0]: r for r in reader.files}
        assert rows["z_alias.bin"][1] == 3
        assert rows["z_alias.bin"][6] == [owner_name]
        assert reader.read("z_alias.bin") == (A if owner_name == "a.bin" else B)
    return dest


def expect_failed_open(lib, path, name, blob, results):
    path.write_bytes(blob)
    handle = ctypes.c_void_p(12345)
    rc = lib.cmpct_open(os.fsencode(path), ctypes.byref(handle))
    assert rc == -3 and not handle.value, (name, rc, handle.value)
    results.append({"name": name, "status": rc, "sha256": hashlib.sha256(blob).hexdigest()})


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_hardlink_owner_o14.py RESULT.json")
    lib = load_library()
    setup(lib)
    observations = []
    with tempfile.TemporaryDirectory(prefix="cmpct-hardlink-o14-") as temp:
        home = Path(temp)
        archive_a = make_archive(home, "a.bin")
        archive_b = make_archive(home, "b.bin")
        pair = {}
        for label, archive, expected in (
            ("a", archive_a, "a.bin"), ("b", archive_b, "b.bin")
        ):
            handle = open_native(lib, archive)
            try:
                paths = map_paths(lib, handle)
                assert all(x in paths for x in
                           ("a.bin", "b.bin", "z_alias.bin", "directory", "symlink"))
                rc, ix = owner(lib, handle, paths["z_alias.bin"])
                assert rc == 0 and ix == paths[expected], (label, rc, ix, paths)
                # No hidden behavior change to the old range reader.
                out = ctypes.create_string_buffer(len(A))
                copied = ctypes.c_size_t(7)
                assert lib.cmpct_entry_read_range(
                    handle, paths["z_alias.bin"], 0, out, len(A), ctypes.byref(copied)
                ) == -7 and copied.value == 0
                # Valid owner ordinal 0 must not be confused with a zeroed failure.
                for plain in ("a.bin", "b.bin", "directory", "symlink"):
                    assert owner(lib, handle, paths[plain]) == (-7, 0)
                assert owner(lib, handle, len(paths) + 1) == (-6, 0)
                null_output = ctypes.c_size_t(12345)
                assert lib.cmpct_entry_hardlink_owner(
                    None, paths["z_alias.bin"], ctypes.byref(null_output)
                ) == -1 and null_output.value == 0
                assert lib.cmpct_entry_hardlink_owner(
                    handle, paths["z_alias.bin"], None
                ) == -1
                pair[label] = {"archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                               "target": expected, "owner_ordinal": ix,
                               "paths": paths}
            finally:
                lib.cmpct_close(handle)
        assert pair["a"]["archive_sha256"] != pair["b"]["archive_sha256"]
        assert pair["a"]["owner_ordinal"] != pair["b"]["owner_ordinal"]

        original = archive_a.read_bytes()
        wire_index, _payload, _flags = wire_parts(original)
        paths = {row[0]: i for i, row in enumerate(wire_index["files"])}
        assert wire_index["files"][paths["z_alias.bin"]][6] == ["a.bin"]
        malformed = [
            ("missing_owner", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, ["missing.bin"])),
            ("self_cycle", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, ["z_alias.bin"])),
            ("directory_owner", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, ["directory"])),
            ("symlink_owner", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, ["symlink"])),
            ("unsafe_owner", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, ["../escape"])),
            ("wrong_size", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(4, len(A) + 1)),
            ("wrong_shape", lambda i: i["files"][paths["z_alias.bin"]].__setitem__(6, [23])),
        ]
        for name, mutation in malformed:
            expect_failed_open(lib, home / (name + ".cmpct"), name,
                               rebuild(original, mutation), observations)
        # Reconstruct a valid alias chain and a signed cycle without relying on
        # the native production graph resolver to mutate either index.
        def add_second_alias(index):
            row = copy.deepcopy(index["files"][paths["z_alias.bin"]])
            row[0] = "y_alias.bin"
            row[6] = ["a.bin"]
            index["files"].append(row)
            index["files"][paths["z_alias.bin"]][6] = ["y_alias.bin"]
        chain = rebuild(original, add_second_alias)
        chain_file = home / "valid-chain.cmpct"
        chain_file.write_bytes(chain)
        handle = open_native(lib, chain_file)
        try:
            indices = map_paths(lib, handle)
            assert owner(lib, handle, indices["z_alias.bin"]) == (0, indices["a.bin"])
            assert owner(lib, handle, indices["y_alias.bin"]) == (0, indices["a.bin"])
        finally:
            lib.cmpct_close(handle)
        observations.append({"name": "valid_chain", "sha256": hashlib.sha256(chain).hexdigest(),
                             "status": "ACCEPT"})
        def add_cycle(index):
            add_second_alias(index)
            index["files"][-1][6] = ["z_alias.bin"]
        expect_failed_open(lib, home / "cycle.cmpct", "two_alias_cycle",
                           rebuild(original, add_cycle), observations)

        # Held-out chain/star same-member-count stress: signed index mutation
        # preserves physical payload bytes and source archive identity.
        source = home / "stress-src"
        source.mkdir()
        # Lexically first ordinary owner: Builder's inode-first dedup order matters.
        (source / "a_root.bin").write_bytes(A)
        for j in range(1024):
            os.link(source / "a_root.bin", source / f"l{j:04d}.bin")
        stress_path = home / "stress-star.cmpct"
        Builder(source, workers=1, reproducible=True).build(stress_path)
        star = stress_path.read_bytes()
        def make_chain(index):
            aliases = [row for row in index["files"] if row[1] == 3]
            aliases.sort(key=lambda row: row[0])
            for i, row in enumerate(aliases):
                row[6] = ["a_root.bin" if i == 0 else aliases[i-1][0]]
        chain_stress = rebuild(star, make_chain)
        measurements = {}
        for name, wire in (("star", star), ("chain", chain_stress)):
            target = home / ("stress-" + name + ".cmpct")
            target.write_bytes(wire)
            timings = []
            for _ in range(7):
                t0 = time.perf_counter_ns()
                h = open_native(lib, target)
                dt = time.perf_counter_ns() - t0
                try:
                    ix = map_paths(lib, h)
                    assert len(ix) == 1025
                    assert owner(lib, h, ix["l1023.bin"]) == (0, ix["a_root.bin"])
                    assert owner(lib, h, ix["l0000.bin"]) == (0, ix["a_root.bin"])
                finally:
                    lib.cmpct_close(h)
                timings.append(dt / 1e6)
            measurements[name] = {"median_open_ms": statistics.median(timings),
                                  "raw_open_ms": timings,
                                  "archive_bytes": len(wire),
                                  "sha256": hashlib.sha256(wire).hexdigest()}
        # Soft diagnostic only; no CI pass/fail from noisy ratio alone.
        observations.append({"name": "1024_chain_star", "status": "PASS",
                             "measurements": measurements})

    result = {
        "schema": "cmpct-native-hardlink-owner-o14-v1",
        "decision": "OWNER_ORDINAL_CANDIDATE_CORRECT_ON_HOSTED_STRUCTURAL_COURT",
        "base_source_sha": "43ba79f9b9395af22a0f408de565704c268a4758",
        "distinct_inode_graph_pair": pair,
        "hostile_and_stress_courts": observations,
        "claims_not_earned": ["release", "official ABBA", "platform portability",
                               "full-tree secure extraction", "source mutation recovery"],
    }
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "cases": len(observations),
                      "stress": measurements}, sort_keys=True))


if __name__ == "__main__":
    main()
