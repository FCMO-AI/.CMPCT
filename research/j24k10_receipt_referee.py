"""Independent stdlib arithmetic/evidence referee for J24K10 component oracle.

Does not import CMPCT or the experiment. Recalculates medians from raw samples;
mutant receipts are rejected without weakening scientific baselines.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics

MODES = ("per_query_physical", "copy_then_prove_once")
KEYS = ("wall_ns", "cpu_ns", "copy_wall_ns", "copied_bytes", "extra_cache_bytes")
COUNTS = (512, 4096)
PADDINGS = (0, 64 * 1024 * 1024)
QUERIES = (1, 8, 64)


def verify(rows):
    if len(rows) != len(COUNTS) * len(PADDINGS) * len(QUERIES):
        raise ValueError("wrong cell count")
    expected = {(n, p, q) for n in COUNTS for p in PADDINGS for q in QUERIES}
    observed = set()
    by_source = {}
    output = []
    for row in rows:
        cell = (row["streams"], row["padding_bytes"], row["queries"])
        if cell not in expected or cell in observed:
            raise ValueError("missing/duplicate/unregistered cell")
        observed.add(cell)
        if (row["schema"] != "cmpct-j24k10-quiescent-copy-cost-oracle-v1"
                or row["scientific_tier"] != "component_only_not_installed_reader_product"
                or not row["no_external_writer_during_measurement"]
                or not row["copy_not_immutable_against_its_owner"]
                or not row["disk_copy_not_atomic_during_source_mutation"]
                or not row["source_format_not_full_r24"]):
            raise ValueError("missing scientific scope/custody warning")
        sha = row["source_sha256"]
        if not isinstance(sha, str) or len(sha) != 64:
            raise ValueError("invalid source hash")
        int(sha, 16)
        source_size = row["source_bytes"]
        # Original J24K09 synthetic framing: (N+1) * (64 BHDR + 64 bytes)
        expected_size = (row["streams"] + 1) * 128 + row["padding_bytes"]
        if source_size != expected_size or row["extra_mapped_archive_bytes"] != source_size:
            raise ValueError("copy/source byte charge mismatch")
        source_key = (row["streams"], row["padding_bytes"])
        if source_key in by_source and by_source[source_key] != sha:
            raise ValueError("per-source SHA changed across query cells")
        by_source[source_key] = sha
        if set(row["raw"]) != set(MODES) or set(row["medians"]) != set(MODES):
            raise ValueError("strategy coverage missing")
        for mode in MODES:
            samples = row["raw"][mode]
            if len(samples) != 10:
                raise ValueError("wrong ABBA sample count")
            for sample in samples:
                if set(sample) != set(KEYS):
                    raise ValueError("incomplete raw sample")
                if any(type(sample[k]) is not int or sample[k] < 0 for k in KEYS):
                    raise ValueError("bad wall/cpu/bytes sample")
                if mode == "copy_then_prove_once":
                    if (sample["copied_bytes"] != source_size
                            or sample["extra_cache_bytes"] <= 0
                            or sample["copy_wall_ns"] > sample["wall_ns"]):
                        raise ValueError("unpaid snapshot bytes/time/cache")
                elif any(sample[k] for k in ("copied_bytes", "extra_cache_bytes", "copy_wall_ns")):
                    raise ValueError("base wrongly charged copy resources")
            for k in KEYS:
                got = row["medians"][mode][k]
                expected_median = statistics.median(s[k] for s in samples)
                if got != expected_median:
                    raise ValueError("median arithmetic mismatch")
        calc_ratio = row["medians"][MODES[0]]["wall_ns"] / max(1, row["medians"][MODES[1]]["wall_ns"])
        if abs(calc_ratio - row["speed_ratio_physical_over_copied"]) > 1e-10:
            raise ValueError("ratio does not match raw medians")
        output.append({"streams": cell[0], "padding_bytes": cell[1],
                       "queries": cell[2], "ratio": calc_ratio,
                       "copy_median_ms": row["medians"][MODES[1]]["wall_ns"] / 1e6,
                       "baseline_median_ms": row["medians"][MODES[0]]["wall_ns"] / 1e6})
    if observed != expected:
        raise ValueError("frozen matrix missing")
    return sorted(output, key=lambda x: (x["streams"], x["padding_bytes"], x["queries"]))


def parse(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("J24K10_RESULT="):
            rows.append(json.loads(line[len("J24K10_RESULT="):]))
    return rows


def adversarial_tests(rows):
    mutants = []
    a = copy.deepcopy(rows)
    a[0]["medians"][MODES[0]]["wall_ns"] += 1
    mutants.append(a)
    a = copy.deepcopy(rows)
    a[0]["raw"][MODES[1]][0]["copied_bytes"] -= 1
    mutants.append(a)
    a = copy.deepcopy(rows)
    a[0]["raw"][MODES[0]].pop()
    mutants.append(a)
    a = copy.deepcopy(rows)
    a[1]["source_sha256"] = "0" * 64
    mutants.append(a)
    a = copy.deepcopy(rows)
    a[0]["copy_not_immutable_against_its_owner"] = False
    mutants.append(a)
    for i, mutant in enumerate(mutants):
        try:
            verify(mutant)
        except (AssertionError, KeyError, ValueError, TypeError):
            continue
        raise AssertionError(f"forged receipt {i} was accepted")
    return len(mutants)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = parse(args.input)
    audited = verify(rows)
    falsifications = adversarial_tests(rows)
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    summary = {"schema": "cmpct-j24k10-independent-referee-v1",
               "frozen_cells": len(audited),
               "raw_observations": sum(len(row["raw"][m]) for row in rows for m in MODES),
               "adversarial_receipts_rejected": falsifications,
               "oracle_receipt_sha256": digest,
               "scientific_tier": "component_only_no_product_credit",
               "audited": audited}
    args.output.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24K10_INDEPENDENT_REFEREE_PASS="+json.dumps({
        "cells": len(audited), "observations": summary["raw_observations"],
        "mutants_rejected": falsifications}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
