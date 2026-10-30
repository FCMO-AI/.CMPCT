#!/usr/bin/env python3
"""J24I52: source-bound native Zstd A/B and same-binary A/A causal court.

Research-only lower rung. Never replaces r24 release parity or a product benchmark.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


class Codec:
    def __init__(self, path: Path):
        self.path = path.resolve(strict=True)
        self.library_sha256 = sha(self.path.read_bytes())
        self.lib = ctypes.CDLL(str(self.path))
        sz = ctypes.c_size_t
        self.lib.cmpct_codec_zstd_compress_bound.argtypes = [sz]
        self.lib.cmpct_codec_zstd_compress_bound.restype = sz
        self.lib.cmpct_codec_zstd_compress.argtypes = [
            ctypes.c_void_p, sz, ctypes.c_int32, ctypes.c_void_p, sz, ctypes.POINTER(sz)
        ]
        self.lib.cmpct_codec_zstd_compress.restype = ctypes.c_int32
        self.lib.cmpct_codec_zstd_decompress.argtypes = [
            ctypes.c_void_p, sz, ctypes.c_void_p, sz, ctypes.POINTER(sz)
        ]
        self.lib.cmpct_codec_zstd_decompress.restype = ctypes.c_int32

    def compress(self, data: bytes, level: int) -> bytes:
        cap = int(self.lib.cmpct_codec_zstd_compress_bound(len(data)))
        if not 0 < cap < len(data) + 2_000_000:
            raise AssertionError("unexpected native compress_bound")
        inp = ctypes.create_string_buffer(data)
        out = ctypes.create_string_buffer(cap)
        length = ctypes.c_size_t()
        code = self.lib.cmpct_codec_zstd_compress(
            inp, len(data), level, out, cap, ctypes.byref(length)
        )
        if code != 0 or length.value > cap:
            raise AssertionError(f"native compress failed: {code}, size {length.value}/{cap}")
        return out.raw[:length.value]

    def decompress(self, compressed: bytes, size: int) -> bytes:
        out = ctypes.create_string_buffer(size)
        inp = ctypes.create_string_buffer(compressed)
        length = ctypes.c_size_t()
        code = self.lib.cmpct_codec_zstd_decompress(
            inp, len(compressed), out, size, ctypes.byref(length)
        )
        if code != 0 or length.value != size:
            raise AssertionError(f"native decompress failed: {code}, size {length.value}/{size}")
        return out.raw[:size]


def public_inputs(root: Path):
    # Replay the public universal_bench generator's PRNG consumption through media.
    # This deliberately avoids regenerating the 3,200 unrelated tiny-file fixtures.
    sys.path.insert(0, str(root / "benchmarks"))
    import universal_bench as u

    u.reset_rng()
    for _ in range(8):
        u.randbytes(512 * 1024)
    random16m = u.randbytes(16 * 1024 * 1024)
    pattern32m = u.patterned(32 * 1024 * 1024, b"large-pattern")
    samples = [
        ("random-256k-a", random16m[:256 * 1024], 3),
        ("random-256k-b", random16m[8 * 1024 * 1024:8 * 1024 * 1024 + 256 * 1024], 5),
        ("random-1m", random16m[2 * 1024 * 1024:3 * 1024 * 1024], 5),
        ("pattern-256k", pattern32m[256 * 1024:512 * 1024], 3),
        ("pattern-1m", pattern32m[6 * 1024 * 1024:7 * 1024 * 1024], 5),
    ]
    return {"random16m_sha256": sha(random16m), "pattern32m_sha256": sha(pattern32m)}, samples


def run_batch(lib: Codec, samples) -> str:
    # Return output identity; hashing is performed after the timed native calls.
    outputs = [(name, lib.compress(data, level)) for name, data, level in samples]
    digest = hashlib.sha256()
    for name, raw in outputs:
        digest.update(name.encode())
        digest.update(len(raw).to_bytes(8, "little"))
        digest.update(raw)
    return digest.hexdigest()


def court(base: Codec, candidate: Codec, samples, label: str):
    # A/A estimates label and chronological drift; B refers to the candidate
    # only in the A/B court. Equal source labels never imply independent sources.
    b = candidate if label == "AB" else base
    records = []
    for group in range(4):
        order = "ABBA" if group % 2 == 0 else "BAAB"
        for slot, name in enumerate(order):
            lib = base if name == "A" else b
            wall, cpu, output_hashes = [], [], []
            for _ in range(7):
                w0, c0 = time.perf_counter_ns(), time.process_time_ns()
                # Hold returned hash outside the timing region as a postcondition.
                result = run_batch(lib, samples)
                c1, w1 = time.process_time_ns(), time.perf_counter_ns()
                wall.append((w1 - w0) / 1e6)
                cpu.append((c1 - c0) / 1e6)
                output_hashes.append(result)
            if len(set(output_hashes)) != 1:
                raise AssertionError("non-deterministic output hash within invocation")
            records.append({
                "court": label, "group": group, "order": order, "slot": slot,
                "label": name, "native_sha256": lib.library_sha256,
                "wall_ms": wall, "cpu_ms": cpu,
                "median_wall_ms": statistics.median(wall),
                "median_cpu_ms": statistics.median(cpu),
                "output_sha256": output_hashes[0],
            })
    if len({r["output_sha256"] for r in records}) != 1:
        raise AssertionError("different compressed output across labels / versions")
    summary = {}
    for name in "AB":
        rows = [r for r in records if r["label"] == name]
        summary[name] = {
            "median_of_invocation_wall_ms": statistics.median(r["median_wall_ms"] for r in rows),
            "median_of_invocation_cpu_ms": statistics.median(r["median_cpu_ms"] for r in rows),
            "invocations": len(rows),
            "samples": sum(len(r["wall_ms"]) for r in rows),
        }
    a, bb = summary["A"]["median_of_invocation_wall_ms"], summary["B"]["median_of_invocation_wall_ms"]
    summary["B_minus_A_wall_ms"] = bb - a
    summary["B_over_A_wall_ratio"] = bb / a
    return {"summary": summary, "observations": records}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-lib", type=Path, required=True)
    ap.add_argument("--candidate-lib", type=Path, required=True)
    ap.add_argument("--base-ref", required=True)
    ap.add_argument("--candidate-ref", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    actual_head = git("rev-parse", "HEAD")
    if actual_head != os.environ.get("EVIDENCE_HEAD"):
        raise AssertionError("evidence HEAD / checkout mismatch")
    if args.base_ref != "f456370e75b71a619104f9e9bb6c622929ba8db8":
        raise AssertionError("unpreregistered base")
    if args.candidate_ref != "0b80ecb9b1742a6c20756f4c9e8e097103881cb4":
        raise AssertionError("unpreregistered candidate")
    if git("rev-parse", args.base_ref) != args.base_ref or git("rev-parse", args.candidate_ref) != args.candidate_ref:
        raise AssertionError("source commits not in checkout ancestry")
    base, cand = Codec(args.base_lib), Codec(args.candidate_lib)
    if base.path == cand.path or base.library_sha256 == cand.library_sha256:
        raise AssertionError("base/candidate native payloads must be distinct and source-bound")
    inputs, samples = public_inputs(root)
    identities = []
    for name, data, level in samples:
        x, y = base.compress(data, level), cand.compress(data, level)
        if x != y or base.decompress(x, len(data)) != data or cand.decompress(y, len(data)) != data:
            raise AssertionError("cross-version Zstd byte identity / exact reconstruction failed")
        identities.append({"name": name, "raw_sha256": sha(data), "level": level,
                           "raw_bytes": len(data), "compressed_bytes": len(x),
                           "compressed_sha256": sha(x)})
    # Warm both sources before timed comparisons. The AA sham is executed first
    # to detect gross environmental drift, not to certify the official gate.
    for _ in range(3):
        for lib in [base, cand]:
            run_batch(lib, samples)
    results = {
        "schema": "cmpct-j24i52-native-codec-v1", "evidence_head": actual_head,
        "base_ref": args.base_ref, "candidate_ref": args.candidate_ref,
        "base_native_path": str(base.path), "candidate_native_path": str(cand.path),
        "base_native_sha256": base.library_sha256,
        "candidate_native_sha256": cand.library_sha256,
        "python": sys.version, "platform": platform.platform(),
        "inputs": inputs, "representative_samples": identities,
        "AA": court(base, cand, samples, "AA"),
        "AB": court(base, cand, samples, "AB"),
        "claim_boundary": "native codec FFI micro-batch, not Builder, ZIP parity, release or user speed",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"evidence_head": actual_head, "AA": results["AA"]["summary"],
                      "AB": results["AB"]["summary"]}, indent=2))


if __name__ == "__main__":
    main()
