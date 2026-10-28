"""Stdlib-only referee for J24C17 exact-source owner-vs-sealed costs.

Never import CMPCT. Recompute all medians from raw independent worker
processes, enforce arm/source/physical identities, and reject forged receipts.
CI success means evidence valid, *not* product economy positive.
"""
import argparse
from collections import defaultdict
import copy
import json
import statistics
from pathlib import Path

FIELDS=("session_wall_ns","session_cpu_ns","open_wall_ns","open_cpu_ns",
        "read_wall_ns","read_cpu_ns","rss_mib")

def audit(d):
    assert d["schema"]=="j24c17-owner-vs-sealed-v1"
    assert d["owner_source"]=="a66fd593a83cc4c71556d3d86d835c51abd20a96"
    assert len(d["source_head"])==40 and all(c in "0123456789abcdef" for c in d["source_head"])
    reps=d["repetitions"]
    assert reps>=3
    raw=d["raw"]
    assert len(raw)==12*reps*2
    grouped=defaultdict(list)
    for r in raw:
        assert r["arm"] in ("owner662","sealed676")
        assert r["case"].startswith(("fixed-","hetero-"))
        assert r["q"] in (1,6,32)
        assert len(r["archive_sha256"])==64
        assert len(r["answer_sha256"])==64
        assert "site-packages" in r["source_path"] or "dist-packages" in r["source_path"]
        assert 0<=r["iteration"]<reps
        for phase in ("wall","cpu"):
            a,b,c=(r[f"{part}_{phase}_ns"] for part in ("open","read","session"))
            assert type(a) is type(b) is type(c) is int
            assert a>=0 and b>=0 and c>=0 and a+b==c
        assert type(r["process_wall_ns"]) is int and r["process_wall_ns"]>0
        assert isinstance(r["rss_mib"],(int,float)) and r["rss_mib"]>=0
        grouped[(r["case"],r["iteration"])].append(r)
    assert len(grouped)==12*reps
    for pair in grouped.values():
        assert len(pair)==2 and {x["arm"] for x in pair}=={"owner662","sealed676"}
        for k in ("case","iteration","archive_sha256","answer_sha256","q","python","host"):
            assert len({x[k] for x in pair})==1, (k,pair)
        for r in pair:
            assert ("owner662" in r["arm"]) == (r["arm"]=="owner662")
    groups=defaultdict(list)
    for r in raw:groups[(r["case"],r["arm"])].append(r)
    expected=[]
    for case in sorted({k[0] for k in groups}):
        for metric in FIELDS:
            a=statistics.median(r[metric] for r in groups[(case,"owner662")])
            b=statistics.median(r[metric] for r in groups[(case,"sealed676")])
            expected.append(dict(case=case,metric=metric,owner662=a,sealed676=b,
                                 sealed_over_owner=b/a if a else None))
    assert len(expected)==len(d["summary"])==12*len(FIELDS)
    for a,b in zip(expected,d["summary"]):
        for k in a:
            if k=="sealed_over_owner" and a[k] is not None:
                assert abs(a[k]-b[k])<1e-10
            else:
                assert a[k]==b[k],(k,a,b)
    return expected

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    d=json.loads(Path(a.input).read_text(encoding="utf-8"))
    summary=audit(d)
    attacks=[
        ("source",lambda x:x.update(source_head="0"*40)),
        ("arm",lambda x:x["raw"][0].update(arm="fake")),
        ("physical",lambda x:x["raw"][0].update(archive_sha256="f"*64)),
        ("sample",lambda x:x["raw"][0].update(session_wall_ns=1)),
        ("summary",lambda x:x["summary"][0].update(sealed676=0)),
        ("count",lambda x:x["raw"].pop()),
        ("answer",lambda x:x["raw"][0].update(answer_sha256="a"*64)),
    ]
    rejected=0
    for name,mutation in attacks:
        forged=copy.deepcopy(d)
        mutation(forged)
        try:audit(forged)
        except AssertionError:rejected+=1
        else:raise RuntimeError(f"referee accepted forged {name}")
    assert rejected==len(attacks)
    out=dict(verdict="SOURCE_LOCKED_OWNER_VS_SEALED_RESEARCH_AUDIT_PASS",
             source_head=d["source_head"],observations=len(d["raw"]),
             comparisons=len(summary),forgeries_rejected=rejected,
             q1_and_q6=[x for x in summary
                        if x["metric"]=="session_wall_ns"])
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__":
    main()
