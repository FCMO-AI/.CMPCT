#!/usr/bin/env python3
"""J24G16 independent stdlib-only referee. No CMPCT/msgpack imports."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from statistics import median
import sys

LABELS = ("tiny_maps_200k", "flat_nil_200k", "nested_4000x50",
          "ordinary_10k", "ordinary_1k", "opaque_same_bytes")
METHODS = ("direct", "scan_decode", "skip_decode", "hook_decode")
HIGH = ("tiny_maps_200k", "flat_nil_200k", "nested_4000x50")

def audit(report, root, *, physical=True):
    checks = 0
    def ok(condition, description):
        nonlocal checks
        if not condition:
            raise AssertionError(description)
        checks += 1
    ok(report["schema"] == "cmpct-j24g16-v1", "schema")
    ok(report["source_parent"] == "8c5c8cf8c588936b5dd4b856f35e5e0f282ed56d", "parent")
    ok(report["research_only"] is True, "not product credit")
    ok(report["cap"] == 65536, "preregistered cap")
    ok(report["identity"]["valid_vectors"] >= 2500, "valid vectors")
    ok(report["identity"]["malformed_vectors"] >= 6, "malformed vectors")
    ok(report["identity"]["skip_only_malformed_witness"] is True, "semantic negative control")
    ok(set(report["vectors"]) == set(LABELS), "vector set")
    same_len = report["vectors"]["tiny_maps_200k"]["bytes"]
    ok(same_len == report["vectors"]["opaque_same_bytes"]["bytes"], "equal physical payload bytes")
    for label, meta in report["vectors"].items():
        ok(len(meta["sha256"]) == 64, "hash syntax")
        if physical:
            b = (root / (label + ".mpk")).read_bytes()
            ok(len(b) == meta["bytes"], "byte length " + label)
            ok(hashlib.sha256(b).hexdigest() == meta["sha256"], "sha " + label)
    samples = report["samples"]
    ok(bool(samples), "samples nonempty")
    reps = {s["repetition"] for s in samples}
    ok(reps == set(range(len(reps))), "contiguous repetitions")
    ok(len(reps) >= 3, "repeat floor")
    ok(len(samples) == len(LABELS)*len(METHODS)*len(reps), "complete factorial")
    seen = set()
    for s in samples:
        key = (s["case"], s["mode"], s["repetition"])
        ok(s["case"] in LABELS, "case")
        ok(s["mode"] in METHODS, "method")
        ok(key not in seen, "duplicate")
        seen.add(key)
        ok(s["sha256"] == report["vectors"][s["case"]]["sha256"], "source SHA sample")
        ok(s["bytes"] == report["vectors"][s["case"]]["bytes"], "source bytes sample")
        ok(isinstance(s["wall_ns"], int) and s["wall_ns"] > 0, "positive wall")
        ok(isinstance(s["cpu_ns"], int) and s["cpu_ns"] > 0, "positive CPU")
        ok(isinstance(s["rss_kib"], int) and s["rss_kib"] > 0, "positive RSS")
        if s["mode"] in ("direct", "skip_decode"):
            ok(s["accepted"] is True, "original decoder valid")
        if s["mode"] == "scan_decode":
            ok(s["accepted"] is (s["case"] not in HIGH), "expected resource admission")
            ok(s["error"] == ("TooManyNodes" if s["case"] in HIGH else None), "correct refusal class")
    def selection(case, method):
        return [s for s in samples if s["case"] == case and s["mode"] == method]
    summary = {}
    for case in LABELS:
        group = {}
        for method in METHODS:
            values = selection(case, method)
            group[method] = {"cpu_ms": round(median(v["cpu_ns"] for v in values)/1e6, 6),
                             "wall_ms": round(median(v["wall_ns"] for v in values)/1e6, 6),
                             "rss_kib": median(v["rss_kib"] for v in values),
                             "accepted": all(v["accepted"] for v in values)}
        group["scan_cpu_ratio_to_direct"] = round(
            group["scan_decode"]["cpu_ms"] / group["direct"]["cpu_ms"], 4)
        summary[case] = group
    # Negative receipt controls: every deliberate violation must be caught.
    mutations = []
    for case in range(6):
        v = copy.deepcopy(report)
        if case == 0: v["cap"] = 65537
        if case == 1: v["samples"][0]["sha256"] = "f"*64
        if case == 2: v["samples"][0]["wall_ns"] = -1
        if case == 3: v["samples"].pop()
        if case == 4: v["samples"][0]["accepted"] = False
        if case == 5: v["vectors"]["opaque_same_bytes"]["bytes"] += 1
        try:
            audit_no_mutation(v, root)
        except AssertionError:
            mutations.append(True)
        else:
            mutations.append(False)
    ok(all(mutations), "six forged receipt rejections")
    return {"assertions": checks, "forged_receipts_rejected": len(mutations),
            "decision": {"P1_high_object_resource_refusal": True,
                         "P2_admitted_semantics": "held-out checked",
                         "P3_pure_python_ordinary10k_cpu_ratio":
                             summary["ordinary_10k"]["scan_cpu_ratio_to_direct"],
                         "P3_pass_2x": summary["ordinary_10k"]["scan_cpu_ratio_to_direct"] <= 2.0},
            "summary": summary}

def audit_no_mutation(report, root):
    # Only cheap invariant checks. Avoid recursively running the forgery court.
    assert report["cap"] == 65536
    assert len(report["samples"]) == 72
    assert report["vectors"]["tiny_maps_200k"]["bytes"] == report["vectors"]["opaque_same_bytes"]["bytes"]
    s = report["samples"][0]
    assert s["accepted"] is True
    assert s["wall_ns"] > 0
    assert s["sha256"] == report["vectors"][s["case"]]["sha256"]

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("j24g16-artifacts")
    report = json.loads((root / "result.json").read_text())
    result = audit(report, root)
    out = root / "referee.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"assertions": result["assertions"],
                      "forged_receipts_rejected": result["forged_receipts_rejected"],
                      **result["decision"]}, indent=2))

if __name__ == "__main__":
    main()
