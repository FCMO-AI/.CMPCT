"""Frozen ONE-G0.2 native authenticated selective verifier falsifier."""
from __future__ import annotations

import json
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import verify_range
from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval
from experiments.one.native_auth_verify import verify_range_native

SIZE=1 << 20
LEAVES=(80,96,112,192)
REQUESTS=((0,4096),("middle",4096),("final",4096),("middle",65536))
REPS=21
WARMUPS=2
WORST_MAX=0.65
MATERIAL_MAX=0.50
MATERIAL_ROWS=12
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


def _paired(control,candidate)->tuple[float,float,float,float]:
    for _ in range(WARMUPS):
        x=control(); x=None; x=candidate(); x=None
    cw=[]; cc=[]; nw=[]; nc=[]; x=None
    for rep in range(REPS):
        order=("candidate","control") if rep & 1 else ("control","candidate")
        for arm in order:
            x=None
            c0=time.process_time_ns(); w0=time.perf_counter_ns()
            x=candidate() if arm == "candidate" else control()
            w1=time.perf_counter_ns(); c1=time.process_time_ns()
            if arm == "control": cw.append(w1-w0); cc.append(c1-c0)
            else: nw.append(w1-w0); nc.append(c1-c0)
    x=None
    return median(cw),median(cc),median(nw),median(nc)


def _decide(rows:list[dict[str,object]])->str:
    expected={(leaf,start,length) for leaf in LEAVES for start,length in _requests(SIZE)}
    observed={(int(r["leaf_bytes"]),int(r["start"]),int(r["length"])) for r in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_NATIVE_AUTH_VERIFY"
    if not all(bool(r["semantic_ok"]) and bool(r["hostile_ok"]) for r in rows):
        return "INVALIDATE_NATIVE_AUTH_VERIFY"
    if any(float(r["wall_ratio"]) > WORST_MAX or float(r["cpu_ratio"]) > WORST_MAX for r in rows):
        return "HOLD_NATIVE_AUTH_VERIFY"
    material=sum(1 for r in rows if float(r["wall_ratio"]) <= MATERIAL_MAX and float(r["cpu_ratio"]) <= MATERIAL_MAX)
    return "ADVANCE_NATIVE_AUTH_VERIFY" if material >= MATERIAL_ROWS else "HOLD_NATIVE_AUTH_VERIFY"


def _tamper_bytes(x:bytes)->bytes:
    return bytes([x[0]^1])+x[1:]


def _must_fail(fn)->bool:
    try: fn()
    except (ValueError,RuntimeError): return True
    return False


def run()->dict[str,object]:
    data=random.Random(SEED).randbytes(SIZE)
    rows=[]
    for leaf in LEAVES:
        tree=build_auth_tree_native(data,leaf)
        for start,length in _requests(SIZE):
            proof=prove_range_packed_interval(data,tree,start,length)
            expected=data[start:start+length]
            base=verify_range(proof,tree.root,start,length)
            native=verify_range_native(proof,tree.root,start,length)
            hostile=[_must_fail(lambda p=proof: verify_range_native(p,_tamper_bytes(tree.root),start,length))]
            if proof.leaf_payloads:
                payloads=list(proof.leaf_payloads); payloads[0]=_tamper_bytes(payloads[0])
                from dataclasses import replace
                badp=replace(proof,leaf_payloads=tuple(payloads))
                hostile.append(_must_fail(lambda p=badp: verify_range_native(p,tree.root,start,length)))
            if proof.siblings:
                from dataclasses import replace
                siblings=list(proof.siblings); lv,idx,d=siblings[0]; siblings[0]=(lv,idx,_tamper_bytes(d))
                bads=replace(proof,siblings=tuple(siblings))
                hostile.append(_must_fail(lambda p=bads: verify_range_native(p,tree.root,start,length)))
                siblings=list(proof.siblings); lv,idx,d=siblings[0]; siblings[0]=(lv,idx+3,d)
                badc=replace(proof,siblings=tuple(siblings))
                hostile.append(_must_fail(lambda p=badc: verify_range_native(p,tree.root,start,length)))
            semantic_ok=(base == expected and native == expected and native == base)
            control=lambda p=proof,r=tree.root,s=start,l=length: verify_range(p,r,s,l)
            candidate=lambda p=proof,r=tree.root,s=start,l=length: verify_range_native(p,r,s,l)
            cw,cc,nw,nc=_paired(control,candidate)
            rows.append({
                "size":SIZE,"leaf_bytes":leaf,"start":start,"length":length,
                "semantic_ok":semantic_ok,"hostile_ok":all(hostile),"siblings":len(proof.siblings),
                "proof_hash_bytes":proof.touched_proof_bytes,"touched_data_bytes":proof.touched_data_bytes,
                "control_wall_ns_median":cw,"control_cpu_ns_median":cc,
                "native_wall_ns_median":nw,"native_cpu_ns_median":nc,
                "wall_ratio":nw/cw,"cpu_ratio":nc/cc,
            })
    decision=_decide(rows)
    return {"schema":"cmpct-one-g02-native-auth-verify-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "size":SIZE,"leaves":list(LEAVES),"repetitions":REPS,"worst_max":WORST_MAX,
            "material_max":MATERIAL_MAX,"material_rows":MATERIAL_ROWS,"rows":rows,"decision":decision,
            "claim_boundary":"in-memory verification implementation only; proof grammar/bytes unchanged; OpenSSL research dependency is not canonical portability authority"}


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_NATIVE_AUTH_VERIFY" else (2 if result["decision"].startswith("INVALIDATE") else 1))
