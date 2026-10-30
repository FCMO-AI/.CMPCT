#!/usr/bin/env python3
"""J24G58 lower-rung exact-parent ABBA, not a release-performance benchmark."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import runpy
import statistics
import subprocess
import sys
import time
import tracemalloc

from cmpct import journal_replay

ROOT = Path(__file__).resolve().parents[1]
PARENT_SOURCE = ROOT / "research" / "j24g58_frozen_parent_replay.py"
PARENT_BLOB = "03743ca2a06c022c2ec64243a90fe373cf91e899"


def source_blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\\x00" + raw).hexdigest()


def case(n):
    rows = [[f"old{i:06}", 9, i] for i in range(n)]
    index = {"files": rows,
             "fsmeta": {"xattrs": [[i, [[b"user.id", str(i).encode()]]]
                                    for i in range(0, n, max(1, n // 8))],
                        "owner_overrides": [[i, 1000+i, 3000+i]]
                                            for i in range(0, n, max(1, n // 16))}}
    ops = [["ren", f"old{i:06}", f"new{i:06}"] for i in range(n)]
    return index, ops


def one(fn, state, ops, cap):
    idx, instructions = copy.deepcopy(state), copy.deepcopy(ops)
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    returned = fn(idx, instructions, max_files=cap)
    wall, cpu = time.perf_counter_ns()-t0, time.process_time_ns()-c0
    assert returned is idx
    return idx, wall, cpu


def main():
    assert source_blob(PARENT_SOURCE) == PARENT_BLOB
    current = ROOT / "src" / "cmpct" / "journal_replay.py"
    assert current.read_bytes().replace(b"\r\n", b"\n") == Path(journal_replay.__file__).read_bytes().replace(b"\r\n", b"\n")
    old = runpy.run_path(str(PARENT_SOURCE))["_apply_journal_ops"]
    new = journal_replay._apply_journal_ops
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out = {"head": sha, "parent_git_blob": PARENT_BLOB,
           "candidate_git_blob": source_blob(current), "python": sys.version,
           "platform": platform.platform(), "cases": {}}
    for n in (64, 512, 2048, 4096):
        state, ops = case(n)
        # Verify equivalence and make data warm before any timed observation.
        baseline, _, _ = one(old, state, ops, n)
        candidate, _, _ = one(new, state, ops, n)
        assert baseline == candidate, n
        samples = {"A": [], "B": []}
        for turn in range(5):
            # ABBA / BAAB alternation; preserve raw samples and timing boundaries.
            order = "ABBA" if turn % 2 == 0 else "BAAB"
            for arm in order:
                _, wall, cpu = one(old if arm == "A" else new, state, ops, n)
                samples[arm].append({"wall_ns": wall, "cpu_ns": cpu, "order": order})
        # Memory measured independently, not mixed into CPU/wall timings.
        mem = {}
        for arm, fn in (("A", old), ("B", new)):
            tracemalloc.start()
            _, _, _ = one(fn, state, ops, n)
            _, peak = tracemalloc.get_traced_memory()
            mem[arm] = peak
            tracemalloc.stop()
        med_a = statistics.median(x["wall_ns"] for x in samples["A"])
        med_b = statistics.median(x["wall_ns"] for x in samples["B"])
        out["cases"][str(n)] = {"samples": samples, "peak_python_alloc_bytes": mem,
                               "median_wall_ns": {"A": med_a, "B": med_b},
                               "median_speedup_A_over_B": med_a/med_b,
                               "output_sha256": hashlib.sha256(repr(candidate).encode()).hexdigest()}
        print(f"N={n} parent={med_a/1e6:.3f}ms candidate={med_b/1e6:.3f}ms ratio={med_a/med_b:.3f}x peakA={mem['A']} peakB={mem['B']}", flush=True)
    target = Path(os.environ.get("J24G58_RESULT", "evidence/j24g58-abba.json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print("J24G58_RESULT", target, "SHA256", hashlib.sha256(target.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
