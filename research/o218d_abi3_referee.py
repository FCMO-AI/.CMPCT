#!/usr/bin/env python3
"""O218d: independent JSON/physical wheel and same-host cross-minor receipt referee."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile

PAIRS = ((65536, 1), (262144, 1), (65536, 256))

def check(a, b, build, wheel_dir):
    wheel_list = list(Path(wheel_dir).glob("*.whl"))
    assert len(wheel_list) == 1
    wheel = wheel_list[0]
    data = wheel.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    assert actual_sha == build["sha256"]
    assert len(data) == build["bytes"] <= 250000
    assert build["wall_ms"] > 0 and build["wall_ms"] < 60000
    assert "cp311-abi3-" in wheel.name
    with zipfile.ZipFile(wheel) as z:
        names = [n for n in z.namelist() if n.endswith((".so", ".pyd"))]
        assert len(names) == 1
        binary_sha = hashlib.sha256(z.read(names[0])).hexdigest()
    assert a["host"]["python"] == [3, 11] and b["host"]["python"] == [3, 13]
    assert a["host"]["os"] == b["host"]["os"]
    assert a["source"] == b["source"] == {
        "parent": "a2d69c89769868fe4a454ce0556f6a19806f0647",
        "pre_reg": "f96a54d058bdac24a6216ec66f47086a7ecfa1ec"}
    for item in (a, b):
        assert item["tier"] == "abi3_wheel_delivery_and_strict_predicate_micro_only"
        assert item["wheel"]["name"] == wheel.name
        assert item["wheel"]["sha256"] == actual_sha
        assert item["wheel"]["bytes"] == len(data)
        assert item["wheel"]["binary_sha256"] == binary_sha
        assert item["semantics"]["cases"] == 5000
        assert item["semantics"]["accepted"] + item["semantics"]["rejected"] == 5000
        assert len(item["semantics"]["decision_sha256"]) == 64
        assert [(r["count"], r["owners"]) for r in item["benchmarks"]] == list(PAIRS)
        for row in item["benchmarks"]:
            raw = row["raw_wall_ns"]
            assert set(raw) == {"native", "python"}
            assert len(raw["native"]) == len(raw["python"]) == 24
            assert all(type(x) is int and x > 0 for mode in raw for x in raw[mode])
            p = statistics.median(raw["python"]) / 1e6
            n = statistics.median(raw["native"]) / 1e6
            assert math.isclose(p, row["python_median_wall_ms"], rel_tol=1e-12)
            assert math.isclose(n, row["native_median_wall_ms"], rel_tol=1e-12)
            assert math.isclose(p/n, row["python_over_native"], rel_tol=1e-12)
            if row["owners"] == 1:
                assert p/n >= 1.5
    assert a["semantics"] == b["semantics"], "cross-minor semantics drift"
    return {"host": a["host"]["os"], "wheel_sha256": actual_sha,
            "build_wall_ms": build["wall_ms"], "wheel_bytes": len(data),
            "semantics_sha256": a["semantics"]["decision_sha256"],
            "python_311": [{k:r[k] for k in ("count","owners","python_over_native")} for r in a["benchmarks"]],
            "python_313": [{k:r[k] for k in ("count","owners","python_over_native")} for r in b["benchmarks"]],
            "decision": "ABI3_WHEEL_MICRO_ROUTE_VIABLE"}

def tamper(a,b,build,wheel_dir):
    probes=[]
    t=copy.deepcopy(a);t["benchmarks"][0]["python_over_native"]*=2;probes.append((t,b,build))
    t=copy.deepcopy(b);t["semantics"]["decision_sha256"]="0"*64;probes.append((a,t,build))
    t=copy.deepcopy(a);t["benchmarks"][1]["raw_wall_ns"]["native"].pop();probes.append((t,b,build))
    t=copy.deepcopy(build);t["sha256"]="0"*64;probes.append((a,b,t))
    t=copy.deepcopy(a);t["host"]["python"]=[3,12];probes.append((t,b,build))
    for args in probes:
        try:check(*args,wheel_dir)
        except (AssertionError,KeyError,TypeError,ValueError,ZeroDivisionError):continue
        raise AssertionError("forged evidence accepted")
    return len(probes)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("evidence",type=Path)
    p.add_argument("--wheel-dir",type=Path,required=True)
    args=p.parse_args()
    ev=args.evidence
    a=json.loads((ev/"py311.json").read_text())
    b=json.loads((ev/"py313.json").read_text())
    build=json.loads((ev/"build.json").read_text())
    result=check(a,b,build,args.wheel_dir)
    result["forgeries_rejected"]=tamper(a,b,build,args.wheel_dir)
    (ev/"referee.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("O218D_ABI3_INDEPENDENT_REFEREE_PASS",json.dumps(result,sort_keys=True))
