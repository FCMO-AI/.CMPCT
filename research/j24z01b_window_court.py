#!/usr/bin/env python3
"""J24Z01b: one preregistered counterfactual on original J24Z01 oracle's call granularity.

Does not change its algorithm, full CRC32/SHA256 obligations, original Reader or any format
semantics. Uses isolated children and the identical O209 physical archive for every arm.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

import j24z01_zstd_stream_oracle as j
from o209_physical_decode_unit_court import _build_inputs

MIB = 1024 * 1024
EXPECTED_WINDOWS = {"B64": 64 * 1024, "B256": 256 * 1024, "B1024": MIB}


def child(archive, mode, sample_sha):
    from cmpct.reader import CMPCT
    before = j.vmhwm_kib()
    t = time.perf_counter_ns()
    c = time.process_time_ns()
    with CMPCT(archive) as reader:
        if mode == "A":
            output = reader.read_range(j.NAME, 32 * MIB, MIB)
            meta = {"source": "unchanged-real-reader"}
        else:
            j.WINDOW = EXPECTED_WINDOWS[mode]
            output, meta = j.stream_range(archive, reader, 32 * MIB, MIB)
            assert meta["max_output_block"] <= j.WINDOW
            assert meta["full_crc32_verified"] and meta["full_sha256_verified"]
        wall, cpu = time.perf_counter_ns() - t, time.process_time_ns() - c
        after = j.vmhwm_kib()
    if len(output) != MIB or hashlib.sha256(output).hexdigest() != sample_sha:
        raise AssertionError("logical selected bytes differ from original")
    return {"mode": mode, "VmHWM_delta_KiB": max(0, after - before),
            "VmHWM_before_KiB": before, "VmHWM_after_KiB": after,
            "wall_ns": wall, "cpu_ns": cpu, **meta}


def run(out, repeats):
    if not sys.platform.startswith("linux") or not Path("/proc/self/status").exists():
        raise RuntimeError("requires actual Linux /proc VmHWM, not portable substitution")
    if repeats < 5:
        raise ValueError("five fresh independent interleaved repetitions required")
    repo = Path(__file__).resolve().parents[1]
    def cmd(*args):
        return subprocess.check_output(args, cwd=repo, text=True).strip()
    head = cmd("git", "rev-parse", "HEAD")
    reader_blob = cmd("git", "hash-object", "src/cmpct/reader.py")
    tool_blob = cmd("git", "hash-object", "research/j24z01b_window_court.py")
    origin_blob = cmd("git", "hash-object", "research/j24z01_zstd_stream_oracle.py")
    variants = _build_inputs(out.parent / "source")
    original = variants["single"]
    archive = out.parent / "source" / "single.cmpct"
    sample = original["sample_sha256"]
    observations = []
    modes = ("A", "B64", "B256", "B1024")
    for repetition in range(repeats):
        order = modes[repetition % 4:] + modes[:repetition % 4]
        for mode in order:
            call = [sys.executable, str(Path(__file__).resolve()), "_child",
                    str(archive), mode, sample]
            child_run = subprocess.run(call, capture_output=True, text=True, check=True)
            obj = json.loads(child_run.stdout)
            obj["repetition"] = repetition
            observations.append(obj)
    def med(mode, key):
        return statistics.median(v[key] for v in observations if v["mode"] == mode)
    summary = {}
    for mode in modes:
        summary[mode] = {"median_VmHWM_delta_KiB": med(mode, "VmHWM_delta_KiB"),
                         "median_wall_ms": med(mode, "wall_ns") / 1e6,
                         "median_cpu_ms": med(mode, "cpu_ns") / 1e6,
                         "repeat_count": repeats}
    def ratio(key, x, y):
        return med(x, key) / max(1, med(y, key))
    cpu_improve = 1 - ratio("cpu_ns", "B1024", "B64")
    wall_improve = 1 - ratio("wall_ns", "B1024", "B64")
    rss_margin = (med("A", "VmHWM_delta_KiB")
                  - med("B1024", "VmHWM_delta_KiB")) / 1024
    vs_a = max(ratio("cpu_ns", "B1024", "A"), ratio("wall_ns", "B1024", "A"))
    decision = ("NO_MATERIAL_MEMORY_MARGIN" if rss_margin < 32
                else "PRODUCT_ECONOMICS_NOT_YET_ESTABLISHED" if vs_a > 2
                else "BOUNDED_STREAM_COUNTERMECHANISM_CONTINUE"
                if min(cpu_improve, wall_improve) >= 0.2 else "BUFFER_AMORTIZATION_WEAK")
    result = {
        "schema": "cmpct-j24z01b-v1",
        "evidence_class": "Linux same-archive full-auth streaming granularity oracle",
        "git_head": head, "reader_git_blob": reader_blob,
        "original_oracle_blob": origin_blob, "followup_oracle_blob": tool_blob,
        "same_source": original, "raw_observations": observations,
        "summary": {"rows": summary,
                    "B1024_cpu_reduction_vs_B64": cpu_improve,
                    "B1024_wall_reduction_vs_B64": wall_improve,
                    "B1024_memory_margin_vs_reader_MiB": rss_margin,
                    "B1024_worst_CPU_or_wall_ratio_vs_reader": vs_a,
                    "decision": decision},
        "limitations": [
            "No product source changed and no earned full Reader benchmark gain",
            "Only one synthetic 64MiB repeated input and Linux native libzstd",
            "Complete physical CRC/SHA and decoded work charged in every B arm",
            "No new fault injection; original J24Z01 three fail-closed controls inherited",
            "A physical whole-frame source unchanged; fresh child process per row",
            "No portable package ABI, full ZIP64, cold I/O, concurrency or release claim"
        ]
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("run", "_child"))
    p.add_argument("args", nargs="*")
    a = p.parse_args()
    if a.mode == "_child":
        if len(a.args) != 3:
            raise SystemExit("_child ARCHIVE MODE SAMPLE_SHA")
        print(json.dumps(child(Path(a.args[0]), a.args[1], a.args[2]), sort_keys=True))
    else:
        if len(a.args) not in (1, 2):
            raise SystemExit("run PATH [REPEATS]")
        run(Path(a.args[0]), int(a.args[1]) if len(a.args) == 2 else 5)


if __name__ == "__main__":
    main()
