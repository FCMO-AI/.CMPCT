#!/usr/bin/env python3
"""J24C15 second-root receipt judge. No CMPCT imports; losses remain valid results."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import statistics

EXPECTED_SOURCES = {
    "released": {"commit": "80c358f8824ec1b20d349c92ed94c898090969b0",
                 "reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8"},
    "native": {"commit": "a639570c1e9f9b36decae3893265be74a6d185b0",
               "reader_blob": "9bca5d1047f9c78984b945d7ca90e3149fe429ab"},
    "fused": {"commit": "a66fd593a83cc4c71556d3d86d835c51abd20a96",
              "reader_blob": "c4d1dee0a31527b814d6e1f41b77abe1cc987996"},
}
EXPECTED_PROFILES = {
    "irregular-raw-65536": (65536, (0, 1, 3, 7, 13, 29, 47, 89), ("raw",)*8),
    "irregular-raw-262144": (262144, (0, 1, 3, 7, 13, 29, 47, 89), ("raw",)*8),
    "mixed-raw-zstd-65536": (65536, (1, 7, 33, 64, 2, 13, 127, 255), ("raw", "zstd")*4),
}
REGIMES = ("q1-early", "q1-tail", "q6-mixed", "q64-mixed")
SEQUENCES = (("released", "native", "fused", "fused", "native", "released"),
             ("fused", "native", "released", "released", "native", "fused"))
RULE = {"material_relative": 0.05, "material_absolute_ms": 3.0,
        "transferred_speedup": 1.2, "rss_delta_bytes": 8*1024*1024}
PHASES = ("open", "ranges", "close")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def expected_fixture(family, regime):
    n, lengths, codecs = EXPECTED_PROFILES[family]
    pieces = [bytes(((19*i+31*j) % 251)+1 for j in range(sz))
              for i,sz in enumerate(lengths)]
    logical = b"".join(pieces[(7*i+i//257+(i//4096)*3) % len(pieces)] for i in range(n))
    total = len(logical)
    if regime == "q1-early":
        starts = [0]
    elif regime == "q1-tail":
        starts = [max(0,total-16)]
    else:
        starts = [max(0,total-17),0,total//2,total//5,max(0,total-1),total//3]
        if regime == "q64-mixed":
            rng = random.Random(241500+n)
            starts += [rng.randrange(total+1) for _ in range(58)]
    ranges = [[start, min(16,total-start),
               logical[start:start+min(16,total-start)].hex()] for start in starts]
    return n,lengths,codecs,logical,ranges


def analyze(raw, directory):
    assert raw["schema"] == "j24c15-source-exact-heldout-v1"
    assert raw["sources"] == EXPECTED_SOURCES
    assert raw["comparison_rule"] == RULE
    assert raw["scope"] == "held-out signed RAW/RAW-Zstd S_CHUNKS; Ubuntu Python 3.11 only; no promotion"
    assert len(bytes.fromhex(raw["evidence_head"])) == 20
    fixture_rows = raw["profiles"]
    assert len(fixture_rows) == len(EXPECTED_PROFILES)*len(REGIMES)
    fixtures = {}
    for s in fixture_rows:
        key=(s["family"],s["regime"])
        assert key not in fixtures
        assert s["family"] in EXPECTED_PROFILES and s["regime"] in REGIMES
        n,lengths,codecs,logical,ranges=expected_fixture(*key)
        assert s["count"] == n
        assert s["owners"] == len(lengths)
        assert s["owner_lengths"] == list(lengths)
        assert s["codec_types"] == list(codecs)
        assert s["logical_bytes"] == len(logical)
        assert s["logical_sha256"] == digest(logical)
        assert s["ranges"] == ranges
        assert s["archive"] == s["family"]+".cmpct"
        wire=(directory/s["archive"]).read_bytes()
        assert len(wire) == s["wire_bytes"]
        assert digest(wire) == s["wire_sha256"]
        manifest = json.loads((directory/(s["family"]+"-"+s["regime"]+".json")).read_text())
        assert manifest == s
        fixtures[key]=s
    assert set(fixtures) == {(fam,reg) for fam in EXPECTED_PROFILES for reg in REGIMES}
    workers = raw["workers"]
    assert len(workers) == len(fixtures)*2*6
    counted, seen = Counter(),set()
    for w in workers:
        key=(w["family"],w["regime"])
        assert key in fixtures
        spec=fixtures[key]
        assert w["count"] == spec["count"]
        arm=w["arm"];cycle=w["cycle"];slot=w["slot"]
        assert arm in EXPECTED_SOURCES and cycle in (0,1) and slot in range(6)
        assert arm == SEQUENCES[cycle][slot]
        identity=(*key,cycle,slot)
        assert identity not in seen
        seen.add(identity)
        counted[(*key,arm)] += 1
        source=w["source"]
        assert source["arm"] == arm
        assert source["reader_blob"] == EXPECTED_SOURCES[arm]["reader_blob"]
        assert source["source_commit"] == EXPECTED_SOURCES[arm]["commit"]
        assert len(bytes.fromhex(source["reader_sha256"])) == 32
        assert "site-packages" in source["reader_path"] or "dist-packages" in source["reader_path"]
        assert w["wire_sha256"] == spec["wire_sha256"]
        assert w["native_probe_calls"] == (0 if arm=="released" else 1)
        assert type(w["process_wall_ns"]) is int and w["process_wall_ns"] > 0
        assert w["rss_highwater_bytes"] is None or (
            type(w["rss_highwater_bytes"]) is int and w["rss_highwater_bytes"] > 0)
        assert len(w["samples"]) == 2
        answer=digest(b"".join(bytes.fromhex(v[2]) for v in spec["ranges"]))
        for sample in w["samples"]:
            assert sample["answer_sha256"] == answer
            for metric in ("cpu","wall"):
                elapsed=sample["session_"+metric+"_ns"]
                assert type(elapsed) is int and elapsed > 0
                phase_ns=[sample[k+"_"+metric+"_ns"] for k in PHASES]
                assert all(type(v) is int and v >= 0 for v in phase_ns)
                assert elapsed == sum(phase_ns)
    assert all(counted[(*k,arm)] == 4 for k in fixtures for arm in EXPECTED_SOURCES)
    budget=raw["budget"]
    assert budget["original_cap"] == 65536
    assert budget["test_cap"] == 4
    assert budget["retained"] == {"alpha.bin": 4}
    budget_file=(directory/"multi-member-budget.cmpct").read_bytes()
    assert digest(budget_file) == budget["wire_sha256"]
    expected_members=(("alpha.bin",b"abcd"*1024),
                      ("beta.bin",b"1234567"*1024),
                      ("gamma.bin",(b"abcd"+b"1234567")*512))
    assert budget["files"] == [
        {"name":name,"size":len(payload),"sha256":digest(payload)}
        for name,payload in expected_members
    ]
    rows=[]
    positives=0
    deficits=[]
    for family in EXPECTED_PROFILES:
        for regime in REGIMES:
            by={}
            for arm in EXPECTED_SOURCES:
                group=[w for w in workers
                       if (w["family"],w["regime"],w["arm"]) == (family,regime,arm)]
                by[arm]={}
                for key in ("session_wall","session_cpu","open_wall","ranges_wall",
                            "ranges_cpu","process_wall"):
                    field=key+"_ns"
                    if key=="process_wall":
                        numbers=[w[field] for w in group]
                    else:
                        numbers=[statistics.median(s[field] for s in w["samples"])
                                 for w in group]
                    by[arm][key+"_ms"]=statistics.median(numbers)/1e6
                rss=[w["rss_highwater_bytes"] for w in group]
                by[arm]["rss_bytes"]=max(rss) if all(x is not None for x in rss) else None
            published,native,fused=(by[x] for x in ("released","native","fused"))
            wall_r=fused["session_wall_ms"]/published["session_wall_ms"]
            cpu_r=fused["session_cpu_ms"]/published["session_cpu_ms"]
            wall_ms=fused["session_wall_ms"]-published["session_wall_ms"]
            cpu_ms=fused["session_cpu_ms"]-published["session_cpu_ms"]
            material_wall=(wall_r >= 1+RULE["material_relative"] and
                           wall_ms >= RULE["material_absolute_ms"])
            material_cpu=(cpu_r >= 1+RULE["material_relative"] and
                          cpu_ms >= RULE["material_absolute_ms"])
            p_rss,f_rss=published["rss_bytes"],fused["rss_bytes"]
            delta_rss=None if p_rss is None or f_rss is None else f_rss-p_rss
            debt_rss=(delta_rss is not None and delta_rss>RULE["rss_delta_bytes"])
            win=(regime.startswith("q6") or regime.startswith("q64")) and (
                wall_r<=1/RULE["transferred_speedup"] and
                cpu_r<=1/RULE["transferred_speedup"] and not debt_rss)
            if win: positives+=1
            if material_wall or material_cpu: deficits.append((family,regime))
            rows.append({"family":family,"regime":regime,"arms":by,
                         "fused_over_released_wall":wall_r,
                         "fused_over_released_cpu":cpu_r,
                         "fused_minus_released_wall_ms":wall_ms,
                         "fused_minus_released_cpu_ms":cpu_ms,
                         "fused_minus_released_rss_bytes":delta_rss,
                         "material_wall_debt":material_wall,
                         "material_cpu_debt":material_cpu,
                         "rss_caution":debt_rss,
                         "transferred_released_floor_win":bool(win)})
    if deficits:
        decision="HELDOUT_RELEASED_FLOOR_DEBT_REQUIRES_REHABILITATION"
    elif positives == 6:
        decision="HELDOUT_SIX_OF_SIX_TRANSFER_RESEARCH"
    elif positives:
        decision="HELDOUT_SCOPED_TRANSFER_RESEARCH"
    else:
        decision="HELDOUT_NO_MATERIAL_TRANSFER"
    return {"schema":"j24c15-independent-referee-v1",
            "evidence_head":raw["evidence_head"],"decision":decision,
            "source":EXPECTED_SOURCES,"workers":len(workers),
            "sessions":len(workers)*2,"positive_q6q64_cells":positives,
            "heldout_floor_debts":deficits,
            "budget_correctness":"PASS (synthetically reduced cap only)",
            "rows":rows,
            "limits":["only Ubuntu Python3.11; no complete release matrix",
                      "published Reader weaker hostile-input semantics",
                      "resource-bound test cap is synthetic, not default cap exhaustion"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    raw=json.loads(x.input.read_text())
    root=x.input.parent/"fixtures"
    verdict=analyze(raw,root)
    for label in ("source","wire","missing-worker","answer","threshold","budget"):
        fake=copy.deepcopy(raw)
        if label=="source":
            fake["workers"][0]["source"]["reader_blob"]="00"*20
        elif label=="wire":
            fake["profiles"][0]["wire_sha256"]="00"*32
        elif label=="missing-worker":
            fake["workers"].pop()
        elif label=="answer":
            fake["workers"][0]["samples"][0]["answer_sha256"]="00"*32
        elif label=="threshold":
            fake["comparison_rule"]["material_relative"]=99.0
        else:
            fake["budget"]["retained"]={"beta.bin":4}
        try:
            analyze(fake,root)
        except (AssertionError,KeyError,TypeError,ValueError,FileNotFoundError):
            pass
        else:
            raise AssertionError("forged receipt accepted: "+label)
    x.output.write_text(json.dumps(verdict,indent=2,sort_keys=True)+"\n")
    print("J24C15_SECOND_ROOT_PASS workers="+str(verdict["workers"]))
    print("J24C15_DECISION="+verdict["decision"])
    for row in verdict["rows"]:
        print(f"J24C15_CELL {row['family']} {row['regime']} "
              f"wall={row['fused_over_released_wall']:.3f}x "
              f"cpu={row['fused_over_released_cpu']:.3f}x "
              f"debt={row['material_wall_debt'] or row['material_cpu_debt']}")


if __name__=="__main__":
    main()
