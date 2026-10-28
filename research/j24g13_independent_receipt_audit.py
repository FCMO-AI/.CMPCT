#!/usr/bin/env python3
"""J24G13 independent receipt referee: stdlib-only; never imports CMPCT.

Checks raw observations/source identity, recalculates medians and ratios,
and probes receipt corruption. This is NOT independent physical decoding.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess

CASES = {
    "writer-rename": (4, 1, False),
    "valid-512": (4, 512, False),
    "orphan-4096": (4, 0, False),
    "independent-4096": (4, 0, False),
    "signed-malformed": (1, 0, True),
}
ARMS = ("eager", "guarded")
MODES = ("off", "on")
READER = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PARENT = "2a56e83a55bdd60a0b9de86e7d09bec2ca4d664d"
PREREG = "7b3aeab46c99a87c75c4fa8886f72fe1702ed6a1"


def strict(path):
    def pairs_unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key " + key)
            result[key] = value
        return result
    return json.loads(
        Path(path).read_text(), object_pairs_hook=pairs_unique,
        parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)),
    )


def check(data, source):
    count = 0

    def require(yes, message):
        nonlocal count
        count += 1
        if not yes:
            raise AssertionError(message)

    require(data["scientific_status"] == "UNTRACED_REPLICATION_NOT_RELEASE_EVIDENCE",
            "scientific status")
    require(data["release_credit"] == 0, "no release")
    require(data["format_changed"] is False, "format")
    require(data["source_mutation_safety_proven"] is False, "source mutation")
    require(data["whole_reader_memory_bound_proven"] is False, "memory bound")
    require(data["reader_blob"] == READER, "reader")
    require(data["parent_head"] == PARENT and data["prereg_commit"] == PREREG,
            "ancestors")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    require(data["head"] == head, "HEAD identity")
    require(source["head"] == head, "source HEAD identity")
    for file in (
        "src/cmpct/reader.py",
        "research/j24g12_lazy_ancestry_court.py",
        "research/j24g13_untraced_cpu_court.py",
        "research/j24g13_independent_receipt_audit.py",
        "docs/v031-research/2026-10-28-j24g13-untraced-cpu-prereg.md",
    ):
        expected = subprocess.check_output(["git", "show", "HEAD:" + file])
        require(expected == Path(file).read_bytes(), "working copy " + file)
        require(file in source["files"], "source file " + file)
        require(
            source["files"][file]["sha256"] == hashlib.sha256(expected).hexdigest(),
            "SHA-256 " + file,
        )
        require(
            source["files"][file]["git_blob"] ==
            subprocess.check_output(["git", "rev-parse", "HEAD:" + file],
                                    text=True).strip(),
            "blob " + file,
        )
    require(
        subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                                text=True).strip() == READER,
        "Reader source guard",
    )
    require(set(data["cases"]) == set(CASES), "fixed case set")
    for name, (reps, depth, expected_error) in CASES.items():
        case = data["cases"][name]
        require(case["case"] == name, "case " + name)
        require(case["expected_depth"] == depth, "depth " + name)
        require(case["expected_error"] is expected_error, "expected_error " + name)
        require(case["repetitions"] == reps, "reps " + name)
        digest = case["archive_sha256"]
        require(isinstance(digest, str) and len(digest) == 64 and
                all(c in "0123456789abcdef" for c in digest), "SHA " + name)
        require(case["archive_bytes"] > 0, "size " + name)
        require(set(case["raw"]) == set(MODES) and
                set(case["median"]) == set(MODES), "modes " + name)
        for mode in MODES:
            require(set(case["raw"][mode]) == set(ARMS), "arms " + name)
            for arm in ARMS:
                rows = case["raw"][mode][arm]
                require(len(rows) == reps, "row count " + name)
                for row in rows:
                    require(row["arm"] == arm and row["tracing"] == mode,
                            "arm / tracer " + name)
                    require(row["archive_sha256"] == digest, "same bytes " + name)
                    require(row["archive_bytes"] == case["archive_bytes"],
                            "same length " + name)
                    require(row["reader_blob"] == READER, "installed reader " + name)
                    require(bool(row["failure"]) is expected_error,
                            "expected malformed result " + name)
                    require(row["expected_failure"] is expected_error,
                            "expected_failure field " + name)
                    for k in ("cpu_ns", "wall_ns", "process_peak_rss_kib"):
                        require(type(row[k]) is int and row[k] > 0,
                                k + " invalid " + name)
                    require(
                        row["peak_python_traced_bytes"] is None if mode == "off"
                        else type(row["peak_python_traced_bytes"]) is int and
                             row["peak_python_traced_bytes"] >= 0,
                        "tracing mode contaminated " + name,
                    )
                keys = ("cpu_ns", "wall_ns", "process_peak_rss_kib")
                if mode == "on":
                    keys += ("peak_python_traced_bytes",)
                for key in keys:
                    median = statistics.median(row[key] for row in rows)
                    stored = case["median"][mode][arm][key]
                    require(math.isclose(median, stored, rel_tol=0, abs_tol=0),
                            "median " + name + "/" + mode + "/" + arm + "/" + key)
            for metric, field in (
                ("cpu_ns", "guard_over_eager_cpu"),
                ("process_peak_rss_kib", "guard_over_eager_rss"),
            ):
                ratio = (case["median"][mode]["guarded"][metric] /
                         case["median"][mode]["eager"][metric])
                require(math.isclose(ratio, case[field][mode],
                                     rel_tol=1e-12, abs_tol=0),
                        "ratio " + name + "/" + metric)
    return count


def main():
    d = strict("j24g13-artifacts/court.json")
    s = strict("j24g13-artifacts/source.json")
    passes = check(d, s)
    attacks = []
    for name, mutate in (
        ("false-cpu", lambda x: x["cases"]["valid-512"]["raw"]["off"]["guarded"][0].__setitem__("cpu_ns", 1)),
        ("fabricate-median", lambda x: x["cases"]["orphan-4096"]["median"]["off"]["eager"].__setitem__("cpu_ns", 1)),
        ("hide-error", lambda x: x["cases"]["signed-malformed"]["raw"]["off"]["eager"][0].__setitem__("failure", None)),
        ("false-source", lambda x: x.__setitem__("reader_blob", "0" * 40)),
        ("fake-release", lambda x: x.__setitem__("release_credit", 1)),
        ("tracer-leak", lambda x: x["cases"]["valid-512"]["raw"]["off"]["guarded"][0].__setitem__("peak_python_traced_bytes", 123)),
    ):
        changed = copy.deepcopy(d)
        mutate(changed)
        try:
            check(changed, s)
        except AssertionError:
            attacks.append(name)
        else:
            raise AssertionError("mutation survived referee: " + name)
    output = {"checks": passes, "mutations_rejected": attacks,
              "scientific_evidence_only": True,
              "source_head": d["head"], "reader_blob": READER}
    Path("j24g13-artifacts/audit.json").write_text(
        json.dumps(output, sort_keys=True, indent=2) + "\n"
    )
    print("J24G13_AUDIT=" + json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
