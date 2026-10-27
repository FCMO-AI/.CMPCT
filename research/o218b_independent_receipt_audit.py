#!/usr/bin/env python3
"""O218b independent receipt referee. Scientific FAIL decision is a valid auditable result."""
import argparse, copy, hashlib, json, math, statistics
from collections import Counter
from pathlib import Path

METHODS=("original","fast","native","unguarded")
PROFILES=((1,1),(4096,1),(65536,1),(262144,1),(65536,256),(262144,256))
EXPECTED={"reader":"dbd4ac576a05a47eae97e1e40de89cf1de440516",
          "validator":"51c2849061f99a4afeddb7666956b24566ce7de0",
          "native_c":"a54f15181d9dbe667b9e8c9d52e927b09c80152f"}

def audit(x):
    assert x["tier"]=="whole_installed_reader_science_not_product"
    assert x["source"]==EXPECTED
    assert x["parent"]=="6372e780be99a31f5ea21b7a3c74fde92cf0bc45"
    assert x["prereg"]=="4ad8b7770693832940e766300bcac4a1ea4f0a84"
    assert x["native_binary_bytes"]>0 and len(x["compiler_argv"])>=6
    assert x["semantics"]["inherited_cases"]>=19
    assert len(x["semantics"]["named_cases"])>=24 and x["semantics"]["fuzz_cases"]==2500
    assert len(x["manifests"])==len(PROFILES)
    manifests={(m["count"],m["owners"]):m for m in x["manifests"]}
    assert set(manifests)==set(PROFILES)
    for m in manifests.values():
        assert len(bytes.fromhex(m["archive_sha256"]))==32
        assert len(bytes.fromhex(m["logical_sha256"]))==32
        assert m["archive_bytes"]>0
        assert m["full_read_verified"]==(m["count"]<=4096)
    rows=x["raw_workers"]
    assert len(rows)==len(PROFILES)*len(METHODS)*3*2
    observed=Counter((r["count"],r["owners"],r["mode"],r["cycle"]) for r in rows)
    assert set(observed)=={(n,o,m,c) for n,o in PROFILES for m in METHODS for c in range(3)}
    assert all(v==2 for v in observed.values())
    by_profile={}
    for r in rows:
        assert r["source"]==EXPECTED and isinstance(r["python"],str)
        assert len(r["samples"])==5
        for s in r["samples"]:
            assert isinstance(s["wall_ns"],int) and 0<s["wall_ns"]<120_000_000_000
            assert isinstance(s["cpu_ns"],int) and 0<s["cpu_ns"]<120_000_000_000
        assert r["vmhwm_bytes"] is None or r["vmhwm_bytes"]>0
    recomputed=[]
    for n,owners in PROFILES:
        ms={}
        for mode in METHODS:
            subset=[r for r in rows if (r["count"],r["owners"],r["mode"])==(n,owners,mode)]
            ms[mode]=statistics.median(statistics.median(s["wall_ns"] for s in r["samples"])
                                       for r in subset)/1e6
        recomputed.append({"count":n,"owners":owners,"median_wall_ms":ms,
           "fast_over_native":ms["fast"]/ms["native"],
           "native_over_unguarded":ms["native"]/ms["unguarded"],
           "native_extra_ms":ms["native"]-ms["unguarded"]})
    assert len(x["summary"])==len(recomputed)
    for want,got in zip(recomputed,x["summary"]):
        assert (want["count"],want["owners"])==(got["count"],got["owners"])
        for k in METHODS:
            assert math.isclose(want["median_wall_ms"][k],got["median_wall_ms"][k],rel_tol=1e-11)
        for k in ("fast_over_native","native_over_unguarded","native_extra_ms"):
            assert math.isclose(want[k],got[k],rel_tol=1e-11,abs_tol=1e-11)
    focus=[s for s in recomputed if s["owners"]==1 and s["count"] in (65536,262144)]
    passed=all(s["fast_over_native"]>=2.5 and s["native_over_unguarded"]<2 and
           s["native_extra_ms"]<=(5 if s["count"]==65536 else 20) for s in focus)
    decision="NATIVE_READER_ROUTE_WORTH_PRODUCTIZATION" if passed else "NATIVE_READER_ROUTE_INSUFFICIENT"
    assert x["decision"]==decision
    return {"decision":decision,"workers":len(rows),"timed_opens":len(rows)*5,
            "profiles":len(PROFILES),"native_binary_bytes":x["native_binary_bytes"],
            "summary":recomputed}

def tamper_court(x):
    attacks=[]
    a=copy.deepcopy(x);a["raw_workers"].pop();attacks.append(("missing_worker",a))
    a=copy.deepcopy(x);a["raw_workers"][0]["samples"][0]["wall_ns"]+=100000;attacks.append(("altered_timing",a))
    a=copy.deepcopy(x);a["source"]["native_c"]="0"*40;attacks.append(("false_source",a))
    a=copy.deepcopy(x);a["summary"][0]["median_wall_ms"]["native"]*=2;attacks.append(("false_median",a))
    a=copy.deepcopy(x);a["decision"]="NATIVE_READER_ROUTE_WORTH_PRODUCTIZATION" if x["decision"]!="NATIVE_READER_ROUTE_WORTH_PRODUCTIZATION" else "NATIVE_READER_ROUTE_INSUFFICIENT";attacks.append(("false_decision",a))
    for name,candidate in attacks:
        try:audit(candidate)
        except (AssertionError,ValueError,TypeError,KeyError,ZeroDivisionError):pass
        else:raise AssertionError("TAMPER_ACCEPTED "+name)
    return len(attacks)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("receipt");p.add_argument("--out")
    args=p.parse_args();data=Path(args.receipt).read_bytes();x=json.loads(data)
    result=audit(x);result["tamper_rejected"]=tamper_court(x)
    result["receipt_sha256"]=hashlib.sha256(data).hexdigest()
    if args.out:Path(args.out).write_text(json.dumps(result,sort_keys=True,indent=2))
    print("O218B_INDEPENDENT_AUDIT=PASS",json.dumps(result,sort_keys=True))
