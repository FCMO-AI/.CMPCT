#!/usr/bin/env python3
"""J24G14 second-root raw/result custody auditor; no CMPCT imports."""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

PARENT = "0684f5d694afc1abccc397ced3bcd1ef3356cb81"
PREREG = "8bb541f3746ca1c766b86d559488c4de726c15be"
READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
CASES = {
    "writer-rename": (3, 1, False),
    "valid-64": (3, 64, False),
    "valid-512": (3, 512, False),
    "valid-2048": (3, 2048, False),
    "orphan-4096": (3, 0, False),
    "independent-4096": (3, 0, False),
    "signed-malformed": (1, 0, True),
}
ARMS = ("eager", "guarded", "adaptive")
SOURCE_PATHS = (
    "src/cmpct/reader.py",
    "research/j24g12_lazy_ancestry_court.py",
    "research/j24g14_adaptive_ancestry_court.py",
    "research/j24g14_independent_receipt_audit.py",
    "docs/v031-research/2026-10-28-j24g14-adaptive-ownership-prereg.md",
)


def load(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError("duplicate key " + k)
            d[k] = v
        return d
    return json.loads(
        Path(path).read_text(), object_pairs_hook=unique,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def verify(d, s):
    checks = 0
    def ok(value, reason):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(reason)
    ok(d["scientific_decision"] == "RESEARCH_ONLY_PENDING_PRODUCT_GATES", "scope")
    ok(d["parent_head"] == PARENT and d["prereg_commit"] == PREREG, "source ancestry")
    ok(d["reader_blob"] == READER_BLOB, "Reader blob")
    ok(d["raw_payload_budget_bytes"] == 1_048_576, "predefined budget")
    ok(d["release_credit"] == 0 and d["format_changed"] is False, "release/format")
    ok(d["global_memory_bound_proven"] is False and
       d["source_mutation_safety_proven"] is False, "unsafe global claim")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    ok(d["head"] == head and s["head"] == head, "exact head")
    for p in SOURCE_PATHS:
        b = subprocess.check_output(["git", "show", "HEAD:" + p])
        ok(Path(p).read_bytes() == b, "checkout " + p)
        ok(p in s["files"], "source file " + p)
        ok(s["files"][p]["sha256"] == hashlib.sha256(b).hexdigest(),
           "SHA source " + p)
        ok(s["files"][p]["git_blob"] == subprocess.check_output(
            ["git", "rev-parse", "HEAD:" + p], text=True).strip(), "blob " + p)
    ok(subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                               text=True).strip() == READER_BLOB, "inherited reader")
    ok(set(d["cases"]) == set(CASES), "case coverage")
    for case, (reps, depth, malformed) in CASES.items():
        c = d["cases"][case]
        ok(c["case"] == case and c["expected_depth"] == depth, "depth " + case)
        ok(c["repetitions"] == reps and c["malformed"] is malformed, "reps " + case)
        ok(isinstance(c["archive_bytes"], int) and c["archive_bytes"] > 0, "size")
        digest = c["sha256"]
        ok(isinstance(digest, str) and len(digest) == 64 and
           all(x in "0123456789abcdef" for x in digest), "digest")
        ok(set(c["raw"]) == set(ARMS) and set(c["median"]) == set(ARMS), "arms")
        for arm in ARMS:
            rows = c["raw"][arm]
            ok(len(rows) == reps, "row count " + case + "/" + arm)
            for row in rows:
                ok(row["arm"] == arm and row["archive_sha256"] == digest,
                   "same physical input " + case)
                ok(row["archive_bytes"] == c["archive_bytes"], "same bytes")
                ok(row["reader_blob"] == READER_BLOB, "reader source")
                ok(bool(row["failure"]) is malformed, "failure law")
                for field in ("cpu_ns", "wall_ns", "rss_kib"):
                    ok(type(row[field]) is int and row[field] > 0,
                       "positive cost " + field)
                ok(row["budget_raw_bytes"] == 1_048_576, "budget")
                ok(type(row["adaptive_switches"]) is int and
                   row["adaptive_switches"] >= 0, "switches")
                ok(0 <= row["max_retained_raw_bytes"] <= 1_048_576, "peak cap")
                if arm != "adaptive":
                    ok(row["adaptive_switches"] == 0, "nonadaptive switch")
            for field in (
                "cpu_ns", "wall_ns", "rss_kib", "adaptive_switches",
                "max_retained_raw_bytes",
            ):
                observed = statistics.median(x[field] for x in rows)
                ok(math.isclose(observed, c["median"][arm][field],
                                rel_tol=0, abs_tol=0), "median " + case + "/" + arm + "/" + field)
        for field, ratio_field in (
            ("cpu_ns", "adaptive_cpu_ratio_to_eager"),
            ("rss_kib", "adaptive_rss_ratio_to_eager"),
        ):
            ratio = c["median"]["adaptive"][field] / c["median"]["eager"][field]
            ok(math.isclose(ratio, c[ratio_field], rel_tol=1e-12, abs_tol=0),
               "ratio " + case + "/" + ratio_field)
    # Structural discriminators are outcomes, not a performance pass gate.
    ok(d["cases"]["valid-64"]["median"]["adaptive"]["adaptive_switches"] == 0,
       "valid64 stays eager")
    ok(d["cases"]["valid-512"]["median"]["adaptive"]["adaptive_switches"] == 0,
       "valid512 stays eager")
    ok(d["cases"]["valid-2048"]["median"]["adaptive"]["adaptive_switches"] >= 1,
       "valid2048 switches")
    ok(d["cases"]["orphan-4096"]["median"]["adaptive"]["adaptive_switches"] >= 1,
       "orphan4096 switches")
    ok(d["cases"]["independent-4096"]["median"]["adaptive"]["adaptive_switches"] == 0,
       "flat invalid stays eager")
    return checks


def main():
    d = load("j24g14-artifacts/court.json")
    s = load("j24g14-artifacts/source.json")
    checks = verify(d, s)
    attacked = []
    cases = (
        ("false-cpu", lambda x: x["cases"]["valid-512"]["raw"]["adaptive"][0].__setitem__("cpu_ns", 1)),
        ("false-sha", lambda x: x["cases"]["orphan-4096"]["raw"]["guarded"][0].__setitem__("archive_sha256", "0" * 64)),
        ("false-median", lambda x: x["cases"]["valid-2048"]["median"]["adaptive"].__setitem__("rss_kib", 1)),
        ("drop-malformed-error", lambda x: x["cases"]["signed-malformed"]["raw"]["adaptive"][0].__setitem__("failure", None)),
        ("false-switch", lambda x: x["cases"]["orphan-4096"]["median"]["adaptive"].__setitem__("adaptive_switches", 0)),
        ("fake-release", lambda x: x.__setitem__("release_credit", 1)),
    )
    for name, f in cases:
        corrupt = copy.deepcopy(d)
        f(corrupt)
        try:
            verify(corrupt, s)
        except AssertionError:
            attacked.append(name)
        else:
            raise AssertionError("forged receipt accepted: " + name)
    result = {"checks": checks, "mutations_rejected": attacked,
              "reader_blob": READER_BLOB, "head": d["head"],
              "independent_physical_archive_replay": False,
              "release_credit": 0}
    Path("j24g14-artifacts/audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print("J24G14_AUDIT=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
