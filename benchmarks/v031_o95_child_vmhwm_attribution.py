#!/usr/bin/env python3
"""O95: genuine O63/O86 child-local Linux VmHWM memory attribution.

Research only. Reuses unchanged O88 fixture generator and real independently
installed engines, without changing O88/O92 instruments or product semantics.
The Linux kernel's VmHWM is sampled *inside* each exec'd benchmark child.
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

import v031_o88_vzip_budget_positive_economics as o88

REPS = 3
EXPECTED = {"o63": o88.BASE_SHA, "o86": o88.CAND_SHA}
FIELDS = ("VmHWM", "VmRSS", "RssAnon")
STAGES = (
    "child_before_import", "after_cmpct_import", "after_builder",
    "after_verify", "after_member_reads", "after_extract",
)


def snapshot() -> dict:
    """All /proc fields are from this child; ru_maxrss is diagnostic only."""
    status = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(tuple(field + ":" for field in FIELDS)):
            k, value = line.split(":", 1)
            status[k.lower() + "_kib"] = int(value.strip().split()[0])
    assert len(status) == len(FIELDS), ("not Linux /proc", status)
    status["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return status


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    stages = {"child_before_import": snapshot()}
    import cmpct.builder as builder_module
    import cmpct.codec as codec_module
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, S_BLOB, S_VZIP, S_PACK
    from cmpct.reader import CMPCT

    pkg = Path(a.package).resolve()
    imports = {
        "builder": Path(builder_module.__file__).resolve(),
        "codec": Path(codec_module.__file__).resolve(),
    }
    assert all(path.is_relative_to(pkg) for path in imports.values()), (pkg, imports)
    stages["after_cmpct_import"] = snapshot()
    root = Path(a.root).resolve()
    expected_rows = json.loads(Path(a.manifest).read_text())
    source = {entry["path"]: entry["zip_sha256"] for entry in expected_rows}
    assert o88.source_digest(root) == source, "source drift pre-create"
    assert "CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES" not in os.environ

    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    builder = Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0)
    output = Path(a.output)
    builder.build(output)
    create_wall = time.perf_counter_ns() - t0
    create_cpu = time.process_time_ns() - c0
    stages["after_builder"] = snapshot()
    assert o88.source_digest(root) == source, "source drift post-create"

    kinds = {row[0]: row[6][0] for row in builder.files if row[1] == K_FILE}
    assert set(kinds) == set(source) and S_PACK not in kinds.values(), kinds
    assert set(kinds.values()).issubset({S_BLOB, S_VZIP})
    if a.case != "shared_low":
        if a.arm == "o86":
            assert set(kinds.values()) == {S_BLOB}, ("O86 budget not applied", kinds)
        else:
            assert set(kinds.values()) == {S_VZIP}, ("historical O63 changed", kinds)

    t1, c1 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(output) as reader:
        assert reader.verify() >= 1
        stages["after_verify"] = snapshot()
        for name in sorted(source):
            assert hashlib.sha256(reader.read(name)).hexdigest() == source[name]
        stages["after_member_reads"] = snapshot()
        dest = output.parent / (output.stem + "-extracted")
        reader.extractall(dest, metadata=False)
        stages["after_extract"] = snapshot()
    reader_wall = time.perf_counter_ns() - t1
    reader_cpu = time.process_time_ns() - c1
    assert {p.name: digest_file(p) for p in dest.glob("*.zip")} == source
    assert o88.source_digest(root) == source, "source drift post-extract"
    assert all(stages[b]["vmhwm_kib"] >= stages[a]["vmhwm_kib"]
               for a, b in zip(STAGES, STAGES[1:])), "VmHWM nonmonotone"

    print(json.dumps({
        "experiment": "O95", "arm": a.arm, "case": a.case,
        "rep": a.rep, "source_commit": EXPECTED[a.arm],
        "source_sha256": source,
        "installed_imports": {k: str(v) for k, v in imports.items()},
        "representation_kinds": kinds,
        "stored_bytes": output.stat().st_size,
        "archive_sha256": digest_file(output),
        "create_wall_ns": create_wall, "create_cpu_ns": create_cpu,
        "verify_read_extract_wall_ns": reader_wall,
        "verify_read_extract_cpu_ns": reader_cpu,
        "child_memory_kib_by_stage": stages,
        "python": sys.version.split()[0],
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    destination = Path(a.report).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-o95-"))
    packages = {"o63": Path(a.o63_package).resolve(),
                "o86": Path(a.o86_package).resolve()}
    report = {
        "experiment": "O95", "status": "scientific-instrument",
        "engine_commits": EXPECTED, "original_fixture_source": o88.BASE_SHA,
        "parent_vm_hwm_before_fixture_kib": snapshot()["vmhwm_kib"],
        "repetitions": REPS, "cases": [], "failures": [],
    }

    def persist() -> None:
        destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    persist()
    for name, expanded_len, ownership in o88.CASES:
        src = scratch / name / "source"
        manifest = o88.fixture(src, expanded_len, ownership)
        manifest_path = scratch / name / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True))
        source = o88.source_digest(src)
        row = {"case": name, "expanded_bytes": expanded_len,
               "ownership": ownership, "manifest": manifest,
               "source_digest": source, "measurements": [],
               "median": None}
        report["cases"].append(row)
        persist()

        for rep in range(REPS):
            order = ("o63", "o86") if rep % 2 == 0 else ("o86", "o63")
            for arm in order:
                env = os.environ.copy()
                env.pop("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", None)
                env["PYTHONPATH"] = str(packages[arm])
                cmd = [
                    sys.executable, str(Path(__file__).resolve()), "--worker",
                    "--arm", arm, "--case", name, "--rep", str(rep),
                    "--package", str(packages[arm]),
                    "--root", str(src),
                    "--manifest", str(manifest_path),
                    "--output", str(scratch / name / f"{arm}-{rep}.cmpct"),
                ]
                try:
                    cp = subprocess.run(
                        cmd, env=env, cwd=scratch, text=True,
                        capture_output=True, timeout=420,
                    )
                    if cp.returncode:
                        raise RuntimeError(
                            f"exit={cp.returncode}; stderr={cp.stderr[-3500:]}; "
                            f"stdout={cp.stdout[-1500:]}"
                        )
                    observation = json.loads(cp.stdout.strip().splitlines()[-1])
                    assert observation["source_sha256"] == source
                    assert observation["arm"] == arm and observation["rep"] == rep
                    assert set(observation["child_memory_kib_by_stage"]) == set(STAGES)
                    row["measurements"].append(observation)
                    persist()
                except Exception as exc:
                    report["failures"].append({
                        "case": name, "arm": arm, "rep": rep,
                        "error": str(exc)[:4000],
                    })
                    persist()
                    raise

        by_arm = {
            arm: [v for v in row["measurements"] if v["arm"] == arm]
            for arm in ("o63", "o86")
        }
        assert all(len(v) == REPS for v in by_arm.values())
        assert all(len({v["archive_sha256"] for v in vrows}) == 1
                   for vrows in by_arm.values()), "archive output nondeterministic"
        assert all(len({v["stored_bytes"] for v in vrows}) == 1
                   for vrows in by_arm.values())
        if name == "shared_over":
            assert by_arm["o63"][0]["stored_bytes"] == 664428
            assert by_arm["o86"][0]["stored_bytes"] == 52641
        if name == "independent_over":
            assert by_arm["o63"][0]["stored_bytes"] == 913287
            assert by_arm["o86"][0]["stored_bytes"] == 52567
        if name == "shared_low":
            assert by_arm["o63"][0]["archive_sha256"] == by_arm["o86"][0]["archive_sha256"]

        med = lambda arm, field: statistics.median(v[field] for v in by_arm[arm])
        stage_med = lambda arm, stage, field: statistics.median(
            v["child_memory_kib_by_stage"][stage][field] for v in by_arm[arm]
        )
        row["median"] = {
            arm: {
                "stored_bytes": by_arm[arm][0]["stored_bytes"],
                "create_wall_ms": med(arm, "create_wall_ns") / 1e6,
                "create_cpu_ms": med(arm, "create_cpu_ns") / 1e6,
                "reader_wall_ms": med(arm, "verify_read_extract_wall_ns") / 1e6,
                "vmhwm_before_import_kib": stage_med(arm, "child_before_import", "vmhwm_kib"),
                "vmhwm_after_import_kib": stage_med(arm, "after_cmpct_import", "vmhwm_kib"),
                "vmhwm_after_builder_kib": stage_med(arm, "after_builder", "vmhwm_kib"),
                "vmhwm_after_reader_kib": stage_med(arm, "after_extract", "vmhwm_kib"),
                "ru_maxrss_before_import_kib": stage_med(arm, "child_before_import", "ru_maxrss_kib"),
                "vmrss_after_builder_kib": stage_med(arm, "after_builder", "vmrss_kib"),
                "rssanon_after_builder_kib": stage_med(arm, "after_builder", "rssanon_kib"),
            } for arm in ("o63", "o86")
        }
        row["median"]["o63_minus_o86_builder_vmhwm_kib"] = (
            row["median"]["o63"]["vmhwm_after_builder_kib"] -
            row["median"]["o86"]["vmhwm_after_builder_kib"]
        )
        row["median"]["material_8mib_attribution_difference"] = (
            row["median"]["o63_minus_o86_builder_vmhwm_kib"] >= 8192
        )
        persist()
        print("O95_CASE=" + json.dumps({"name": name, **row["median"]},
                                       sort_keys=True), flush=True)
    report["parent_vm_hwm_after_fixture_kib"] = snapshot()["vmhwm_kib"]
    assert not report["failures"]
    assert sum(len(x["measurements"]) for x in report["cases"]) == 18
    report["decision"] = (
        "MATERIAL_O63_CHILD_VMHWM_DIFFERENCE_ON_TESTED_FAMILY"
        if any(x["median"]["material_8mib_attribution_difference"]
               for x in report["cases"] if x["expanded_bytes"] > 64 * o88.MIB)
        else "NO_MATERIAL_CHILD_VMHWM_DIFFERENCE_ON_TESTED_FAMILY"
    )
    persist()
    print("O95_ACTUAL_SOURCE_EXACT_PRODUCT_CHILDREN=18", flush=True)
    print("O95_DECISION=" + report["decision"], flush=True)
    print("O95_RAW_REPORT=" + str(destination), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=("o63", "o86"))
    p.add_argument("--rep", type=int)
    p.add_argument("--case")
    p.add_argument("--root")
    p.add_argument("--manifest")
    p.add_argument("--output")
    p.add_argument("--package")
    p.add_argument("--o63-package")
    p.add_argument("--o86-package")
    p.add_argument("--report", default="o95-evidence/o95-raw.json")
    args = p.parse_args()
    worker(args) if args.worker else court(args)


if __name__ == "__main__":
    main()
