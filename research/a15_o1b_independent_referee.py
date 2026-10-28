#!/usr/bin/env python3
"""Independent receipt audit for A15-O1b in-process CPU/wall samples."""
import argparse
import copy
import hashlib
import json
import statistics
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(root,r):
    parent_bytes=(root/"result.json").read_bytes()
    parent=json.loads(parent_bytes)
    if r.get("schema")!="a15-o1b-inprocess-inversion-v1" or r.get("claim_level")!="scientific_inprocess_component_only":
        raise ValueError("schema")
    if r.get("source_receipt_sha256")!=sha(parent_bytes):
        raise ValueError("parent court not bound")
    rows=r.get("cases")
    if not isinstance(rows,list) or len(rows)!=6:
        raise ValueError("rows")
    prev={x["label"]:x for x in parent["cases"]}
    if {x["label"] for x in rows}!=set(prev):
        raise ValueError("cases omitted")
    for row in rows:
        original=prev[row["label"]]
        folder=root/row["label"]
        for field,expected in (("source_sha256",original["source_sha256"]),
                               ("a15_sha256",original["a15_sha256"]),
                               ("ref_sha256",original["chunkref_sha256"])):
            if row[field]!=expected:
                raise ValueError("mismatched signed identity")
        if sha((folder/"source.bin").read_bytes())!=row["source_sha256"]:
            raise ValueError("source file differs")
        if sha((folder/"a15.bin").read_bytes())!=row["a15_sha256"]:
            raise ValueError("a15 file differs")
        if sha((folder/"chunkref.bin").read_bytes())!=row["ref_sha256"]:
            raise ValueError("ref file differs")
        observations=row["raw"]
        if len(observations)!=144:
            raise ValueError("wrong number of observations")
        for target in (0,17,31):
            for rep in range(12):
                cells=[x for x in observations if x["target"]==target and x["repetition"]==rep]
                expected=["a15","ref","ref","a15"] if rep%2==0 else ["ref","a15","a15","ref"]
                if [x["arm"] for x in cells]!=expected:
                    raise ValueError("ABBA violation")
                truth=(folder/"source.bin").read_bytes()[target*65536:(target+1)*65536]
                if any(x["sha256"]!=sha(truth) or x["wall_ns"]<0 or x["cpu_ns"]<0 for x in cells):
                    raise ValueError("raw timing or member hash")
        for arm in ("a15","ref"):
            samples=[x for x in observations if x["arm"]==arm]
            stats=row["arms"][arm]
            if stats["count"]!=72:
                raise ValueError("sample count")
            if stats["wall_median_ns"]!=statistics.median(x["wall_ns"] for x in samples) or stats["cpu_median_ns"]!=statistics.median(x["cpu_ns"] for x in samples):
                raise ValueError("forged median")
        if abs(row["ref_over_a15_wall"] - row["arms"]["ref"]["wall_median_ns"]/row["arms"]["a15"]["wall_median_ns"])>1e-12:
            raise ValueError("wall ratio")
        if abs(row["ref_over_a15_cpu"] - row["arms"]["ref"]["cpu_median_ns"]/row["arms"]["a15"]["cpu_median_ns"])>1e-12:
            raise ValueError("CPU ratio")
    verdict=all(x["ref_over_a15_wall"]>=1.5 and x["ref_over_a15_cpu"]>=1.5 for x in rows)
    if verdict is not r["prediction_met"]:
        raise ValueError("verdict")
    return verdict

def main(root):
    receipt=json.loads((root/"inprocess.json").read_text())
    verdict=verify(root,receipt)
    rejected=0
    def falsify(f):
        nonlocal rejected
        clone=copy.deepcopy(receipt)
        f(clone)
        try:verify(root,clone)
        except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError):
            rejected+=1
            return
        raise AssertionError("receipt falsification accepted")
    falsify(lambda x:x["cases"][0].update({"source_sha256":"0"*64}))
    falsify(lambda x:x["cases"][0].update({"ref_sha256":"0"*64}))
    falsify(lambda x:x["cases"][0]["arms"]["ref"].update({"wall_median_ns":1}))
    falsify(lambda x:x["cases"][0]["arms"]["a15"].update({"count":1}))
    falsify(lambda x:x["cases"][0]["raw"][0].update({"sha256":"0"*64}))
    falsify(lambda x:x.update({"prediction_met":not verdict}))
    data={"schema":"a15-o1b-independent-audit-v1","cases":len(receipt["cases"]),
          "observations":sum(len(x["raw"]) for x in receipt["cases"]),
          "forged_rejected":rejected,"prediction_met":verdict,
          "source_sha256":sha((root/"inprocess.json").read_bytes()),"verdict":"PASS"}
    (root/"inprocess_referee.json").write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print(json.dumps(data,sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    main(p.parse_args().root)
