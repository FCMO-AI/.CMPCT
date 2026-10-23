#!/usr/bin/env python3
"""O1: independent native C/system-libz bounded streaming parity against pinned Python zlib."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import zlib

LEVELS = (0, 1, 6, 9)
CHUNKS = (1, 4096, 65536)
ANCHOR_SHA = "708bee4f14697a0938db8dffa4b2f2783db2b662bd279ea584e717daf70cb1fc"
ANCHOR_DEFLATE = "4b4c4a4ec483929350105ec500"
ANCHOR_ARCHIVE_SHA = "febef1d1f1157066204c468d74e81e14c6f79d1490ab2e76e024beed3ce3fb81"

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def compressed_python(data, level):
    z = zlib.compressobj(level, zlib.DEFLATED, -15)
    return z.compress(data) + z.flush()

def compressed_python_chunked(data, level, chunk):
    """Feed identical input segmentation to the same zlib runtime, with no intermediate flush."""
    z = zlib.compressobj(level, zlib.DEFLATED, -15)
    stream = bytearray()
    for offset in range(0, len(data), chunk):
        stream.extend(z.compress(data[offset:offset+chunk]))
    stream.extend(z.flush())
    return bytes(stream)

def run_native(binary, data, level, chunk):
    p = subprocess.run([str(binary), str(level), str(chunk)], input=data, capture_output=True, check=True, timeout=30)
    if p.stderr:
        raise RuntimeError("native stderr: " + repr(p.stderr))
    return p.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    original = Path(__file__).with_name("v031_vzip_mode2_native_backend_probe.py")
    module = importlib.util.spec_from_file_location("prior_vzip_o0", original)
    prior = importlib.util.module_from_spec(module)
    module.loader.exec_module(prior)
    samples = prior.fixed_samples()  # independently verifies 861-byte frozen archive SHA
    assert len(samples) == 7
    assert sha(samples["golden_75"]) == ANCHOR_SHA
    assert compressed_python(samples["golden_75"], 6).hex() == ANCHOR_DEFLATE
    binary = args.binary.resolve()
    c_version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    rows = []
    for family, data in samples.items():
        assert len(data) <= 1024 * 1024
        for level in LEVELS:
            expected = compressed_python(data, level)
            assert zlib.decompress(expected, -15) == data
            for chunk in CHUNKS:
                expected_feedmatched = compressed_python_chunked(data, level, chunk)
                assert zlib.decompress(expected_feedmatched, -15) == data
                t0 = time.perf_counter_ns()
                actual = run_native(binary, data, level, chunk)
                measured_process_ns = time.perf_counter_ns() - t0
                repeat = run_native(binary, data, level, chunk)
                if repeat != actual:
                    raise AssertionError(("native nondeterministic", family, level, chunk))
                if zlib.decompress(actual, -15) != data:
                    raise AssertionError(("native inflation mismatch", family, level, chunk))
                equal = actual == expected
                equal_feedmatched = actual == expected_feedmatched
                python_feed_differs_from_onecall = expected_feedmatched != expected
                first = None if equal else next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), min(len(actual), len(expected)))
                rows.append({
                    "family": family, "level": level, "chunk": chunk,
                    "source_len": len(data), "source_sha256": sha(data),
                    "python_len": len(expected), "native_len": len(actual),
                    "python_sha256": sha(expected), "native_sha256": sha(actual),
                    "byte_identical": equal, "first_difference_offset": first,
                    "feedmatched_python_sha256": sha(expected_feedmatched),
                    "native_equals_feedmatched_python": equal_feedmatched,
                    "python_feed_differs_from_onecall": python_feed_differs_from_onecall,
                    "feedmatched_first_native_diff": None if equal_feedmatched else next((i for i,(a,b) in enumerate(zip(actual,expected_feedmatched)) if a != b),min(len(actual),len(expected_feedmatched))),
                    "golden_native_hex": actual.hex() if family == "golden_75" and level == 6 else None,
                    "native_process_wall_ns": measured_process_ns
                })
    different = [r for r in rows if not r["byte_identical"]]
    provider_different = [r for r in rows if not r["native_equals_feedmatched_python"]]
    feed_different = [r for r in rows if r["python_feed_differs_from_onecall"]]
    result = {
        "schema": "cmpct-vzip-mode2-c-libz-streaming-o1-v1",
        "episode": "VZIP-M2-LIBZ-STREAM-O1-001",
        "preregistration": "benchmarks/history/2026-10-23-v031-vzip-mode2-c-zlib-streaming-o1-prereg.md",
        "frozen_archive_sha256": ANCHOR_ARCHIVE_SHA,
        "runtime": {
            "python": sys.version.split()[0], "python_zlib_compiled": zlib.ZLIB_VERSION,
            "python_zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
            "native_libz_version": c_version,
            "platform": platform.platform(),
            "python_oracle_max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "child_max_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        },
        "families": list(samples), "levels": list(LEVELS), "chunks": list(CHUNKS),
        "comparisons": len(rows), "byte_identical": len(rows)-len(different), "byte_different": len(different),
        "mismatch_coordinates": [[r["family"],r["level"],r["chunk"]] for r in different],
        "decision": "HOST_LIBZ_PARITY_IN_TESTED_REGIME" if not different else "C_LIBZ_OR_CHUNK_STREAM_PARITY_FALSIFIED",
        "o1b_feedmatched_comparisons": len(rows),
        "o1b_native_vs_feedmatched_different": len(provider_different),
        "o1b_python_feed_vs_onecall_different": len(feed_different),
        "o1b_provider_mismatch_coordinates": [[r["family"],r["level"],r["chunk"]] for r in provider_different],
        "o1b_feed_effect_coordinates": [[r["family"],r["level"],r["chunk"]] for r in feed_different],
        "o1b_decision": "FEED_BOUNDARY_CAUSE_SUPPORTED_TESTED_HOST" if not provider_different and len(feed_different)==len(different) and {(r["family"],r["level"],r["chunk"]) for r in feed_different}=={(r["family"],r["level"],r["chunk"]) for r in different} else "FEED_BOUNDARY_ALONE_NOT_SUFFICIENT",
        "no_product_credit": True, "cases": rows
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:result[k] for k in ("comparisons","byte_identical","byte_different","decision","mismatch_coordinates",
                                  "o1b_native_vs_feedmatched_different","o1b_python_feed_vs_onecall_different","o1b_decision")},sort_keys=True))

if __name__ == "__main__":
    main()
