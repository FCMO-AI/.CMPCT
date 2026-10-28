#!/usr/bin/env python3
"""J24C11 independent receipt arithmetic and negative-path referee.

Validates recorded source/wire/answer identity and recomputes every group; it
does not execute CMPCT or confer new product/release authority.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import statistics


def check(payload):
    assert payload["schema"] == "j24c11-path-equivalence-v1"
    assert payload["inherited_j24c10_q1_scientific_decision"] == "NOT_PROMOTABLE"
    assert payload["release_credit"] is False
    assert payload["host"] in ("Linux", "Darwin", "Windows")
    assert len(payload["source_head"]) == 40
    assert len(payload["reader_sha256"]) == 64
    assert "site-packages" in payload["installed_reader"] or "dist-packages" in payload["installed_reader"]
    assert payload["q_policy"] == {"early-one": 8192, "late-ragged": 16}
    rows = payload["records"]
    assert len(rows) == 64
    groups = {}
    for item in rows:
        assert item["kind"] in ("early-one", "late-ragged")
        assert item["arm"] in ("strict", "witness")
        assert type(item["cycle"]) is int and 0 <= item["cycle"] < 8
        assert type(item["order_index"]) is int and 0 <= item["order_index"] < 4
        assert item["length"] == 16
        assert item["repetitions"] == payload["q_policy"][item["kind"]]
        assert item["n"] == (65536 if item["kind"] == "early-one" else 262144)
        assert item["offset"] == (12 if item["kind"] == "early-one" else item["offset"])
        assert type(item["proof_dispatch_calls"]) is int and item["proof_dispatch_calls"] == 0
        assert len(item["wire_sha256"]) == 64
        assert len(item["answer_sha256"]) == 64
        assert item["answer_sha256"] == item["expected_answer_sha256"]
        assert type(item["wall_ns"]) is int and item["wall_ns"] > 0
        assert type(item["cpu_ns"]) is int and item["cpu_ns"] >= 0
        groups.setdefault(item["kind"], {}).setdefault(item["arm"], []).append(item)
    assert set(groups) == {"early-one", "late-ragged"}
    all_details = {}
    for kind in sorted(groups):
        arms = groups[kind]
        assert set(arms) == {"strict", "witness"}
        assert all(len(a) == 16 for a in arms.values())
        union = [x for a in arms.values() for x in a]
        assert len(set(x["wire_sha256"] for x in union)) == 1
        assert len(set(x["answer_sha256"] for x in union)) == 1
        for cycle in range(8):
            actual = {x["order_index"]: x["arm"] for x in union if x["cycle"] == cycle}
            expected = ("strict", "witness", "witness", "strict") if cycle % 2 == 0 else (
                "witness", "strict", "strict", "witness")
            assert tuple(actual[i] for i in range(4)) == expected
        s = arms["strict"]
        w = arms["witness"]
        sw = statistics.median(x["wall_ns"] for x in s)
        ww = statistics.median(x["wall_ns"] for x in w)
        sc = statistics.median(x["cpu_ns"] for x in s)
        wc = statistics.median(x["cpu_ns"] for x in w)
        result = payload["summary"][kind]
        fields = {
            "strict_wall_median_ns": sw, "witness_wall_median_ns": ww,
            "wall_ratio": sw / ww, "strict_cpu_median_ns": sc,
            "witness_cpu_median_ns": wc, "cpu_ratio": sc / wc if wc > 0 else None,
            "cpu_resolved": sc > 0 and wc > 0,
            "zero_proof_dispatch": True,
        }
        for k, v in fields.items():
            observed = result[k]
            if isinstance(v, float):
                assert math.isclose(v, observed, rel_tol=1e-12), (kind, k, v, observed)
            else:
                assert observed == v, (kind, k, v, observed)
        all_details[kind] = {"cpu_resolved": fields["cpu_resolved"],
                             "zero_proof_dispatch": True,
                             "wall_ratio": fields["wall_ratio"],
                             "cpu_ratio": fields["cpu_ratio"]}
    assert set(payload["summary"]) == set(groups)
    return {"receipt_arithmetic": "PASS",
            "path_equivalence": "PASS_ZERO_DISPATCH_AND_EXACT_ANSWERS",
            "cpu_resolution": ("PASS" if all(x["cpu_resolved"] for x in all_details.values())
                               else "INCOMPLETE"),
            "product_release_credit": False,
            "inherited_j24c10_q1_result": "NOT_PROMOTABLE",
            "host": payload["host"], "samples": len(rows), "groups": all_details}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = check(payload)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print("J24C11_REFEREE", json.dumps(result, sort_keys=True))
    bad = json.loads(json.dumps(payload))
    bad["records"][0]["proof_dispatch_calls"] = 1
    try:
        check(bad)
    except AssertionError:
        print("J24C11_TAMPER_REJECTED")
    else:
        raise AssertionError("tampered negative-path evidence accepted")


if __name__ == "__main__":
    main()
