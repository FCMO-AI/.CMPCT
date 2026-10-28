#!/usr/bin/env python3
"""Independent J24C19 receipt referee: no import from the experimental court."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics

import msgpack

N_VALUES=(4096,65536,262144)
SHAPES=("fixed","mixed")


def expected_wire(n,shape):
    # This deliberately reimplements fixture bytes from the r24 schema rather
    # than calling the court's generate/check functions.
    ids=[0]*n if shape=="fixed" else [i&1 for i in range(n)]
    raw=b"A"*n if shape=="fixed" else b"ABC"*(n//2)+(b"A" if n&1 else b"")
    blobs=[[0,1,1,0,0]]
    if shape=="mixed": blobs.append([1,2,2,0,0])
    row=["fixture.bin",0,420,0,len(raw),hashlib.sha256(raw).digest(),[1,ids]]
    return msgpack.packb({"v":24,"files":[row],"blobs":blobs,"recipes":[]},use_bin_type=True)


def verify(doc):
    assert doc["schema"]=="cmpct-j24c19-tuple-first-oracle-v1"
    assert re.fullmatch("[a-f0-9]{40}",doc["source_sha"]), "source SHA"
    assert doc["phase"]=="MICRO_RESEARCH_NOT_PRODUCT"
    cases=doc["cases"]
    assert len(cases)==6
    got=set()
    summary=[]
    for case in cases:
        n,shape=case["n"],case["shape"]
        assert n in N_VALUES and shape in SHAPES and (n,shape) not in got
        got.add((n,shape))
        wire=expected_wire(n,shape)
        assert case["payload_sha256"]==hashlib.sha256(wire).hexdigest()
        assert case["payload_bytes"]==len(wire)
        assert len(case["runs"])==4
        assert [x["mode"] for x in case["runs"]]==[
            "freeze_after","tuple_first","tuple_first","freeze_after"
        ]
        samples={"freeze_after":[],"tuple_first":[]}
        for run in case["runs"]:
            assert run["payload_sha256"]==case["payload_sha256"]
            assert len(run["samples"])==3
            assert run["peak_rss_before_kib"] is None or run["peak_rss_before_kib"]>=0
            assert run["peak_rss_after_kib"] is None or run["peak_rss_after_kib"]>=0
            for sample in run["samples"]:
                for k in ("wall_ns","cpu_ns"):
                    assert type(sample[k]) is int and sample[k]>0
                    assert sample[k]<120_000_000_000
                samples[run["mode"]].append(sample)
        speed={}
        for metric in ("wall_ns","cpu_ns"):
            baseline=statistics.median(x[metric] for x in samples["freeze_after"])
            candidate=statistics.median(x[metric] for x in samples["tuple_first"])
            assert baseline>0 and candidate>0
            speed[metric]=candidate/baseline
        summary.append({"n":n,"shape":shape,"candidate_over_control":speed})
    assert got=={(n,s) for n in N_VALUES for s in SHAPES}
    # Scientific outcome is deliberately not the validity of evidence.
    # The strict performance decision is preregistered and evaluated here.
    large=[x for x in summary if x["n"]>=65536]
    decision=("ECONOMIC_HEADROOM_COMPONENT_ONLY" if all(
        x["candidate_over_control"]["cpu_ns"]<=0.95 and
        x["candidate_over_control"]["wall_ns"]<=0.95 for x in large)
        else "RETIRE_TUPLE_FIRST_AS_IMMEDIATE_SHIPPING_OPTIMIZATION")
    return {"decision":decision,"cases":summary,"observations":72}


def hostile_referee_selftest(doc):
    import copy
    variants=[]
    def mutate(fn):
        d=copy.deepcopy(doc)
        fn(d)
        variants.append(d)
    mutate(lambda d:d["cases"][0].update(payload_sha256="0"*64))
    mutate(lambda d:d["cases"][0].update(payload_bytes=1))
    mutate(lambda d:d["cases"][0]["runs"][0].update(mode="tuple_first"))
    mutate(lambda d:d["cases"][0]["runs"][0]["samples"][0].update(cpu_ns=0))
    mutate(lambda d:d.update(source_sha="MERGE_SHA_UNBOUND"))
    mutate(lambda d:d["cases"][0].update(n=123))
    mutate(lambda d:d["cases"][0]["runs"].pop())
    for i,v in enumerate(variants):
        try: verify(v)
        except (AssertionError,KeyError,TypeError,ValueError,IndexError): pass
        else: raise AssertionError("forged receipt accepted: %d" % i)
    return len(variants)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("receipt",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    doc=json.loads(args.receipt.read_text())
    out=verify(doc)
    out["forgeries_rejected"]=hostile_referee_selftest(doc)
    print(json.dumps(out,indent=2,sort_keys=True))
    if args.out:args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    main()
