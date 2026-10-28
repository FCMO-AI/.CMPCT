#!/usr/bin/env python3
"""J24G20 post-result causal replay: fork/exec versus default spawn RSS custody.

Exploratory infrastructure evidence, not part of frozen H2; no product code.
Tests whether process-wide ru_maxrss inherits the supervisor's old high watermark
when a short subprocess is used after a large fixture has been constructed.
"""
from __future__ import annotations
import gc
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys


def rss():
    d = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmHWM:", "VmRSS:")):
            d[line.split(":", 1)[0]] = int(line.split()[1])
    d["ru_maxrss"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return d


CHILD = """import json, resource
from pathlib import Path
d = {}
for line in Path('/proc/self/status').read_text().splitlines():
    if line.startswith(('VmHWM:', 'VmRSS:')):
        d[line.split(':', 1)[0]] = int(line.split()[1])
d['ru_maxrss'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps(d))
"""


def run():
    before = rss()
    # Touch every page; an uncommitted bytearray is not a memory proof.
    payload = bytearray(70 * 1024 * 1024)
    for i in range(0, len(payload), 4096):
        payload[i] = 1
    allocated = rss()
    del payload
    gc.collect()
    freed = rss()
    observations = {}
    for mode in ("default", "fork_exec"):
        observations[mode] = []
        for repetition in range(3):
            kwargs = {} if mode == "default" else {"preexec_fn": lambda: None}
            p = subprocess.run([sys.executable, "-c", CHILD],
                               capture_output=True, text=True, **kwargs)
            assert p.returncode == 0, p.stderr
            observations[mode].append(json.loads(p.stdout))
    # A distinct instrumented observable; not an acceptance threshold.
    default = observations["default"]
    forked = observations["fork_exec"]
    output = {
        "schema": "cmpct-j24g20-posix-rss-custody-v1",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "before": before, "allocated": allocated, "freed": freed,
        "observations": observations,
        "default_inherited_peak_observed": all(
            r["ru_maxrss"] > r["VmHWM"] + 16384 for r in default),
        "fork_exec_delta_peak_observed": all(
            r["ru_maxrss"] <= r["VmHWM"] + 8192 for r in forked),
        "product_or_release_claim": False,
        "note": "Exploratory post-result causal replay; not frozen J24G20 H2 credit."
    }
    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    run()
