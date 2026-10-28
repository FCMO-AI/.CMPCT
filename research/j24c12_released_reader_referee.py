#!/usr/bin/env python3
"""Independent J24C12 receipt auditor. A negative performance verdict is valid science."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics

SOURCES = {
    "released": {"commit": "80c358f8824ec1b20d349c92ed94c898090969b0",
                 "reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8"},
    "strict": {"commit": "0a128ff55c7ae0f14c6bdf019a81b40f0d894eff",
               "reader_blob": "b37b786966ac1506a0439567d4a58eea472d85f8"},
    "native": {"commit": "a639570c1e9f9b36decae3893265be74a6d185b0",
               "reader_blob": "9bca5d1047f9c78984b945d7ca90e3149fe429ab"},
}
PROFILES = ((4096, 1), (65536, 1), (65536, 256), (262144, 1))
PHASES = ("open", "list", "ranges", "full_verify", "close")
SEQUENCES = (("released", "strict", "native", "native", "strict", "released"),
             ("native", "strict", "released", "released", "strict", "native"))
DECISION = {"floor_wall_ratio": 1.05, "floor_wall_extra_ms": 3.0,
            "floor_cpu_ratio": 1.05, "floor_cpu_extra_ms": 3.0,
            "rss_extra_bytes": 8 * 1024 * 1024}


def evaluate(raw: dict, fixture_dir: Path) -> dict:
    assert raw["schema"] == "cmpct-j24c12-released-reader-triplet-v1"
    assert raw["source_refs"] == SOURCES
    assert raw["decision"] == DECISION
    assert len(bytes.fromhex(raw["evidence_head"])) == 20
    assert raw["platform"] == "linux", "preregistered single-host Linux court only"
    fixtures = {(r["count"], r["owners"]): r for r in raw["fixtures"]}
    assert set(fixtures) == set(PROFILES)
    for profile, f in fixtures.items():
        count, owners = profile
        chunks = tuple(bytes((65+i % 23, 66, 67, 68)) for i in range(owners))
        logical = b"".join(chunks[i % owners] for i in range(count))
        assert len(logical) == f["logical_bytes"] == count*4
        assert hashlib.sha256(logical).hexdigest() == f["logical_sha256"]
        assert f["archive"] == f"r24-{count}-{owners}.cmpct"
        assert f["spec"] == f"r24-{count}-{owners}.json"
        wire = (fixture_dir / f["archive"]).read_bytes()
        assert len(wire) == f["archive_bytes"]
        assert hashlib.sha256(wire).hexdigest() == f["archive_sha256"]
        assert json.loads((fixture_dir / f["spec"]).read_text()) == f
        expected_offsets = (0, 8, len(logical)//2-16, len(logical)//2,
                            len(logical)-32, len(logical)-16)
        assert f["ranges"] == [
            [pos, logical[pos:pos+16].hex()] for pos in expected_offsets
        ]
    workers = raw["workers"]
    assert len(workers) == len(PROFILES)*3*6
    seen, counts = set(), Counter()
    for r in workers:
        p = (r["count"], r["owners"])
        arm, cycle, slot = r["arm"], r["cycle"], r["slot"]
        assert p in fixtures and arm in SOURCES
        assert cycle in (0, 1, 2) and slot in range(6)
        assert arm == SEQUENCES[cycle%2][slot], (p, cycle, slot, arm)
        key = (*p, cycle, slot)
        assert key not in seen
        seen.add(key)
        counts[(*p, arm)] += 1
        src = r["source"]
        assert src["arm"] == arm
        assert src["source_commit"] == SOURCES[arm]["commit"]
        assert src["reader_blob"] == SOURCES[arm]["reader_blob"]
        assert len(bytes.fromhex(src["reader_sha256"])) == 32
        assert "site-packages" in src["reader_path"] or "dist-packages" in src["reader_path"]
        assert r["archive_sha256"] == fixtures[p]["archive_sha256"]
        assert r["native_probe_calls"] == (1 if arm == "native" else 0)
        assert type(r["process_wall_ns"]) is int and r["process_wall_ns"] > 0
        assert r["rss_highwater_bytes"] is None or (
            type(r["rss_highwater_bytes"]) is int and r["rss_highwater_bytes"] > 0)
        assert len(r["samples"]) == 3
        expected_digest = hashlib.sha256(b"".join(
            bytes.fromhex(hx) for _, hx in fixtures[p]["ranges"]
        )).hexdigest()
        for s in r["samples"]:
            assert s["range_sha256"] == expected_digest
            for kind in ("cpu", "wall"):
                assert s["session_" + kind + "_ns"] > 0
                for phase in PHASES:
                    value = s[phase + "_" + kind + "_ns"]
                    assert type(value) is int and value >= 0
                assert s["session_" + kind + "_ns"] == sum(
                    s[phase + "_" + kind + "_ns"] for phase in PHASES)
    assert len(seen) == len(workers)
    assert counts == Counter({
        (n, o, arm): 6 for n, o in PROFILES for arm in SOURCES
    })
    rows = []
    wall_debt = cpu_debt = rss_caution = False
    for n, o in PROFILES:
        by = {}
        for arm in SOURCES:
            group = [w for w in workers if (w["count"],w["owners"],w["arm"])==(n,o,arm)]
            measures = {}
            for phase in ("session_wall","session_cpu","open_wall","open_cpu",
                          "ranges_wall","ranges_cpu","full_verify_wall","close_wall"):
                measures[phase+"_ms"] = statistics.median(
                    statistics.median(s[phase+"_ns"] for s in w["samples"])
                    for w in group
                ) / 1e6
            rss = [w["rss_highwater_bytes"] for w in group]
            measures["rss_max_bytes"] = max(rss) if all(x is not None for x in rss) else None
            by[arm] = measures
        pub = by["released"]
        nat = by["native"]
        wall_ratio = nat["session_wall_ms"]/pub["session_wall_ms"]
        cpu_ratio = nat["session_cpu_ms"]/pub["session_cpu_ms"]
        wall_ms = nat["session_wall_ms"]-pub["session_wall_ms"]
        cpu_ms = nat["session_cpu_ms"]-pub["session_cpu_ms"]
        rss_pub = pub["rss_max_bytes"]
        rss_nat = nat["rss_max_bytes"]
        rss_bytes = None if rss_pub is None or rss_nat is None else rss_nat-rss_pub
        flagged_wall = wall_ratio>=1.05 and wall_ms>=3.0
        flagged_cpu = cpu_ratio>=1.05 and cpu_ms>=3.0
        flagged_rss = rss_bytes is not None and rss_bytes>8*1024*1024
        if n>=65536:
            wall_debt |= flagged_wall
            cpu_debt |= flagged_cpu
            rss_caution |= flagged_rss
        rows.append({
            "count":n,"owners":o,"arms":by,
            "native_over_released_wall_ratio":wall_ratio,
            "native_minus_released_wall_ms":wall_ms,
            "native_over_released_cpu_ratio":cpu_ratio,
            "native_minus_released_cpu_ms":cpu_ms,
            "native_minus_released_rss_bytes":rss_bytes,
            "wall_debt":flagged_wall,"cpu_debt":flagged_cpu,
            "rss_caution":flagged_rss,
            "strict_over_native_wall_ratio":(
                by["strict"]["session_wall_ms"]/nat["session_wall_ms"]
            ),
        })
    return {
        "schema":"cmpct-j24c12-released-triplet-referee-v1",
        "evidence_head":raw["evidence_head"],
        "decision":"MATERIAL_PUBLISHED_FLOOR_DEBT" if wall_debt or cpu_debt else
                   ("RSS_ONLY_CAUTION" if rss_caution else "NO_MATERIAL_FLOOR_DEBT_SIGNAL"),
        "wall_debt":wall_debt,"cpu_debt":cpu_debt,"rss_caution":rss_caution,
        "workers":len(workers),"sessions":len(workers)*3,
        "rows":rows,
        "scope":"valid fixed RAW S_CHUNKS single Linux host; no safety equivalence or release credit",
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=json.loads(args.input.read_text())
    fixture_dir=args.input.parent/"fixtures"
    verdict=evaluate(raw,fixture_dir)
    for mutant in ("wrong-answer","wrong-source","missing-worker","false-native","threshold-tamper"):
        forged=copy.deepcopy(raw)
        if mutant=="wrong-answer":
            forged["workers"][0]["samples"][0]["range_sha256"]="00"*32
        elif mutant=="wrong-source":
            forged["workers"][0]["source"]["reader_blob"]="00"*20
        elif mutant=="missing-worker":
            forged["workers"].pop()
        elif mutant=="false-native":
            next(x for x in forged["workers"] if x["arm"]=="native")["native_probe_calls"]=0
        else:
            forged["decision"]["floor_wall_ratio"]=100
        try:
            evaluate(forged,fixture_dir)
        except (AssertionError, ValueError, KeyError):
            pass
        else:
            raise AssertionError("auditor accepted forged receipt "+mutant)
    args.output.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n")
    print(f"J24C12_AUDITOR_PASS workers={verdict['workers']} sessions={verdict['sessions']}")
    print("J24C12_DECISION="+verdict["decision"])
    for r in verdict["rows"]:
        print(f"J24C12_PROFILE {r['count']}/{r['owners']} native/published wall="
              f"{r['native_over_released_wall_ratio']:.4f}, extra={r['native_minus_released_wall_ms']:.4f}ms")


if __name__ == "__main__":
    main()
