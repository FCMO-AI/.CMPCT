#!/usr/bin/env python3
"""O197 source-exact, research-only mutation sweep for optional native CDC.
Provenance: preregistration in PR #516 discussion before this instrument.
No CMPCT archive/codec speed or default-packaging claim is made here.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time

SOURCE_BLOB = "a6253beece20ce8aad3cdb605a6d9fcaa50d9364"
MEMBER_SIZE = 3 * 1024 * 1024
MODES = ("fixed256", "fixed512", "native")
SEEDS = range(197, 209)
POSITIONS = (1, MEMBER_SIZE // 3, 2 * MEMBER_SIZE // 3)
HEADER_BYTES = 64  # CMPCT BHDR.size; approximate RAW representation, not an archive.
MIN, AVG, MAX = 128 * 1024, 512 * 1024, 2 * 1024 * 1024


def authenticate_and_compile(root: Path, build: Path):
    source = root / "native/cmpct_cdc.c"
    sha = subprocess.check_output(["git", "-C", str(root), "hash-object", str(source)],
                                  text=True).strip()
    if sha != SOURCE_BLOB:
        raise RuntimeError(f"native source drift: {sha}, expected {SOURCE_BLOB}")
    compiler = os.environ.get("CC", "cc")
    proc = subprocess.run([compiler, "-O2", "-std=c11", "-Wall", "-Wextra",
                           "-shared", "-fPIC", str(source), "-o", str(build)],
                          capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(proc.stdout + "\n" + proc.stderr)
    lib = ctypes.CDLL(str(build))
    lib.cmpct_cdc_cut.argtypes = (ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.c_size_t, ctypes.c_size_t,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
                                  ctypes.c_size_t)
    lib.cmpct_cdc_cut.restype = ctypes.c_size_t
    return lib, compiler


def chunks(raw: bytes, mode: str, lib):
    if mode != "native":
        size = int(mode[5:]) * 1024
        return [raw[i:i + size] for i in range(0, len(raw), size)]
    capacity = max(4, len(raw) // MIN + 4)
    ends = (ctypes.c_uint64 * capacity)()
    owned = ctypes.create_string_buffer(raw)
    count = lib.cmpct_cdc_cut(owned, len(raw), MIN, AVG, MAX, ends, capacity)
    if count == 0 or count > capacity:
        raise RuntimeError(f"native CDC failure: {count}")
    offsets = [int(ends[i]) for i in range(count)]
    if offsets[-1] != len(raw) or offsets != sorted(set(offsets)):
        raise AssertionError("CDC offsets not complete and strictly increasing")
    cuts = [raw[a:b] for a, b in zip([0] + offsets[:-1], offsets)]
    if not all(0 < len(c) <= MAX for c in cuts):
        raise AssertionError("CDC chunk size outside native bounds")
    return cuts


def charged_result(base, modified, mode, lib):
    t0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    a, b = chunks(base, mode, lib), chunks(modified, mode, lib)
    segment_wall_ms = (time.perf_counter_ns() - t0) / 1e6
    segment_cpu_ms = (time.process_time_ns() - cpu0) / 1e6
    if b"".join(a) != base or b"".join(b) != modified:
        raise AssertionError("lossless reconstruction failed")
    unique = {}
    for chunk in a + b:
        h = hashlib.sha256(chunk).digest()
        old = unique.setdefault(h, chunk)
        if old != chunk:
            raise AssertionError("SHA collision or chunk identity corruption")
    unique_bytes = sum(map(len, unique.values()))
    return {
        "unique_raw_bytes": unique_bytes, "unique_chunks": len(unique),
        "all_chunks": len(a) + len(b),
        "chunk_header_bytes": len(unique) * HEADER_BYTES,
        "raw_plus_header_proxy_bytes": unique_bytes + len(unique) * HEADER_BYTES,
        "max_decode_chunk_bytes": max(map(len, unique.values())),
        "segment_wall_ms": round(segment_wall_ms, 6),
        "segment_cpu_ms": round(segment_cpu_ms, 6),
        "exact_reconstruction": True
    }


def main():
    root = Path(__file__).resolve().parents[1]
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="o197-native-") as tmp:
        lib, compiler = authenticate_and_compile(root, Path(tmp) / "cdc.so")
        entries = []
        for seed in SEEDS:
            raw = hashlib.shake_256(f"CMPCT-O197-FIXTURE-{seed}".encode()).digest(MEMBER_SIZE)
            for pos in POSITIONS:
                inplace = bytearray(raw)
                inplace[pos] ^= 1
                scenarios = {
                    "overwrite_1byte": bytes(inplace),
                    "insert_1byte": raw[:pos] + b"Q" + raw[pos:-1]
                }
                for kind, sibling in scenarios.items():
                    assert len(sibling) == len(raw)
                    results = {mode: charged_result(raw, sibling, mode, lib)
                               for mode in MODES}
                    strongest_fixed = min(results[x]["raw_plus_header_proxy_bytes"]
                                          for x in MODES if x != "native")
                    native = results["native"]["raw_plus_header_proxy_bytes"]
                    entries.append({
                        "seed": seed, "position": pos, "case": kind,
                        "input_sha256": hashlib.sha256(raw).hexdigest(),
                        "sibling_sha256": hashlib.sha256(sibling).hexdigest(),
                        "strategies": results,
                        "native_saving_vs_best_fixed_bytes": strongest_fixed - native,
                        "native_saving_vs_best_fixed_percent":
                            round(100 * (strongest_fixed - native) / strongest_fixed, 6)
                    })
    summaries = {}
    for name in ("overwrite_1byte", "insert_1byte"):
        values = [x["native_saving_vs_best_fixed_percent"]
                  for x in entries if x["case"] == name]
        summaries[name] = {
            "n": len(values), "min_percent": min(values),
            "median_percent": statistics.median(values),
            "max_percent": max(values), "native_loss_count": sum(x < 0 for x in values),
            "native_win_count": sum(x > 0 for x in values)
        }
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True).strip()
    result = {
        "schema": "cmpct-o197-native-mutation-charged-oracle-v1",
        "evidence_class": "SOURCE_EXACT_MICRO_RESEARCH_NOT_PRODUCT",
        "source_head": head, "source_blob": SOURCE_BLOB,
        "os": platform.platform(), "compiler": compiler, "member_bytes": MEMBER_SIZE,
        "seeds": [min(SEEDS), max(SEEDS)], "positions": POSITIONS,
        "charged_bytes": "unique raw chunk bytes + 64 bytes per unique physical record",
        "missing_costs": "actual compressed CMPCT blobs/index, format, decode throughput, RSS, temporary IO, Builder/Reader packaging and full archive size",
        "baseline_control": ["fixed256", "fixed512"],
        "elapsed_wall_s": round(time.time() - started, 6),
        "summary": summaries, "observations": entries
    }
    dest = Path("o197-evidence")
    dest.mkdir(exist_ok=True)
    (dest / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    for name, row in summaries.items():
        print("O197", name, json.dumps(row, sort_keys=True))
    print("O197_EXACT_SOURCE_MICRO_COURT=PASS", head, SOURCE_BLOB)
    print("O197_PRODUCT_GATE=UNMEASURED")


if __name__ == "__main__":
    main()
