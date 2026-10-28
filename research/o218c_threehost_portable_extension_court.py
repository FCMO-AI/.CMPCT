#!/usr/bin/env python3
"""O218c: source-exact 3-host installed Reader C extension transfer, research-only.

Uses existing unmodified O218 C and O218b validators; neither adds a Reader
implementation nor claims a package/wheel/release ABI.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time

import o218b_native_full_reader_court as inherited

PROFILES = ((65536, 1), (262144, 1), (65536, 256))
METHODS = ("original", "fast", "native", "unguarded")
CYCLES = 2
WORKERS_PER_CYCLE = 2
SAMPLES_PER_WORKER = 5
EXPECTED_PARENT = "d3d87e5df39ab9e58043cab74d5b2a1d87f5bed5"
BRANCH = "agent/phased1-v031-o218c-threehost-portable-extension-20261027"
C_SOURCE = Path(__file__).resolve().parent / "o218_fastscan.c"
ALL_GATES = (65536, 262144)

def _command(*args: str, cwd: Path, timeout: int = 300):
    begin = time.perf_counter_ns()
    result = subprocess.run(list(args), cwd=str(cwd), check=True,
                            capture_output=True, text=True, timeout=timeout)
    return result, time.perf_counter_ns() - begin

def build_unmodified_extension(root: Path, evidence_dir: Path):
    """Use CPython's supported platform-specific compiler via setuptools."""
    from setuptools import Extension, setup  # noqa: F401 -- package capability check
    from setuptools.dist import Distribution
    from setuptools.command.build_ext import build_ext

    # Direct setuptools build_ext avoids a subprocess setup script, yet selects
    # MSVC on Windows, clang on macOS and the platform CC on Linux.
    ext = Extension("_o218_fastscan", [str(C_SOURCE)])
    distribution = Distribution({"name": "cmpct-o218c-research",
                                 "ext_modules": [ext]})
    command = build_ext(distribution)
    # A loaded .pyd cannot be deleted on Windows: compile into retained evidence.
    command.build_lib = str(evidence_dir)
    command.build_temp = str(root / "obj")
    command.inplace = False
    command.force = True
    command.ensure_finalized()
    start = time.perf_counter_ns()
    command.run()
    wall_ns = time.perf_counter_ns() - start
    candidates = list(evidence_dir.rglob("_o218_fastscan*"))
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    matched = [p for p in candidates if p.is_file() and p.name.endswith(suffix)]
    if len(matched) != 1:
        raise AssertionError(f"one compiled extension required: {candidates} suffix={suffix}")
    binary = matched[0]
    module = inherited.load_binary(str(binary))
    if not hasattr(module, "scan_refs"):
        raise AssertionError("host built C source but did not expose scan_refs")
    return module, binary, {
        "build_wall_ns": wall_ns,
        "binary_bytes": binary.stat().st_size,
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "python_extension_suffix": suffix,
        "platform_compiler_type": command.compiler.compiler_type,
        "python_executable": sys.executable,
    }

