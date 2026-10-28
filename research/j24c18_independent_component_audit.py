#!/usr/bin/env python3
"""Independent stdlib-only referee for the component oracle, not CMPCT product evidence."""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import statistics


REQUIRED = {
    "four-65536": (65536, 4),
    "four-262144": (262144, 4),
    "four-1048576": (1048576, 4),
    "many-262144": (262144, 256),
}
ARMS = {"control", "fused"}


def audit(result, source_digest):
    assert result.get("schema") == "j24c18-fused-seal-component-v1"
    assert result.get("source_parent_sha") == "3b6a73f9205f40f11124cd9ff332407e52cebb93"
    assert result.get("source_sha256") == source_digest, "unbound native component"
    assert set(result.get("cases", [])) == set(REQUIRED), "missing cases"
    repetitions = result.get("repetitions")
    assert type(repetitions) is int and repetitions >= 9
    rows = result["records"]
    assert len(rows) == 2 * repetitions * len(REQUIRED), "missing/raw extra process"
    by_key = {}
    for r in rows:
        case, arm, rep = r["case"], r["arm"], r["rep"]
        assert case in REQUIRED and arm in ARMS
        assert type(rep) is int and 0 <= rep < repetitions
        k = case, arm, rep
        assert k not in by_key, "duplicate observation"
        by_key[k] = r
        n, owners = REQUIRED[case]
        assert r["n"] == n and r["owners"] == owners
        assert r["checkpoint_count"] == (n + 255) // 256
        assert type(r["expected"]) is int and r["expected"] >= 0
        assert isinstance(r["digest"], str) and len(r["digest"]) == 64
        assert all(c in "0123456789abcdef" for c in r["digest"])
        assert type(r["wall_ms"]) in (int, float) and 0 < r["wall_ms"] < 10000
        assert type(r["cpu_ms"]) in (int, float) and 0 < r["cpu_ms"] < 10000
        if r["process_hwm_kib"] is not None:
            assert 0 < r["process_hwm_kib"] < 10_000_000
    stats = {}
    for case in REQUIRED:
        for rep in range(repetitions):
            a = by_key[case, "control", rep]
            b = by_key[case, "fused", rep]
            assert a["expected"] == b["expected"], "logical-size discrepancy"
            assert a["digest"] == b["digest"], "proof/ref semantic divergence"
            assert a["python"] == b["python"] and a["platform"] == b["platform"], "host mismatch"
        vals = {arm: [by_key[case, arm, i] for i in range(repetitions)] for arm in ARMS}
        cpu = {arm: statistics.median(r["cpu_ms"] for r in vals[arm]) for arm in ARMS}
        wall = {arm: statistics.median(r["wall_ms"] for r in vals[arm]) for arm in ARMS}
        rss = {}
        for arm in ARMS:
            samples = [r["process_hwm_kib"] for r in vals[arm]]
            rss[arm] = statistics.median(samples) if all(v is not None for v in samples) else None
        wall_ratio = wall["fused"] / wall["control"]
        cpu_ratio = cpu["fused"] / cpu["control"]
        extra_rss_mib = ((rss["fused"] - rss["control"]) / 1024
                         if rss["fused"] is not None and rss["control"] is not None else None)
        stats[case] = {
            "wall_ms": wall, "cpu_ms": cpu, "rss_hwm_kib": rss,
            "wall_ratio": wall_ratio, "cpu_ratio": cpu_ratio,
            "extra_rss_mib": extra_rss_mib,
        }
    decisive = ("four-65536", "four-262144")
    pass_wall = all(stats[c]["wall_ratio"] <= 0.95 for c in decisive)
    pass_cpu = all(stats[c]["cpu_ratio"] <= 1.05 for c in decisive)
    pass_mem = all(stats[c]["extra_rss_mib"] is None or
                   stats[c]["extra_rss_mib"] <= 8 for c in decisive)
    # Never turn absence of Windows HWM into measured zero. Pass_mem only
    # means no *observed* veto; separate disclosure remains mandatory.
    verdict = ("COMPONENT_WARRANT_PENDING_PRODUCT" if pass_wall and pass_cpu and pass_mem
               else "REJECT_C_PER_ITEM_FUSED_FREEZE_ROUTE")
    return {"verdict": verdict, "cases": stats,
            "raw_records_validated": len(rows),
            "repetitions_per_arm": repetitions,
            "cross_arm_equality": True,
            "component_only": True,
            "unmeasured": ["installed Reader", "released v0.30 comparison",
                           "full cold Q1/Q6/Q64", "archive size/extract",
                           "general runtime", "format/release", "RSS on unavailable hosts"]}


def hostile_contract(result, digest):
    mutations = []
    a = copy.deepcopy(result); a["records"].pop(); mutations.append(a)
    a = copy.deepcopy(result); a["records"][0]["wall_ms"] = 0; mutations.append(a)
    a = copy.deepcopy(result); a["records"][0]["digest"] = "a" * 64; mutations.append(a)
    a = copy.deepcopy(result); a["source_sha256"] = "0" * 64; mutations.append(a)
    a = copy.deepcopy(result); a["records"][0]["checkpoint_count"] += 1; mutations.append(a)
    a = copy.deepcopy(result); a["records"][0]["arm"] = "fused"; mutations.append(a)
    a = copy.deepcopy(result); a["records"][0]["n"] += 1; mutations.append(a)
    for i, m in enumerate(mutations):
        try:
            audit(m, digest)
        except (AssertionError, ValueError, TypeError, KeyError, ZeroDivisionError):
            continue
        raise AssertionError(f"forged receipt accepted: {i}")
    return len(mutations)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    root = Path(__file__).resolve().parent
    component = root / "j24c18_fused_copy_component.c"
    digest = hashlib.sha256(component.read_bytes()).hexdigest()
    raw = json.loads(Path(a.input).read_text("utf-8"))
    out = audit(raw, digest)
    out["hostile_receipts_rejected"] = hostile_contract(raw, digest)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", "utf-8")
    print("J24C18_INDEPENDENT_RECEIPT_PASS_COMPONENT_ONLY",
          out["verdict"], out["raw_records_validated"],
          "hostile_rejections", out["hostile_receipts_rejected"])
    for k,v in out["cases"].items():
        print(k,"ratio",round(v["wall_ratio"],4),
              "CPU",round(v["cpu_ratio"],4),"RSS_delta_MiB",v["extra_rss_mib"])
