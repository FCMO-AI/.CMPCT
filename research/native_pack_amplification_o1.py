#!/usr/bin/env python3
"""O1: native r24 S_PACK amplification, exact archive bytes, read-only evidence.

The paired decoded-once arm is an oracle about *hypothetical* immutable snapshots,
not a safe product cache, and neither arm is an official release benchmark.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import struct
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.codec import CODEC_RAW, CODEC_ZSTD, S_PACK, BHDR, sha, zd
from cmpct.reader import CMPCT

NAMES = 256
SIZE = 768
READ_START = 17
READ_SIZE = 64
REPS = 7
COUNTS = (1, 16, 128, 256)
LIBRARY = Path(__file__).resolve().parents[1] / "native/cmpct-core/target/release/libcmpct_core.so"


def source_bytes(kind: str, index: int) -> bytes:
    if kind == "entropy":
        return hashlib.shake_256(f"cmpct-pack-o1-entropy-{index:05d}".encode()).digest(SIZE)
    prefix = f"entry={index:05d};component=worker;priority={index % 17:02d};\n".encode()
    motif = (b"kind=config;owner=bounded;codec=pack;mode=immutable;"
             b"output=exact;reads=selective;verify=sha256;\n")
    return (prefix + motif * 12)[:SIZE].ljust(SIZE, b"-")


def make_corpus(home: Path, kind: str) -> dict:
    source = home / (kind + "-input")
    source.mkdir()
    tree_hash = hashlib.sha256()
    for i in range(NAMES):
        name = f"entry-{i:05d}.txt"
        data = source_bytes(kind, i)
        (source / name).write_bytes(data)
        tree_hash.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    archive = home / (kind + ".cmpct")
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as ar:
        groups = {}
        for row in ar.files:
            if row[1] == 0 and row[6] and row[6][0] == S_PACK:
                groups.setdefault(int(row[6][1]), []).append(row)
        assert groups, (kind, "Builder created no S_PACK")
        pack_idx, members = max(groups.items(), key=lambda pair: (len(pair[1]), ar.blobs[pair[0]][1]))
        meta = ar.blobs[pack_idx]
        expected_codec = CODEC_ZSTD if kind == "structured" else CODEC_RAW
        assert int(meta[3]) == expected_codec, (kind, "no expected physical codec", meta, groups.keys())
        assert len(members) == NAMES, (kind, len(members), NAMES)
        assert int(meta[1]) >= 100 * 1024, (kind, "pack too small", meta)
        physical = int(ar.record_base) + int(meta[0])
        wire = archive.read_bytes()
        fields = BHDR.unpack_from(wire, physical)
        assert fields[0] == b"CMA4"
        assert fields[1] == expected_codec
        assert fields[4] == int(meta[1]) and fields[5] == int(meta[2])
        assert fields[6] == int(meta[4])
        data_start = physical + BHDR.size + fields[6]
        physical_payload = wire[data_start:data_start + fields[5]]
        assert len(physical_payload) == fields[5]
        decoded = physical_payload if expected_codec == CODEC_RAW else zd(physical_payload, fields[4])
        assert len(decoded) == fields[4] and sha(decoded) == fields[8]
        refs = [
            {"name": row[0], "offset": int(row[6][2]), "size": int(row[6][3])}
            for row in sorted(members, key=lambda row: row[0])
        ]
        for ref in refs:
            expected = (source / ref["name"]).read_bytes()
            assert decoded[ref["offset"]: ref["offset"] + ref["size"]] == expected
    return {
        "kind": kind, "source_tree_sha256": tree_hash.hexdigest(),
        "archive": str(archive), "source_dir": str(source),
        "archive_sha256": hashlib.sha256(wire).hexdigest(),
        "archive_bytes": len(wire), "physical_codec": expected_codec,
        "pack_index": pack_idx, "pack_uncompressed_bytes": int(meta[1]),
        "pack_compressed_bytes": int(meta[2]),
        "pack_sha256": fields[8].hex(),
        "pack_payload_offset": data_start, "members": refs,
        "expected_read_length": READ_SIZE,
    }


def native_api():
    lib = ctypes.CDLL(str(LIBRARY))
    lib.cmpct_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_open.restype = ctypes.c_int32
    lib.cmpct_close.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.argtypes = [ctypes.c_void_p]
    lib.cmpct_entry_count.restype = ctypes.c_size_t
    lib.cmpct_entry_path.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_path.restype = ctypes.c_int32
    lib.cmpct_entry_read_range.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint64,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.cmpct_entry_read_range.restype = ctypes.c_int32
    return lib


def measure_one(manifest: dict) -> dict:
    assert hashlib.sha256(Path(manifest["archive"]).read_bytes()).hexdigest() == manifest["archive_sha256"]
    lib = native_api()
    handle = ctypes.c_void_p()
    assert lib.cmpct_open(os.fsencode(manifest["archive"]), ctypes.byref(handle)) == 0
    results = {}
    expected = {}
    for ref in manifest["members"]:
        raw = (Path(manifest["source_dir"]) / ref["name"]).read_bytes()
        expected[ref["name"]] = raw[READ_START: READ_START + READ_SIZE]
        assert len(expected[ref["name"]]) == READ_SIZE
    try:
        by_name = {}
        for i in range(lib.cmpct_entry_count(handle)):
            length = ctypes.c_size_t()
            assert lib.cmpct_entry_path(handle, i, None, 0, ctypes.byref(length)) == 0
            dest = ctypes.create_string_buffer(length.value + 1)
            assert lib.cmpct_entry_path(handle, i, dest, len(dest), ctypes.byref(length)) == 0
            by_name[dest.value.decode()] = i
        assert set(expected).issubset(by_name)
        refs = manifest["members"]

        def native(batch):
            outputs = []
            for ref in batch:
                dst = ctypes.create_string_buffer(READ_SIZE)
                got = ctypes.c_size_t()
                ret = lib.cmpct_entry_read_range(
                    handle, by_name[ref["name"]], READ_START,
                    dst, READ_SIZE, ctypes.byref(got)
                )
                assert ret == 0 and got.value == READ_SIZE, (ref, ret, got.value)
                outputs.append(dst.raw[:got.value])
            return outputs

        def single_snapshot(batch):
            # Deliberately one complete read+decode+SHA per *batch*, NOT per member.
            # This sacrifices the current reader's inter-call tamper detection;
            # do not infer a cache is safe from favorable runtime measurements.
            with Path(manifest["archive"]).open("rb") as source:
                source.seek(manifest["pack_payload_offset"])
                payload = source.read(manifest["pack_compressed_bytes"])
            assert len(payload) == manifest["pack_compressed_bytes"]
            if manifest["physical_codec"] == CODEC_ZSTD:
                decoded = zd(payload, manifest["pack_uncompressed_bytes"])
            else:
                decoded = payload
            assert len(decoded) == manifest["pack_uncompressed_bytes"]
            assert hashlib.sha256(decoded).hexdigest() == manifest["pack_sha256"]
            return [
                decoded[ref["offset"] + READ_START: ref["offset"] + READ_START + READ_SIZE]
                for ref in batch
            ]

        def timed(operation, batch):
            cpu0 = time.process_time_ns()
            wall0 = time.perf_counter_ns()
            out = operation(batch)
            wall1 = time.perf_counter_ns()
            cpu1 = time.process_time_ns()
            assert len(out) == len(batch)
            for ref, actual in zip(batch, out):
                assert actual == expected[ref["name"]], (manifest["kind"], ref["name"])
            return {"wall_ns": wall1 - wall0, "cpu_ns": cpu1 - cpu0}

        # Consume first-use import, mmap, filesystem-cache and native symbol costs.
        native(refs[:2]); single_snapshot(refs[:2])
        for count in COUNTS:
            batch = refs[:count]
            samples = {"native": [], "one_decode_oracle": []}
            for _ in range(REPS):
                for label, action in (("native", native), ("one_decode_oracle", single_snapshot),
                                      ("one_decode_oracle", single_snapshot), ("native", native)):
                    samples[label].append(timed(action, batch))
            results[str(count)] = {
                "raw": samples,
                "median_native_ms": statistics.median(s["wall_ns"] for s in samples["native"]) / 1e6,
                "median_snapshot_ms": statistics.median(s["wall_ns"] for s in samples["one_decode_oracle"]) / 1e6,
                "median_native_cpu_ms": statistics.median(s["cpu_ns"] for s in samples["native"]) / 1e6,
                "median_snapshot_cpu_ms": statistics.median(s["cpu_ns"] for s in samples["one_decode_oracle"]) / 1e6,
                "native_complete_decode_bytes_inferred": count * manifest["pack_uncompressed_bytes"]
                    if manifest["physical_codec"] == CODEC_ZSTD else 0,
                "oracle_decoded_bytes_inferred": manifest["pack_uncompressed_bytes"]
                    if manifest["physical_codec"] == CODEC_ZSTD else 0,
                "native_requested_output_bytes": count * READ_SIZE,
                "physical_compressed_bytes_per_native_read_upper": manifest["pack_compressed_bytes"]
                    if manifest["physical_codec"] == CODEC_ZSTD else READ_SIZE,
                "oracle_physical_bytes_read": manifest["pack_compressed_bytes"],
            }
        return {
            "corpus": {k: v for k, v in manifest.items() if k != "members"},
            "native_build_library": str(LIBRARY),
            "observations": results,
            "peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "decoded_once_live_bytes_lower_bound": manifest["pack_uncompressed_bytes"],
            "validity": "same actual r24 Builder archive, read-only Rust native C ABI, source-exact positive bytes",
            "warning": "Oracle assumes scoped immutability, not current native per-read SHA freshness. Not product/cache/release evidence.",
        }
    finally:
        lib.cmpct_close(handle)


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--measure":
        manifest = json.loads(Path(sys.argv[2]).read_text())
        result = measure_one(manifest)
        Path(sys.argv[3]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("O1_CHILD", manifest["kind"], "rss_kib", result["peak_rss_kib_process"])
        return
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_pack_amplification_o1.py RESULT.json")
    destination = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="cmpct-native-pack-o1-") as td:
        home = Path(td)
        outputs = []
        for kind in ("structured", "entropy"):
            manifest = make_corpus(home, kind)
            manifest_path = home / (kind + "-manifest.json")
            receipt_path = home / (kind + "-result.json")
            manifest_path.write_text(json.dumps(manifest, sort_keys=True))
            subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--measure",
                 str(manifest_path), str(receipt_path)],
                check=True,
            )
            outputs.append(json.loads(receipt_path.read_text()))
        receipt = {
            "schema": "cmpct-v031-native-pack-runtime-o1-v1",
            "status": "READ_ONLY_PRODUCT_PROFILING_NOT_CACHE",
            "source_fingerprint": os.environ.get("EVIDENCE_HEAD", "LOCAL_UNBOUND"),
            "reader_parent_pr": 307, "immutable_r24_format": 24,
            "host": {"platform": sys.platform, "python": sys.version, "uname": list(os.uname())},
            "repetitions": REPS, "interleaving": "ABBA per count",
            "cases": outputs,
        }
        destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        for case in outputs:
            print("CASE", case["corpus"]["kind"], "codec", case["corpus"]["physical_codec"],
                  "pack", case["corpus"]["pack_uncompressed_bytes"], "bytes")
            for n, row in case["observations"].items():
                print("READS", n, "native_ms", round(row["median_native_ms"], 4),
                      "snapshot_oracle_ms", round(row["median_snapshot_ms"], 4))
        print("O1_RESULTS", destination, hashlib.sha256(destination.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