def run(output: Path):
    # Child worker cwd differs; absolute artifact paths also avoid Win32 DLL-lock
    # cleanup errors and preserve the exact loaded binary for the independent audit.
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source = inherited.source_identity()  # Reader, validator and C from actual installed source
    with tempfile.TemporaryDirectory(prefix="cmpct-o218c-") as temp:
        root = Path(temp)
        native, binary, build = build_unmodified_extension(root, output.parent)
        # Host binary remains on disk for the referee and for Windows DLL lifetime.
        build["artifact"] = binary.name
        semantics = inherited.semantics(native)  # Original O215 + 24 named + 2500 fuzz
        if semantics["inherited_cases"] < 19 or len(semantics["named_cases"]) != 24:
            raise AssertionError("inherited semantic controls missing")

        # O215 produces genuine self-authenticated r24 fixtures independently of Builder.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
        from test_o215_fixed_chunk_admission import _make_archive

        manifests, raw, summary = [], [], []
        rng = random.Random(21820261027)
        for refs_count, owners_count in PROFILES:
            refs, logical, blobs = inherited.build_case(refs_count, owners_count)
            wire = _make_archive(refs, logical, blobs=blobs)
            fixture = root / f"o218c-{refs_count}-{owners_count}.cmpct"
            fixture.write_bytes(wire)
            immutable = output.parent / f"o218c-{refs_count}-{owners_count}.cmpct"
            immutable.write_bytes(wire)
            manifest = {
                "count": refs_count, "owners": owners_count,
                "archive_bytes": len(wire),
                "archive_sha256": hashlib.sha256(wire).hexdigest(),
                "logical_sha256": hashlib.sha256(logical).hexdigest(),
                "artifact": immutable.name,
            }
            manifests.append(manifest)
            for cycle in range(CYCLES):
                arms = list(METHODS) * WORKERS_PER_CYCLE
                rng.shuffle(arms)
                for mode in arms:
                    cmd = (sys.executable,
                           str(Path(inherited.__file__).resolve()),
                           "--worker", str(fixture), str(len(logical)),
                           mode, str(binary))
                    completed, process_wall_ns = _command(*cmd, cwd=root, timeout=240)
                    result = json.loads(completed.stdout.strip())
                    if result["mode"] != mode or result["source"] != source:
                        raise AssertionError("worker source/mode identity drift")
                    result.update(count=refs_count, owners=owners_count,
                                  cycle=cycle, archive_sha256=manifest["archive_sha256"],
                                  fresh_process_wall_ns=process_wall_ns)
                    raw.append(result)
            samples = {}
            for mode in METHODS:
                workers = [w for w in raw if w["count"] == refs_count
                           and w["owners"] == owners_count and w["mode"] == mode]
                samples[mode] = {
                    "median_constructor_wall_ms": statistics.median(
                        statistics.median(s["wall_ns"] for s in w["samples"])
                        for w in workers) / 1e6,
                    "median_constructor_cpu_ms": statistics.median(
                        statistics.median(s["cpu_ns"] for s in w["samples"])
                        for w in workers) / 1e6,
                    "median_fresh_process_wall_ms": statistics.median(
                        w["fresh_process_wall_ns"] for w in workers) / 1e6,
                }
            fast_native = (samples["fast"]["median_constructor_wall_ms"] /
                           samples["native"]["median_constructor_wall_ms"])
            summary.append({
                "count": refs_count, "owners": owners_count,
                "by_mode": samples, "fast_over_native": fast_native,
                "native_over_unguarded": (
                    samples["native"]["median_constructor_wall_ms"] /
                    samples["unguarded"]["median_constructor_wall_ms"]),
            })
            print(f"O218C_PROFILE host={sys.platform} count={refs_count} "
                  f"owners={owners_count} fast_over_native={fast_native:.4f}", flush=True)

        positive = all(row["fast_over_native"] >= 2.0
                       for row in summary
                       if row["owners"] == 1 and row["count"] in ALL_GATES)
        result = {
            "tier": "portable_host_extension_full_reader_research_not_product",
            "decision": ("HOST_C_EXTENSION_VIABLE" if positive else
                         "HOST_C_EXTENSION_ECONOMICS_NOT_PROVEN"),
            "host": {"platform": sys.platform, "python": sys.version,
                     "machine": __import__("platform").machine()},
            "parent": EXPECTED_PARENT, "branch": BRANCH, "source": source,
            "build": build, "semantics": semantics,
            "profiles": manifests, "raw_workers": raw, "summary": summary,
            "timing_contract": {
                "cycles": CYCLES, "workers_per_mode_cycle": WORKERS_PER_CYCLE,
                "samples_per_worker": SAMPLES_PER_WORKER,
                "compile_outside_constructor": True,
                "startup_outside_constructor": True,
                "unsafe_arm": "timing_floor_only_not_valid_product",
            },
            "unmeasured": [
                "wheel distribution/stable ABI/PyPy/ARM",
                "complete mixed-codec, signed journal, recovery and release parity",
                "VMHWM where OS does not expose Linux procfs",
                "native build lifecycle inside shipping product",
            ],
        }
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(f"O218C_DECISION={result['decision']}", flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.output)

if __name__ == "__main__":
    main()
