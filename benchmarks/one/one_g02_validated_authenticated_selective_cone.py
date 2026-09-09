"""ONE-G0.2 shared-open authenticated selective-cone falsifier.

Frozen by ONE_G02_VALIDATED_AUTHENTICATED_SELECTIVE_CONE_PREREG_2026-09-09.md.
Both arms share one immutable fully validated Program snapshot and one AuthTree. The only
per-request difference is generic vs native reconstruction of the same authenticated cone.
"""
from __future__ import annotations

import gc
import json
import os
import statistics
import time

from benchmarks.one.one_g02_authenticated_native_selective_cone import (
    FAMILIES,
    LAW_FAMILIES,
    LEAF_BYTES,
    MAX_MEDIAN_MOVEMENT_RATIO,
    MAX_POSITIVE_CPU_RATIO,
    ROUNDS,
    SIZES,
    _requests,
)
from benchmarks.one.one_g02_native_law_terminal_reader import _case
from benchmarks.one.one_g02_selective_preflight_scaling import _with_unrelated_nodes
from experiments.one.auth_tree import build_auth_tree
from experiments.one.authenticated_native_selective_cone import (
    reconstruct_validated_authenticated_native_range,
)
from experiments.one.ir import Node, OneError, Program, Ref, Root
from experiments.one.range_vm import RangeEvaluator
from experiments.one.selective_auth import reconstruct_validated_authenticated_range
from experiments.one.validated_program import validate_program_snapshot

UNRELATED_COUNTS = (0, 64, 256, 1024, 4096)
MAX_FIXED_CONE_GROWTH = 2.0
AMORTIZATION_REQUESTS = (1, 4, 16, 64)


def _clock(fn):
    w0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    value = fn()
    return value, time.perf_counter_ns() - w0, time.process_time_ns() - c0


def _median_cpu(fn, rounds=ROUNDS):
    value = fn()
    samples = []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for _ in range(rounds):
            c0 = time.process_time_ns()
            value = fn()
            samples.append(time.process_time_ns() - c0)
    finally:
        if enabled:
            gc.enable()
    return value, int(statistics.median(samples))


def _paired(base_fn, cand_fn):
    base_fn(); cand_fn()
    bw=[]; bc=[]; cw=[]; cc=[]
    base=cand=None
    enabled=gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for i in range(ROUNDS):
            order=("base","cand") if i%2==0 else ("cand","base")
            for arm in order:
                if arm=="base":
                    base,w,c=_clock(base_fn); bw.append(w); bc.append(c)
                else:
                    cand,w,c=_clock(cand_fn); cw.append(w); cc.append(c)
    finally:
        if enabled:
            gc.enable()
    return base,int(statistics.median(bw)),int(statistics.median(bc)),cand,int(statistics.median(cw)),int(statistics.median(cc))


def _open_program(program):
    validated, wall, cpu = _clock(lambda: validate_program_snapshot(program))
    return validated, wall, cpu


def _hostile_controls():
    failures=[]
    program=_case(32*1024,"xor")
    full,_=RangeEvaluator(program).reconstruct("current",0,32*1024)
    tree=build_auth_tree(full,LEAF_BYTES)
    validated=validate_program_snapshot(program)
    wrong=bytes([tree.root[0]^1])+tree.root[1:]
    for label,fn in (
        ("generic_wrong_commitment",lambda: reconstruct_validated_authenticated_range(validated,"current",tree,wrong,0,64)),
        ("native_wrong_commitment",lambda: reconstruct_validated_authenticated_native_range(validated,"current",tree,wrong,0,64)),
    ):
        try: fn(); failures.append(label)
        except (OneError,ValueError): pass

    malformed=Program(
        nodes=(Node("add8",refs=(Ref(1),Ref(1)),declared_length=64),),
        roots={"root":Root(Ref(0),64,"0"*64)},
    )
    try:
        validate_program_snapshot(malformed); failures.append("malformed_program_obtained_authority")
    except OneError: pass
    return {"passed":not failures,"failures":failures}


def _fixed_cone_growth():
    rows=[]
    maxima={}
    for family in ("add8","xor"):
        base=_case(128*1024,family)
        generic_zero=native_zero=None
        for unrelated in UNRELATED_COUNTS:
            program=_with_unrelated_nodes(base,unrelated)
            validated=validate_program_snapshot(program)
            full,_=RangeEvaluator.from_validated(validated).reconstruct("current",0,128*1024)
            tree=build_auth_tree(full,LEAF_BYTES)
            _,gcpu=_median_cpu(lambda v=validated,t=tree: reconstruct_validated_authenticated_range(v,"current",t,t.root,0,64))
            _,ncpu=_median_cpu(lambda v=validated,t=tree: reconstruct_validated_authenticated_native_range(v,"current",t,t.root,0,64))
            if generic_zero is None:
                generic_zero=gcpu; native_zero=ncpu
            rows.append({
                "family":family,"unrelated_nodes":unrelated,"program_nodes":len(program.nodes),
                "generic_cpu_ns":gcpu,"native_cpu_ns":ncpu,
                "generic_growth":gcpu/max(generic_zero,1),
                "native_growth":ncpu/max(native_zero,1),
            })
        group=[r for r in rows if r["family"]==family]
        maxima[family]={
            "generic":max(r["generic_growth"] for r in group),
            "native":max(r["native_growth"] for r in group),
        }
    return rows,maxima


