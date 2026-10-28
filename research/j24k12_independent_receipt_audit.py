#!/usr/bin/env python3
"""Independent second-root J24K12 receipt audit (stdlib only; no CMPCT imports).

Recomputes every median and verifies authentic original input/archive bytes,
source custody and negative evidence. Forged test receipts must be rejected.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

CASES = ("q1_early", "q1_tail", "q8_mixed", "q64_tail")
SIZES = (64, 512, 4096)
METRICS = ("opened_wall_ns", "opened_cpu_ns", "read_wall_ns", "read_cpu_ns",
           "total_wall_ns", "total_cpu_ns", "process_wall_ns")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_c():
    tree = ast.parse(Path("research/j24k11_bhdr_oracle.py").read_text(encoding="utf-8"))
    for obj in tree.body:
        if isinstance(obj, ast.Assign) and any(isinstance(n, ast.Name) and n.id == "C_SOURCE"
                                                for n in obj.targets):
            return ast.literal_eval(obj.value)
    raise AssertionError("C_SOURCE not found")


def expect_queries(size, case):
    if case == "q1_early": return [(4, 1)]
    if case == "q1_tail": return [(size - 8, 1)]
    if case == "q8_mixed":
        return [(size - 8, 1), (size // 2, 1), (4, 1), (size - 8, 1),
                (4, 1), (size // 2, 1), (size - 8, 1), (size // 2, 1)]
    if case == "q64_tail": return [(size - 1 - (i % 32), 1) for i in range(64)]
    raise AssertionError("unknown query profile")


def audit(doc, workdir):
    assert doc["schema"] == "j24k12-authentic-installed-r24-v1"
    assert doc["class"] == "installed_scientific_adapter_not_published_product"
    assert doc["cell_count"] == 12
    assert doc["observations"] == 120
    assert len(doc["cells"]) == 12
    assert doc["native_build_ns"] > 0
    sources = {
        "reader_sha256": "src/cmpct/reader.py",
        "codec_sha256": "src/cmpct/codec.py",
        "instrument_sha256": "research/j24k12_installed_bhdr_batch.py",
    }
    for field, file in sources.items():
        actual = subprocess.check_output(["git", "show", "HEAD:" + file])
        assert sha(actual) == doc["source"][field], field
    assert sha(source_c().encode()) == doc["source"]["c_scanner_sha256"]
    assert doc["signed_attack"]["preflight_reject"] == "ValidationError"
    assert {x[0] for x in doc["signed_attack"]["rejections"]} == {"control", "batch"}
    mutant = workdir / "signed-mismatch.cmpct"
    assert sha(mutant.read_bytes()) == doc["signed_attack"]["signed_mutant_sha256"]
    seen = set()
    min_ratio = math.inf
    for cell in doc["cells"]:
        n, case = cell["n_streams"], cell["scenario"]
        assert n in SIZES and case in CASES and (n, case) not in seen
        seen.add((n, case))
        artifact = workdir / f"{n}.cmpct"
        original = workdir / f"input-{n}" / "science.zip"
        assert sha(artifact.read_bytes()) == cell["archive_sha256"]
        raw = original.read_bytes()
        assert sha(raw) == cell["truth_sha256"]
        queries = expect_queries(len(raw), case)
        assert cell["queries_sha256"] == sha(json.dumps(queries).encode())
        expected = sha(b"".join(raw[start:start+ln] for start, ln in queries))
        assert cell["query_digest"] == expected
        for method in ("control", "batch"):
            rows = cell["observations"][method]
            assert len(rows) == 5
            for row in rows:
                assert row["strategy"] == method and row["scenario"] == case
                assert row["n_queries"] == len(queries)
                assert row["archive_sha256"] == cell["archive_sha256"]
                assert row["truth_sha256"] == cell["truth_sha256"]
                assert row["query_digest"] == expected
                assert all(type(row[m]) is int and row[m] >= 0 for m in METRICS)
                assert row["peak_rss_mib"] is None or (type(row["peak_rss_mib"]) in (float, int)
                           and 0 <= row["peak_rss_mib"] < 1_000_000)
                assert row["total_wall_ns"] >= row["read_wall_ns"]
                assert row["total_cpu_ns"] >= row["read_cpu_ns"]
            for metric in METRICS:
                median = statistics.median(x[metric] for x in rows)
                assert cell["median"][method][metric] == median, (n, case, method, metric)
        for metric in ("total_wall_ns", "total_cpu_ns", "read_wall_ns",
                       "read_cpu_ns", "process_wall_ns"):
            ratio = cell["median"]["control"][metric] / max(1, cell["median"]["batch"][metric])
            assert math.isclose(ratio, cell["ratio"][metric], rel_tol=1e-12)
            if n >= 512 and case == "q64_tail" and metric in ("total_wall_ns", "total_cpu_ns"):
                min_ratio = min(min_ratio, ratio)
    assert seen == {(n, case) for n in SIZES for case in CASES}
    assert math.isclose(min_ratio, doc["min_decisive_total_ratio"], rel_tol=1e-12)
    decision = ("INSTALLED_BATCH_HEADROOM" if min_ratio >= 1.20
                else "INSTALLED_BATCH_HEADROOM_NOT_PROVEN")
    assert doc["decision"] == decision
    return {"verdict": "PASS", "decisive_ratio": min_ratio, "decision": decision,
            "cells": len(seen), "raw_worker_observations": 120,
            "signed_mutation_rejections": 2}


def adversarial_audit(doc, workdir):
    # Forge a numeric outcome and a false no-regression claim; referee must reject each.
    cases = []
    a = copy.deepcopy(doc)
    a["cells"][0]["median"]["batch"]["total_wall_ns"] += 1
    cases.append(("forged_median", a))
    b = copy.deepcopy(doc)
    b["cells"][0]["observations"]["batch"][0]["query_digest"] = "0" * 64
    cases.append(("forged_bytes", b))
    c = copy.deepcopy(doc)
    c["signed_attack"]["rejections"] = [["control", "OSError"]]
    cases.append(("hidden_negative", c))
    d = copy.deepcopy(doc)
    d["source"]["reader_sha256"] = "0" * 64
    cases.append(("source_drift", d))
    e = copy.deepcopy(doc)
    e["decision"] = "INSTALLED_BATCH_HEADROOM"
    e["min_decisive_total_ratio"] = -1
    cases.append(("forged_promotion", e))
    for name, corrupted in cases:
        try: audit(corrupted, workdir)
        except (AssertionError, KeyError, TypeError, ValueError, OSError):
            continue
        raise AssertionError("forged evidence accepted: " + name)
    return len(cases)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py results.json workdir")
    document = json.loads(Path(sys.argv[1]).read_text())
    folder = Path(sys.argv[2])
    result = audit(document, folder)
    result["forgeries_rejected"] = adversarial_audit(document, folder)
    print("J24K12_AUDIT=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
