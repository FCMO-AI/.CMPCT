#!/usr/bin/env python3
"""Independent, standard-library-only referee of J24K06 component ABBA receipts.

Checks the actual raw samples, component work charged by each branch, and the
reported medians/ratios. This deliberately does not claim complete product
performance, RSS, format identity or archive-size credit.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import statistics


class ReceiptError(ValueError):
    pass


def ensure(condition: bool, why: str) -> None:
    if not condition:
        raise ReceiptError(why)


def finite_num(x, *, positive: bool = False) -> None:
    ensure(type(x) in (float, int) and math.isfinite(x), "invalid numeric sample")
    ensure(x > 0 if positive else x >= 0, "negative/zero sample")


def audit(receipt: dict, source_sha: str | None = None) -> dict:
    ensure(type(receipt) is dict and receipt.get("not_product_credit") is True, "product-credit boundary lost")
    ensure(receipt.get("not_rss") is True, "RSS boundary lost")
    ensure(receipt.get("decision") == "CORRECTNESS_PASS_WITH_EXPLICIT_PREFIX_REGENERATION_COST", "decision mismatch")
    if source_sha:
        ensure(receipt.get("experiment_source_sha") == source_sha, "source SHA mismatch")
    results = receipt.get("cases")
    ensure(type(results) is list and len(results) == 6, "must cover two workload families x three offsets")
    identified = set()
    ratios = {}
    for row in results:
        kind, loc = row["case"], row["range"]
        ensure(kind in ("repeated", "incompressible"), "unknown family")
        ensure(loc in ("prefix", "overlap-first", "suffix"), "unknown offset")
        ensure((kind, loc) not in identified, "duplicate workload")
        identified.add((kind, loc))
        ensure(row["input_raw_bytes"] == 2 * 1024 * 1024, "changed raw input size")
        sizes = row["stream_lengths"]
        ensure(type(sizes) is list and len(sizes) == 2 and all(type(n) is int and n > 0 for n in sizes), "invalid regenerated stream geometry")
        ensure(row["returned_bytes"] in (2, 32), "changed range length")
        arms = row["raw_observations"]
        ensure(type(arms) is dict and set(arms) == {"parent", "candidate"}, "missing comparator arm")
        actual = {}
        for name in ("parent", "candidate"):
            samples = arms[name]
            ensure(type(samples) is list and len(samples) == 8, "ABBA must have eight samples per arm")
            for sample in samples:
                finite_num(sample["wall_ns"], positive=True)
                finite_num(sample["cpu_ns"])
                n_calls = 0 if loc == "prefix" or (loc == "suffix" and name == "parent") else (
                    1 if loc == "overlap-first" else 2
                )
                ensure(sample["stream_calls"] == n_calls, "skipped regeneration work not charged")
                ensure(sample["raw_bytes_recompressed"] == n_calls * (1024 * 1024), "raw recompression accounting mismatch")
                expected_stream_bytes = (
                    0 if n_calls == 0 else sizes[0] if n_calls == 1 else sum(sizes)
                )
                ensure(sample["stream_bytes"] == expected_stream_bytes, "generated stream cost mismatch")
            actual[name] = {
                "wall_ns": statistics.median(s["wall_ns"] for s in samples),
                "cpu_ns": statistics.median(s["cpu_ns"] for s in samples),
            }
            for key in ("wall_ns", "cpu_ns"):
                expected = row["median"][name][key]
                finite_num(expected)
                ensure(abs(expected - actual[name][key]) < 1e-6, "reported median changed")
            peak = row["median"][name]["peak_python_alloc_bytes"]
            ensure(type(peak) is int and peak >= 0, "Python allocation peak invalid")
        expected_ratio = actual["candidate"]["wall_ns"] / actual["parent"]["wall_ns"]
        ensure(math.isclose(row["candidate_over_parent_wall_ratio"], expected_ratio, rel_tol=1e-12, abs_tol=1e-12), "reported speed ratio changed")
        ratios[kind + ":" + loc] = expected_ratio
    ensure(len(identified) == 6, "workload matrix incomplete")
    return {
        "decision": "PASS",
        "source_sha": receipt.get("experiment_source_sha"),
        "total_timed_observations": 6 * 2 * 8,
        "exact_case_count": len(identified),
        "mode2_prefix_cost_ratios": ratios,
        "scope": "component-only, no product/RSS credit",
    }


def _audit_mutant_sensitivity(original: dict) -> int:
    # Verify the referee itself detects a falsified raw cost, summary, and
    # provenance assertion. Never weaken comparators to make a receipt pass.
    mutant_fields = [
        ("raw", lambda v: v["cases"][0]["raw_observations"]["candidate"][0].update({"stream_calls": 123})),
        ("ratio", lambda v: v["cases"][0].update({"candidate_over_parent_wall_ratio": 999})),
        ("provenance", lambda v: v.update({"not_product_credit": False})),
    ]
    rejected = 0
    for _, mutate in mutant_fields:
        forged = copy.deepcopy(original)
        mutate(forged)
        try:
            audit(forged)
        except ReceiptError:
            rejected += 1
        else:
            raise AssertionError("referee accepted deliberate forged receipt")
    return rejected


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sha", type=str, default=None)
    a = ap.parse_args()
    evidence = json.loads(a.receipt.read_text(encoding="utf-8"))
    result = audit(evidence, a.sha)
    result["forged_receipts_rejected"] = _audit_mutant_sensitivity(evidence)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24K06_INDEPENDENT_COST_REFEREE_PASS=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
