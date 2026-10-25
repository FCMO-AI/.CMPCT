#!/usr/bin/env python3
"""O95b: O86 same-installed-engine VZIP budget-causality memory falsifier.

This never edits O95, O88, product, benchmarks, format or release policy.
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
import tempfile
import time

import v031_o88_vzip_budget_positive_economics as o88
from v031_o95_child_vmhwm_attribution import snapshot

REPS = 3
BUDGET = {"default": None, "allow_vzip": str(128 * o88.MIB)}


def worker(a: argparse.Namespace) -> None:
    initial = snapshot()
    import cmpct.builder as builder_module
    import cmpct.codec as codec_module
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import K_FILE, S_BLOB, S_VZIP, S_PACK

    pkg = Path(a.package).resolve()
    assert Path(builder_module.__file__).resolve().is_relative_to(pkg)
    assert Path(codec_module.__file__).resolve().is_relative_to(pkg)
    assert os.environ.get("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES") == BUDGET[a.arm]
    src = Path(a.root)
    expected = json.loads(Path(a.manifest).read_text())
    hashes = {x["path"]: x["zip_sha256"] for x in expected}
    assert o88.source_digest(src) == hashes
    after_import = snapshot()

    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    builder = Builder(src, workers=1, reproducible=True, reproducible_epoch_ns=0)
    out = Path(a.output)
    builder.build(out)
    wall_ns = time.perf_counter_ns() - t0
    cpu_ns = time.process_time_ns() - c0
    after_builder = snapshot()
    kinds = {row[0]: row[6][0] for row in builder.files if row[1] == K_FILE}
    assert set(kinds) == set(hashes) and S_PACK not in kinds.values()
    expected_kind = S_BLOB if a.arm == "default" else S_VZIP
    assert set(kinds.values()) == {expected_kind}, (a.arm, kinds)
    assert o88.source_digest(src) == hashes
    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        for name in sorted(hashes):
            assert hashlib.sha256(reader.read(name)).hexdigest() == hashes[name]
        dest = out.parent / (out.stem + "-extract")
        reader.extractall(dest, metadata=False)
    after_reader = snapshot()
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in dest.glob("*.zip")} == hashes
    assert o88.source_digest(src) == hashes
    assert after_builder["vmhwm_kib"] >= after_import["vmhwm_kib"]
    assert after_reader["vmhwm_kib"] >= after_builder["vmhwm_kib"]

    print(json.dumps({
        "experiment": "O95b", "arm": a.arm, "rep": a.rep,
        "engine": o88.CAND_SHA, "source_hashes": hashes,
        "budget_value": BUDGET[a.arm],
        "kinds": kinds, "archive_bytes": out.stat().st_size,
        "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "create_wall_ns": wall_ns, "create_cpu_ns": cpu_ns,
        "child_before_import": initial, "after_import": after_import,
        "after_builder": after_builder, "after_reader": after_reader,
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    pkg = Path(a.o86_package).resolve()
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-o95b-"))
    src = scratch / "original-shared-over" / "source"
    fixture = o88.fixture(src, 65 * o88.MIB, "shared")
    manifest = scratch / "original-manifest.json"
    manifest.write_text(json.dumps(fixture, sort_keys=True, indent=2))
    hashes = o88.source_digest(src)
    dest = Path(a.report).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "experiment": "O95b", "status": "science-only",
        "engine_commit": o88.CAND_SHA, "source": fixture,
        "source_hashes": hashes, "reps": REPS,
        "observations": [], "failures": [], "summary": None,
    }

    def persist():
        dest.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")

    persist()
    for rep in range(REPS):
        order = ("default", "allow_vzip") if rep % 2 == 0 else ("allow_vzip", "default")
        for arm in order:
            env = os.environ.copy()
            env.pop("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", None)
            if BUDGET[arm] is not None:
                env["CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES"] = BUDGET[arm]
            env["PYTHONPATH"] = str(pkg)
            cmd = [
                sys.executable, str(Path(__file__).resolve()), "--worker",
                "--arm", arm, "--rep", str(rep),
                "--package", str(pkg), "--root", str(src),
                "--manifest", str(manifest),
                "--output", str(scratch / f"{arm}-{rep}.cmpct"),
            ]
            cp = subprocess.run(cmd, env=env, cwd=scratch,
                                text=True, capture_output=True, timeout=420)
            if cp.returncode:
                report["failures"].append({"arm": arm, "rep": rep,
                                           "exit": cp.returncode,
                                           "stderr": cp.stderr[-3000:],
                                           "stdout": cp.stdout[-1500:]})
                persist()
                raise RuntimeError(f"O95b {arm}/{rep} exit={cp.returncode}")
            obs = json.loads(cp.stdout.strip().splitlines()[-1])
            assert obs["source_hashes"] == hashes and obs["arm"] == arm
            report["observations"].append(obs)
            persist()
    arms = {
        a: [x for x in report["observations"] if x["arm"] == a]
        for a in ("default", "allow_vzip")
    }
    assert all(len(x) == REPS for x in arms.values())
    assert all(len({x["archive_sha256"] for x in xs}) == 1
               for xs in arms.values()), "nondeterministic archive"
    assert arms["default"][0]["archive_bytes"] == 52641
    assert arms["allow_vzip"][0]["archive_bytes"] == 664428
    assert o88.source_digest(src) == hashes

    peak = lambda arm: statistics.median(x["after_builder"]["vmhwm_kib"]
                                         for x in arms[arm])
    medcpu = lambda arm: statistics.median(x["create_cpu_ns"]
                                           for x in arms[arm]) / 1e6
    report["summary"] = {
        "default_archive_bytes": arms["default"][0]["archive_bytes"],
        "allow_vzip_archive_bytes": arms["allow_vzip"][0]["archive_bytes"],
        "default_vmhwm_kib": peak("default"),
        "allow_vzip_vmhwm_kib": peak("allow_vzip"),
        "extra_vmhwm_kib": peak("allow_vzip") - peak("default"),
        "default_create_cpu_ms": medcpu("default"),
        "allow_vzip_create_cpu_ms": medcpu("allow_vzip"),
    }
    report["decision"] = (
        "BUDGET_IS_CAUSAL_OWNER_ON_TESTED_FAMILY"
        if report["summary"]["extra_vmhwm_kib"] >= 64 * 1024
        else "BUDGET_NOT_SUFFICIENT_TO_EXPLAIN_O95_MEMORY"
    )
    persist()
    print("O95B_GENUINE_SAME_ENGINE_CHILDREN=6", flush=True)
    print("O95B_RESULT=" + json.dumps(report["summary"], sort_keys=True), flush=True)
    print("O95B_DECISION=" + report["decision"], flush=True)
    print("O95B_RAW_REPORT=" + str(dest), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=tuple(BUDGET))
    p.add_argument("--rep", type=int)
    p.add_argument("--package")
    p.add_argument("--root")
    p.add_argument("--manifest")
    p.add_argument("--output")
    p.add_argument("--o86-package")
    p.add_argument("--report", default="o95b-evidence/o95b-raw.json")
    a = p.parse_args()
    worker(a) if a.worker else court(a)


if __name__ == "__main__":
    main()