def run():
    rows=[]; positive_cpu=[]; positive_movement=[]; open_cpus=[]; exact_ok=True
    for n in SIZES:
        for family in FAMILIES:
            program=_case(n,family)
            validated,open_wall,open_cpu=_open_program(program)
            open_cpus.append(open_cpu)
            full,_=RangeEvaluator.from_validated(validated).reconstruct("current",0,n)
            tree=build_auth_tree(full,LEAF_BYTES)
            for request_name,start,length in _requests(n):
                base_fn=lambda v=validated,t=tree,s=start,l=length: reconstruct_validated_authenticated_range(v,"current",t,t.root,s,l)
                cand_fn=lambda v=validated,t=tree,s=start,l=length: reconstruct_validated_authenticated_native_range(v,"current",t,t.root,s,l)
                base,bw,bc,cand,cw,cc=_paired(base_fn,cand_fn)
                bv,bs=base; cv,cs=cand; expected=full[start:start+length]
                exact=(bv==cv==expected)
                if not exact: raise AssertionError("shared-open authenticated output mismatch")
                exact_ok &= exact
                cpu_ratio=cc/max(bc,1)
                base_move=bs.range_work_bytes+bs.proof_payload_bytes+bs.proof_hash_bytes
                cand_move=cs.modeled_data_movement_bytes
                move_ratio=cand_move/max(base_move,1)
                positive=family in LAW_FAMILIES
                if positive:
                    positive_cpu.append(cpu_ratio); positive_movement.append(move_ratio)
                rows.append({
                    "root_bytes":n,"family":family,"kind":"law" if positive else "control",
                    "request":request_name,"start":start,"length":length,"semantic_ok":exact,
                    "one_time_open_wall_ns":open_wall,"one_time_open_cpu_ns":open_cpu,
                    "generic_wall_ns":bw,"generic_cpu_ns":bc,
                    "native_wall_ns":cw,"native_cpu_ns":cc,
                    "native_over_generic_cpu":cpu_ratio,"native_over_generic_wall":cw/max(bw,1),
                    "generic_modeled_movement_bytes":base_move,
                    "native_modeled_movement_bytes":cand_move,
                    "native_over_generic_movement":move_ratio,
                    "cone_bytes":cs.cone_bytes,"root_bytes_avoided":n-cs.cone_bytes,
                    "native_peak_temporary_bytes":cs.peak_temporary_bytes,
                    "stored_auth_index_bytes":cs.auth_index_bytes,
                    "stage_native_prepare_cpu_ns":cs.prepare_cpu_ns,
                    "stage_native_execute_cpu_ns":cs.execute_cpu_ns,
                    "stage_proof_prepare_cpu_ns":cs.proof_prepare_cpu_ns,
                    "stage_verify_cpu_ns":cs.verify_cpu_ns,
                })

    fixed_rows,fixed_max=_fixed_cone_growth()
    hostile=_hostile_controls()
    median_cpu=statistics.median(positive_cpu)
    worst_cpu=max(positive_cpu)
    median_move=statistics.median(positive_movement)
    fixed_ok=all(
        max(v["generic"],v["native"])<=MAX_FIXED_CONE_GROWTH
        for v in fixed_max.values()
    )
    gates={
        "semantic_ok":exact_ok,
        "hostile_rejection_ok":hostile["passed"],
        "no_whole_root_positive":all(r["cone_bytes"]<r["root_bytes"] for r in rows if r["kind"]=="law"),
        "fixed_cone_cpu_growth_ok":fixed_ok,
        "median_native_cpu_below_generic":median_cpu<1.0,
        "worst_native_cpu_ok":worst_cpu<=MAX_POSITIVE_CPU_RATIO,
        "median_native_movement_ok":median_move<=MAX_MEDIAN_MOVEMENT_RATIO,
        "temporary_state_cone_bounded":all(r["native_peak_temporary_bytes"]<=3*r["cone_bytes"]+4096 for r in rows if r["kind"]=="law"),
    }
    median_open=int(statistics.median(open_cpus))
    median_generic=int(statistics.median(r["generic_cpu_ns"] for r in rows if r["kind"]=="law"))
    median_native=int(statistics.median(r["native_cpu_ns"] for r in rows if r["kind"]=="law"))
    amortization={str(k):{
        "generic_open_plus_requests_cpu_ns":median_open+k*median_generic,
        "native_open_plus_requests_cpu_ns":median_open+k*median_native,
        "native_over_generic":(median_open+k*median_native)/max(median_open+k*median_generic,1),
    } for k in AMORTIZATION_REQUESTS}
    advance=all(gates.values())
    return {
        "schema":"cmpct-one-g02-validated-authenticated-selective-cone-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "rounds":ROUNDS,"leaf_bytes":LEAF_BYTES,
        "summary":{
            "median_positive_native_over_generic_cpu":median_cpu,
            "worst_positive_native_over_generic_cpu":worst_cpu,
            "median_positive_native_over_generic_movement":median_move,
            "fixed_cone_max_growth":fixed_max,
            "median_one_time_open_cpu_ns":median_open,
            "amortization":amortization,"hostile":hostile,"gates":gates,"advance":advance,
            "decision":"ADVANCE_VALIDATED_AUTHENTICATED_SELECTIVE_CONE" if advance else ("INVALIDATE_VALIDATED_AUTHENTICATED_SELECTIVE_CONE" if not exact_ok or not hostile["passed"] else "HOLD_VALIDATED_AUTHENTICATED_SELECTIVE_CONE"),
        },
        "fixed_cone_rows":fixed_rows,"rows":rows,
    }


if __name__=="__main__":
    result=run(); print(json.dumps(result,sort_keys=True))
    if not result["summary"]["advance"]: raise SystemExit(1)
