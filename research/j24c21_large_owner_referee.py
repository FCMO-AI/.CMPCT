#!/usr/bin/env python3
"""Independent J24C21 receipt referee, without importing CMPCT or the court module.

Reconstructs all three deterministic logical workloads from a second algorithm,
checks original signed archive byte identities, source/process matrix, and raw
observations. Negative performance verdicts are valid scientific SUCCESS.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
from statistics import median

ARMS = ("published", "fused", "sealed")
SHAPES = ("Q1_early", "Q6_spread", "Q32_spread")
PROFILES = ("tiny_repeat_65k", "large_repeat_262k", "large_distinct_8k")
SOURCES = {
    "published": "80c358f8824ec1b20d349c92ed94c898090969b0",
    "fused": "a66fd593a83cc4c71556d3d86d835c51abd20a96",
    "sealed": "3b6a73f9205f40f11124cd9ff332407e52cebb93",
}
METRICS = ("open_wall_ns", "open_cpu_ns", "read_wall_ns", "read_cpu_ns",
           "session_wall_ns", "session_cpu_ns", "outer_process_wall_ns")


def fail(message):
    raise ValueError("J24C21 INDEPENDENT REFEREE: " + message)


def reconstruct(profile):
    if profile == "tiny_repeat_65k":
        owners = (b"A", b"B")
        refs = (i & 1 for i in range(65536))
    elif profile == "large_repeat_262k":
        owners = (hashlib.shake_256(b"CMPCT-J24C21-A").digest(4096),
                  hashlib.shake_256(b"CMPCT-J24C21-B").digest(4096))
        refs = (i & 1 for i in range(262144))
    elif profile == "large_distinct_8k":
        owners = tuple(hashlib.shake_256(b"CMPCT-J24C21-owner-" + i.to_bytes(4, "big"))
                       .digest(4096) for i in range(4096))
        refs = ((i * 2053 + 17) % 4096 for i in range(8192))
    else:
        fail("unexpected profile")
    return owners, list(refs)


def validate(report, root):
    if report.get("schema") != "j24c21-court-v1":
        fail("unexpected court schema")
    if report.get("sources") != SOURCES:
        fail("historical source commits changed")
    repetitions = report.get("repetitions")
    if type(repetitions) is not int or repetitions < 4:
        fail("fewer than four repeated processes")
    manifest_path = root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != report.get("fixture_manifest_sha256"):
        fail("fixture manifest identity changed")
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "j24c21-fixtures-v1":
        fail("fixture schema changed")
    if set(manifest.get("profiles", {})) != set(PROFILES):
        fail("profile set changed")
    if manifest["profiles"] != report.get("profiles"):
        fail("embedded profiles differ from fixture manifest")
    for profile in PROFILES:
        entry = report["profiles"][profile]
        file = root / entry["archive"]
        if file.name != profile + ".cmpct":
            fail("fixture filename changed")
        if hashlib.sha256(file.read_bytes()).hexdigest() != entry["archive_sha256"]:
            fail("archive bytes drifted")
        if file.stat().st_size != entry["archive_bytes"]:
            fail("archive byte accounting mismatch")
        owners, refs = reconstruct(profile)
        if len(owners) != entry["physical_blob_count"]:
            fail("physical owner count changed")
        if sum(map(len, owners)) != entry["physical_payload_bytes"]:
            fail("physical bytes changed")
        if len(refs) != entry["reference_count"]:
            fail("reference count changed")
        h = hashlib.sha256()
        size = 0
        for i in refs:
            h.update(owners[i])
            size += len(owners[i])
        if h.hexdigest() != entry["logical_sha256"] or size != entry["logical_bytes"]:
            fail("independent logical identity inconsistent")
        if set(entry["queries"]) != set(SHAPES):
            fail("query shape set changed")
        for shape, queries in entry["queries"].items():
            if len(queries) != {"Q1_early": 1, "Q6_spread": 6, "Q32_spread": 32}[shape]:
                fail("query count changed")
            seen = set()
            for q in queries:
                start, length = q["start"], q["length"]
                if type(start) is not int or type(length) is not int or start < 0 or length < 0 or start + length > size:
                    fail("invalid request bounds")
                if (start, length) in seen:
                    fail("duplicated request")
                seen.add((start, length))
                unit = len(owners[0])
                first = start // unit
                after = (start + length + unit - 1) // unit
                window = b"".join(owners[refs[i]] for i in range(first, after))
                want = window[start - first * unit:start - first * unit + length]
                if hashlib.sha256(want).hexdigest() != q["sha256"]:
                    fail("independent range digest mismatch")
    expected_total = len(PROFILES) * len(SHAPES) * len(ARMS) * repetitions
    rows = report.get("observations")
    if not isinstance(rows, list) or len(rows) != expected_total:
        fail("incomplete/extra process matrix")
    groups = defaultdict(list)
    source_reader_digest = {}
    for row in rows:
        if row.get("schema") != "j24c21-probe-v1":
            fail("probe schema changed")
        arm, profile, shape = row.get("arm"), row.get("profile"), row.get("shape")
        if arm not in ARMS or profile not in PROFILES or shape not in SHAPES:
            fail("invalid process arm/profile/shape")
        if row.get("source_commit") != SOURCES[arm]:
            fail("source commit mismatch")
        sha = row.get("source_tree_reader_sha256")
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            fail("missing installed Reader source digest")
        if arm in source_reader_digest and source_reader_digest[arm] != sha:
            fail("Reader source changed across processes")
        source_reader_digest[arm] = sha
        if row.get("archive_sha256") != report["profiles"][profile]["archive_sha256"]:
            fail("process used different physical archive")
        if row.get("answer_count") != {"Q1_early": 1, "Q6_spread": 6, "Q32_spread": 32}[shape]:
            fail("process answer count mismatch")
        if row.get("answer_bytes") != sum(q["length"] for q in report["profiles"][profile]["queries"][shape]):
            fail("process answer-byte count mismatch")
        if not str(row.get("python", "")).startswith("3.11."):
            fail("not an installed CPython 3.11 comparative process")
        rep = row.get("repetition")
        if type(rep) is not int or not 0 <= rep < repetitions:
            fail("invalid repetition id")
        for metric in METRICS:
            value = row.get(metric)
            if type(value) is not int or value < 0:
                fail("missing or negative timing")
        if row["session_wall_ns"] < row["open_wall_ns"] + row["list_wall_ns"]:
            fail("impossible wall timing decomposition")
        if row["session_cpu_ns"] < row["open_cpu_ns"] + row["list_cpu_ns"]:
            fail("impossible CPU timing decomposition")
        rss = row.get("peak_rss_kib")
        if rss is not None and (type(rss) is not int or rss <= 0):
            fail("invalid RSS field")
        groups[(profile, shape, arm)].append(row)
    if len(set(source_reader_digest.values())) < 3:
        fail("comparison reused a Reader file across sources")
    for k, rows in groups.items():
        if len(rows) != repetitions or sorted(x["repetition"] for x in rows) != list(range(repetitions)):
            fail(f"missing/duplicated repetitions at {k}")
    summary = {}
    for profile in PROFILES:
        summary[profile] = {}
        for shape in SHAPES:
            med = {arm: {metric: median(row[metric] for row in groups[profile, shape, arm])
                         for metric in METRICS} for arm in ARMS}
            for arm in ARMS:
                vals = [row["peak_rss_kib"] for row in groups[profile, shape, arm]]
                med[arm]["peak_rss_kib"] = median(vals) if all(v is not None for v in vals) else None
            summary[profile][shape] = {
                "median_by_arm": med,
                "sealed_over_published_wall": med["sealed"]["session_wall_ns"] / med["published"]["session_wall_ns"],
                "sealed_over_published_cpu": med["sealed"]["session_cpu_ns"] / med["published"]["session_cpu_ns"],
                "sealed_over_fused_wall": med["sealed"]["session_wall_ns"] / med["fused"]["session_wall_ns"],
            }
    target = summary["large_repeat_262k"]["Q6_spread"]["median_by_arm"]
    q6_pass = all(
        target["published"][metric] - target["sealed"][metric] >= 3_000_000
        and target["sealed"][metric] <= 0.95 * target["published"][metric]
        for metric in ("session_wall_ns", "session_cpu_ns")
    )
    q1_debt = {}
    for profile in ("large_repeat_262k", "large_distinct_8k"):
        m = summary[profile]["Q1_early"]["median_by_arm"]
        q1_debt[profile] = any(
            m["sealed"][k] - m["published"][k] >= 3_000_000
            and m["sealed"][k] >= 1.05 * m["published"][k]
            for k in ("session_wall_ns", "session_cpu_ns")
        )
    rss_debt = {}
    for profile in PROFILES:
        for shape in SHAPES:
            m = summary[profile][shape]["median_by_arm"]
            a, b = m["sealed"]["peak_rss_kib"], m["published"]["peak_rss_kib"]
            rss_debt[profile + "/" + shape] = (a - b > 8192 if a is not None and b is not None else None)
    return {
        "schema": "j24c21-independent-decision-v1",
        "source_reader_sha256": source_reader_digest,
        "validated_processes": len(rows) * 0 + expected_total,
        "signed_physical_profiles": len(PROFILES),
        "q6_large_repeat_research_material": q6_pass,
        "early_q1_veto_by_profile": q1_debt,
        "rss_eight_mib_debt_by_profile": rss_debt,
        "research_decision": "RETAIN_Q6_LARGE_OWNER" if q6_pass else "NO_MATERIAL_Q6_LARGE_OWNER",
        "promotion_authorized": False,
        "results": summary,
        "scope": "installed Linux cp311 valid signed RAW r24 only; no codec / hostile / release credit",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--fixtures", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = json.loads(a.input.read_text(encoding="utf-8"))
    result = validate(report, a.fixtures)
    # A referee is itself testable. Every mutation must fail closed.
    cases = {
        "source": lambda r: r["observations"][0].__setitem__("source_commit", "0" * 40),
        "archive": lambda r: r["observations"][0].__setitem__("archive_sha256", "0" * 64),
        "answer": lambda r: r["observations"][0].__setitem__("answer_bytes", -1),
        "time": lambda r: r["observations"][0].__setitem__("session_cpu_ns", -1),
        "repetition": lambda r: r["observations"][0].__setitem__("repetition", 999),
        "missing": lambda r: r["observations"].pop(),
        "fixture": lambda r: r["profiles"]["tiny_repeat_65k"]["logical_sha256"].__class__,
    }
    for name, tamper in cases.items():
        mutant = copy.deepcopy(report)
        if name == "fixture":
            mutant["profiles"]["tiny_repeat_65k"]["logical_sha256"] = "0" * 64
        else:
            tamper(mutant)
        try:
            validate(mutant, a.fixtures)
        except (ValueError, KeyError, TypeError):
            continue
        fail("referee accepted altered receipt: " + name)
    result["adversarial_receipts_rejected"] = len(cases)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("validated_processes", "research_decision",
                                             "early_q1_veto_by_profile",
                                             "adversarial_receipts_rejected")}, sort_keys=True))


if __name__ == "__main__":
    main()
