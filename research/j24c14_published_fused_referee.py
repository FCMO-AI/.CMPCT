#!/usr/bin/env python3
"""J24C14 independent published-vs-fused receipt auditor; negative verdicts are valid."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics

SOURCES = {
    "released": {"commit": "80c358f8824ec1b20d349c92ed94c898090969b0", "reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8"},
    "native": {"commit": "a639570c1e9f9b36decae3893265be74a6d185b0", "reader_blob": "9bca5d1047f9c78984b945d7ca90e3149fe429ab"},
    "fused": {"commit": "a66fd593a83cc4c71556d3d86d835c51abd20a96", "reader_blob": "c4d1dee0a31527b814d6e1f41b77abe1cc987996"},
}
PROFILES = ((4096, 1), (65536, 1), (65536, 256), (262144, 1))
PHASES = ("open", "list", "ranges", "full_verify", "close")
SEQUENCES = (("released", "native", "fused", "fused", "native", "released"),
             ("fused", "native", "released", "released", "native", "fused"))
DECISION = {"win_wall_ratio": 0.95, "win_wall_saved_ms": 3.0,
            "win_cpu_ratio": 0.95, "win_cpu_saved_ms": 3.0,
            "native_regression_ratio": 1.05, "native_regression_ms": 3.0,
            "rss_extra_bytes": 8 * 1024 * 1024}


def evaluate(raw: dict, fixture_dir: Path) -> dict:
    assert raw["schema"] == "cmpct-j24c14-published-fused-triplet-v1"
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
        assert r["native_probe_calls"] == (1 if arm in ("native","fused") else 0)
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
    wins = []
    native_debt = False
    rss_caution = False
    for n,o in PROFILES:
        by = {}
        for arm in SOURCES:
            group = [w for w in workers if (w["count"],w["owners"],w["arm"]) == (n,o,arm)]
            measures = {}
            for phase in ("session_wall","session_cpu","open_wall","open_cpu",
                          "ranges_wall","ranges_cpu","full_verify_wall","close_wall"):
                measures[phase+"_ms"] = statistics.median(
                    statistics.median(s[phase+"_ns"] for s in w["samples"]) for w in group
                ) / 1e6
            rss = [w["rss_highwater_bytes"] for w in group]
            measures["rss_max_bytes"] = max(rss) if all(x is not None for x in rss) else None
            by[arm] = measures
        pub, nat, fused = by["released"], by["native"], by["fused"]
        saved_wall = pub["session_wall_ms"] - fused["session_wall_ms"]
        saved_cpu = pub["session_cpu_ms"] - fused["session_cpu_ms"]
        r_wall = fused["session_wall_ms"]/pub["session_wall_ms"]
        r_cpu = fused["session_cpu_ms"]/pub["session_cpu_ms"]
        win_wall = r_wall <= DECISION["win_wall_ratio"] and saved_wall >= DECISION["win_wall_saved_ms"]
        win_cpu = r_cpu <= DECISION["win_cpu_ratio"] and saved_cpu >= DECISION["win_cpu_saved_ms"]
        native_reg_wall = (fused["session_wall_ms"] >= DECISION["native_regression_ratio"] * nat["session_wall_ms"] and
                          fused["session_wall_ms"] - nat["session_wall_ms"] >= DECISION["native_regression_ms"])
        native_reg_cpu = (fused["session_cpu_ms"] >= DECISION["native_regression_ratio"] * nat["session_cpu_ms"] and
                         fused["session_cpu_ms"] - nat["session_cpu_ms"] >= DECISION["native_regression_ms"])
        rss_pub,rss_fused = pub["rss_max_bytes"], fused["rss_max_bytes"]
        rss_delta = None if rss_pub is None or rss_fused is None else rss_fused-rss_pub
        flag_rss = rss_delta is not None and rss_delta>DECISION["rss_extra_bytes"]
        major = n>=65536
        if major:
            wins.append(win_wall and win_cpu)
            native_debt |= (native_reg_wall or native_reg_cpu)
            rss_caution |= flag_rss
        rows.append({
            "count":n, "owners":o, "arms":by, "major":major,
            "fused_over_released_wall_ratio":r_wall,
            "fused_over_released_cpu_ratio":r_cpu,
            "fused_saved_released_wall_ms":saved_wall,
            "fused_saved_released_cpu_ms":saved_cpu,
            "win_wall":win_wall, "win_cpu":win_cpu,
            "fused_over_native_wall_ratio":fused["session_wall_ms"]/nat["session_wall_ms"],
            "fused_over_native_cpu_ratio":fused["session_cpu_ms"]/nat["session_cpu_ms"],
            "native_reg_wall":native_reg_wall,"native_reg_cpu":native_reg_cpu,
            "fused_minus_released_rss_bytes":rss_delta,"rss_caution":flag_rss,
        })
    assert len(wins)==3, "expected exactly three major profiles"
    if all(wins) and not native_debt and not rss_caution:
        result="STRONG_RELEASED_Q6_REHABILITATION_RESEARCH"
    elif any(wins) and not native_debt:
        result="PROFILE_LIMITED_RESEARCH_WIN"
    else:
        result="NO_GENERAL_RELEASED_Q6_REHABILITATION"
    return {
        "schema":"cmpct-j24c14-published-fused-referee-v1",
        "evidence_head":raw["evidence_head"],"decision":result,
        "major_wins":sum(wins), "major_rows":len(wins),
        "native_regression_debt":native_debt,"rss_caution":rss_caution,
        "workers":len(workers),"sessions":len(workers)*3,"rows":rows,
        "scope":"valid signed fixed RAW S_CHUNKS single Linux runner; released arm economics only, not safety equivalence or release authority",
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=json.loads(args.input.read_text())
    fixture_dir=args.input.parent/"fixtures"
    verdict=evaluate(raw,fixture_dir)
    for mutant in ("wrong-answer","wrong-source","missing-worker","false-native","false-fused","threshold-tamper"):
        forged=copy.deepcopy(raw)
        if mutant=="wrong-answer":
            forged["workers"][0]["samples"][0]["range_sha256"]="00"*32
        elif mutant=="wrong-source":
            forged["workers"][0]["source"]["reader_blob"]="00"*20
        elif mutant=="missing-worker":
            forged["workers"].pop()
        elif mutant=="false-native":
            next(x for x in forged["workers"] if x["arm"]=="native")["native_probe_calls"]=0
        elif mutant=="false-fused":
            next(x for x in forged["workers"] if x["arm"]=="fused")["native_probe_calls"]=0
        else:
            forged["decision"]["win_wall_ratio"]=100
        try:
            evaluate(forged,fixture_dir)
        except (AssertionError, ValueError, KeyError):
            pass
        else:
            raise AssertionError("auditor accepted forged receipt "+mutant)
    args.output.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n")
    print(f"J24C14_AUDITOR_PASS workers={verdict['workers']} sessions={verdict['sessions']}")
    print("J24C14_DECISION="+verdict["decision"])
    for r in verdict["rows"]:
        print(f"J24C14_PROFILE {r['count']}/{r['owners']} fused/released wall="
              f"{r['fused_over_released_wall_ratio']:.4f}, saved={r['fused_saved_released_wall_ms']:.4f}ms")


if __name__ == "__main__":
    main()
