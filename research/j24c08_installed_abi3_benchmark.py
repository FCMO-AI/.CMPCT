#!/usr/bin/env python3
"""J24C08 source-exact installed-Reader A/B constructor economics (no release credit).

The only A/B change is a private scanner callable set to None in the strict
control worker. It runs the original validator on the same installed source.
Native workers use the product as installed, with no research injection.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

import cmpct.reader as reader_module
import cmpct._chunk_admission as admission
from cmpct.reader import CMPCT

COUNTS = ((65536, 1), (262144, 1), (65536, 256))
CYCLES = 4
IN_WORKER_REPEATS = 5


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source():
    return {"reader": digest(inspect.getfile(reader_module)),
            "admission": digest(inspect.getfile(admission)),
            "reader_path": str(Path(inspect.getfile(reader_module)).resolve())}


def rss():
    if sys.platform == "linux":
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) * 1024
        except OSError:
            pass
    if sys.platform == "darwin":
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except (ImportError, OSError):
            pass
    return None


def worker(path, size, mode):
    if mode not in ("strict", "native"):
        raise ValueError("unknown arm")
    if mode == "strict":
        admission._scan_refs = None
    elif admission._scan_refs is None:
        raise RuntimeError("native arm must have an active shipping extension")
    # Untimed parity control: the original physical bytes and public range answers
    # must match before timing. A late S_CHUNKS range is O(reference_count) and
    # MUST NOT contaminate the preregistered constructor-only wall/CPU samples.
    with CMPCT(Path(path)) as rd:
        assert len(rd.files) == 1 and rd.files[0][4] == size
        assert rd.read_range("fixed.bin", size - 4, 4) == b"ABCD"
    samples = []
    for index in range(IN_WORKER_REPEATS):
        start = time.perf_counter_ns()
        cpu_start = time.process_time_ns()
        with CMPCT(Path(path)) as rd:
            assert len(rd.files) == 1 and rd.files[0][4] == size
        samples.append({"wall_ns": time.perf_counter_ns() - start,
                        "cpu_ns": time.process_time_ns() - cpu_start,
                        "sample": index})
    result = {"mode": mode, "size": size, "source": source(), "rss_bytes": rss(),
              "samples": samples, "native_available": admission._scan_refs is not None}
    print(json.dumps(result, sort_keys=True))


def controller(output):
    if admission._scan_refs is None:
        raise RuntimeError("installed product native extension not available")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive
    installed = source()
    if not any(v in Path(installed["reader_path"]).parts for v in ("site-packages", "dist-packages")):
        raise RuntimeError("not a noneditable installed Reader: " + installed["reader_path"])

    rows, fixtures = [], []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c08-economics-") as td:
        for count, owner_count in COUNTS:
            blobs = tuple(bytes([65 + i % 23, 66, 67, 68]) for i in range(owner_count))
            refs = [i % owner_count for i in range(count)]
            logical = b"".join(blobs[i] for i in refs)
            wire = _make_archive(refs, logical, blobs=blobs)
            file = Path(td) / f"refs-{count}-{owner_count}.cmpct"
            file.write_bytes(wire)
            fixtures.append({"count": count, "owners": owner_count,
                             "archive_bytes": len(wire),
                             "archive_sha256": hashlib.sha256(wire).hexdigest(),
                             "logical_sha256": hashlib.sha256(logical).hexdigest()})
            # Two paired A/B/B/A blocks and two B/A/A/B blocks; no reader
            # source, runner, process/fixture semantics or timing boundaries change.
            for cycle in range(CYCLES):
                arms = ("strict", "native", "native", "strict") if cycle % 2 == 0 else (
                    "native", "strict", "strict", "native")
                for slot, mode in enumerate(arms):
                    command = [sys.executable, str(Path(__file__).resolve()),
                               "--worker", str(file), str(len(logical)), mode]
                    before = time.perf_counter_ns()
                    p = subprocess.run(command, capture_output=True, text=True,
                                       cwd=td, timeout=120, check=True)
                    spawn_wall = time.perf_counter_ns() - before
                    value = json.loads(p.stdout)
                    assert value["mode"] == mode and value["size"] == len(logical)
                    assert value["source"] == installed
                    value.update({"count": count, "owners": owner_count,
                                  "cycle": cycle, "slot": slot,
                                  "total_process_wall_ns": spawn_wall})
                    rows.append(value)
            print(f"J24C08_PROFILE count={count} owners={owner_count} workers={CYCLES * 4}", flush=True)
    out = {"schema": "cmpct-j24c08-installed-economics-v1",
           "evidence_head": os.environ.get("EVIDENCE_SHA", "unbound-local"),
           "source": installed, "python": sys.version,
           "platform": sys.platform, "fixtures": fixtures,
           "raw_workers": rows, "prospective": {
              "focus": [65536, 262144], "strict_over_native_wall_at_least": 2.0,
              "rss_growth_max_bytes": 8 * 1024 * 1024},
           "nonclaims": ["native constructor ≠ whole product archive create/extract",
                         "startup/process wall excluded from constructor timing",
                         "same installed wheel/native binary under both arms",
                         "not official D5 benchmark or release authority"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(f"J24C08_RAW_WORKERS={len(rows)} SOURCE_READER={installed['reader']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", nargs=3)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker[0], int(args.worker[1]), args.worker[2])
    else:
        if args.output is None:
            parser.error("controller needs --output")
        controller(args.output)
