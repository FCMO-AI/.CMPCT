"""ONE-G0.2 native exact relation-proof falsifier."""
from __future__ import annotations

import gc, json, random, statistics, time
from experiments.one.relation_span_growth import grow_relation_spans
from experiments.one.native_relation_span_growth import grow_relation_spans_native

SIZES=(64*1024,256*1024,1024*1024)
OPS=("add8","xor")
ROUNDS=9
MAX_MEDIAN_PRODUCTIVE_CPU_RATIO=0.25
MAX_PRODUCTIVE_CPU_RATIO=0.50
MAX_MEDIAN_HOSTILE_CPU_RATIO=1.00
MAX_HOSTILE_CPU_RATIO=1.50

def _parent(n,seed):
    r=random.Random(seed);return bytes(r.randrange(256) for _ in range(n))
def _apply(p,op,v):return bytes(((x+v)&255) if op=="add8" else (x^v) for x in p)
def _case(n,op,family):
    p=_parent(n,0xA11CE+n+(0 if op=="add8" else 7));v=37 if op=="add8" else 167;c=bytearray(_apply(p,op,v))
    if family=="sparse_cracks":
        for q in range(65521,n,65537):c[q]^=1
    elif family=="early_mismatch":c[64]^=1
    elif family=="late_mismatch":c[min(n-1,64+4095)]^=1
    elif family=="false_seed":c[0]^=1
    elif family=="multi_region":
        for q in range(32749,n,32771):c[q]^=1
    noms=tuple(range(0,n-63,64))
    return p,bytes(c),v,noms

def _time(fn,p,c,op,v,noms):
    xs=[];last=None;enabled=gc.isenabled()
    try:
        if enabled:gc.disable()
        fn(p,c,op=op,value=v,nominations=noms)
        for _ in range(ROUNDS):
            t=time.process_time_ns();last=fn(p,c,op=op,value=v,nominations=noms);xs.append(time.process_time_ns()-t)
    finally:
        if enabled:gc.enable()
    return int(statistics.median(xs)),last

def run():
    families=("exact","sparse_cracks","early_mismatch","late_mismatch","false_seed","multi_region")
    rows=[];productive=[];hostile=[]
    for n in SIZES:
        for op in OPS:
            for fam in families:
                p,c,v,noms=_case(n,op,fam)
                # alternate timing order by stable matrix parity
                if ((n//65536)+(0 if op=="add8" else 1)+families.index(fam))%2:
                    nc,nr=_time(grow_relation_spans_native,p,c,op,v,noms);pc,pr=_time(grow_relation_spans,p,c,op,v,noms)
                else:
                    pc,pr=_time(grow_relation_spans,p,c,op,v,noms);nc,nr=_time(grow_relation_spans_native,p,c,op,v,noms)
                semantic=(nr==pr);ratio=nc/max(pc,1);kind="productive" if fam in {"exact","sparse_cracks","multi_region"} else "hostile"
                (productive if kind=="productive" else hostile).append(ratio)
                rows.append({"bytes":n,"op":op,"family":fam,"kind":kind,"semantic_ok":semantic,"python_cpu_ns":pc,"native_cpu_ns":nc,"native_over_python_cpu":ratio,"compared_bytes":pr.compared_bytes,"accepted_bytes":pr.accepted_bytes,"rejected_seeds":pr.rejected_seeds,"run_count":len(pr.runs)})
    invalid=any(not r["semantic_ok"] for r in rows)
    hold=(statistics.median(productive)>MAX_MEDIAN_PRODUCTIVE_CPU_RATIO or max(productive)>MAX_PRODUCTIVE_CPU_RATIO or statistics.median(hostile)>MAX_MEDIAN_HOSTILE_CPU_RATIO or max(hostile)>MAX_HOSTILE_CPU_RATIO)
    decision="INVALIDATE_NATIVE_EXACT_RELATION_PROOF" if invalid else "HOLD_NATIVE_EXACT_RELATION_PROOF" if hold else "ADVANCE_NATIVE_EXACT_RELATION_PROOF"
    print(json.dumps({"experiment":"ONE-G0.2 native exact relation proof","decision":decision,"source_sha":__import__("os").environ.get("EVIDENCE_HEAD"),"median_productive_cpu_ratio":statistics.median(productive),"worst_productive_cpu_ratio":max(productive),"median_hostile_cpu_ratio":statistics.median(hostile),"worst_hostile_cpu_ratio":max(hostile),"rows":rows},sort_keys=True))
    return 0 if decision=="ADVANCE_NATIVE_EXACT_RELATION_PROOF" else 1
if __name__=="__main__":raise SystemExit(run())
