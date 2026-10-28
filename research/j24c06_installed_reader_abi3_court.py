#!/usr/bin/env python3
"""O218e prospective full installed Reader economics: safe Python vs direct C vs abi3.

Research only. The Reader/validator are unchanged, source-pinned, and installed as
wheels. No result is a product release or proof of signed-journal recovery.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile

import j24c06_o218b_native_reader as inherited
import j24c06_o218c_native_host as host_native
import j24c06_o216_fastpath as o216

PARENT = "fdd5b040dbbaeaac79f029c2ab5c58162ec894cd"
PREREG = "c65874a3c548016d7135727959214884eeb306c2"
PROFILES = ((65536, 1), (262144, 1), (65536, 256))
MODES = ("original", "fast", "direct", "abi3", "unguarded")
CYCLES, WORKERS_PER_MODE_CYCLE, SAMPLES_PER_WORKER = 2, 2, 5
SEED = 21820261028

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stable_module():
    m = importlib.import_module("_o218_fastscan")
    if not hasattr(m, "scan_refs"):
        raise AssertionError("installed abi3 wheel missing scan_refs")
    return m

def wheel_identity(wheel_dir: Path, module):
    wheels = list(wheel_dir.glob("*.whl"))
    if len(wheels) != 1 or "cp311-abi3-" not in wheels[0].name:
        raise AssertionError(f"not exactly one cp311-abi3 wheel: {wheels}")
    with zipfile.ZipFile(wheels[0]) as archive:
        binaries = [n for n in archive.namelist()
                    if n.endswith((".so", ".pyd")) and "_o218_fastscan" in n]
        if len(binaries) != 1:
            raise AssertionError(binaries)
        binary_sha = digest(archive.read(binaries[0]))
    module_path = Path(module.__file__).resolve()
    if "site-packages" not in str(module_path).replace("\\", "/") and "dist-packages" not in str(module_path).replace("\\", "/"):
        raise AssertionError("ABI3 not imported from installed package: " + str(module_path))
    if digest(module_path.read_bytes()) != binary_sha:
        raise AssertionError("installed ABI3 binary differs from wheel")
    return {"wheel_name": wheels[0].name, "wheel_bytes": wheels[0].stat().st_size,
            "wheel_sha256": digest(wheels[0].read_bytes()),
            "installed_binary_sha256": binary_sha, "installed_binary_bytes": module_path.stat().st_size,
            "installed_binary_path": str(module_path)}

def make_fixtures(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    source = inherited.source_identity()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive
    rows = []
    for count, owners in PROFILES:
        refs, logical, blobs = inherited.build_case(count, owners)
        wire = _make_archive(refs, logical, blobs=blobs)
        file = output / f"j24c06-{count}-{owners}.cmpct"
        file.write_bytes(wire)
        rows.append({"count": count, "owners": owners, "archive": file.name,
                     "archive_bytes": len(wire), "archive_sha256": digest(wire),
                     "logical_bytes": len(logical), "logical_sha256": digest(logical)})
    manifest = {"tier": "source_exact_fixture_not_product", "source": source,
                "parent": PARENT, "prereg": PREREG, "rows": rows}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("O218E_FIXTURES_BUILT " + json.dumps({"rows": len(rows), "source": source}), flush=True)

def validate_manifest(folder: Path):
    obj = json.loads((folder / "manifest.json").read_text())
    if obj["source"] != inherited.source_identity() or obj["parent"] != PARENT or obj["prereg"] != PREREG:
        raise AssertionError("source manifest drift")
    if [(x["count"], x["owners"]) for x in obj["rows"]] != list(PROFILES):
        raise AssertionError("unexpected fixture profiles")
    for entry in obj["rows"]:
        archive = folder / entry["archive"]
        if archive.stat().st_size != entry["archive_bytes"] or digest(archive.read_bytes()) != entry["archive_sha256"]:
            raise AssertionError("signed-wire fixture mutated")
    return obj

def worker(archive: Path, logical_size: int, mode: str, direct_path: Path):
    source = inherited.source_identity()
    abi3 = stable_module()
    direct = inherited.load_binary(str(direct_path))
    if mode == "direct":
        inherited.validation._validate_storage = inherited.native_validator(direct)
    elif mode == "abi3":
        inherited.validation._validate_storage = inherited.native_validator(abi3)
    else:
        inherited.install(mode, direct)
    with inherited.CMPCT(archive) as rd:
        if len(rd.files) != 1 or rd.files[0][4] != logical_size:
            raise AssertionError("Reader logical size mismatch")
        if rd.read_range("fixed.bin", 0, 4) != b"ABCD":
            raise AssertionError("Reader selected bytes mismatch")
    samples = []
    for _ in range(SAMPLES_PER_WORKER):
        begin, begin_cpu = time.perf_counter_ns(), time.process_time_ns()
        with inherited.CMPCT(archive) as rd:
            if len(rd.files) != 1 or rd.files[0][4] != logical_size:
                raise AssertionError("Reader file contract drift")
        samples.append({"wall_ns": time.perf_counter_ns() - begin,
                        "cpu_ns": time.process_time_ns() - begin_cpu})
    rss = None
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                rss = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    print(json.dumps({"mode": mode, "source": source, "samples": samples,
                      "vmhwm_bytes": rss, "python_minor": list(sys.version_info[:2]),
                      "abi3_binary_sha256": digest(Path(abi3.__file__).read_bytes()),
                      "direct_binary_sha256": digest(direct_path.read_bytes())}, sort_keys=True))

def run(folder: Path, out: Path, wheel_dir: Path):
    folder, out, wheel_dir = folder.resolve(), out.resolve(), wheel_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = validate_manifest(folder)
    source = manifest["source"]
    abi3 = stable_module()
    wheel = wheel_identity(wheel_dir, abi3)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c06-direct-") as temp:
        root = Path(temp)
        direct, binary, build = host_native.build_unmodified_extension(root, out)
        direct_semantics = inherited.semantics(direct)
        abi3_semantics = inherited.semantics(abi3)
        if direct_semantics != abi3_semantics:
            raise AssertionError("direct-C versus abi3 semantic drift")
        semantics = {"inherited_cases": direct_semantics["inherited_cases"],
                     "named_cases": direct_semantics["named_cases"],
                     "fuzz_cases": direct_semantics["fuzz_cases"],
                     "decision_sha256": digest(json.dumps(direct_semantics, sort_keys=True).encode())}
        raw = []
        progress = out / "raw-workers.jsonl"
        rng = random.Random(SEED + sys.version_info.minor)
        with progress.open("w", encoding="utf-8") as handle:
            for entry in manifest["rows"]:
                archive = folder / entry["archive"]
                for cycle in range(CYCLES):
                    arms = list(MODES) * WORKERS_PER_MODE_CYCLE
                    rng.shuffle(arms)
                    for mode in arms:
                        cmd = [sys.executable, str(Path(__file__).resolve()),
                               "--worker", str(archive), str(entry["logical_bytes"]),
                               mode, str(binary)]
                        start = time.perf_counter_ns()
                        done = subprocess.run(cmd, cwd=temp, capture_output=True, text=True, timeout=180)
                        fresh_ns = time.perf_counter_ns() - start
                        if done.returncode:
                            raise AssertionError(f"worker {mode} failed: {done.stderr[-2500:]} {done.stdout[-1000:]}")
                        row = json.loads(done.stdout.strip())
                        if row["mode"] != mode or row["source"] != source:
                            raise AssertionError("worker source/mode mismatch")
                        if row["abi3_binary_sha256"] != wheel["installed_binary_sha256"] or row["direct_binary_sha256"] != build["binary_sha256"]:
                            raise AssertionError("worker native binary identity drift")
                        row.update({"count": entry["count"], "owners": entry["owners"],
                                    "cycle": cycle, "archive_sha256": entry["archive_sha256"],
                                    "fresh_process_wall_ns": fresh_ns})
                        raw.append(row)
                        handle.write(json.dumps(row, sort_keys=True) + "\n")
                        handle.flush()
        summary = []
        for entry in manifest["rows"]:
            samples = {}
            for mode in MODES:
                workers = [x for x in raw if x["count"] == entry["count"] and
                           x["owners"] == entry["owners"] and x["mode"] == mode]
                if len(workers) != CYCLES * WORKERS_PER_MODE_CYCLE:
                    raise AssertionError(f"worker count discrepancy: {entry} {mode}")
                samples[mode] = {
                    "median_constructor_wall_ms": statistics.median(
                        statistics.median(y["wall_ns"] for y in w["samples"])
                        for w in workers) / 1e6,
                    "median_constructor_cpu_ms": statistics.median(
                        statistics.median(y["cpu_ns"] for y in w["samples"])
                        for w in workers) / 1e6,
                    "median_fresh_process_wall_ms": statistics.median(
                        w["fresh_process_wall_ns"] for w in workers) / 1e6,
                    "median_vmhw_bytes_linux_only": (
                        statistics.median(w["vmhwm_bytes"] for w in workers)
                        if all(w["vmhwm_bytes"] is not None for w in workers) else None),
                    "zero_cpu_samples": sum(y["cpu_ns"] == 0 for w in workers for y in w["samples"]),
                }
            fast_over_abi3 = samples["fast"]["median_constructor_wall_ms"] / samples["abi3"]["median_constructor_wall_ms"]
            abi3_over_direct = samples["abi3"]["median_constructor_wall_ms"] / samples["direct"]["median_constructor_wall_ms"]
            summary.append({"count": entry["count"], "owners": entry["owners"],
                            "by_mode": samples, "safe_python_over_abi3": fast_over_abi3,
                            "abi3_over_direct": abi3_over_direct,
                            "abi3_over_unsafe": samples["abi3"]["median_constructor_wall_ms"] /
                                                samples["unguarded"]["median_constructor_wall_ms"]})
        focus = [x for x in summary if x["owners"] == 1 and x["count"] in (65536, 262144)]
        if len(focus) != 2:
            raise AssertionError("prereg focus missing")
        strong = all(x["safe_python_over_abi3"] >= 2.0 and x["abi3_over_direct"] <= 2.0 for x in focus)
        negative = any(x["safe_python_over_abi3"] <= 1.0 for x in focus)
        decision = ("ABI3_FULL_READER_STRONG_HOST_PASS" if strong else
                    "ABI3_FULL_READER_ECONOMIC_NEGATIVE" if negative else
                    "ABI3_FULL_READER_INSUFFICIENT_OR_AMBIGUOUS")
        result = {"tier": "whole_installed_reader_research_not_product",
                  "decision": decision, "source": source, "parent": PARENT,
                  "prereg": PREREG,
                  "host": {"platform": sys.platform, "machine": platform.machine(),
                           "python_minor": list(sys.version_info[:2]), "python_executable": sys.executable},
                  "wheel": wheel,
                  "direct_native": {**build, "artifact": binary.name},
                  "semantics": semantics, "fixtures": manifest["rows"],
                  "raw_workers": raw, "raw_workers_sha256": digest(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()), "summary": summary,
                  "timing_contract": {"cycles": CYCLES, "workers_per_mode_cycle": WORKERS_PER_MODE_CYCLE,
                                      "samples_per_worker": SAMPLES_PER_WORKER,
                                      "startup_and_wheel_build_excluded_from_constructor": True,
                                      "unguarded_is_unsafe_lower_bound_only": True},
                  "unmeasured": ["signed transaction recovery", "heterogeneous codecs",
                                 "Reader #569 composition", "full release parity",
                                 "macOS/Windows full-process RSS", "PyPy and ARM"],
                  }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("O218E_DECISION=" + decision, flush=True)
        for row in summary:
            print("O218E_PROFILE=" + json.dumps({
                "count": row["count"], "owners": row["owners"],
                "safe_python_over_abi3": row["safe_python_over_abi3"],
                "abi3_over_direct": row["abi3_over_direct"]}, sort_keys=True), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--make-fixtures", type=Path)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--wheel-dir", type=Path)
    parser.add_argument("--worker", nargs=4)
    args = parser.parse_args()
    if args.worker:
        archive, logical, mode, direct = args.worker
        if mode not in MODES:
            parser.error("unknown worker mode")
        worker(Path(archive), int(logical), mode, Path(direct))
    elif args.make_fixtures:
        make_fixtures(args.make_fixtures)
    elif args.fixtures and args.output and args.wheel_dir:
        run(args.fixtures, args.output, args.wheel_dir)
    else:
        parser.error("provide --make-fixtures or --fixtures --output --wheel-dir")

if __name__ == "__main__":
    main()
