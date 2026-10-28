#!/usr/bin/env python3
"""J24C10 independent raw receipt arithmetic referee (not product execution)."""
from __future__ import annotations
import argparse, hashlib, json, statistics
from pathlib import Path

def check(payload):
    assert payload["schema"] == "j24c10-installed-range-v1"
    assert payload["product_release_credit"] is False
    rows = payload["records"]
    assert len(rows) == 2*3*2*2*payload["repetitions"], len(rows)
    summaries={}
    for n in (65536,262144):
        for family in ("one","owners256","ragged"):
            for pos in ("early","late"):
                key=f"{n}/{family}/{pos}"
                arms={}
                for arm in ("strict","witness"):
                    a=[x for x in rows if x["n"]==n and x["family"]==family
                       and x["position"]==pos and x["arm"]==arm]
                    assert len(a)==payload["repetitions"], (key,arm,len(a))
                    assert set(x["repeat"] for x in a)==set(range(payload["repetitions"]))
                    assert len(set(x["source_wire_sha256"] for x in a))==1
                    assert all(x["wire_sha256"]==x["source_wire_sha256"] for x in a)
                    assert all(x["result_sha256"]==a[0]["result_sha256"] for x in a)
                    assert all(x["native_installed"] is True for x in a)
                    assert all(x["open_wall_ns"]>0 and x["read_wall_ns"]>0
                               and x["total_wall_ns"]>=x["open_wall_ns"]+x["read_wall_ns"]
                               and x["process_wall_ns"]>=x["total_wall_ns"] for x in a)
                    assert all(x["open_cpu_ns"]>=0 and x["read_cpu_ns"]>=0
                               and x["total_cpu_ns"]>=x["open_cpu_ns"]+x["read_cpu_ns"] for x in a)
                    arms[arm]=a
                assert len(set(x["source_wire_sha256"] for a in arms.values() for x in a))==1
                assert len(set(x["result_sha256"] for a in arms.values() for x in a))==1
                if family!="ragged" and pos=="late":
                    assert all(x["proof_cache"]==4 for x in arms["witness"])
                sv=statistics.median(x["read_wall_ns"] for x in arms["strict"])
                wv=statistics.median(x["read_wall_ns"] for x in arms["witness"])
                ratio=sv/wv
                result=payload["summary"][key]
                assert result["strict_median_read_ns"]==sv
                assert result["witness_median_read_ns"]==wv
                assert abs(result["ratio_strict_over_witness"]-ratio)<1e-10
                summaries[key]=ratio
    decision=all(summaries[f"{n}/{family}/late"]>=2.0
                 for n in (65536,262144) for family in ("one","owners256"))
    assert payload["late_four_profile_wall_gate"] is decision
    return {"status":"PASS_RECEIPT_ARITHMETIC",
            "scientific_wall_gate":"PASS" if decision else "FAIL",
            "samples":len(rows),"groups":len(summaries),
            "min_late_ratio":min(summaries[f"{n}/{family}/late"]
                    for n in (65536,262144) for family in ("one","owners256")),
            "release_credit":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    decision=check(data)
    Path(args.output).write_text(json.dumps(decision,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(decision,sort_keys=True))
    clone=json.loads(json.dumps(data))
    clone["records"][0]["result_sha256"]="0"*64
    try:check(clone)
    except AssertionError:pass
    else:raise AssertionError("tampered receipt was accepted")

if __name__=="__main__":main()
