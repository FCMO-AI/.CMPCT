#!/usr/bin/env python3
"""Independent receipt audit of O219. No dependency on the O219 bench implementation."""
import argparse
import hashlib
import json
import math
import statistics
import random
import msgpack
from pathlib import Path

EXPECTED = {(65536,1),(65536,65536),(262144,1),(262144,262144)}
METHODS = {"strong_py","o216_like","native"}
FIELDS = ("decode_wall_ns","decode_cpu_ns","check_wall_ns","check_cpu_ns",
          "total_wall_ns","total_cpu_ns")

def audit(path):
    d = json.loads(Path(path).read_text())
    checks = 0
    def require(ok, why):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(why)
    require(d["schema"]=="O219_index_decode_v1", "schema")
    require(d["product_credit"] is False, "product credit")
    require(d["source_pr"]==577, "source PR")
    require(d["base_sha"]=="6372e780be99a31f5ea21b7a3c74fde92cf0bc45", "base")
    require(d["prereg_commit"]=="c76e0b2f5b54ecbaffafa0adf0e14759b2c52a37", "prereg")
    require(d["tier"]=="same-wire in-process decode+admission oracle", "tier")
    require(8 <= d["repeats"] <= 100, "repeats")
    require(len(d["cases"])==4, "cases")
    require({(c["n"],c["unique"]) for c in d["cases"]}==EXPECTED,"profiles")
    for c in d["cases"]:
        require(c["wire_bytes"]>0, "nonempty wire")
        require(len(c["wire_sha256"])==64 and all(ch in "0123456789abcdef" for ch in c["wire_sha256"]), "digest")
        require(c["declared"]>=0,"declared")
        # Independent fixture reconstruction, not a call into benchmark code.
        n,u=c["n"],c["unique"]
        rng=random.Random(218+n+u)
        owners=min(n,u)
        rebuilt_blobs=[[i*37,17+i%7,33,0,0] for i in range(owners)]
        rebuilt_refs=([0]*n if u==1 else list(range(n)) if u==n
                      else [rng.randrange(owners) for _ in range(n)])
        rebuilt=msgpack.packb({"r":rebuilt_refs,"b":rebuilt_blobs},use_bin_type=True)
        require(c["wire_bytes"]==len(rebuilt),"wire length versus independent fixture")
        require(c["wire_sha256"]==hashlib.sha256(rebuilt).hexdigest(),
                "wire SHA versus independent fixture")
        require(c["declared"]==sum(rebuilt_blobs[i][1] for i in rebuilt_refs),
                "logical size versus independent fixture")
    samples = d["samples"]
    require(len(samples)==4*3*d["repeats"], "sample count")
    buckets = {}
    for row in samples:
        key = (row["n"],row["unique"],row["method"])
        require((row["n"],row["unique"]) in EXPECTED and row["method"] in METHODS,"unknown arm")
        require(type(row["repeat"]) is int and 0<=row["repeat"]<d["repeats"],"repeat")
        require(all(type(row[f]) is int and row[f]>=0 for f in FIELDS), "measurements")
        # Perf/cpu clocks are sampled in different instants; total must telescope exactly.
        require(row["total_wall_ns"]==row["decode_wall_ns"]+row["check_wall_ns"],"wall sum")
        require(row["total_cpu_ns"]==row["decode_cpu_ns"]+row["check_cpu_ns"],"CPU sum")
        buckets.setdefault(key,[]).append(row)
    for n, u in EXPECTED:
        for name in METHODS:
            rows=buckets[(n,u,name)]
            require(len(rows)==d["repeats"],"arm missing")
            require({r["repeat"] for r in rows}==set(range(d["repeats"])),"repeat missing/dupe")
    require(len(d["summary"])==4,"summary length")
    decisions=[]
    for row in d["summary"]:
        n,u=row["n"],row["unique"]
        require((n,u) in EXPECTED,"summary profile")
        med=row["methods"]
        require(set(med)==METHODS,"summary methods")
        for name in METHODS:
            sample_rows=buckets[(n,u,name)]
            for field in ("total_wall_ns","total_cpu_ns","decode_wall_ns","check_wall_ns"):
                observed=statistics.median(s[field] for s in sample_rows)/1e6
                require(math.isclose(med[name][field],observed,rel_tol=1e-12,abs_tol=1e-9),
                        "aggregate mismatch " + str((n,u,name,field)))
        ratio=med["o216_like"]["total_wall_ns"]/med["native"]["total_wall_ns"]
        frac=med["o216_like"]["decode_wall_ns"]/med["o216_like"]["total_wall_ns"]
        require(math.isclose(row["total_wall_ratio_py_over_native"],ratio,rel_tol=1e-12),"ratio")
        require(math.isclose(row["baseline_decode_fraction"],frac,rel_tol=1e-12),"fraction")
        decisions.append(ratio >=2)
    require(d["decision"]==("WHOLE_INDEX_ORACLE_AT_LEAST_2X" if all(decisions)
                           else "WHOLE_INDEX_ORACLE_BELOW_2X"),"decision mismatch")
    return {"verdict":"PASS","checks":checks,"sample_count":len(samples),
            "decision":d["decision"],
            "evidence_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest()}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output")
    args=p.parse_args()
    result=audit(args.input)
    if args.output:
        Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps(result,sort_keys=True))
