#!/usr/bin/env python3
"""Independent standard-library J24G11 receipt verifier. Never imports CMPCT.

Verifies *receipts* and derived decisions only, not an independent .cmpct decode.
"""
import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

def audit(x):
    assert x["release_credit"] == 0
    assert x["base"] == "da5552d4f74113de1887fdad9683b433bb6e6cf2"
    assert x["base_reader_blob"] == "0a8a7afa036cb4988b80836bcbe550c3b5d0bb40"
    assert x["candidate_reader_blob"] == "4bcedb059316171963d258fc93caaa49fec56f12"
    assert x["prereg"] == "70a54adeae8c77fe8693f84be6fbd0ab15b5b4f6"
    assert not x["total_RSS_bounded"]
    assert not x["per_chain_seen_chain_bounded"]
    assert not x["same_inode_mutation_supported"]
    assert len(x["first_party_archive_sha256"]) == 64
    assert len(x["logical_sha256"]) == 64
    a=x["oracle"]
    assert a["u64_extremes_exact"] and a["overflow_rejected"] and a["disk_cleanup"]
    assert a["disk_overflow_rows"] == 131074
    assert a["disk_overflow_bytes"] > 0
    assert a["packed_payload_bytes"] == a["positive"]*8
    assert a["packed_payload_bytes"] <= a["tier_cap_bytes"] == 1<<20
    count=0
    cases=x["cases"]
    assert set(cases)=={
        "alternating-16400","random-16400","uniform-ap-16400",
        "flat-1024","valid-first-party-rename"}
    for name, case in cases.items():
        assert case["case"]==name
        assert len(case["archive_sha256"])==64
        assert case["archive_bytes"]>0
        raw=case["raw"];assert set(raw)=={"parent","candidate","unbounded"}
        assert set(case["median_wall_ms"])==set(raw)
        for k, samples in raw.items():
            assert len(samples)>=3,(name,k,len(samples))
            assert len({v["physical_bytes"] for v in samples})==1
            assert samples[0]["physical_bytes"]==case["archive_bytes"]
            assert all(v["wall_ms"]>0 and v["cpu_ms"]>0 for v in samples)
            assert all(v["decoder_calls"]==case["calls"][k][i]
                       for i,v in enumerate(samples))
            assert abs(statistics.median(v["wall_ms"] for v in samples) -
                       case["median_wall_ms"][k]) < 1e-9
            assert abs(statistics.median(v["cpu_ms"] for v in samples) -
                       case["median_cpu_ms"][k]) < 1e-9
            count+=len(samples)
        expected=16401 if "16400" in name else (1025 if name=="flat-1024" else 2)
        assert all(all(v==expected for v in cs) for cs in case["calls"].values())
        assert abs(case["parent_to_candidate_wall"]-
                   case["median_wall_ms"]["parent"]/case["median_wall_ms"]["candidate"])<1e-9
        assert abs(case["unbounded_to_candidate_wall"]-
                   case["median_wall_ms"]["unbounded"]/case["median_wall_ms"]["candidate"])<1e-9
        if name in ("alternating-16400","random-16400"):
            proof=case["physical_proof"]
            assert proof["len"]==16400 and proof["packed_count"]==16400
            assert proof["packed_payload_bytes"]==16400*8
            assert not proof["sqlite_created"] and proof["path"] is None
    speed=all(cases[n]["parent_to_candidate_wall"]>=1.2 for n in
              ("alternating-16400","random-16400"))
    normal=all(cases[n]["median_wall_ms"]["candidate"] <=
               cases[n]["median_wall_ms"]["parent"]*1.25 for n in
               ("uniform-ap-16400","flat-1024","valid-first-party-rename"))
    assert x["speed_gate_met"] == speed and x["normal_gate_met"] == normal
    assert x["decision"] == ("PROMISING_NARROW_SEED" if speed and normal else "NARROW_OR_RETIRE")
    return {"independently_checked_raw_samples":count,
            "speed_gate":speed,"normal_gate":normal,"decision":x["decision"]}

def selftest(x):
    bad=[
        lambda z:z.__setitem__("release_credit",1),
        lambda z:z["cases"]["alternating-16400"]["median_wall_ms"].__setitem__("candidate",999),
        lambda z:z["cases"]["random-16400"]["calls"]["parent"].__setitem__(0,42),
        lambda z:z["cases"]["random-16400"]["physical_proof"].__setitem__("sqlite_created",True),
        lambda z:z["oracle"].__setitem__("packed_payload_bytes",3),
        lambda z:z.__setitem__("speed_gate_met",not z["speed_gate_met"]),
    ]
    for alter in bad:
        tamper=copy.deepcopy(x)
        alter(tamper)
        try:audit(tamper)
        except AssertionError:pass
        else:raise AssertionError("independent auditor accepted deliberate tamper")
    return len(bad)

def main():
    inp=Path(sys.argv[1] if len(sys.argv)>1 else "j24g11-artifacts/court.json")
    result=json.loads(inp.read_text())
    checks=audit(result)
    checks["tamper_cases_rejected"]=selftest(result)
    checks["scope"]="receipt consistency only; not an independent physical archive reconstruction"
    target=inp.with_name("audit.json")
    target.write_text(json.dumps(checks,indent=2,sort_keys=True)+"\n")
    print("J24G11_INDEPENDENT_RECEIPT_AUDIT="+json.dumps(checks,sort_keys=True))

if __name__=="__main__":main()
