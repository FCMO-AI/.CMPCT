#!/usr/bin/env python3
"""O92c: independent Linux resource-accounting oracle, not CMPCT product code."""
from __future__ import annotations

import gc
import json
import os
import resource
import subprocess
import sys
from pathlib import Path

MIB = 1024 * 1024
ALLOC = 192 * MIB


def witness() -> dict:
    mem = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmHWM:", "VmRSS:", "RssAnon:")):
            k, raw = line.split(":", 1)
            mem[k] = int(raw.strip().split()[0])
    mem["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mem["pid"] = os.getpid()
    return mem


def child() -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError(p.stderr[-1000:] + p.stdout[-1000:])
    return json.loads(p.stdout.strip())


def main() -> None:
    assert sys.platform.startswith("linux")
    if "--child" in sys.argv:
        print(json.dumps(witness(), sort_keys=True))
        return
    report = {"experiment": "O92c", "python": sys.version.split()[0],
              "parent_initial": witness(), "child_unprimed": child()}
    payload = bytearray(ALLOC)
    for idx in range(0, len(payload), 4096):
        payload[idx] = 1  # materialize pages
    report["parent_with_allocation"] = witness()
    del payload
    gc.collect()
    report["parent_after_free"] = witness()
    report["children_after_parent_peak"] = [child() for _ in range(3)]
    parent_peak = report["parent_with_allocation"]["ru_maxrss_kib"]
    report["parent_peak_rss_kib"] = parent_peak
    children = report["children_after_parent_peak"]
    report["inherited_ru_maxrss"] = all(
        c["ru_maxrss_kib"] >= parent_peak * 0.92 and
        c["ru_maxrss_kib"] > c["VmHWM"] * 3
        for c in children)
    report["clean_child_rss_kib"] = report["child_unprimed"]["VmHWM"]
    report["decision"] = (
        "CONFIRMED_INHERITED_ACCOUNTING" if report["inherited_ru_maxrss"] else
        "FALSIFIED_OR_AMBIGUOUS"
    )
    dest = Path(os.environ.get("O92C_REPORT", "o92c-evidence/o92c-raw.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("O92C_ACTUAL_CHILD_PROCESSES=4", flush=True)
    print("O92C_DECISION=" + report["decision"], flush=True)
    print("O92C_RAW=" + json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
