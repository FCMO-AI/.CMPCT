#!/usr/bin/env python3
"""J24G17 stdlib-only referee: physical inputs, receipts, decision and forgery tests.

Independent from the C counter, msgpack decoder and timing producer. It does
NOT claim independent full CMPCT archive reconstruction or product speed.
"""
from __future__ import annotations
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

CASES = ("ordinary_10k", "ordinary_1k", "tiny_maps_200k",
         "flat_nil_200k", "nested_4000x50", "opaque_same_bytes")
MODES = ("direct", "native_decode", "skip_decode")
REFUSED = {"tiny_maps_200k", "flat_nil_200k", "nested_4000x50"}

def audit(data, physical):
    checks = 0
    def require(value, reason):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(reason)
    require(data["schema"] == "cmpct-j24g17-research-v1", "schema")
    require(data["research_only"] is True, "scope")
    require(data["prereg_commit"] == "32099051333c9a23328bf3bc99778afe8ace8e0f", "prereg")
    identity = data["identity"]
    require(identity["valid"] == 2510, "valid count")
    require(identity["malformed"] == 7, "malformed count")
    require(identity["semantic_skip_counterexample"] is True, "semantic skip counterexample")
    manifest = data["vectors"]
    require(set(manifest) == set(CASES), "case set")
    for case in CASES:
        b = (physical / (case + ".mpk")).read_bytes()
        require(manifest[case]["bytes"] == len(b), case + " length")
        require(manifest[case]["sha256"] == hashlib.sha256(b).hexdigest(), case + " SHA")
    require(manifest["tiny_maps_200k"]["bytes"] == manifest["opaque_same_bytes"]["bytes"],
            "matched hostile/opaque sizes")
    records = data["raw"]
    n = len([r for r in records if r["case"] == CASES[0] and r["mode"] == MODES[0]])
    require(n >= 5, ">=5 fresh workers")
    require(len(records) == len(CASES)*len(MODES)*n, "crossed design")
    for case in CASES:
        for mode in MODES:
            group = [r for r in records if r["case"] == case and r["mode"] == mode]
            require(len(group) == n, "workers per cell")
            require(sorted(r["worker_index"] for r in group) == list(range(n)), "distinct worker indices")
            sampled = []
            for r in group:
                require(r["sha256"] == manifest[case]["sha256"], "source SHA")
                require(isinstance(r["rss_kib"], int) and r["rss_kib"] > 0, "RSS")
                require(len(r["samples"]) >= 3, "repetitions")
                for s in r["samples"]:
                    require(isinstance(s["cpu_ns"], int) and s["cpu_ns"] > 0, "CPU")
                    require(isinstance(s["wall_ns"], int) and s["wall_ns"] > 0, "wall")
                    expect = "refused_token_cap" if mode == "native_decode" and case in REFUSED else "accepted"
                    require(s["status"] == expect, case + "/" + mode + " status")
                    sampled.append(s)
            median_cpu = int(statistics.median(s["cpu_ns"] for s in sampled))
            median_wall = int(statistics.median(s["wall_ns"] for s in sampled))
            median_rss = int(statistics.median(r["rss_kib"] for r in group))
            stats = data["stats"][case][mode]
            require(stats["cpu_ns_median"] == median_cpu, "median CPU")
            require(stats["wall_ns_median"] == median_wall, "median wall")
            require(stats["rss_kib_median"] == median_rss, "median RSS")
            require(stats["samples"] == len(sampled), "sample count")
    d = data["decision"]
    ordinary = data["stats"]["ordinary_10k"]
    for field in ("cpu_ns_median", "wall_ns_median"):
        ratio = ordinary["native_decode"][field] / ordinary["direct"][field]
        require(abs(d[field+"_ratio"]-ratio) < 1e-12, "ratio "+field)
    require(d["H2_pass"] == all(d[k] <= 2 for k in
            ("cpu_ns_median_ratio", "wall_ns_median_ratio")), "H2 classification")
    r = data["stats"]["tiny_maps_200k"]
    saving = r["direct"]["rss_kib_median"] - r["native_decode"]["rss_kib_median"]
    require(d["hostile_rss_saved_kib"] == saving, "RSS saving")
    require(d["H3_pass"] == (saving >= 16384), "H3 classification")
    require(d["semantic_refusal_not_product_compatibility"] is True, "scope disclaimer")
    return checks

def main():
    folder = Path(sys.argv[1])
    original = json.loads((folder / "result.json").read_text())
    good = audit(original, folder)
    mutations = []
    def mutation(fn):
        x = copy.deepcopy(original)
        fn(x)
        mutations.append(x)
    mutation(lambda x: x["vectors"]["tiny_maps_200k"].update({"sha256": "0"*64}))
    mutation(lambda x: x["raw"][0].update({"sha256": "f"*64}))
    mutation(lambda x: x["raw"][0]["samples"][0].update({"cpu_ns": 1}))
    mutation(lambda x: x["decision"].update({"H2_pass": not x["decision"]["H2_pass"]}))
    mutation(lambda x: x["decision"].update({"hostile_rss_saved_kib": 0}))
    mutation(lambda x: x["raw"][0]["samples"][0].update({"status": "refused_token_cap"}))
    rejected = 0
    for mutated in mutations:
        try:
            audit(mutated, folder)
        except AssertionError:
            rejected += 1
    assert rejected == len(mutations), (rejected, len(mutations))
    print(json.dumps({"checks": good, "forgeries_rejected": rejected,
                      "decision": original["decision"],
                      "scope": "research receipts/physical MessagePack only; no product credit"}, indent=2))
if __name__ == "__main__":
    main()
