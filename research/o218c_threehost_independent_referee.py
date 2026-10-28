#!/usr/bin/env python3
"""O218c independent raw receipt referee (no import of original experiment)."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics

PROFILES = ((65536, 1), (262144, 1), (65536, 256))
METHODS = ("original", "fast", "native", "unguarded")
SOURCE = {
    "reader": "dbd4ac576a05a47eae97e1e40de89cf1de440516",
    "validator": "51c2849061f99a4afeddb7666956b24566ce7de0",
    "native_c": "a54f15181d9dbe667b9e8c9d52e927b09c80152f",
}
PARENT = "d3d87e5df39ab9e58043cab74d5b2a1d87f5bed5"
EXPECTED_TIER = "portable_host_extension_full_reader_research_not_product"

def check(data, basedir: Path):
    assert data["tier"] == EXPECTED_TIER
    assert data["parent"] == PARENT and data["source"] == SOURCE
    assert data["host"]["platform"] in ("linux", "darwin", "win32")
    assert data["host"]["machine"] and data["host"]["python"]
    build = data["build"]
    assert build["build_wall_ns"] > 0 and build["binary_bytes"] > 0
    assert len(bytes.fromhex(build["binary_sha256"])) == 32
    assert build["platform_compiler_type"] in ("unix", "msvc", "mingw32")
    ext = basedir / build["artifact"]
    assert ext.is_file() and ext.stat().st_size == build["binary_bytes"]
    assert hashlib.sha256(ext.read_bytes()).hexdigest() == build["binary_sha256"]

    semantics = data["semantics"]
    assert semantics["inherited_cases"] >= 19
    assert len(semantics["named_cases"]) == 24 and semantics["fuzz_cases"] == 2500
    assert all(entry["outcome"][0] in ("ACCEPT", "REJECT")
               for entry in semantics["named_cases"])

    tc = data["timing_contract"]
    assert tc == {
        "cycles": 2, "workers_per_mode_cycle": 2,
        "samples_per_worker": 5, "compile_outside_constructor": True,
        "startup_outside_constructor": True,
        "unsafe_arm": "timing_floor_only_not_valid_product",
    }
    manifests = {(m["count"], m["owners"]): m for m in data["profiles"]}
    assert set(manifests) == set(PROFILES)
    for (n, owners), m in manifests.items():
        assert m["archive_bytes"] > 0
        assert len(bytes.fromhex(m["logical_sha256"])) == 32
        assert len(bytes.fromhex(m["archive_sha256"])) == 32
        wire = basedir / m["artifact"]
        assert wire.is_file() and wire.stat().st_size == m["archive_bytes"]
        assert hashlib.sha256(wire.read_bytes()).hexdigest() == m["archive_sha256"]

    workers = data["raw_workers"]
    assert len(workers) == len(PROFILES) * len(METHODS) * 2 * 2
    counts = Counter((w["count"], w["owners"], w["mode"], w["cycle"])
                     for w in workers)
    assert set(counts) == {
        (n, owners, mode, cycle)
        for n, owners in PROFILES for mode in METHODS for cycle in range(2)
    }
    assert all(count == 2 for count in counts.values())
    for row in workers:
        assert row["source"] == SOURCE and row["mode"] in METHODS
        assert row["archive_sha256"] == manifests[
            (row["count"], row["owners"])]["archive_sha256"]
        assert len(row["samples"]) == 5 and row["fresh_process_wall_ns"] > 0
        assert row["vmhwm_bytes"] is None or row["vmhwm_bytes"] > 0
        for sample in row["samples"]:
            assert type(sample["wall_ns"]) is int and 0 < sample["wall_ns"] < 120e9
            assert type(sample["cpu_ns"]) is int and 0 < sample["cpu_ns"] < 120e9
        assert isinstance(row["python"], str) and row["python"]

    recomputed = []
    for n, owners in PROFILES:
        by_mode = {}
        for mode in METHODS:
            sub = [w for w in workers if (w["count"], w["owners"], w["mode"])
                   == (n, owners, mode)]
            assert len(sub) == 4
            by_mode[mode] = {
                "median_constructor_wall_ms": statistics.median(
                    statistics.median(s["wall_ns"] for s in w["samples"])
                    for w in sub) / 1e6,
                "median_constructor_cpu_ms": statistics.median(
                    statistics.median(s["cpu_ns"] for s in w["samples"])
                    for w in sub) / 1e6,
                "median_fresh_process_wall_ms": statistics.median(
                    w["fresh_process_wall_ns"] for w in sub) / 1e6,
            }
        recomputed.append({
            "count": n, "owners": owners, "by_mode": by_mode,
            "fast_over_native": (
                by_mode["fast"]["median_constructor_wall_ms"] /
                by_mode["native"]["median_constructor_wall_ms"]),
            "native_over_unguarded": (
                by_mode["native"]["median_constructor_wall_ms"] /
                by_mode["unguarded"]["median_constructor_wall_ms"]),
        })
    assert len(recomputed) == len(data["summary"])
    for got, claimed in zip(recomputed, data["summary"]):
        assert got["count"] == claimed["count"] and got["owners"] == claimed["owners"]
        for mode in METHODS:
            for key, value in got["by_mode"][mode].items():
                assert math.isclose(value, claimed["by_mode"][mode][key], rel_tol=1e-12)
        for key in ("fast_over_native", "native_over_unguarded"):
            assert math.isclose(got[key], claimed[key], rel_tol=1e-12)
    positive = all(row["fast_over_native"] >= 2.0 for row in recomputed
                   if row["owners"] == 1 and row["count"] in (65536, 262144))
    decision = ("HOST_C_EXTENSION_VIABLE" if positive else
                "HOST_C_EXTENSION_ECONOMICS_NOT_PROVEN")
    assert decision == data["decision"]
    return {"host": data["host"]["platform"], "decision": decision,
            "workers": len(workers), "timed_opens": len(workers)*5,
            "binary_bytes": build["binary_bytes"],
            "build_wall_ms": build["build_wall_ns"]/1e6,
            "summary": recomputed}

def forge_tests(data, directory):
    probes = []
    x = copy.deepcopy(data)
    x["raw_workers"].pop()
    probes.append(("missing_worker", x))
    x = copy.deepcopy(data)
    for w in x["raw_workers"]:
        if w["count"] == 262144 and w["mode"] == "native":
            for s in w["samples"]:
                s["wall_ns"] *= 8
    probes.append(("counterfeit_timing", x))
    x = copy.deepcopy(data)
    x["source"]["native_c"] = "0" * 40
    probes.append(("wrong_C_source", x))
    x = copy.deepcopy(data)
    x["summary"][0]["fast_over_native"] *= 2
    probes.append(("counterfeit_ratio", x))
    x = copy.deepcopy(data)
    x["decision"] = ("HOST_C_EXTENSION_ECONOMICS_NOT_PROVEN"
                     if data["decision"] == "HOST_C_EXTENSION_VIABLE"
                     else "HOST_C_EXTENSION_VIABLE")
    probes.append(("counterfeit_decision", x))
    x = copy.deepcopy(data)
    x["profiles"][0]["archive_sha256"] = "0" * 64
    probes.append(("counterfeit_archive", x))
    x = copy.deepcopy(data)
    x["build"]["binary_sha256"] = "0" * 64
    probes.append(("counterfeit_binary", x))
    for label, item in probes:
        try:
            check(item, directory)
        except (AssertionError, KeyError, TypeError, ValueError, ZeroDivisionError):
            pass
        else:
            raise AssertionError(f"O218C_FORGERY_ACCEPTED {label}")
    return len(probes)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    original = args.input.read_bytes()
    receipt = json.loads(original)
    audited = check(receipt, args.input.parent)
    audited["receipt_sha256"] = hashlib.sha256(original).hexdigest()
    audited["forgeries_rejected"] = forge_tests(receipt, args.input.parent)
    if args.output:
        args.output.write_text(json.dumps(audited, sort_keys=True, indent=2) + "\n")
    print("O218C_INDEPENDENT_REFEREE=PASS", json.dumps(audited, sort_keys=True))
