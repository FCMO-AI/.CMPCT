#!/usr/bin/env python3
"""J24C18: source-bound C-native fused-copy component oracle, NOT a CMPCT Reader benchmark.

Both arms run the same exact-source C S_CHUNKS proof from J24C17, including
all 256-stride checkpoints, over identical deterministic built-in lists.
The only changed variable is when/how the immutable tuple is allocated:
after the C scan using CPython tuple(refs) versus inside the same C pass.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


CASES = (
    ("four-65536", 65536, 4),
    ("four-262144", 262144, 4),
    ("four-1048576", 1048576, 4),
    ("many-262144", 262144, 256),
)
ARMS = ("control", "fused")


def prepared(case: str):
    name, n, nowners = next(x for x in CASES if x[0] == case)
    rng = random.Random(241800 + n + nowners)
    # Exact bounded synthetic descriptors; zero and heterogeneous sizes
    # keep the native proof's real logical-prefix accounting relevant.
    blobs = [[i * 3, (i * 17 + 1) % 19, (i * 17 + 1) % 19, 0, 0]
             for i in range(nowners)]
    blobs[1][1] = blobs[1][2] = 0
    refs = [rng.randrange(nowners) for _ in range(n)]
    expected = sum(blobs[i][1] for i in refs)
    return refs, blobs, expected


def rss_kib():
    if sys.platform == "win32":
        # Windows peak RSS is deliberately unknown if a process API is not
        # explicitly installed. Do not silently report zero.
        return None
    import resource
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(raw / 1024, 3) if sys.platform == "darwin" else int(raw)


def worker(case, arm, repetition):
    import _j24c18_fusion as native

    refs, blobs, expected = prepared(case)
    n = len(refs)
    assert type(refs) is list and type(blobs) is list
    assert n >= 512
    gc.collect()
    cpu0 = time.process_time_ns()
    wall0 = time.perf_counter_ns()
    if arm == "control":
        marks = native.scan_refs_index(refs, blobs, expected)
        assert type(marks) is tuple
        frozen = tuple(refs)
    elif arm == "fused":
        pair = native.scan_refs_index_copy(refs, blobs, expected)
        assert type(pair) is tuple and len(pair) == 2
        marks, frozen = pair
    else:
        raise ValueError(arm)
    wall_ms = (time.perf_counter_ns() - wall0) / 1000000
    cpu_ms = (time.process_time_ns() - cpu0) / 1000000
    assert type(marks) is tuple and type(frozen) is tuple
    assert len(marks) == (n + 255) // 256
    assert len(frozen) == n
    assert frozen == tuple(refs)
    # Independent Python reconstruction of all 256-stride logical offsets.
    prefix = 0
    for j, idx in enumerate(refs):
        if j % 256 == 0:
            assert marks[j // 256] == prefix, (j, prefix)
        prefix += blobs[idx][1]
    assert prefix == expected
    digest = hashlib.sha256(repr((marks, frozen)).encode("utf-8")).hexdigest()
    return {
        "case": case, "arm": arm, "rep": repetition, "n": n, "owners": len(blobs),
        "expected": expected, "checkpoint_count": len(marks),
        "digest": digest, "wall_ms": wall_ms, "cpu_ms": cpu_ms,
        "process_hwm_kib": rss_kib(), "python": sys.version,
        "platform": platform.platform(),
    }


def assert_negative_inputs():
    import _j24c18_fusion as native
    valid_blobs = [[0, 1, 1, 0, 0], [1, 0, 0, 0, 0]]
    examples = [
        ([0] * 511 + [True], 512),
        ([0] * 511 + [-1], 511),
        ([0] * 511 + [3], 511),
        ([0] * 511 + [2**100], 511),
        ([0] * 512, 513),
    ]
    for refs, total in examples:
        a = native.scan_refs_index(refs, valid_blobs, total)
        b = native.scan_refs_index_copy(refs, valid_blobs, total)
        assert a is False and b is False, ("false positive", refs[-1], total)
    print("J24C18_BOTH_NATIVE_ARMS_REJECT_ALL_FIVE_HOSTILE_CASES")


def compile_module(src: Path, scratch: Path):
    shutil.copy2(src, scratch / src.name)
    (scratch / "setup.py").write_text(
        "from setuptools import setup, Extension\n"
        "setup(name='j24c18-oracle',version='0',ext_modules=["
        "Extension('_j24c18_fusion',['j24c18_fused_copy_component.c'],"
        "py_limited_api=True,extra_compile_args=[])] )\n",
        encoding="utf-8",
    )
    done = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        cwd=scratch, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False,
    )
    if done.returncode:
        raise RuntimeError("component native build failed:\n" + done.stdout[-5000:])
    assert list(scratch.glob("_j24c18_fusion*")), "native component module absent"


def launch(args):
    source = Path(__file__).resolve().parent / "j24c18_fused_copy_component.c"
    assert source.is_file(), source
    repetitions = args.repetitions
    assert repetitions >= 9
    records = []
    with tempfile.TemporaryDirectory(prefix="j24c18-component-") as tmp:
        scratch = Path(tmp)
        compile_module(source, scratch)
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([tmp, env.get("PYTHONPATH", "")])
        sub_args = [sys.executable, str(Path(__file__).resolve())]
        pre = subprocess.run(sub_args + ["--invalid"], env=env,
                             capture_output=True, text=True, check=True)
        print(pre.stdout.strip(), flush=True)
        for case_name, _, _ in CASES:
            for rep in range(repetitions):
                # Paired alternating ordering defeats persistent side/thermal bias;
                # times are measured inside each worker, not process startup.
                sequence = ARMS if rep % 2 == 0 else tuple(reversed(ARMS))
                for arm in sequence:
                    cmd = sub_args + ["--worker", "--case", case_name,
                                      "--arm", arm, "--rep", str(rep)]
                    done = subprocess.run(cmd, env=env, cwd=str(source.parent.parent),
                                          capture_output=True, text=True, check=True)
                    records.append(json.loads(done.stdout))
    output = {
        "schema": "j24c18-fused-seal-component-v1",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_parent_sha": "3b6a73f9205f40f11124cd9ff332407e52cebb93",
        "source_ref": "FCMO-AI/.CMPCT#676",
        "evidence_sha": os.environ.get("EVIDENCE_SHA", "local-unbound"),
        "python": sys.version,
        "platform": platform.platform(),
        "cases": [x[0] for x in CASES],
        "repetitions": repetitions,
        "records": records,
    }
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, _, _ in CASES:
        d = {arm: statistics.median(x["wall_ms"] for x in records
                                   if x["case"] == name and x["arm"] == arm)
             for arm in ARMS}
        print(f"{name}: control={d['control']:.3f}ms "
              f"fused={d['fused']:.3f}ms ratio={d['fused']/d['control']:.4f}", flush=True)
    print("J24C18_COMPONENT_RUN_COMPLETE", dest, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("--invalid", action="store_true")
    ap.add_argument("--case", choices=[x[0] for x in CASES])
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--output", default="receipts/j24c18-component.json")
    ap.add_argument("--repetitions", type=int, default=9)
    a = ap.parse_args()
    if a.invalid:
        assert_negative_inputs()
    elif a.worker:
        print(json.dumps(worker(a.case, a.arm, a.rep), sort_keys=True))
    else:
        launch(a)
