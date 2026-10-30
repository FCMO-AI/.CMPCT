#!/usr/bin/env python3
"""Detached stdlib-only referee for J24I53 raw scientific evidence.

This parser never imports CMPCT. It recomputes from the original samples, and
contains deliberate forged-receipt refusal controls. It is not a release gate.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics


FRESH = "FRESH"
PREFIX = "PREFIX"
EXPECTED = (
    ("CONTEXT", (FRESH,PREFIX,PREFIX,FRESH)),
    ("CONTEXT", (PREFIX,FRESH,FRESH,PREFIX)),
    ("SHAM", (FRESH,FRESH,FRESH,FRESH)),
    ("SHAM", (FRESH,FRESH,FRESH,FRESH)),
)


def digest(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        while block:=f.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def same(a: float, b: float) -> None:
    if abs(float(a)-float(b)) > 1e-8 * max(1,abs(float(a)),abs(float(b))):
        raise AssertionError(("inconsistent summary",a,b))


def ratio(xs,ys):
    av,bv=statistics.median(xs),statistics.median(ys)
    assert av>0 and bv>0
    return {"a":av,"b":bv,"delta":bv-av,"ratio":bv/av}


def referee(x: dict, arc: Path, native: Path | None = None):
    assert x["schema"]=="cmpct-j24i53-context-court-v1"
    assert x["preregistered_at_commit"]=="95134f0470baac94df700c8088c04caabd05c883"
    assert len(x["evidence_head"])==40
    rec=x["observations"]
    assert len(rec)==16
    for idx,r in enumerate(rec):
        court,sequence=EXPECTED[idx//4]
        slot=idx%4
        assert r["court"]==court and r["group"]==idx//4
        assert r["slot"]==slot and r["sequence"]==list(sequence)
        assert r["context"]==sequence[slot]
        assert r["label"]==("A" if slot in (0,3) else "B")
        assert r["reps"]==3 and len(r["samples"])==3
        assert len(r["prefix"])==(3 if r["context"]=="PREFIX" else 0)
        if r["context"]=="PREFIX":
            assert [y["name"] for y in r["prefix"]]==["tiny","source","media"]
        for y in r["samples"]:
            assert y["wall_ms"]>0 and y["cpu_ms"]>0
            assert y["archive_bytes"]==x["physical_archive"]["size"]
            assert y["archive_sha256"]==x["physical_archive"]["sha256"]
        for k in ["wall","cpu"]:
            observed=statistics.median(s[k+"_ms"] for s in r["samples"])
            same(observed,r["median_"+k+"_ms"])
    assert len({r["native_sha256"] for r in rec})==1
    assert len({r["module"] for r in rec})==1
    assert all(r["native_sha256"]==x["native_sha256"] for r in rec)
    assert arc.stat().st_size==x["physical_archive"]["size"]
    assert digest(arc)==x["physical_archive"]["sha256"]
    if native is not None:
        assert digest(native)==x["native_sha256"]
    assert x["tree_fingerprint_before_after"]["file_count"]>3000
    assert set(x["binary_inputs"])=={"random16m.bin","pattern32m.bin"}
    assert x["binary_inputs"]["random16m.bin"]["size"]==16*1024*1024
    assert x["binary_inputs"]["pattern32m.bin"]["size"]==32*1024*1024
    treatment=rec[:8]
    sham=rec[8:]
    for i in (0,1):
        group=treatment[i*4:(i+1)*4]
        for k in ("wall","cpu"):
            a=[r["median_"+k+"_ms"] for r in group if r["context"]=="FRESH"]
            b=[r["median_"+k+"_ms"] for r in group if r["context"]=="PREFIX"]
            stats=ratio(a,b)
            saved=x["groups"][i][k]
            for src,dst in [("a","fresh_median"),("b","prefix_median"),
                            ("delta","delta_ms"),("ratio","ratio")]:
                same(stats[src],saved[dst])
    def samples(rows,k,pred):
        return [s[k+"_ms"] for r in rows if pred(r) for s in r["samples"]]
    values={}
    for k in ("wall","cpu"):
        z=ratio(samples(treatment,k,lambda r:r["context"]==FRESH),
                samples(treatment,k,lambda r:r["context"]==PREFIX))
        v=x["context_"+k]
        for src,dst in [("a","fresh_median"),("b","prefix_median"),
                        ("delta","delta_ms"),("ratio","ratio")]:
            same(z[src],v[dst])
        assert v["samples_each"]==12
        values["context_"+k]=z
        sh=ratio(samples(sham,k,lambda r:r["label"]=="A"),
                 samples(sham,k,lambda r:r["label"]=="B"))
        stored=x["sham_"+k]
        for src,dst in [("a","A_median"),("b","B_median"),
                        ("delta","delta_ms"),("ratio","ratio")]:
            same(sh[src],stored[dst])
        values["sham_"+k]=sh
    def material(z):
        return z["ratio"]>1.05 and z["delta"]>3
    def drift(z):
        return abs(z["delta"])>3 and (z["ratio"]>1.05 or z["ratio"]<1/1.05)
    sign=all(x["groups"][i][k]["delta_ms"]>0 for i in (0,1) for k in ("wall","cpu"))
    if drift(values["sham_wall"]) or drift(values["sham_cpu"]):
        decision="AMBIGUOUS_SHAM_DRIFT"
    elif material(values["context_wall"]) and material(values["context_cpu"]) and sign:
        decision="CONTEXT_COST_SUPPORTED"
    elif not sign or (material(values["context_wall"])!=material(values["context_cpu"])):
        decision="AMBIGUOUS_SIGN_OR_CPU"
    else:
        decision="CONTEXT_COST_NOT_REPRODUCED"
    assert x["decision"]==decision
    return {"evidence_head":x["evidence_head"],"decision":decision,
            "context_wall":values["context_wall"],"context_cpu":values["context_cpu"],
            "sham_wall":values["sham_wall"],"sham_cpu":values["sham_cpu"],
            "archive_sha256":digest(arc),"native_sha256":x["native_sha256"]}


def forge_test(original, arc, native):
    for mutation in ("sample_wall","sample_sha","source_native","control_label","decision","group_summary"):
        f=copy.deepcopy(original)
        if mutation=="sample_wall":
            f["observations"][0]["samples"][0]["wall_ms"]+=150
        elif mutation=="sample_sha":
            f["observations"][0]["samples"][0]["archive_sha256"]="0"*64
        elif mutation=="source_native":
            f["observations"][1]["native_sha256"]="a"*64
        elif mutation=="control_label":
            f["observations"][8]["label"]="B"
        elif mutation=="decision":
            f["decision"]="CONTEXT_COST_SUPPORTED" if f["decision"]!="CONTEXT_COST_SUPPORTED" else "CONTEXT_COST_NOT_REPRODUCED"
        else:
            f["groups"][0]["wall"]["delta_ms"]+=15
        try:
            referee(f,arc,native)
        except AssertionError:
            continue
        raise AssertionError(("failed to refuse forged evidence",mutation))
    return 6


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--result",type=Path,required=True)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--native",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    x=json.loads(a.result.read_text())
    report=referee(x,a.archive,a.native)
    report["forgeries_rejected"]=forge_test(x,a.archive,a.native)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
