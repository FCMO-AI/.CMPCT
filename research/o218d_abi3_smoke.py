#!/usr/bin/env python3
"""O218d: independently compare optional CPython abi3 wheel with exact Python semantics."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import random
import statistics
import sys
import time
import zipfile
import _o218_fastscan as native

SEED = 21820261028
PROFILES = ((65536, 1), (262144, 1), (65536, 256))

def strict_python(refs, blobs, size):
    """Independent exact built-in-list control, not the native implementation."""
    if type(refs) is not list or type(blobs) is not list or type(size) is not int:
        return False
    if size < 0 or size > sys.maxsize:
        return False
    total = 0
    for idx in refs:
        if type(idx) is not int or idx < 0 or idx >= len(blobs):
            return False
        row = blobs[idx]
        if type(row) is not list or len(row) != 5:
            return False
        length = row[1]
        if type(length) is not int or length < 0 or length > sys.maxsize:
            return False
        if total > sys.maxsize - length:
            return False
        total += length
    return total == size

class SubList(list):
    pass

class SubInt(int):
    pass

def make_cases():
    rng = random.Random(SEED)
    pool = (0, 1, 2, -1, True, False, 0.0, None, "0", 2**120, [0], {}, SubInt(0))
    cases = []
    for i in range(5000):
        blobs = [[0, rng.randint(0, 50), 0, 0, 0] for _ in range(3)]
        refs = [rng.randrange(3) for _ in range(rng.randrange(14))]
        size = sum(blobs[j][1] for j in refs)
        mutation = i % 25
        if mutation == 0: refs = tuple(refs)
        elif mutation == 1: blobs = tuple(blobs)
        elif mutation == 2: refs = SubList(refs)
        elif mutation == 3: size = SubInt(size)
        elif mutation == 4: size = True
        elif mutation == 5: size = -1
        elif mutation == 6: size = 2**120
        elif mutation == 7: size += 1
        elif mutation == 8: refs.append(True)
        elif mutation == 9: refs.append(False)
        elif mutation == 10: refs.append(-1)
        elif mutation == 11: refs.append(300)
        elif mutation == 12: refs.append("0")
        elif mutation == 13: refs.append(0.0)
        elif mutation == 14: refs.append(None)
        elif mutation == 15: refs.append(SubInt(1))
        elif mutation == 16: refs.append(2**120)
        elif mutation == 17: refs.extend(rng.choice(pool) for _ in range(3))
        elif mutation == 18: blobs[0] = tuple(blobs[0])
        elif mutation == 19: blobs[0] = [0, 0, 0]
        elif mutation == 20: blobs[0][1] = True
        elif mutation == 21: blobs[0][1] = -1
        elif mutation == 22: blobs[0][1] = 2**120
        elif mutation == 23: refs = []; size = 0
        else: refs = [0]; size = blobs[0][1]
        cases.append((refs, blobs, size))
    return cases

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def run(wheel_dir: Path):
    wheels = list(wheel_dir.glob("*.whl"))
    assert len(wheels) == 1, wheels
    wheel = wheels[0]
    assert "cp311-abi3-" in wheel.name, wheel.name
    with zipfile.ZipFile(wheel) as z:
        extensions = [n for n in z.namelist() if n.endswith((".so", ".pyd"))]
        assert len(extensions) == 1 and "_o218_fastscan" in extensions[0], extensions
        binary_inside_sha = sha256(z.read(extensions[0]))
    actual_binary = Path(native.__file__).read_bytes()
    assert sha256(actual_binary) == binary_inside_sha
    assert native.scan_refs([], [], 0) is True
    results = []
    for refs, blobs, size in make_cases():
        expected = strict_python(refs, blobs, size)
        actual = native.scan_refs(refs, blobs, size)
        assert type(actual) is bool and actual == expected, (refs, blobs, size, expected, actual)
        results.append("1" if actual else "0")
    summary = []
    for count, owners in PROFILES:
        blobs = [[0, j % 17 + 1, 0, 0, 0] for j in range(owners)]
        refs = [j % owners for j in range(count)]
        length = sum(blobs[j][1] for j in refs)
        assert native.scan_refs(refs, blobs, length) is True
        assert strict_python(refs, blobs, length) is True
        for _ in range(3):
            assert native.scan_refs(refs, blobs, length) and strict_python(refs, blobs, length)
        observations = {"native": [], "python": []}
        for cycle in range(12):
            order = ("python", "native", "native", "python") if cycle % 2 else ("native", "python", "python", "native")
            for mode in order:
                func = native.scan_refs if mode == "native" else strict_python
                start = time.perf_counter_ns()
                answer = func(refs, blobs, length)
                elapsed = time.perf_counter_ns() - start
                assert answer is True and elapsed > 0
                observations[mode].append(elapsed)
        med = {k: statistics.median(v) / 1e6 for k, v in observations.items()}
        summary.append({"count": count, "owners": owners, "raw_wall_ns": observations,
                        "native_median_wall_ms": med["native"], "python_median_wall_ms": med["python"],
                        "python_over_native": med["python"] / med["native"]})
    return {
        "tier": "abi3_wheel_delivery_and_strict_predicate_micro_only",
        "host": {"os": sys.platform, "machine": platform.machine(), "python": list(sys.version_info[:2])},
        "source": {"parent": "a2d69c89769868fe4a454ce0556f6a19806f0647", "pre_reg": "f96a54d058bdac24a6216ec66f47086a7ecfa1ec"},
        "wheel": {"name": wheel.name, "bytes": wheel.stat().st_size, "sha256": sha256(wheel.read_bytes()),
                  "binary_sha256": binary_inside_sha, "binary_bytes": len(actual_binary), "binary_name": extensions[0]},
        "semantics": {"cases": len(results), "accepted": results.count("1"), "rejected": results.count("0"),
                      "decision_sha256": sha256("".join(results).encode())},
        "benchmarks": summary,
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--wheel-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.wheel_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("O218D_ABI3_SMOKE_PASS", json.dumps({
        "host": result["host"], "wheel": result["wheel"]["name"],
        "semantics": result["semantics"], "ratios": [round(r["python_over_native"], 3) for r in result["benchmarks"]]}))
