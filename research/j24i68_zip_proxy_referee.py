#!/usr/bin/env python3
"""Research-only ZIP co-drift diagnostic for three source-identical r24 ABBA runs.
No import of CMPCT and no modification of its frozen release evaluator.
Usage: python research/j24i68_zip_proxy_referee.py J24I65_provider_ABBA_evidence_bundle.zip
"""
import argparse
import hashlib
import io
import json
import math
import statistics
import zipfile

EXPECTED = {
    "cmpct_p835_firstfailure_12981944713.zip": ("cf20ded12b7e5b6348a9fc272cadc7565dc4e76982e1760fce674b1b2e7e1598", "fe7669f7f1a07720187219200e24a972fa650f6b", "09e38915b79a83964cc816d5130251b3e748121e"),
    "cmpct_source_identical_835_12986955317.zip": ("aedd2d6150746f5c6bcef4b0e8a41af5ed5f5c9f9fbb0c3ba78b54da59bbd1ee", "fe7669f7f1a07720187219200e24a972fa650f6b", "09e38915b79a83964cc816d5130251b3e748121e"),
    "cmpct_source_identical_837_12988780098.zip": ("1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b", "09e38915b79a83964cc816d5130251b3e748121e", "1ea579c5837d3b783614f423c423a121878dc0ca"),
}
TREE = "b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f"
CORPORA = ("tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined")
MODES = ("library", "cli")
FIELDS = ("create_s_median", "extract_s_median")

def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [None] * len(values)
    k = 0
    while k < len(order):
        end = k + 1
        while end < len(order) and values[order[end]] == values[order[k]]:
            end += 1
        for i in range(k, end):
            result[order[i]] = (k + 1 + end) / 2
        k = end
    return result

def spearman(a, b):
    if len(a) < 3:
        return None
    r, s = ranks(a), ranks(b)
    ra, rb = statistics.fmean(r), statistics.fmean(s)
    va, vb = sum((x-ra)**2 for x in r), sum((x-rb)**2 for x in s)
    return sum((x-ra)*(y-rb) for x,y in zip(r,s)) / math.sqrt(va*vb) if va and vb else None

def source_rows(raw, name):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        sha, base_head, cand_head = EXPECTED[name]
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError("original provider ZIP digest differs: "+name)
        d = {n: json.loads(z.read(n)) for n in ("base-a.json","base-b.json","candidate-a.json","candidate-b.json")}
        corpus = json.loads(z.read("corpus.json"))
        if corpus["tree_sha256"] != TREE:
            raise ValueError("corpus identity changed: "+name)
        if json.loads(z.read("base-native.json"))["source_commit"] != base_head:
            raise ValueError("base source HEAD changed: "+name)
        proof = json.loads(z.read("candidate.json"))
        if (proof["source_commit"],proof["comparison_base_commit"]) != (cand_head,base_head):
            raise ValueError("candidate Git source HEAD changed: "+name)
        for o in d.values():
            if set(o["corpora"]) != set(CORPORA):
                raise ValueError("corpus membership changed")
        rows = []
        for corpus_name in CORPORA:
            for mode in MODES:
                for field in FIELDS:
                    snapshots = {
                        (side,block): d[side+"-"+block+".json"]["corpora"][corpus_name][mode]
                        for side in ("base","candidate") for block in ("a","b")
                    }
                    cmpct_bytes = {int(s["cmpct"]["bytes"]) for s in snapshots.values()}
                    if len(cmpct_bytes)!=1:
                        raise ValueError("deterministic CMPCT byte parity failed")
                    row = {"corpus":corpus_name,"mode":mode,"field":field}
                    for engine in ("cmpct","zip"):
                        val = lambda side,block: 1000*float(snapshots[(side,block)][engine][field])
                        base = statistics.median((val("base","a"),val("base","b")))
                        candidate = statistics.median((val("candidate","a"),val("candidate","b")))
                        row[engine+"_delta_ms"]=candidate-base
                        row[engine+"_delta_pct"]=100*(candidate/base-1)
                        row[engine+"_a_delta_ms"]=val("candidate","a")-val("base","a")
                        row[engine+"_b_delta_ms"]=val("candidate","b")-val("base","b")
                    row["official_cmpct_red"]=row["cmpct_delta_pct"]>5 and row["cmpct_delta_ms"]>3
                    rows.append(row)
        return rows

def verdict(rows):
    selected = [r for r in rows if abs(r["cmpct_delta_ms"])>1 and abs(r["zip_delta_ms"])>1]
    agree=sum((r["cmpct_delta_ms"]>0)==(r["zip_delta_ms"]>0) for r in selected)
    rho=spearman([r["cmpct_delta_ms"] for r in rows], [r["zip_delta_ms"] for r in rows])
    red = [r for r in rows if r["official_cmpct_red"]]
    return {
        "cell_count":len(rows),
        "both_above_1ms":len(selected),
        "same_direction_count":agree,
        "same_direction_fraction":agree/len(selected) if selected else None,
        "spearman_ms":rho,
        "preregistered_h1_survives":bool(selected) and agree/len(selected)>=.75 and rho is not None and rho>=.5,
        "official_cmpct_reds":[{"corpus":r["corpus"],"mode":r["mode"],"field":r["field"],"cmpct_delta_ms":r["cmpct_delta_ms"],"zip_delta_ms":r["zip_delta_ms"]} for r in red],
        "cmpct_a_b_delta_sign_flips":sum(r["cmpct_a_delta_ms"]*r["cmpct_b_delta_ms"]<0 for r in rows),
        "zip_a_b_delta_sign_flips":sum(r["zip_a_delta_ms"]*r["zip_b_delta_ms"]<0 for r in rows),
        "leave_one_corpus_out_rho":{c:spearman([r["cmpct_delta_ms"] for r in rows if r["corpus"]!=c],[r["zip_delta_ms"] for r in rows if r["corpus"]!=c]) for c in CORPORA},
    }

def analyze(bundle):
    results={}
    with zipfile.ZipFile(bundle) as z:
        for n in EXPECTED:
            raw=z.read(n)
            rows=source_rows(raw,n)
            results[n]={"provider_zip_sha256":EXPECTED[n][0],"verdict":verdict(rows),"all_rows":rows}
    return {"schema":"j24i68-zip-codrift-v1","results":results,"all_three_h1_survive":all(r["verdict"]["preregistered_h1_survives"] for r in results.values()),"claim_boundary":"research-only; original full-product threshold unchanged; source-identical scope inherited from prior independent source-blob audit; correlated cells are not independent statistical trials"}

def selftest():
    assert ranks([9,2,2,4])==[4,1.5,1.5,3]
    assert abs(spearman([1,2,3],[3,2,1])+1)<1e-12
    assert abs(spearman([1,2,3],[1,2,3])-1)<1e-12

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("bundle",help="J24I65 full provider artifact bundle ZIP")
    p.add_argument("--output")
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    result=json.dumps(analyze(a.bundle),indent=2,sort_keys=True)+"\n"
    if a.output:
        with open(a.output,"w",encoding="utf-8") as f:f.write(result)
    else:
        print(result,end="")
