#!/usr/bin/env python3
"""J24C15 held-out signed r24 irregular-geometry/codec installed Reader court.

Research only. No Builder, threshold, product, comparator or package mutation.
All three independently installed historical/product Readers receive identical
Builder-independent archive bytes, paths and read operations. Positive and
negative data are preserved with a source-identity witness.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

from j24c14_published_fused_triplet import SOURCES, highwater, source_info

PROFILES = (("irregular-raw-65536", 65536, "raw"),
            ("irregular-raw-262144", 262144, "raw"),
            ("mixed-raw-zstd-65536", 65536, "mixed"))
REGIMES = ("q1-early", "q1-tail", "q6-mixed", "q64-mixed")
SEQUENCES = (("released", "native", "fused", "fused", "native", "released"),
             ("fused", "native", "released", "released", "native", "fused"))
CYCLES = 2
SAMPLES = 2
EXPECTED_BLOBS = {a: v["reader_blob"] for a, v in SOURCES.items()}


def hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def records_for(kind: str):
    if kind == "raw":
        sizes = (0, 1, 3, 7, 13, 29, 47, 89)
        codecs = ("raw",) * len(sizes)
    else:
        sizes = (1, 7, 33, 64, 2, 13, 127, 255)
        codecs = ("raw", "zstd") * 4
    return [(bytes(((19 * i + 31 * j) % 251) + 1 for j in range(sz)), codec)
            for i, (sz, codec) in enumerate(zip(sizes, codecs))]


def refs_for(n: int, owners: int):
    # Not the modulo-owners pattern used by J24C14: block rotations and
    # changing ownership deliberately cross stride-256 logical boundaries.
    return [(7 * i + i // 257 + (i // 4096) * 3) % owners for i in range(n)]


def signed_archive(records, members):
    """Serialize an independent complete r24 archive, including physical BHDR."""
    import msgpack
    from cmpct.codec import (MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
                             CODEC_RAW, CODEC_ZSTD, K_FILE, S_CHUNKS, zc, sha)
    physical = bytearray()
    blobs = []
    for payload, mode in records:
        codec = CODEC_RAW if mode == "raw" else CODEC_ZSTD
        compressed = payload if mode == "raw" else zc(payload, 6)
        blobs.append([len(physical), len(payload), len(compressed), codec, 0])
        physical.extend(BHDR.pack(BMAGIC, codec, 0, 0, len(payload),
                                  len(compressed), 0,
                                  binascii.crc32(payload) & 0xffffffff,
                                  sha(payload)))
        physical.extend(compressed)
    files = []
    for name, refs in members:
        logical = b"".join(records[i][0] for i in refs)
        files.append([name, K_FILE, 0o644, 946684800000000000,
                      len(logical), sha(logical), [S_CHUNKS, refs]])
    index = {"v": VERSION, "files": files, "blobs": blobs, "recipes": [],
             "dict_blob": None, "fsmeta": {}}
    raw = msgpack.packb(index, use_bin_type=True)
    compressed_index = zc(raw, 12)
    wire = (HDR.pack(MAGIC, VERSION, 0, len(compressed_index), len(raw),
                     len(physical), sha(raw)) + compressed_index +
            bytes(physical) + compressed_index +
            FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed_index),
                     len(raw), 0, sha(raw)))
    return wire


def queries_for(logical: bytes, regime: str, seed: int):
    size = len(logical)
    rnd = random.Random(seed)
    if regime == "q1-early":
        offsets = [0]
    elif regime == "q1-tail":
        offsets = [max(0, size - 16)]
    else:
        offsets = [max(0, size - 17), 0, size // 2, size // 5,
                   max(0, size - 1), size // 3]
        if regime == "q64-mixed":
            offsets.extend(rnd.randrange(size + 1) for _ in range(58))
    assert len(offsets) == (1 if regime.startswith("q1") else
                            6 if regime.startswith("q6") else 64)
    return [[p, min(16, size - p),
             logical[p:p + min(16, size - p)].hex()] for p in offsets]


def measure(path: Path, spec: dict):
    from cmpct.reader import CMPCT
    wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(path) as rd:
        wall1, cpu1 = time.perf_counter_ns(), time.process_time_ns()
        names = tuple(rd.by)
        assert names == ("fixed.bin",), names
        combined = hashlib.sha256()
        for start, length, expected_hex in spec["ranges"]:
            obtained = rd.read_range("fixed.bin", start, length)
            assert obtained.hex() == expected_hex, (start, length)
            combined.update(obtained)
        wall2, cpu2 = time.perf_counter_ns(), time.process_time_ns()
    wall3, cpu3 = time.perf_counter_ns(), time.process_time_ns()
    return {"open_wall_ns": wall1 - wall0, "open_cpu_ns": cpu1 - cpu0,
            "ranges_wall_ns": wall2 - wall1, "ranges_cpu_ns": cpu2 - cpu1,
            "close_wall_ns": wall3 - wall2, "close_cpu_ns": cpu3 - cpu2,
            "session_wall_ns": wall3 - wall0,
            "session_cpu_ns": cpu3 - cpu0,
            "answer_sha256": combined.hexdigest()}


def worker(archive: Path, spec_path: Path, arm: str):
    if arm not in SOURCES:
        raise ValueError("unknown source arm")
    spec = json.loads(spec_path.read_text())
    wire = archive.read_bytes()
    assert hexdigest(wire) == spec["wire_sha256"]
    source = source_info(arm)
    from cmpct.reader import CMPCT
    native_calls = 0
    if arm != "released":
        import cmpct._chunk_admission as admission
        hook_name = "_scan_refs_index" if arm == "fused" else "_scan_refs"
        original = getattr(admission, hook_name)
        assert original is not None, "ABI3 helper must exist in installed wheel"
        def spy(*args):
            nonlocal native_calls
            native_calls += 1
            return original(*args)
        setattr(admission, hook_name, spy)
    try:
        with CMPCT(archive) as rd:
            refs = rd.by["fixed.bin"][6][1]
            assert len(refs) == spec["count"]
            marks = getattr(rd, "_chunk_range_marks", {}).get("fixed.bin")
            if arm == "fused":
                assert marks is not None and len(marks) == (len(refs) + 255)//256
                assert type(original(refs, rd.index["blobs"], rd.by["fixed.bin"][4])) is tuple
            elif arm == "native":
                assert marks is None and original(refs, rd.index["blobs"], rd.by["fixed.bin"][4]) is True
            else:
                assert marks is None
            assert hexdigest(rd.read("fixed.bin")) == spec["logical_sha256"]
            assert rd.verify() == 1
    finally:
        if arm != "released":
            setattr(admission, hook_name, original)
    assert native_calls == (0 if arm == "released" else 1)
    samples = [measure(archive, spec) for _ in range(SAMPLES)]
    print(json.dumps({"arm": arm, "source": source, "count": spec["count"],
                      "family": spec["family"], "regime": spec["regime"],
                      "wire_sha256": spec["wire_sha256"],
                      "native_probe_calls": native_calls,
                      "rss_highwater_bytes": highwater(), "samples": samples},
                     sort_keys=True))


def budget_court(outdir: Path):
    # Distinct correctness/proof lane. Temporary cap=4 triggers the same code
    # branch as a naturally saturated cap, without pretending to measure 65k.
    import cmpct.reader as reader
    from cmpct.reader import CMPCT
    original_cap = reader._MAX_CHUNK_RANGE_HINTS
    assert original_cap == 65536
    records = [(b"abcd", "raw"), (b"1234567", "raw")]
    members = [("alpha.bin", [0] * 1024),
               ("beta.bin", [1] * 1024),
               ("gamma.bin", [0, 1] * 512)]
    logical = {name: b"".join(records[i][0] for i in refs)
               for name, refs in members}
    wire = signed_archive(records, members)
    path = outdir / "multi-member-budget.cmpct"
    path.write_bytes(wire)
    reader._MAX_CHUNK_RANGE_HINTS = 4
    try:
        with CMPCT(path) as rd:
            assert list(rd.by) == [name for name, _ in members]
            assert rd._chunk_range_hint_count == 4
            assert {name: len(marks) for name, marks in rd._chunk_range_marks.items()} == {"alpha.bin": 4}
            for name, raw in logical.items():
                assert rd.read(name) == raw
                for start, length in ((0, 8), (len(raw)//2, 8), (len(raw)-8, 8)):
                    assert rd.read_range(name, start, length) == raw[start:start+length]
            assert rd.verify() == 3
    finally:
        reader._MAX_CHUNK_RANGE_HINTS = original_cap
    return {"wire_sha256": hexdigest(wire), "original_cap": original_cap,
            "test_cap": 4, "retained": {"alpha.bin": 4},
            "files": [{"name": n, "size": len(logical[n]),
                       "sha256": hexdigest(logical[n])} for n, _ in members]}


def controller(output: Path, executables):
    for arm, py in executables.items():
        assert Path(py).is_file(), (arm, py)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Worker executes from an isolated cwd; signed fixture paths must be absolute.
    fixture_dir = output.resolve().parent / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_specs, workers = [], []
    with tempfile.TemporaryDirectory(prefix="j24c15-independent-cwd-") as cwd:
        for family, n, kind in PROFILES:
            records = records_for(kind)
            refs = refs_for(n, len(records))
            logical = b"".join(records[i][0] for i in refs)
            wire = signed_archive(records, [("fixed.bin", refs)])
            archive = fixture_dir / (family + ".cmpct")
            archive.write_bytes(wire)
            for regime in REGIMES:
                ranges = queries_for(logical, regime, 241500 + n)
                spec = {"family": family, "count": n, "regime": regime,
                        "owners": len(records), "codec_types": [c for _, c in records],
                        "owner_lengths": [len(p) for p, _ in records],
                        "logical_bytes": len(logical), "logical_sha256": hexdigest(logical),
                        "wire_bytes": len(wire), "wire_sha256": hexdigest(wire),
                        "ranges": ranges, "archive": archive.name}
                manifest = fixture_dir / (family + "-" + regime + ".json")
                manifest.write_text(json.dumps(spec, sort_keys=True) + "\n")
                fixture_specs.append(spec)
                for cycle in range(CYCLES):
                    for slot, arm in enumerate(SEQUENCES[cycle]):
                        t0 = time.perf_counter_ns()
                        cp = subprocess.run(
                            [executables[arm], str(Path(__file__).resolve()),
                             "--worker", str(archive), str(manifest), arm],
                            cwd=cwd, capture_output=True, text=True, timeout=120)
                        elapsed = time.perf_counter_ns() - t0
                        if cp.returncode:
                            raise RuntimeError(f"{family}/{regime}/{arm}/cycle{cycle}/slot{slot}: "
                                               f"{cp.stdout[-1000:]} {cp.stderr[-3000:]}")
                        row = json.loads(cp.stdout)
                        row.update(cycle=cycle, slot=slot, process_wall_ns=elapsed)
                        workers.append(row)
                print(f"J24C15_COMPLETED {family} {regime} workers={len(workers)}", flush=True)
        budget = budget_court(fixture_dir)
    receipt = {"schema": "j24c15-source-exact-heldout-v1",
               "evidence_head": os.environ.get("EVIDENCE_SHA", "unbound-local"),
               "sources": SOURCES, "profiles": fixture_specs, "workers": workers,
               "budget": budget,
               "comparison_rule": {"material_relative": 0.05,
                                   "material_absolute_ms": 3.0,
                                   "transferred_speedup": 1.2,
                                   "rss_delta_bytes": 8 * 1024 * 1024},
               "scope": "held-out signed RAW/RAW-Zstd S_CHUNKS; Ubuntu Python 3.11 only; no promotion"}
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(f"J24C15_WORKERS={len(workers)} SESSIONS={len(workers)*SAMPLES}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--released-python")
    ap.add_argument("--native-python")
    ap.add_argument("--fused-python")
    ap.add_argument("--worker", nargs=3)
    args = ap.parse_args()
    if args.worker:
        worker(Path(args.worker[0]), Path(args.worker[1]), args.worker[2])
    else:
        if not (args.output and args.released_python and args.native_python and args.fused_python):
            ap.error("controller requires output and three independent installed Python executables")
        controller(args.output, {"released": args.released_python,
                                 "native": args.native_python,
                                 "fused": args.fused_python})


if __name__ == "__main__":
    main()
