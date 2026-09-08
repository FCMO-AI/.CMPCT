"""Frozen ONE-G0.2 authenticated selective-open stage-owner profiler."""
from __future__ import annotations

import json
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import build_auth_tree, prove_range, verify_range
from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval

SIZE=1 << 20
LEAVES=(80,96,112,192)
REQUESTS=((0,4096),("middle",4096),("final",4096),("middle",65536))
PIPELINES=("reference","packed_interval")
REPS=21
WARMUPS=2
OWNER_SHARE=0.60
OWNER_ROWS=12
SEED=0xA075E1EC


def _requests(size:int)->tuple[tuple[int,int],...]:
    out=[]
    for where,length in REQUESTS:
        if where == 0: start=0
        elif where == "middle": start=(size-length)//2
        elif where == "final": start=size-length
        else: raise AssertionError(where)
        out.append((start,length))
    return tuple(out)


def _proof_fn(pipeline:str,data:bytes,ref_tree,native_tree,start:int,length:int):
    if pipeline == "reference":
        return prove_range(data,ref_tree,start,length)
    if pipeline == "packed_interval":
        return prove_range_packed_interval(data,native_tree,start,length)
    raise AssertionError(pipeline)


def _median_stage(fn)->tuple[float,float]:
    for _ in range(WARMUPS):
        result=fn(); result=None
    wall=[]; cpu=[]; result=None
    for _ in range(REPS):
        result=None
        c0=time.process_time_ns(); w0=time.perf_counter_ns()
        result=fn()
        w1=time.perf_counter_ns(); c1=time.process_time_ns()
        wall.append(w1-w0); cpu.append(c1-c0)
    result=None
    return median(wall),median(cpu)


def _paired_stages(proof_fn,verify_fn)->tuple[float,float,float,float]:
    for _ in range(WARMUPS):
        result=proof_fn(); result=None
        result=verify_fn(); result=None
    pw=[]; pc=[]; vw=[]; vc=[]; result=None
    for rep in range(REPS):
        order=("verify","proof") if rep & 1 else ("proof","verify")
        for stage in order:
            result=None
            c0=time.process_time_ns(); w0=time.perf_counter_ns()
            result=proof_fn() if stage == "proof" else verify_fn()
            w1=time.perf_counter_ns(); c1=time.process_time_ns()
            if stage == "proof": pw.append(w1-w0); pc.append(c1-c0)
            else: vw.append(w1-w0); vc.append(c1-c0)
    result=None
    return median(pw),median(pc),median(vw),median(vc)


def _decide(rows:list[dict[str,object]])->str:
    expected={(pipeline,leaf,start,length) for pipeline in PIPELINES for leaf in LEAVES for start,length in _requests(SIZE)}
    observed={(str(r["pipeline"]),int(r["leaf_bytes"]),int(r["start"]),int(r["length"])) for r in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER"
    if not all(bool(r["semantic_ok"]) for r in rows):
        return "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER"
    verification_owners=[]; proof_owners=[]
    for pipeline in PIPELINES:
        subset=[r for r in rows if r["pipeline"] == pipeline]
        v=sum(1 for r in subset if float(r["verify_wall_share"]) >= OWNER_SHARE and float(r["verify_cpu_share"]) >= OWNER_SHARE)
        p=sum(1 for r in subset if float(r["proof_wall_share"]) >= OWNER_SHARE and float(r["proof_cpu_share"]) >= OWNER_SHARE)
        verification_owners.append(v >= OWNER_ROWS)
        proof_owners.append(p >= OWNER_ROWS)
    if all(verification_owners):
        return "OWNER_AUTH_VERIFY"
    if all(proof_owners):
        return "OWNER_PROOF_EXTRACT"
    return "DISTRIBUTED_AUTH_SELECTIVE_OPEN"


def run()->dict[str,object]:
    data=random.Random(SEED).randbytes(SIZE)
    rows=[]
    for leaf in LEAVES:
        ref_tree=build_auth_tree(data,leaf)
        native_tree=build_auth_tree_native(data,leaf)
        if native_tree.root != ref_tree.root:
            raise AssertionError("native/reference root mismatch")
        for start,length in _requests(SIZE):
            ref_proof=prove_range(data,ref_tree,start,length)
            packed_proof=prove_range_packed_interval(data,native_tree,start,length)
            expected=data[start:start+length]
            semantic_base=(ref_proof == packed_proof and
                           verify_range(ref_proof,ref_tree.root,start,length) == expected and
                           verify_range(packed_proof,native_tree.root,start,length) == expected)
            for pipeline in PIPELINES:
                tree_root=ref_tree.root if pipeline == "reference" else native_tree.root
                stable_proof=ref_proof if pipeline == "reference" else packed_proof
                proof_fn=lambda p=pipeline,s=start,l=length: _proof_fn(p,data,ref_tree,native_tree,s,l)
                verify_fn=lambda pr=stable_proof,r=tree_root,s=start,l=length: verify_range(pr,r,s,l)
                proof_wall,proof_cpu,verify_wall,verify_cpu=_paired_stages(proof_fn,verify_fn)
                composed_wall,composed_cpu=_median_stage(lambda p=pipeline,r=tree_root,s=start,l=length: verify_range(_proof_fn(p,data,ref_tree,native_tree,s,l),r,s,l))
                wall_sum=proof_wall+verify_wall; cpu_sum=proof_cpu+verify_cpu
                rows.append({
                    "pipeline":pipeline,"size":SIZE,"leaf_bytes":leaf,"start":start,"length":length,
                    "semantic_ok":semantic_base,"siblings":len(stable_proof.siblings),
                    "proof_hash_bytes":stable_proof.touched_proof_bytes,"touched_data_bytes":stable_proof.touched_data_bytes,
                    "proof_wall_ns_median":proof_wall,"proof_cpu_ns_median":proof_cpu,
                    "verify_wall_ns_median":verify_wall,"verify_cpu_ns_median":verify_cpu,
                    "composed_wall_ns_median":composed_wall,"composed_cpu_ns_median":composed_cpu,
                    "proof_wall_share":proof_wall/wall_sum,"proof_cpu_share":proof_cpu/cpu_sum,
                    "verify_wall_share":verify_wall/wall_sum,"verify_cpu_share":verify_cpu/cpu_sum,
                    "stage_sum_over_composed_wall":wall_sum/composed_wall,"stage_sum_over_composed_cpu":cpu_sum/composed_cpu,
                })
    decision=_decide(rows)
    return {"schema":"cmpct-one-g02-auth-selective-open-stage-owner-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "size":SIZE,"leaves":list(LEAVES),"repetitions":REPS,"owner_share":OWNER_SHARE,"owner_rows":OWNER_ROWS,
            "rows":rows,"decision":decision,
            "claim_boundary":"in-memory selective-open stage ownership only; tree creation, product I/O, RSS, portability and on-disk sidecar placement remain outside scope"}


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"] != "INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER" else 2)
