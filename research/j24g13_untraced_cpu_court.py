#!/usr/bin/env python3
"""J24G13 independent untraced-CPU/total-RSS court for J24G12.

Runs the original installed Reader and the unchanged J24G12 guarded
research model in fresh children against identical first-party archive
bytes. Tracemalloc ON/OFF is a matched experimental dimension. Research
only; this instrument is deliberately not CMPCT product code.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

import cmpct.reader as product
from cmpct.builder import Builder
from cmpct.transactions import append_rename
from j24g12_lazy_ancestry_court import (
    ARMS, PAYLOAD, check_member, git_source_guard, make_tail,
)

PARENT = "2a56e83a55bdd60a0b9de86e7d09bec2ca4d664d"
PREREG = "7b3aeab46c99a87c75c4fa8886f72fe1702ed6a1"
READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
SOURCE = "research/j24g13_untraced_cpu_court.py"
CASES = (
    ("writer-rename", "writer", 1, 4),
    ("valid-512", "valid", 512, 4),
    ("orphan-4096", "orphan", 4096, 4),
    ("independent-4096", "independent", 4096, 4),
    ("signed-malformed", "malformed", 1, 1),
)
BOTH_ARMS = ("eager", "guarded")
TRACING = ("off", "on")


def source_guard():
    git_source_guard()
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", PARENT, "HEAD"],
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREREG, "HEAD"],
        check=False,
    ).returncode == 0
    assert subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
        text=True,
    ).strip() == READER_BLOB
    assert Path(SOURCE).read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:" + SOURCE]
    ), "research instrument must be exact committed Git source"
    assert platform.system() == "Linux", "RSS semantics are Linux-specific"


def run_worker(archive, arm, footer, depth, member, trace, expect_error):
    assert arm in BOTH_ARMS and trace in TRACING
    assert not tracemalloc.is_tracing()
    cls = ARMS[arm]
    if trace == "on":
        tracemalloc.start()
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    error = None
    try:
        with cls(Path(archive)) as reader:
            check_member(reader, int(footer), int(depth), member)
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)[:240]}
    cpu_ns = time.process_time_ns() - start_cpu
    wall_ns = time.perf_counter_ns() - start_wall
    peak_python = None
    if trace == "on":
        _, peak_python = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    else:
        assert not tracemalloc.is_tracing()
    # Hash and source identification are deliberately outside the timed op.
    out = {
        "arm": arm, "tracing": trace,
        "cpu_ns": cpu_ns, "wall_ns": wall_ns,
        "peak_python_traced_bytes": peak_python,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "archive_bytes": Path(archive).stat().st_size,
        "archive_sha256": hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
        "failure": error, "expected_failure": bool(expect_error),
        "runner_python": platform.python_version(),
        "reader_blob": READER_BLOB,
    }
    print("J24G13_ROW=" + json.dumps(out, sort_keys=True), flush=True)
    if expect_error:
        assert error is not None, "signed malformed footer must fail"
    else:
        assert error is None, error


def sample_case(label, archive, footer, depth, member, repetitions, expect_error=False):
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    size = archive.stat().st_size
    raw = {mode: {arm: [] for arm in BOTH_ARMS} for mode in TRACING}
    for rep in range(repetitions):
        # Fully specified, interleaved ABBA order: no ex-post ordering choice.
        arms = BOTH_ARMS if rep % 2 == 0 else tuple(reversed(BOTH_ARMS))
        modes = TRACING if rep % 2 == 0 else tuple(reversed(TRACING))
        for trace in modes:
            for arm in arms:
                cmd = [
                    sys.executable, str(Path(__file__).resolve()), "--worker",
                    str(archive), arm, str(footer), str(depth), member,
                    trace, "1" if expect_error else "0",
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if proc.returncode:
                    raise RuntimeError(
                        f"{label}/{trace}/{arm}/rep{rep}: rc={proc.returncode}, "
                        f"stdout={proc.stdout[-1000:]}, stderr={proc.stderr[-2500:]}"
                    )
                lines = [
                    line.removeprefix("J24G13_ROW=")
                    for line in proc.stdout.splitlines()
                    if line.startswith("J24G13_ROW=")
                ]
                assert len(lines) == 1, (label, arm, trace, lines)
                row = json.loads(lines[0])
                assert row["archive_sha256"] == digest
                assert row["archive_bytes"] == size
                assert row["failure"] is not None if expect_error else row["failure"] is None
                assert row["peak_python_traced_bytes"] is None if trace == "off" else (
                    isinstance(row["peak_python_traced_bytes"], int)
                )
                raw[trace][arm].append(row)
    medians = {
        mode: {
            arm: {
                key: statistics.median(row[key] for row in raw[mode][arm])
                for key in ("cpu_ns", "wall_ns", "process_peak_rss_kib")
            } | ({
                "peak_python_traced_bytes": statistics.median(
                    row["peak_python_traced_bytes"] for row in raw[mode][arm]
                )
            } if mode == "on" else {})
            for arm in BOTH_ARMS
        }
        for mode in TRACING
    }
    return {
        "case": label, "archive_sha256": digest, "archive_bytes": size,
        "expected_footer": footer, "expected_depth": depth,
        "expected_error": expect_error, "repetitions": repetitions,
        "raw": raw, "median": medians,
        "guard_over_eager_cpu": {
            mode: medians[mode]["guarded"]["cpu_ns"] / medians[mode]["eager"]["cpu_ns"]
            for mode in TRACING
        },
        "guard_over_eager_rss": {
            mode: medians[mode]["guarded"]["process_peak_rss_kib"] /
                medians[mode]["eager"]["process_peak_rss_kib"]
            for mode in TRACING
        },
    }


def main():
    source_guard()
    output = Path(os.environ.get("J24G13_ARTIFACTS", "j24g13-artifacts"))
    output.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g13-") as tmp:
        root = Path(tmp)
        tree = root / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(PAYLOAD)
        basepath = root / "base.cmpct"
        Builder(tree).build(basepath)
        with product.CMPCT(basepath) as reader:
            checkpoint = reader.latest_footer_pos
            check_member(reader, checkpoint, 0, "owner.bin")
        base = basepath.read_bytes()
        cases = {}
        for label, mode, n, reps in CASES:
            archive = root / (label + ".cmpct")
            if mode == "writer":
                archive.write_bytes(base)
                append_rename(archive, "owner.bin", "renamed.bin")
                with product.CMPCT(archive) as reader:
                    footer = reader.latest_footer_pos
                depth = 1
                member = "renamed.bin"
            else:
                raw, footer, depth = make_tail(
                    base, checkpoint, n,
                    "orphan" if mode == "malformed" else mode,
                    corrupt=(mode == "malformed"),
                )
                archive.write_bytes(raw)
                member = "owner.bin"
            cases[label] = sample_case(
                label, archive, footer, depth, member, reps,
                expect_error=(mode == "malformed"),
            )
            short = {
                "case": label, "median": cases[label]["median"],
                "guard_over_eager_cpu": cases[label]["guard_over_eager_cpu"],
                "guard_over_eager_rss": cases[label]["guard_over_eager_rss"],
            }
            print("J24G13_CASE=" + json.dumps(short, sort_keys=True), flush=True)

        result = {
            "scientific_status": "UNTRACED_REPLICATION_NOT_RELEASE_EVIDENCE",
            "parent_head": PARENT, "prereg_commit": PREREG,
            "reader_blob": READER_BLOB,
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cases": cases,
            "release_credit": 0,
            "whole_reader_memory_bound_proven": False,
            "source_mutation_safety_proven": False,
            "format_changed": False,
        }
        (output / "court.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
        print("J24G13_RESULT=" + json.dumps({
            "off_valid_guard_cpu_ratio": cases["valid-512"]["guard_over_eager_cpu"]["off"],
            "on_valid_guard_cpu_ratio": cases["valid-512"]["guard_over_eager_cpu"]["on"],
            "off_orphan_guard_cpu_ratio": cases["orphan-4096"]["guard_over_eager_cpu"]["off"],
            "off_orphan_guard_rss_ratio": cases["orphan-4096"]["guard_over_eager_rss"]["off"],
            "release_credit": 0,
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        run_worker(
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
            sys.argv[7], bool(int(sys.argv[8])),
        )
    else:
        main()
