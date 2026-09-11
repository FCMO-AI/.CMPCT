"""Frozen ONE-G0.2 native auth-verifier prepacked-boundary falsifier."""
from __future__ import annotations

import json
import os
import random
import time
from statistics import median

from experiments.one.auth_tree import verify_range
from experiments.one.native_auth_tree import build_auth_tree_native, prove_range_packed_interval
from experiments.one.native_auth_verify import verify_range_native
from experiments.one.native_auth_verify_prepacked import prepare_native_range_proof, verify_range_native_prepacked

SIZE=1 << 20
LEAVES=(80,96,112,192)
REQUESTS=((0,4096),("middle",4096),("final",4096),("middle",65536))
REPS=21
WARMUPS=2
CONTROL_WORST_MAX=0.65
CONTROL_MATERIAL_MAX=0.50
CONTROL_MATERIAL_ROWS=12
BOUNDARY_MATERIAL_MAX=0.90
BOUNDARY_MATERIAL_ROWS=12
BOUNDARY_WORST_MAX=1.03
SEED=0xA075B0D1


def _requests(size:int)->tuple[tuple[int,int],...]:
    out=[]
    for where,length in REQUESTS:
        if where == 0: start=0
        elif where == "middle": start=(size-length)//2
        elif where == "final": start=size-length
        else: raise AssertionError(where)
        out.append((start,length))
    return tuple(out)


def _three_way(control,charged,prepacked)->dict[str,float]:
    for _ in range(WARMUPS):
        x=control(); x=None; x=charged(); x=None; x=prepacked(); x=None
    wall={"control":[],"charged":[],"prepacked":[]}
    cpu={"control":[],"charged":[],"prepacked":[]}
    arms={"control":control,"charged":charged,"prepacked":prepacked}
    rotations=(
        ("control","charged","prepacked"),
        ("charged","prepacked","control"),
        ("prepacked","control","charged"),
    )
    x=None
    for rep in range(REPS):
        for arm in rotations[rep % len(rotations)]:
            x=None
            c0=time.process_time_ns(); w0=time.perf_counter_ns()
            x=arms[arm]()
            w1=time.perf_counter_ns(); c1=time.process_time_ns()
            wall[arm].append(w1-w0); cpu[arm].append(c1-c0)
    x=None
    return {
        "control_wall":median(wall["control"]),"control_cpu":median(cpu["control"]),
        "charged_wall":median(wall["charged"]),"charged_cpu":median(cpu["charged"]),
        "prepacked_wall":median(wall["prepacked"]),"prepacked_cpu":median(cpu["prepacked"]),
    }


def _decide(rows:list[dict[str,object]])->str:
    expected={(leaf,start,length) for leaf in LEAVES for start,length in _requests(SIZE)}
    observed={(int(r["leaf_bytes"]),int(r["start"]),int(r["length"])) for r in rows}
    if len(rows) != len(expected) or observed != expected:
        return "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    if not all(bool(r["semantic_ok"]) and bool(r["hostile_ok"]) for r in rows):
        return "INVALIDATE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    if any(float(r["prepacked_control_wall_ratio"]) > CONTROL_WORST_MAX or float(r["prepacked_control_cpu_ratio"]) > CONTROL_WORST_MAX for r in rows):
        return "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    material_control=sum(1 for r in rows if float(r["prepacked_control_wall_ratio"]) <= CONTROL_MATERIAL_MAX and float(r["prepacked_control_cpu_ratio"]) <= CONTROL_MATERIAL_MAX)
    if material_control < CONTROL_MATERIAL_ROWS:
        return "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    if any(float(r["prepacked_charged_wall_ratio"]) > BOUNDARY_WORST_MAX or float(r["prepacked_charged_cpu_ratio"]) > BOUNDARY_WORST_MAX for r in rows):
        return "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    material_boundary=sum(1 for r in rows if float(r["prepacked_charged_wall_ratio"]) <= BOUNDARY_MATERIAL_MAX and float(r["prepacked_charged_cpu_ratio"]) <= BOUNDARY_MATERIAL_MAX)
    if material_boundary < BOUNDARY_MATERIAL_ROWS:
        return "HOLD_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"
    return "ADVANCE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY"


def _flip(data:bytes)->bytes:
    return bytes([data[0]^1])+data[1:]


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
            prepared=prepare_native_range_proof(proof,tree.root)
            expected=data[start:start+length]
            base=verify_range(proof,tree.root,start,length)
            charged=verify_range_native(proof,tree.root,start,length)
            prepacked=verify_range_native_prepacked(prepared,start,length)
            hostile=[_must_fail(lambda p=proof: verify_range_native(p,_flip(tree.root),start,length))]
            semantic_ok=(base == expected and charged == expected and prepacked == expected and charged == base and prepacked == base)
            control=lambda p=proof,r=tree.root,s=start,l=length: verify_range(p,r,s,l)
            charged_fn=lambda p=proof,r=tree.root,s=start,l=length: verify_range_native(p,r,s,l)
            prepacked_fn=lambda p=prepared,s=start,l=length: verify_range_native_prepacked(p,s,l)
            t=_three_way(control,charged_fn,prepacked_fn)
            row={
                "size":SIZE,"leaf_bytes":leaf,"start":start,"length":length,
                "semantic_ok":semantic_ok,"hostile_ok":all(hostile),"siblings":len(proof.siblings),
                "proof_hash_bytes":proof.touched_proof_bytes,"touched_data_bytes":proof.touched_data_bytes,
                "control_wall_ns_median":t["control_wall"],"control_cpu_ns_median":t["control_cpu"],
                "charged_wall_ns_median":t["charged_wall"],"charged_cpu_ns_median":t["charged_cpu"],
                "prepacked_wall_ns_median":t["prepacked_wall"],"prepacked_cpu_ns_median":t["prepacked_cpu"],
                "charged_control_wall_ratio":t["charged_wall"]/t["control_wall"],
                "charged_control_cpu_ratio":t["charged_cpu"]/t["control_cpu"],
                "prepacked_control_wall_ratio":t["prepacked_wall"]/t["control_wall"],
                "prepacked_control_cpu_ratio":t["prepacked_cpu"]/t["control_cpu"],
                "prepacked_charged_wall_ratio":t["prepacked_wall"]/t["charged_wall"],
                "prepacked_charged_cpu_ratio":t["prepacked_cpu"]/t["charged_cpu"],
            }
            rows.append(row)
    decision=_decide(rows)
    return {
        "schema":"cmpct-one-g02-native-auth-verify-prepacked-boundary-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "size":SIZE,"leaves":list(LEAVES),"repetitions":REPS,
        "control_worst_max":CONTROL_WORST_MAX,"control_material_max":CONTROL_MATERIAL_MAX,
        "control_material_rows":CONTROL_MATERIAL_ROWS,"boundary_material_max":BOUNDARY_MATERIAL_MAX,
        "boundary_material_rows":BOUNDARY_MATERIAL_ROWS,"boundary_worst_max":BOUNDARY_WORST_MAX,
        "rows":rows,"decision":decision,
        "claim_boundary":"causal implementation probe only: existing RangeProof elements and native hash grammar unchanged; proof preparation is moved outside the hot call to isolate Python-to-ctypes marshalling cost",
    }


if __name__ == "__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ADVANCE_PREPACKED_NATIVE_AUTH_VERIFY_BOUNDARY" else (2 if result["decision"].startswith("INVALIDATE") else 1))
