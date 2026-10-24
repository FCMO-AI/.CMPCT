#!/usr/bin/env python3
"""O3: source-exact independent/native product court for bounded, opt-in PACK batches.

Fixed vectors are authored independently of the CMPCT Builder. The stress/ABBA
cohort uses the ordinary public Builder and rechecks every returned byte.
Neither mechanism changes the wire format nor replaces ordinary single reads.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import struct
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.codec import CODEC_ZSTD, S_PACK
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/conformance/v24-pack.json"
LIBRARY = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
REPS = 7
COUNTS = (1, 16, 128, 256)


class Request(ctypes.Structure):
    _fields_ = [
        ("entry_index", ctypes.c_size_t),
        ("offset", ctypes.c_uint64),
        ("length", ctypes.c_size_t),
    ]


def load_library():
    lib = ctypes.CDLL(str(LIBRARY))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_path.restype = ctypes.c_int
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int
    lib.cmpct_pack_read_batch.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(Request), ctypes.c_size_t,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_pack_read_batch.restype = ctypes.c_int
    return lib


def open_native(lib, path):
    handle = ctypes.c_void_p()
    status = lib.cmpct_open(os.fsencode(path), ctypes.byref(handle))
    assert status == 0 and handle.value, (str(path), status)
    return handle


def map_paths(lib, handle):
    result = {}
    for index in range(lib.cmpct_entry_count(handle)):
        size = ctypes.c_size_t()
        assert lib.cmpct_entry_path(handle, index, None, 0, ctypes.byref(size)) == 0
        buf = ctypes.create_string_buffer(size.value + 1)
        assert lib.cmpct_entry_path(handle, index, buf, len(buf), ctypes.byref(size)) == 0
        result[buf.value.decode()] = index
    return result


def batch(lib, handle, requests, capacity=None, sentinel=0xA5):
    values = (Request * len(requests))(*[Request(*row) for row in requests])
    total = sum(x[2] for x in requests)
    if capacity is None:
        capacity = total
    out = ctypes.create_string_buffer(bytes([sentinel]) * max(capacity, 1))
    written = ctypes.c_size_t(987654)
    status = lib.cmpct_pack_read_batch(
        handle, values, len(values), out, capacity, ctypes.byref(written)
    )
    return status, out.raw[:capacity], written.value


def serial(lib, handle, requests):
    values = []
    for index, start, length in requests:
        out = ctypes.create_string_buffer(max(1, length))
        n = ctypes.c_size_t()
        status = lib.cmpct_entry_read_range(
            handle, index, start, out, length, ctypes.byref(n)
        )
        assert status == 0 and n.value == length, (index, start, length, status)
        values.append(out.raw[:length])
    return b"".join(values)


def fixed_court(lib, home):
    vectors = json.loads(GOLDEN.read_text())["vectors"]
    results = []
    # C ABI contract regression: a valid out_read pointer must be cleared
    # even when archive itself is null. A null out_read must never be dereferenced.
    null_output = ctypes.create_string_buffer(bytes([0xA5]) * 8)
    null_witness = ctypes.c_size_t(987654)
    null_requests = (Request * 1)(Request(0, 0, 8))
    null_status = lib.cmpct_pack_read_batch(
        None, null_requests, 1, null_output, 8, ctypes.byref(null_witness)
    )
    assert null_status == -1 and null_witness.value == 0
    assert null_output.raw == bytes([0xA5]) * 8
    for vector in vectors:
        wire = base64.b64decode(vector["archive_base64"], validate=True)
        assert hashlib.sha256(wire).hexdigest() == vector["archive_sha256"]
        path = home / f"{vector['name']}.cmpct"
        path.write_bytes(wire)
        handle = open_native(lib, path)
        try:
            paths = map_paths(lib, handle)
            requests = []
            for spec in vector["ranges"]:
                requests.append((paths[spec["name"]], spec["offset"], spec["length"]))
            # Duplicate and complete-member range: independent per-member SHA is retained.
            name = "alpha-copy.txt"
            requests.extend([
                (paths[name], 0, vector["files"][name]["size"]),
                (paths[name], 0, 0),
                requests[0],
            ])
            want = b"".join(
                bytes.fromhex(vector["files"][next(n for n, i in paths.items() if i == ix)]["hex"])[offset:offset + length]
                for ix, offset, length in requests
            )
            if vector["physical_codec"] == CODEC_ZSTD:
                status, actual, length = batch(lib, handle, requests)
                assert status == 0 and length == len(want) and actual == want
                assert serial(lib, handle, requests) == want
                # Reject underallocated output without changing any caller-owned bytes.
                status, untouched, length = batch(lib, handle, requests, len(want) - 1)
                assert status == -6 and length == 0 and set(untouched) == {0xA5}
                for bad in [
                    [(len(paths) + 42, 0, 1)],
                    [(paths[name], vector["files"][name]["size"], 1)],
                ]:
                    status, untouched, length = batch(lib, handle, bad)
                    assert status == -6 and length == 0 and set(untouched) == {0xA5}
                # Both mutations occur against the SAME native-open handle. No cache
                # can silently reuse the last successful decoded PACK across batches.
                compressed_index_size = struct.unpack_from("<Q", wire, 12)[0]
                physical_header = 68 + compressed_index_size
                physical_payload = physical_header + 64
                for bad_offset in [physical_header + 32, physical_payload]:
                    previous = wire[bad_offset]
                    with path.open("r+b") as fd:
                        fd.seek(bad_offset)
                        fd.write(bytes([previous ^ 1]))
                        fd.flush()
                        os.fsync(fd.fileno())
                    status, untouched, length = batch(lib, handle, requests)
                    assert status != 0 and length == 0 and set(untouched) == {0xA5}, (bad_offset, status)
                    with path.open("r+b") as fd:
                        fd.seek(bad_offset)
                        fd.write(bytes([previous]))
                        fd.flush()
                        os.fsync(fd.fileno())
                    status, actual, length = batch(lib, handle, requests)
                    assert status == 0 and actual == want and length == len(want)
                assert path.read_bytes() == wire
            else:
                # RAW is deliberately excluded: packing all RAW bytes would enlarge
                # isolated selective physical reads and weaken locality economics.
                status, untouched, length = batch(lib, handle, requests)
                assert status == -7 and length == 0 and set(untouched) == {0xA5}
            results.append({"vector": vector["name"], "codec": vector["physical_codec"],
                            "passes": True, "sha256": vector["archive_sha256"]})
        finally:
            lib.cmpct_close(handle)
    return results


def source_bytes(i):
    prefix = f"entry={i:05d};worker=bounded;priority={i % 17};\n".encode()
    motif = b"kind=config;codec=pack;mode=verified;data=exact;read=selective;\n"
    return (prefix + motif * 14)[:768].ljust(768, b"-")



def linux_proc_rchar():
    """Linux process logical read(2) bytes; not physical storage I/O."""
    path = Path("/proc/self/io")
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith("rchar:"):
            return int(line.partition(":")[2].strip())
    raise RuntimeError("/proc/self/io has no rchar counter")


def product_court(lib, home):
    source = home / "stress-input"
    source.mkdir()
    # 512 members force at least two physical micro-PACK owners under the
    # ordinary bounded pack builder, testing real mixed-owner rejection.
    for i in range(512):
        (source / f"entry-{i:05d}.txt").write_bytes(source_bytes(i))
    archive = home / "stress.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as ar:
        groups = {}
        for row in ar.files:
            if row[1] == 0 and row[6] and row[6][0] == S_PACK:
                groups.setdefault(int(row[6][1]), []).append(row)
        assert len(groups) >= 2, ("expected 2 physical PACK owners", len(groups))
        candidates = [(owner, rows) for owner, rows in groups.items()
                      if len(rows) >= 256 and int(ar.blobs[owner][3]) == CODEC_ZSTD]
        assert candidates, ("no 256+ member Zstd PACK", len(groups))
        owner, rows = max(candidates, key=lambda q: len(q[1]))
        assert ar.blobs[owner][1] <= 16 * 1024 * 1024
        other_owner, other_rows = next((o, r) for o, r in groups.items() if o != owner)
        source_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    handle = open_native(lib, archive)
    try:
        mapped = map_paths(lib, handle)
        pool = sorted(mapped[r[0]] for r in rows)
        assert len(pool) >= 256
        # Ordinal index determines source identity through map_paths reverse map.
        reverse = {v: k for k, v in mapped.items()}
        raw = {}
        for size in COUNTS:
            reqs = [(index, 17, 64) for index in pool[:size]]
            expected = b"".join((source / reverse[i]).read_bytes()[17:81] for i in pool[:size])
            assert serial(lib, handle, reqs) == expected
            status, data, written = batch(lib, handle, reqs)
            assert status == 0 and data == expected and written == len(expected)
            arms = {
                "serial": {"ms": [], "cpu_ms": [], "rchar_delta": []},
                "batch": {"ms": [], "cpu_ms": [], "rchar_delta": []},
            }
            for turn in range(REPS):
                for label in (["serial", "batch", "batch", "serial"] if turn % 2 == 0
                              else ["batch", "serial", "serial", "batch"]):
                    # O4 additive counters were prospectively registered AFTER the
                    # immutable O3 result. Read /proc OUTSIDE the wall/CPU window.
                    before_rchar = linux_proc_rchar()
                    t0 = time.perf_counter_ns()
                    cpu0 = time.process_time_ns()
                    actual = (serial(lib, handle, reqs) if label == "serial"
                              else batch(lib, handle, reqs)[1])
                    cpu1 = time.process_time_ns()
                    elapsed = time.perf_counter_ns() - t0
                    after_rchar = linux_proc_rchar()
                    assert actual == expected
                    arms[label]["ms"].append(elapsed / 1e6)
                    arms[label]["cpu_ms"].append((cpu1 - cpu0) / 1e6)
                    if before_rchar is not None and after_rchar is not None:
                        arms[label]["rchar_delta"].append(after_rchar - before_rchar)
            raw[size] = {
                label: {
                    **samples,
                    "median_ms": statistics.median(samples["ms"]),
                    "median_cpu_ms": statistics.median(samples["cpu_ms"]),
                    "median_rchar_delta": (
                        statistics.median(samples["rchar_delta"])
                        if samples["rchar_delta"] else None
                    ),
                }
                for label, samples in arms.items()
            }
        mixed = [(pool[0], 0, 1), (mapped[other_rows[0][0]], 0, 1)]
        status, untouched, written = batch(lib, handle, mixed)
        assert status == -7 and written == 0 and set(untouched) == {0xA5}
        # A 16 MiB+ declared output fails before decoder or caller publication.
        many = [(pool[0], 0, 64)] * 1025
        status, untouched, written = batch(lib, handle, many)
        assert status == -4 and written == 0 and set(untouched) == {0xA5}
        return {
            "archive_sha256": source_sha,
            "pack_count": len(groups),
            "selected_pack_members": len(rows),
            "selected_owner": owner,
            "selected_decoded_bytes": int(ar.blobs[owner][1]),
            "physical_codec": CODEC_ZSTD,
            "raw_abba": raw,
            "rss_max_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "controls": "mixed-owner, oversized-request-count, per-member equivalence",
        }
    finally:
        lib.cmpct_close(handle)


def main():
    assert LIBRARY.is_file(), ("must build exact-source release Rust library", str(LIBRARY))
    lib = load_library()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-pack-batch-o3-") as td:
        home = Path(td)
        fixed = fixed_court(lib, home)
        product = product_court(lib, home)
    payload = {"schema": "cmpct-native-pack-batch-o3-v1",
               "resource_measurement": "o4-linux-process-cpu-and-proc-rchar",
               "native_library_sha256": hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
               "fixed_independent": fixed, "builder_product": product,
               "status": "HOSTED_COURT_PASS"}
    assert len(sys.argv) == 2, "usage: python tests/native_pack_batch_abi.py RESULT_JSON"
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "fixed": fixed,
                      "product": {k:v for k,v in product.items() if k != "raw_abba"},
                      "median_ms": {n:{k:v["median_ms"] for k,v in sample.items()}
                                    for n,sample in product["raw_abba"].items()},
                      "median_cpu_ms": {n:{k:v["median_cpu_ms"] for k,v in sample.items()}
                                       for n,sample in product["raw_abba"].items()},
                      "median_rchar_delta": {n:{k:v["median_rchar_delta"] for k,v in sample.items()}
                                           for n,sample in product["raw_abba"].items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
