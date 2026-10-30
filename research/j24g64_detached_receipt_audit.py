#!/usr/bin/env python3
"""Independent standard-library-only J24G64 receipt referee.

Arithmetic and causal evidence consistency, not a second archive implementation.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

PARENT = "9dc765a902c0f5c424639caf9cdfd571cca2d6e6"
PREREG = "624eec80b90ec25bf22501f66b92b7a32e6b928b"
SOURCE = "03743ca2a06c022c2ec64243a90fe373cf91e899"


def review(document: dict, expected_head: str) -> dict:
    assert isinstance(document, dict)
    assert document.get("schema") == "cmpct-j24g64-mixed-fsmeta-research-v1"
    assert isinstance(expected_head, str) and re.fullmatch(r"[a-f0-9]{40}", expected_head)
    origin = document.get("source")
    assert isinstance(origin, dict)
    assert origin.get("head") == expected_head
    assert origin.get("baseline_source_blob") == SOURCE
    assert origin.get("prereg") == PREREG
    assert document.get("members") == 2048
    assert document.get("generations") == 63
    assert document.get("sparse_xattr_records") >= 50
    assert document.get("sparse_owner_records") >= 25
    assert document.get("archive_bytes_added") == 0
    assert re.fullmatch(r"[a-f0-9]{64}", document.get("final_index_msgpack_sha256", ""))
    edges = document.get("targeted_semantic_edges")
    assert isinstance(edges, dict) and len(edges) == 14
    for key in ("delete-and-recreate-same-name",
                "rename-then-reuse-old-name", "rename-return-cycle",
                "rename-transfer-metadata", "retain-metadata-on-replace",
                "delete-put-rename-recreate", "self-rename-no-rekey",
                "replace-only-retains-original-order"):
        assert edges.get(key) == "factored"
    for key in ("collision-fallback", "missing-source-fallback",
                "missing-delete-fallback", "multi-op-generation-fallback"):
        assert edges.get(key, "").startswith("fallback:")
    assert edges.get("future-op-exact-failure") == "matched-exception"
    assert edges.get("file-limit-exact-failure") == "matched-exception"
    counts = document.get("differential")
    assert isinstance(counts, dict)
    assert all(type(v) is int and v >= 0 for v in counts.values())
    assert sum(counts.values()) == 5000
    assert counts.get("factored", 0) > 500
    assert counts.get("matched-exception", 0) > 0
    assert sum(v for k, v in counts.items() if k.startswith("fallback:")) > 500
    observations = document.get("raw_samples")
    assert isinstance(observations, list) and len(observations) == 32
    for block in range(8):
        expected = ["reference", "factored", "factored", "reference"] if block % 2 == 0 else [
            "factored", "reference", "reference", "factored"]
        actual = [row for row in observations if row.get("block") == block]
        assert len(actual) == 4
        assert [row["phase"] for row in actual] == [0, 1, 2, 3]
        assert [row["variant"] for row in actual] == expected
        for row in actual:
            assert type(row["wall_ns"]) is int and row["wall_ns"] > 0
            assert type(row["cpu_ns"]) is int and row["cpu_ns"] >= 0
    aa = [row["wall_ns"] for row in observations if row["variant"] == "reference"]
    bb = [row["wall_ns"] for row in observations if row["variant"] == "factored"]
    assert len(aa) == len(bb) == 16
    ma, mb = statistics.median(aa), statistics.median(bb)
    assert document["wall_median_ns"] == {"reference": ma, "factored": mb}
    assert document["wall_speedup"] == ma / mb
    trace = document["tracemalloc"]
    assert set(trace) == {"reference", "factored"}
    for row in trace.values():
        assert type(row["peak_traced_bytes"]) is int and row["peak_traced_bytes"] > 0
        assert type(row["retained_traced_bytes"]) is int and row["retained_traced_bytes"] >= 0
        assert row["peak_traced_bytes"] >= row["retained_traced_bytes"]
    extra = trace["factored"]["peak_traced_bytes"] - trace["reference"]["peak_traced_bytes"]
    assert document["extra_peak_traced_bytes"] == extra
    decision = "MIXED_FSMETA_REPLAY_SEED" if ma / mb >= 2 and extra <= 2097152 else "NO_BOUNDED_MIXED_FSMETA_WIN"
    assert document["decision"] == decision
    assert isinstance(document.get("limitations"), list) and len(document["limitations"]) >= 5
    return {
        "schema": "cmpct-j24g64-detached-review-v1",
        "result_head": expected_head,
        "pre_result_commit": PREREG,
        "helper_blob": SOURCE,
        "number_of_samples": len(observations),
        "number_of_differential_cases": sum(counts.values()),
        "median_reference_ns": ma,
        "median_factored_ns": mb,
        "recomputed_speedup": ma / mb,
        "extra_traced_bytes": extra,
        "decision": decision,
        "scope": "independent arithmetic/provenance review of receipts only",
    }


def _hostile_controls(original: dict, expected_head: str) -> dict:
    attacks = {}
    def attack(name, edit):
        specimen = copy.deepcopy(original)
        edit(specimen)
        try:
            review(specimen, expected_head)
        except (AssertionError, KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
            attacks[name] = "REJECTED"
        else:
            raise AssertionError("adversarial receipt accepted: " + name)
    attack("source-substitution", lambda p: p["source"].update(head="0" * 40))
    attack("baseline-helper-substitution", lambda p: p["source"].update(baseline_source_blob="1" * 40))
    attack("sample-omission", lambda p: p["raw_samples"].pop())
    attack("phase-order-perturbation", lambda p: p["raw_samples"][0].update(phase=3))
    attack("timing-branch-tampering", lambda p: [v.update(wall_ns=v["wall_ns"] * 3) for v in p["raw_samples"] if v["variant"] == "reference"])
    attack("metadata-records-erased", lambda p: p.update(sparse_xattr_records=0))\n    attack("identity-lineage-control-falsified", lambda p: p["targeted_semantic_edges"].update({"delete-and-recreate-same-name": "fallback:inconclusive"}))
    attack("differential-count-manipulation", lambda p: p["differential"].update(factored=p["differential"]["factored"] + 1))
    attack("false-product-decision", lambda p: p.update(decision="MIXED_FSMETA_REPLAY_SEED" if p["decision"] != "MIXED_FSMETA_REPLAY_SEED" else "NO_BOUNDED_MIXED_FSMETA_WIN"))
    return attacks


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: independent_receipt_audit.py result.json exact_head output.json")
    source = Path(sys.argv[1])
    raw = source.read_bytes()
    data = json.loads(raw)
    head = sys.argv[2]
    result = review(data, head)
    result["original_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    result["adversarial"] = _hostile_controls(data, head)
    assert len(result["adversarial"]) == 9
    output = Path(sys.argv[3])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("J24G64_DETACHED_DECISION", result["decision"])
    print("J24G64_DETACHED_ATTACKS", len(result["adversarial"]))
    print("J24G64_DETACHED_SHA256", hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
