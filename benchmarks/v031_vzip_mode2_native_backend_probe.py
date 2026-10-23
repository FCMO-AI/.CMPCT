#!/usr/bin/env python3
"""Source-pinned O0 experiment: flate2 rust_backend vs zlib raw-Deflate byte identity.

Deliberately never claims native VZIP mode-2 support. A standards-valid but byte-different
Deflate stream is an exact-reconstruction FAILURE for that mode, not a codec failure.
"""
import argparse
import base64
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import zlib
from pathlib import Path


GOLDEN_DEFLATE = bytes.fromhex("4b4c4a4ec483929350105ec500")
GOLDEN_MEMBER_SHA256 = "708bee4f14697a0938db8dffa4b2f2783db2b662bd279ea584e717daf70cb1fc"
LEVELS = (0, 1, 6, 9)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fixed_samples():
    # Independent fixed-vector content: do not regenerate an archive through CMPCT's Builder.
    # Cross-check the immutable builder-independent full archive, not merely hardcoded probe data.
    # A silent fixture edit must invalidate the scientific interpretation of this backend comparison.
    vector_path = Path(__file__).resolve().parents[1] / "tests/conformance/v24-virtual-zip-deflate-mode2.json"
    vector = json.loads(vector_path.read_text(encoding="utf-8"))["vector"]
    archive = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(archive) == 861
    assert digest(archive) == "febef1d1f1157066204c468d74e81e14c6f79d1490ab2e76e024beed3ce3fb81"
    assert digest(archive) == vector["archive_sha256"]
    assert vector["member"]["exact_deflate_hex"] == GOLDEN_DEFLATE.hex()
    assert vector["member"]["logical_sha256"] == GOLDEN_MEMBER_SHA256
    golden = zlib.decompress(GOLDEN_DEFLATE, -15)
    assert len(golden) == 75 and digest(golden) == GOLDEN_MEMBER_SHA256
    rng = random.Random(0xCF2026)
    random_block = rng.randbytes(32768)
    shifted = bytearray(random_block + random_block)
    for index in range(0, len(shifted), 2111):
        shifted[index] ^= 0x5A
    logs = b"".join(
        f"2026-10-23T12:{i%60:02d}:00Z service=storage seq={i:06d} status={i%9} payload={i%17:02d}\\n".encode()
        for i in range(1024)
    )
    rows = b"".join(
        ('{"kind":"record","id":%d,"tag":"%s","amount":%d}\\n'
         % (i, "kindA" if i % 3 else "kindB", (i*i) % 10007)).encode()
        for i in range(1400)
    )
    return {
        "golden_75": golden,
        "zeros_8k": bytes(8192),
        "high_entropy_32k": random_block,
        "alternating_pattern_32k": (b"ABCD" * 8192),
        "shifted_related_64k": bytes(shifted),
        "structured_logs": logs,
        "json_rows": rows,
    }


def zlib_raw(data, level):
    co = zlib.compressobj(level, zlib.DEFLATED, -15)
    return co.compress(data) + co.flush()


def git_output(*args):
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def compare(binary):
    fixed = fixed_samples()
    rows = []
    mismatches = []
    for family, raw in fixed.items():
        for level in LEVELS:
            expected = zlib_raw(raw, level)
            def native_once():
                finished = subprocess.run(
                    [str(binary), str(level)], input=raw, capture_output=True, check=True, timeout=15
                )
                assert not finished.stderr, finished.stderr.decode(errors="replace")
                return finished.stdout
            actual = native_once()
            repeat = native_once()
            # These are instrumentation controls; neither different Deflate bytes nor a different
            # coding strategy can be called a product win, but every stream must decode exactly.
            if actual != repeat:
                raise AssertionError(f"native output non-deterministic: {family}, level {level}")
            if zlib.decompress(actual, -15) != raw:
                raise AssertionError(f"native stream corrupted source: {family}, level {level}")
            if zlib.decompress(expected, -15) != raw:
                raise AssertionError(f"zlib reference corrupted source: {family}, level {level}")
            match = actual == expected
            first_diff = None
            if not match:
                first_diff = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b),
                                  min(len(actual), len(expected)))
                mismatches.append([family, level])
            rows.append({
                "family": family,
                "tier": "immutable_independent_golden" if family == "golden_75" else "held_out_synthetic",
                "level": level,
                "source_len": len(raw),
                "source_sha256": digest(raw),
                "python_stream_len": len(expected),
                "native_stream_len": len(actual),
                "python_stream_sha256": digest(expected),
                "native_stream_sha256": digest(actual),
                "byte_identical": match,
                "first_difference_offset": first_diff,
                "exact_inflate_both": True,
                "native_deterministic_repeated": True,
                "python_stream_hex": expected.hex() if family == "golden_75" else None,
                "native_stream_hex": actual.hex() if family == "golden_75" else None,
            })
    gold_level6 = next(row for row in rows if row["family"] == "golden_75" and row["level"] == 6)
    golden_python_matches_frozen = gold_level6["python_stream_hex"] == GOLDEN_DEFLATE.hex()
    return {
        "schema": "cmpct-vzip-mode2-native-backend-parity-v1",
        "status": "research_only_not_native_reader_support",
        "source": {
            "head": git_output("rev-parse", "HEAD"),
            "preregistered_episode": "VZIP-M2-BACKEND-001",
            "rust_probe_blob": git_output("hash-object", "native/cmpct-core/examples/vzip_mode2_backend_probe.rs"),
            "python_probe_blob": git_output("hash-object", "benchmarks/v031_vzip_mode2_native_backend_probe.py"),
            "cargo_manifest_blob": git_output("hash-object", "native/cmpct-core/Cargo.toml"),
        },
        "runtime": {
            "python": sys.version.split()[0],
            "python_zlib_compiled": zlib.ZLIB_VERSION,
            "python_zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
            "platform": platform.platform(),
            "rust_binary": str(binary),
        },
        "golden_python_level6_matches_frozen": golden_python_matches_frozen,
        "samples": len(fixed),
        "levels": list(LEVELS),
        "comparisons": len(rows),
        "byte_equal": len(rows) - len(mismatches),
        "byte_different": len(mismatches),
        "mismatch_coordinates": mismatches,
        "decision": (
            "CURRENT_RUST_BACKEND_NOT_DROPIN_BYTE_EXACT_MODE2"
            if mismatches else "NO_DIFFERENCE_FOUND_NOT_UNIVERSAL_PARITY"
        ),
        "no_product_credit": True,
        "cases": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.binary.absolute())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "decision", "golden_python_level6_matches_frozen", "samples",
        "comparisons", "byte_equal", "byte_different", "mismatch_coordinates"
    )}, sort_keys=True))
    if not result["golden_python_level6_matches_frozen"]:
        print("WARNING: host zlib already differs from frozen Python mode-2 golden", file=sys.stderr)


if __name__ == "__main__":
    main()
