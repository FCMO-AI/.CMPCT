#!/usr/bin/env python3
"""O92: stage-attributed process RSS on genuine O63/O86 installed CMPCT.

Research-only child of frozen O88; never substitute a simulated codec or a
different source tree. An RSS high-water mark is not an allocation snapshot.
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
EXPECTED_SOURCE = {"o63": o88.BASE_SHA, "o86": o88.CAND_SHA}
MIB = 1024 * 1024


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rss() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def worker(a: argparse.Namespace) -> None:
    import cmpct.builder as builder_module
    import cmpct.codec as codec_module
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import K_FILE, S_BLOB, S_VZIP

    pkg = Path(a.package).resolve()
    assert Path(builder_module.__file__).resolve().is_relative_to(pkg)
    assert Path(codec_module.__file__).resolve().is_relative_to(pkg)
    root = Path(a.root).resolve()
    manifest = json.loads(Path(a.manifest).read_text())
    expected = {entry["path"]: entry["zip_sha256"] for entry in manifest}
    assert o88.source_digest(root) == expected
    assert "CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES" not in os.environ

    stages = {"imported_before_build": rss()}
    start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    out = Path(a.output)
    builder = Builder(root, workers=1, reproducible=True,
                      reproducible_epoch_ns=0)
    builder.build(out)
    create_wall = time.perf_counter_ns() - start
    create_cpu = time.process_time_ns() - cpu_start
    stages["after_builder_build"] = rss()
    assert o88.source_digest(root) == expected, "source changed after build"

    kinds = {row[0]: row[6][0] for row in builder.files if row[1] == K_FILE}
    assert set(kinds) == set(expected)
    assert set(kinds.values()).issubset({S_BLOB, S_VZIP})
    if a.arm == "o86":
        assert all(k == S_BLOB for k in kinds.values()), kinds
    else:
        assert all(k == S_VZIP for k in kinds.values()), kinds

    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        stages["after_verify"] = rss()
        for rel in sorted(expected):
            assert hashlib.sha256(reader.read(rel)).hexdigest() == expected[rel]
        stages["after_three_reader_reads"] = rss()
        dest = out.parent / (out.stem + "-extract")
        reader.extractall(dest, metadata=False)
        stages["after_extractall"] = rss()
    assert {p.name: sha(p) for p in dest.glob("*.zip")} == expected
    assert o88.source_digest(root) == expected, "source changed after extraction"
    sequence = list(stages.values())
    assert sequence == sorted(sequence), stages  # Linux high-water is monotone
    assert out.stat().st_size > 0

    print(json.dumps({
        "experiment": "O92", "arm": a.arm, "rep": a.rep,
        "source_commit": EXPECTED_SOURCE[a.arm],
        "source_digest": expected,
        "source_kinds": kinds,
        "builder_path": str(Path(builder_module.__file__).resolve()),
        "codec_path": str(Path(codec_module.__file__).resolve()),
        "complete_archive_bytes": out.stat().st_size,
        "archive_sha256": sha(out),
        "rss_kib_linux_peak_by_phase": stages,
        "builder_create_wall_ns": create_wall,
        "builder_create_cpu_ns": create_cpu,
        "python": sys.version.split()[0],
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    destination = Path(a.report).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-o92-"))
    root = scratch / "shared_over" / "src"
    manifest = o88.fixture(root, 65 * MIB, "shared")
    assert all(m["declared_inflated_bytes"] == 65 * MIB for m in manifest)
    manifest_file = scratch / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, sort_keys=True, indent=2))
    expected = o88.source_digest(root)
    packages = {"o63": Path(a.o63_package).resolve(),
                "o86": Path(a.o86_package).resolve()}
    report = {
        "experiment": "O92", "status": "research-only",
        "source": manifest, "source_digest": expected,
        "comparators": EXPECTED_SOURCE,
        "replications": REPS, "observations": [], "failures": [],
        "summary": None,
    }

    def persist() -> None:
        destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")

    persist()
    for rep in range(REPS):
        order = ("o63", "o86") if rep % 2 == 0 else ("o86", "o63")
        for arm in order:
            env = os.environ.copy()
            env.pop("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", None)
            env["PYTHONPATH"] = str(packages[arm])
            cmd = [
                sys.executable, str(Path(__file__).resolve()), "--worker",
                "--arm", arm, "--rep", str(rep), "--root", str(root),
                "--manifest", str(manifest_file),
                "--output", str(scratch / f"{arm}-{rep}.cmpct"),
                "--package", str(packages[arm]),
            ]
            try:
                process = subprocess.run(
                    cmd, env=env, cwd=scratch,
                    capture_output=True, text=True, timeout=420,
                )
                if process.returncode:
                    raise RuntimeError(f"exit={process.returncode}\n" +
                                       process.stderr[-3000:] +
                                       process.stdout[-1500:])
                row = json.loads(process.stdout.strip().splitlines()[-1])
                assert row["source_digest"] == expected
                assert row["arm"] == arm and row["rep"] == rep
                assert all(value >= 0 for value in
                           row["rss_kib_linux_peak_by_phase"].values())
                report["observations"].append(row)
                persist()
            except Exception as exc:
                report["failures"].append({
                    "arm": arm, "rep": rep, "error": str(exc)[:4000]
                })
                persist()
                raise
    by_arm = {
        arm: [o for o in report["observations"] if o["arm"] == arm]
        for arm in ("o63", "o86")
    }
    assert all(len(rows) == REPS for rows in by_arm.values())
    assert all(len({row["archive_sha256"] for row in rows}) == 1
               for rows in by_arm.values())
    assert all(len({row["complete_archive_bytes"] for row in rows}) == 1
               for rows in by_arm.values())
    assert by_arm["o63"][0]["complete_archive_bytes"] == 664428
    assert by_arm["o86"][0]["complete_archive_bytes"] == 52641
    assert o88.source_digest(root) == expected

    labels = [
        "imported_before_build", "after_builder_build",
        "after_verify", "after_three_reader_reads", "after_extractall",
    ]
    medians = {
        arm: {
            phase: statistics.median([
                row["rss_kib_linux_peak_by_phase"][phase] for row in rows
            ]) for phase in labels
        } for arm, rows in by_arm.items()
    }
    report["summary"] = {
        "median_peak_rss_kib_by_phase": medians,
        "create_only_peak_delta_o63_minus_o86_kib":
            medians["o63"]["after_builder_build"] -
            medians["o86"]["after_builder_build"],
        "reader_lift_o63_kib":
            medians["o63"]["after_extractall"] -
            medians["o63"]["after_builder_build"],
        "reader_lift_o86_kib":
            medians["o86"]["after_extractall"] -
            medians["o86"]["after_builder_build"],
        "source_sha_equal": True,
    }
    persist()
    print("O92_GENUINE_SOURCE_EXACT_INSTALLED_PROCESSES=6")
    print("O92_PHASE_RSS_RESULT=" + json.dumps(report["summary"],
                                               sort_keys=True))
    print("O92_RAW_REPORT=" + str(destination))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=("o63", "o86"))
    p.add_argument("--rep", type=int)
    p.add_argument("--root")
    p.add_argument("--manifest")
    p.add_argument("--output")
    p.add_argument("--package")
    p.add_argument("--o63-package")
    p.add_argument("--o86-package")
    p.add_argument("--report", default="o92-evidence/o92-raw.json")
    a = p.parse_args()
    worker(a) if a.worker else court(a)


if __name__ == "__main__":
    main()
