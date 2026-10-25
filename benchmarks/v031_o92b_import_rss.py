#!/usr/bin/env python3
"""O92b import-phase memory oracle, genuinely installed original O63/O86.

No Builder, Reader instance, archive or codec candidate is constructed.
Linux ru_maxrss is peak-to-date; VmRSS/RssAnon are live snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

REPS = 3
SOURCES = {
    "o63": "18e32cae012f5dca9fc47f10d194f8b81005c85c",
    "o86": "6225e30f3e21c0783aa56726b52a3a3583540f99",
}


def snapshot() -> dict:
    fields = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:", "RssAnon:", "RssFile:", "VmSize:")):
            k, v = line.split(":", 1)
            fields[k] = int(v.strip().split()[0])
    assert "VmRSS" in fields and "VmHWM" in fields
    fields["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return fields


def worker(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    assert "cmpct" not in sys.modules, "CMPCT prematurely imported"
    steps = {"pure_python_harness": snapshot()}
    started = time.perf_counter_ns()

    import cmpct
    steps["after_cmpct_init"] = snapshot()

    import cmpct.builder as bm
    steps["after_builder_import"] = snapshot()

    import cmpct.codec as cm
    steps["after_codec_import"] = snapshot()

    import cmpct.reader as rm
    steps["after_reader_import"] = snapshot()

    import cmpct.native_codec as nm
    steps["after_native_codec_import"] = snapshot()
    pkg = Path(a.package).resolve()
    imports = {
        "package": str(Path(cmpct.__file__).resolve()),
        "builder": str(Path(bm.__file__).resolve()),
        "codec": str(Path(cm.__file__).resolve()),
        "reader": str(Path(rm.__file__).resolve()),
        "native_codec": str(Path(nm.__file__).resolve()),
    }
    assert all(Path(path).is_relative_to(pkg) for path in imports.values())
    high = [step["ru_maxrss_kib"] for step in steps.values()]
    assert high == sorted(high), steps
    assert all(abs(row["VmHWM"] - row["ru_maxrss_kib"]) < 4096
               for row in steps.values()), "Linux highwater witnesses disagree"

    print(json.dumps({
        "experiment": "O92b", "source_commit": SOURCES[a.arm],
        "arm": a.arm, "rep": a.rep, "steps": steps,
        "imports": imports, "elapsed_ns": time.perf_counter_ns() - started,
        "python": sys.version.split()[0],
        "sys_platform": sys.platform,
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    report_path = Path(a.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    install = {"o63": Path(a.o63_package).resolve(),
               "o86": Path(a.o86_package).resolve()}
    report = {
        "experiment": "O92b", "status": "research-oracle-only",
        "source_commits": SOURCES, "repetitions": REPS,
        "observations": [], "failures": [], "summary": None,
    }

    def persist() -> None:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    persist()
    for rep in range(REPS):
        order = ("o63", "o86") if rep % 2 == 0 else ("o86", "o63")
        for arm in order:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(install[arm])
            cmd = [sys.executable, str(Path(__file__).resolve()),
                   "--worker", "--arm", arm, "--rep", str(rep),
                   "--package", str(install[arm])]
            try:
                c = subprocess.run(cmd, env=env, capture_output=True,
                                   text=True, timeout=45)
                if c.returncode:
                    raise RuntimeError(f"exit={c.returncode}\n" +
                                       c.stdout[-1000:] + c.stderr[-3000:])
                row = json.loads(c.stdout.strip().splitlines()[-1])
                assert row["experiment"] == "O92b" and row["rep"] == rep
                assert row["arm"] == arm and row["source_commit"] == SOURCES[arm]
                assert row["steps"]["pure_python_harness"]["VmRSS"] > 0
                report["observations"].append(row)
                persist()
            except Exception as exc:
                report["failures"].append({
                    "arm": arm, "rep": rep, "error": str(exc)[:4000]
                })
                persist()
                raise

    phases = list(report["observations"][0]["steps"])
    metrics = ["ru_maxrss_kib", "VmRSS", "VmHWM", "RssAnon"]
    medians = {
        arm: {
            phase: {
                field: statistics.median([
                    obs["steps"][phase][field]
                    for obs in report["observations"] if obs["arm"] == arm
                ]) for field in metrics
            } for phase in phases
        } for arm in SOURCES
    }
    assert len(report["observations"]) == 2 * REPS
    report["summary"] = medians
    persist()
    print("O92B_ACTUAL_FRESH_IMPORT_PROCESSES=6")
    print("O92B_IMPORT_MEMORY_RESULT=" + json.dumps(medians, sort_keys=True))
    print("O92B_RAW_REPORT=" + str(report_path))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=("o63", "o86"))
    p.add_argument("--rep", type=int)
    p.add_argument("--package")
    p.add_argument("--o63-package")
    p.add_argument("--o86-package")
    p.add_argument("--report", default="o92b-evidence/o92b-raw.json")
    a = p.parse_args()
    worker(a) if a.worker else court(a)


if __name__ == "__main__":
    main()
