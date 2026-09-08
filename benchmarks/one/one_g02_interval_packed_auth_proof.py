"""Frozen ONE-G0.2 interval packed authenticated-range proof falsifier."""
from __future__ import annotations

import json
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range
from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval

SIZES=(256 << 10,1 << 20)
LEAVES=(80,96,112,192)
REQUESTS=((0,4096),("middle",4096),("final",4096),("middle",65536))
REPS=21
WARMUPS=2
DECISION_SIZE=1 << 20
LARGE_MAX=1.10
SMALL_MAX=1.15
LARGE_NONREGRESS_REQUIRED=14
SEED=0x1A7E2A1


def _requests(size:int)->tuple[tuple[int,int],...]:
    out=[]
    for where,length in REQUESTS:
        if where == 0: start=0
        elif where == "middle": start=(size-length)//2
        elif where == "final": start=size-length
        else: raise AssertionError(where)
        out.append((start,length))
    return tuple(out)


def _paired(data:bytes,ref_tree,native_tree,start:int,length:int)->tuple[float,float,float,float]:
    for _ in range(WARMUPS):
        prove_range(data,ref_tree,start,length); prove_range_packed_interval(data,native_tree,start,length)
    rw=[]; rc=[]; nw=[]; nc=[]
    result=None
    for rep in range(REPS):
        order=("candidate","reference") if rep & 1 else ("reference","candidate")
        for arm in order:
            # Destroy the preceding arm's RangeProof before either timer starts.  The
            # assignment below would otherwise decref the old object inside the next
            # arm's interval, contaminating a falsifier whose signal is only a few percent.
            result=None
            c0=time.process_time_ns(); w0=time.perf_counter_ns()
            result=(prove_range_packed_interval(data,native_tree,start,length)
                    if arm == "candidate" else prove_range(data,ref_tree,start,length))
            w1=time.perf_counter_ns(); c1=time.process_time_ns()
            if arm == "candidate": nw.append(w1-w0); nc.append(c1-c0)
            else: rw.append(w1-w0); rc.append(c1-c0)
    result=None
    return median(rw),median(rc),median(nw),median(nc)


def _decide(rows:list[dict[str,object]])->str:
    if len(rows) != len(SIZES)*len(LEAVES)*len(REQUESTS):
        return "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"
    if not all(bool(r["semantic_ok"]) and int(r["tree_digest_bytes_read"]) == int(r["proof_hash_bytes"]) for r in rows):
        return "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"
    large=[r for r in rows if int(r["size"]) == DECISION_SIZE]
    small=[r for r in rows if int(r["size"]) != DECISION_SIZE]
    if len(large) != 16 or len(small) != 16:
        return "INVALIDATE_INTERVAL_PACKED_AUTH_PROOF"
    large_hard=all(float(r["candidate_over_ref_wall"]) <= LARGE_MAX and float(r["candidate_over_ref_cpu"]) <= LARGE_MAX for r in large)
    nonreg=sum(1 for r in large if float(r["candidate_over_ref_wall"]) <= 1.0 and float(r["candidate_over_ref_cpu"]) <= 1.0)
    small_ok=all(float(r["candidate_over_ref_wall"]) <= SMALL_MAX and float(r["candidate_over_ref_cpu"]) <= SMALL_MAX for r in small)
    return "ADVANCE_INTERVAL_PACKED_AUTH_PROOF" if large_hard and nonreg >= LARGE_NONREGRESS_REQUIRED and small_ok else "HOLD_INTERVAL_PACKED_AUTH_PROOF"


def run()->dict[str,object]:
    rows=[]
    for size in SIZES:
        data=random.Random(SEED ^ size).randbytes(size)
        for leaf in LEAVES:
            ref_tree=build_auth_tree(data,leaf); native_tree=build_auth_tree_native(data,leaf)
            for start,length in _requests(size):
                expected=prove_range(data,ref_tree,start,length)
                got=prove_range_packed_interval(data,native_tree,start,length)
                semantic_ok=(native_tree.root == ref_tree.root and got == expected and
                             verify_range(got,native_tree.root,start,length) == data[start:start+length])
                rw,rc,nw,nc=_paired(data,ref_tree,native_tree,start,length)
                rows.append({
                    "size":size,"leaf_bytes":leaf,"start":start,"length":length,"semantic_ok":semantic_ok,
                    "siblings":len(got.siblings),"proof_hash_bytes":got.touched_proof_bytes,
                    "tree_digest_bytes_read":32*len(got.siblings),
                    "reference_wall_ns_median":rw,"reference_cpu_ns_median":rc,
                    "candidate_wall_ns_median":nw,"candidate_cpu_ns_median":nc,
                    "candidate_over_ref_wall":nw/rw,"candidate_over_ref_cpu":nc/rc,
                })
    decision=_decide(rows)
    return {"schema":"cmpct-one-g02-interval-packed-auth-proof-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "sizes":list(SIZES),"leaves":list(LEAVES),"repetitions":REPS,"decision_size":DECISION_SIZE,
            "large_ratio_max":LARGE_MAX,"small_ratio_max":SMALL_MAX,"large_nonregress_required":LARGE_NONREGRESS_REQUIRED,
            "rows":rows,"decision":decision,
            "claim_boundary":"proof generation from prebuilt trees only; contiguous-interval arithmetic replaces per-level selected/needed sets; creation, verification throughput, RSS and product I/O remain outside scope"}


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_INTERVAL_PACKED_AUTH_PROOF" else 2)
