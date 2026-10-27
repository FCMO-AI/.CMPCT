#!/usr/bin/env python3
"""O228b: true released-Builder CDC occurrence + fully charged virtual-index oracle.
Research-only; never writes or accepts a new CMPCT storage tag on disk.
"""
from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import random
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

import msgpack
from cmpct.core import Builder, CMPCT
from cmpct.codec import HDR, S_CDC, S_CHUNKS, zc
import cmpct.builder as builder_module
import cmpct.reader as reader_module

SIZE = 16 * 1024 * 1024
PROFILES = ("zero", "one-period", "two-period", "shifted", "structured", "independent")


def source_bytes(name: str) -> bytes:
    p = random.Random(20261027).randbytes(1024 * 1024)
    q = random.Random(20261028).randbytes(1024 * 1024)
    if name == "zero":
        return bytes(SIZE)
    if name == "one-period":
        return p * 16
    if name == "two-period":
        return (p + q) * 8
    if name == "shifted":
        return ((p + b"inserted-drift" * 73) * 16)[:SIZE]
    if name == "structured":
        word = b"sku=008371|timestamp=2026-10-27|status=active|bytes=0012345\n"
        return (word * (SIZE // len(word) + 1))[:SIZE]
    if name == "independent":
        return random.Random(20261029).randbytes(SIZE)
    raise ValueError(name)


def semantic_sha(refs, runs):
    h1 = hashlib.sha256()
    for length, owner in refs:
        h1.update(struct.pack("<QQ", length, owner))
    h2 = hashlib.sha256()
    for count, length, owner in runs:
        chunk = struct.pack("<QQ", length, owner)
        for _ in range(count):
            h2.update(chunk)
    assert h1.digest() == h2.digest()
    return h1.hexdigest()


def make_runs(refs):
    runs = []
    for length, owner in refs:
        if runs and runs[-1][1] == length and runs[-1][2] == owner:
            runs[-1][0] += 1
        else:
            runs.append([1, length, owner])
    return runs


def decode_child(file: str):
    raw = Path(file).read_bytes()
    tracemalloc.start()
    t = time.perf_counter_ns()
    c = time.process_time_ns()
    ix = msgpack.unpackb(raw, raw=False)
    cpu = time.process_time_ns() - c
    wall = time.perf_counter_ns() - t
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    print(json.dumps({"wall_ns": wall, "cpu_ns": cpu,
                      "heap_peak": peak, "entries": len(ix["files"][0][6][1])}))


def profile(name, root: Path):
    src = root / "input"
    src.mkdir()
    payload = source_bytes(name)
    digest = hashlib.sha256(payload).hexdigest()
    (src / "data.bin").write_bytes(payload)
    del payload
    gc.collect()
    output = root / "original.cmpct"
    t = time.perf_counter_ns()
    c = time.process_time_ns()
    b = Builder(src, workers=1, reproducible=True)
    stats = b.build(output)
    build_wall = time.perf_counter_ns() - t
    build_cpu = time.process_time_ns() - c
    with CMPCT(output) as reader:
        assert reader.verify() == 1
        assert hashlib.sha256(reader.read("data.bin")).hexdigest() == digest
        for off in (0, SIZE // 2 - 64, SIZE - 64):
            expected = source_bytes(name)[off:off + 64]
            assert reader.read_range("data.bin", off, 64) == expected
        index = reader.index
        assert len(index["files"]) == 1
        storage = index["files"][0][6]
        assert storage[0] == S_CDC, f"{name} not S_CDC: {storage[0]}"
        refs = storage[1]
        owners = len(set(x[1] for x in refs))
        runs = make_runs(refs)
        sem = semantic_sha(refs, runs)
    original = output.read_bytes()
    header = HDR.unpack(original[:HDR.size])
    compressed_original_length = header[3]
    packed_original = msgpack.packb(index, use_bin_type=True)
    assert len(zc(packed_original, 12)) == compressed_original_length
    experiment = copy.deepcopy(index)
    experiment["files"][0][6] = [105, runs]
    t = time.perf_counter_ns()
    c = time.process_time_ns()
    packed_runs = msgpack.packb(experiment, use_bin_type=True)
    comp_runs = zc(packed_runs, 12)
    oracle_wall = time.perf_counter_ns() - t
    oracle_cpu = time.process_time_ns() - c
    new_size = len(original) + 2 * (len(comp_runs) - compressed_original_length)
    assert new_size > 0
    observations = {}
    for label, wire in (("literal", packed_original), ("runs", packed_runs)):
        f = root / (label + ".msgpack")
        f.write_bytes(wire)
        trials = []
        for _ in range(3):
            got = subprocess.run([sys.executable, __file__, "--decode-child", str(f)],
                                 capture_output=True, text=True, check=True, timeout=45)
            trials.append(json.loads(got.stdout))
        observations[label] = trials
    m = lambda key, field: statistics.median(x[field] for x in observations[key])
    ratio = m("literal", "heap_peak") / max(1, m("runs", "heap_peak"))
    return {
        "name": name, "builder_sha": hashlib.sha256(Path(builder_module.__file__).read_bytes()).hexdigest(),
        "reader_sha": hashlib.sha256(Path(reader_module.__file__).read_bytes()).hexdigest(),
        "archive_sha256": hashlib.sha256(original).hexdigest(),
        "logical_sha256": digest, "logical_bytes": SIZE, "archive_bytes": len(original),
        "index_bytes": compressed_original_length, "oracle_index_bytes": len(comp_runs),
        "full_archive_byte_delta": new_size - len(original),
        "full_archive_pct_delta": (new_size - len(original)) / len(original) * 100,
        "cdc_ref_count": len(refs), "distinct_owners": owners,
        "run_count": len(runs), "max_run": max(x[0] for x in runs),
        "ref_semantic_sha256": sem, "file_integrity_pass": True,
        "builder_wall_ns": build_wall, "builder_cpu_ns": build_cpu,
        "candidate_index_encode_wall_ns": oracle_wall,
        "candidate_index_encode_cpu_ns": oracle_cpu,
        "unpack_heap_ratio": ratio, "decode_trials": observations,
        "builder_stats": stats,
    }


def main(out):
    rows = []
    for name in PROFILES:
        with tempfile.TemporaryDirectory(prefix="o228b-" + name + "-") as d:
            row = profile(name, Path(d))
            rows.append(row)
        print(name, row["cdc_ref_count"], row["run_count"],
              row["full_archive_byte_delta"], round(row["unpack_heap_ratio"], 3),
              file=sys.stderr, flush=True)
    assert len(rows) == 6 and all(x["file_integrity_pass"] for x in rows)
    qualifying = [x for x in rows if x["name"] not in ("zero", "independent")
                  and x["max_run"] >= 8 and x["unpack_heap_ratio"] >= 2
                  and x["full_archive_byte_delta"] <= 0]
    material = [x for x in rows if x["full_archive_pct_delta"] <= -1.0]
    decision = ("BOUNDED_BUILDER_TRANSFER_SEED" if len(qualifying) >= 2 and material
                else "NO_BUILDER_TRANSFER_AT_THIS_SCALE")
    result = {
        "schema": "cmpct-o228b-builder-transfer-v1",
        "status": "RESEARCH_ONLY_NO_PRODUCT_CREDIT",
        "released_reference": "main@80c358f8824ec1b20d349c92ed94c898090969b0",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version, "msgpack": str(msgpack.version),
        "rows": rows, "qualifying_nontrivial": [x["name"] for x in qualifying],
        "material_savings_profiles": [x["name"] for x in material],
        "decision": decision,
    }
    Path(out).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": decision, "rows": len(rows),
                      "child_process_observations": 36}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--decode-child")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.decode_child:
        decode_child(args.decode_child)
    elif args.output:
        main(args.output)
    else:
        parser.error("specify --output or --decode-child")
