#!/usr/bin/env python3
"""J24G62 detached, standard-library-only receipt auditor + hostile mutation tests.

Evidence arithmetic and chain provenance are checked here. This is NOT a
second physical CMPCT decoder and does not authenticate original ZIP bytes.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import statistics
import sys

PINS = {
    "src/cmpct/builder.py": "a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2",
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/transactions.py": "3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11",
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
    "src/cmpct/validation.py": "5ea3b8f26058b0983c9686295c73f15472bc3ffe",
}


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def close(a, b, label):
    require(math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-4),
            "mismatch " + label)


def audit(report: dict, expected_head: str):
    require(report["schema"] == "cmpct-j24g62-research-v1", "schema")
    require(report["prereg_commit"] == "13bfa4574fd56af39475f3cb9e3bd5f64e06e148", "prereg")
    require(report["parent_research_head"] == "fb5d96cdb8855fe3e01868792e65b79d3d61661d", "parent")
    require(report["source"]["head"] == expected_head and len(expected_head) == 40, "head")
    sources = report["source"]["sources"]
    require(set(sources) == set(PINS), "source set")
    for path, pinned in PINS.items():
        require(sources[path]["git_blob"] == pinned, "source pin " + path)
    require(report["members"] == 2048 and report["generations"] == 63, "corpus identity")
    require(report["observed_route"] == "factored", "physical branch not entered")
    sha = report["physical_archive_sha256"]
    require(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), "physical SHA")
    archive = report["complete_archive_bytes"]
    require(set(archive) == {"chain", "checkpoint"}, "archive size fields")
    require(archive["checkpoint"] - archive["chain"] == report["checkpoint_premium_bytes"],
            "checkpoint charged bytes")
    require(archive["chain"] > 0 and archive["checkpoint"] >= archive["chain"], "archive sizes")
    counts = report["differential"]
    require(sum(counts.values()) == 2200, "differential count")
    require(counts.get("factored", 0) > 0, "fast path never executed in differential")
    require(counts.get("matched-exception", 0) > 0, "missing invalid-op differential")
    require(any(k.startswith("fallback:") for k in counts), "no fallback tested")
    samples = report["samples"]
    require(len(samples) == 32, "raw observation count")
    for block in range(8):
        records = [x for x in samples if x["block"] == block]
        require(len(records) == 4, "block count")
        records = sorted(records, key=lambda x: x["phase"])
        require([x["phase"] for x in records] == list(range(4)), "phase")
        sequence = [x["variant"] for x in records]
        correct = (["baseline", "factored", "factored", "baseline"]
                   if block % 2 == 0
                   else ["factored", "baseline", "baseline", "factored"])
        require(sequence == correct, "altered ABBA sequence")
        for row in records:
            require(type(row["wall_ns"]) is int and 0 < row["wall_ns"] < 10**12,
                    "wall sample")
            require(type(row["cpu_ns"]) is int and 0 <= row["cpu_ns"] < 10**12,
                    "CPU sample")
            correct_route = "original" if row["variant"] == "baseline" else "factored"
            require(row["route"] == correct_route, "route")
    a = [x for x in samples if x["variant"] == "baseline"]
    b = [x for x in samples if x["variant"] == "factored"]
    require(len(a) == len(b) == 16, "AB balance")
    wall_a = statistics.median(row["wall_ns"] for row in a)
    wall_b = statistics.median(row["wall_ns"] for row in b)
    cpu_a = statistics.median(row["cpu_ns"] for row in a)
    cpu_b = statistics.median(row["cpu_ns"] for row in b)
    require(wall_a > 0 and wall_b > 0 and cpu_b > 0, "measurement denominator")
    for name, v in (("baseline", wall_a), ("factored", wall_b)):
        close(report["wall_median_ns"][name], v, "wall " + name)
    for name, v in (("baseline", cpu_a), ("factored", cpu_b)):
        close(report["cpu_median_ns"][name], v, "cpu " + name)
    close(report["wall_speedup"], wall_a/wall_b, "speedup")
    close(report["cpu_speedup"], cpu_a/cpu_b, "CPU speedup")
    mem = report["tracemalloc"]
    require(set(mem) == {"baseline", "factored"}, "allocation strata")
    for key in mem:
        record = mem[key]
        require(type(record["peak_traced_bytes"]) is int
                and record["peak_traced_bytes"] >= record["retained_traced_bytes"] >= 0,
                "traced allocation")
    overhead = mem["factored"]["peak_traced_bytes"] - mem["baseline"]["peak_traced_bytes"]
    require(overhead == report["extra_peak_traced_bytes"], "allocation delta")
    decision = ("BOUNDED_RENAME_FACTORIZATION_SEED"
                if wall_a/wall_b >= 3 and overhead <= 2 * 1024 * 1024
                else "NO_BOUNDED_RENAME_FACTORIZATION_WIN")
    require(report["status"] == decision, "altered outcome/decision")
    return {"decision": decision, "wall_speedup": wall_a / wall_b,
            "extra_peak_traced_bytes": overhead, "raw_samples": len(samples)}


def hostile(report: dict, head: str):
    # These are receipt-level transformations, not corrupt archive mutations.
    transforms = [
        lambda x: x["samples"].pop(),
        lambda x: x["source"]["sources"]["src/cmpct/reader.py"].update(git_blob="0"*40),
        lambda x: x["samples"][0].update(wall_ns=x["samples"][0]["wall_ns"]*2),
        lambda x: x["samples"][0].update(variant="factored"),
        lambda x: x.update(checkpoint_premium_bytes=x["checkpoint_premium_bytes"]+1),
        lambda x: x["differential"].update(factored=x["differential"].get("factored", 0)+1),
        lambda x: x.update(wall_speedup=x["wall_speedup"] + 0.1),
        lambda x: x.update(status="BOUNDED_RENAME_FACTORIZATION_SEED"
                          if x["status"] != "BOUNDED_RENAME_FACTORIZATION_SEED"
                          else "NO_BOUNDED_RENAME_FACTORIZATION_WIN"),
    ]
    for i, operation in enumerate(transforms):
        altered = copy.deepcopy(report)
        operation(altered)
        try:
            audit(altered, head)
        except (AssertionError, ValueError, KeyError, TypeError, ZeroDivisionError):
            continue
        raise AssertionError(f"receipt mutation {i} was accepted")
    return len(transforms)


def main():
    require(len(sys.argv) in (3, 4), "usage: audit.py report.json SHA [output.json]")
    p = Path(sys.argv[1])
    record = json.loads(p.read_text())
    outcome = audit(record, sys.argv[2])
    outcome["hostile_mutations_rejected"] = hostile(record, sys.argv[2])
    print(json.dumps(outcome, sort_keys=True))
    if len(sys.argv) == 4:
        Path(sys.argv[3]).write_text(json.dumps(outcome, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
