"""ONE-G0.2 three-arm falsifier for batched terminal Fill execution."""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import json
import os
import statistics
import subprocess
import sys
import time

from benchmarks.one.one_g02_compact_observer_handoff_writer import FAMILIES, _case
from benchmarks.one.one_g02_post_segment_control_cost_owner import _literal_program
from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.growable_wire import _encode_program_growable_prevalidated
from experiments.one.ir import Ref, Root
from experiments.one.native_observe_small_vector import observe_native_small_vector
from experiments.one.native_terminal_fill import evaluate_terminal_roots_bulk_fill
from experiments.one.run_fill_law import program_from_observed_runs
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program

SIZES = (64 << 10, 256 << 10, 1 << 20)
REPETITIONS = 21
CONTROL_MAX = 1.05
LONG_RUNS_OVER_SCALAR_MAX = 0.75
TRAFFIC_MAX = 1.05
TEMP_MAX = 1.05
LONG_RUNS_1M_WIRE_MAX = 0.55
STRUCTURED_1M_WIRE_MAX = 0.90


def _programs(source: bytes, target: bytes):
    previous_digest=sha256(source).hexdigest(); current_digest=sha256(target).hexdigest()
    observation=observe_native_small_vector(target).materialize()
    previous_root=Root(Ref(0),len(source),previous_digest)
    control,_=_literal_program(source,target,previous_root,current_digest)
    candidate,stats=program_from_observed_runs(source,target,observation.runs,current_digest=current_digest,previous_digest=previous_digest)
    control.validate_shape(); candidate.validate_shape()
    cw,cws=_encode_program_growable_prevalidated(control); kw,kws=_encode_program_growable_prevalidated(candidate)
    return decode_program(cw),decode_program(kw),cws,kws,stats


def _time_three(control, candidate):
    samples={"control_wall":[],"control_cpu":[],"scalar_wall":[],"scalar_cpu":[],"bulk_wall":[],"bulk_cpu":[]}
    evaluators=(
        ("control",evaluate_terminal_roots_fused,control),
        ("scalar",evaluate_terminal_roots_fused,candidate),
        ("bulk",evaluate_terminal_roots_bulk_fill,candidate),
    )
    was_enabled=gc.isenabled()
    try:
        if was_enabled: gc.disable()
        for _,fn,p in evaluators: fn(p)
        for rep in range(REPETITIONS):
            shift=rep%3
            order=evaluators[shift:]+evaluators[:shift]
            for name,fn,p in order:
                c0=time.process_time_ns(); w0=time.perf_counter_ns(); value=fn(p); w1=time.perf_counter_ns(); c1=time.process_time_ns()
                if not value[0]: raise AssertionError("terminal evaluator produced no roots")
                samples[f"{name}_wall"].append(w1-w0); samples[f"{name}_cpu"].append(c1-c0)
    finally:
        if was_enabled: gc.enable()
    return {key:float(statistics.median(vals)) for key,vals in samples.items()}


def _child(size:int,family:str)->dict:
    source,target=_case(family,size)
    control,candidate,cws,kws,compiler_stats=_programs(source,target)
    reference,_=evaluate(candidate)
    control_value,control_stats=evaluate_terminal_roots_fused(control)
    scalar_value,scalar_stats=evaluate_terminal_roots_fused(candidate)
    bulk_value,bulk_stats=evaluate_terminal_roots_bulk_fill(candidate)
    expected={"previous":source,"current":target}
    semantic_ok=reference==control_value==scalar_value==bulk_value==expected
    if not semantic_ok: raise AssertionError(f"native terminal Fill semantic mismatch: {size=} {family=}")
    if bulk_stats.modeled_memory_traffic_bytes != scalar_stats.modeled_memory_traffic_bytes or bulk_stats.peak_temporary_bytes != scalar_stats.peak_temporary_bytes:
        raise AssertionError("bulk Fill changed fused resource accounting")
    scalars={
        "semantic_ok":semantic_ok,
        "qualifying_fill_runs":compiler_stats.qualifying_runs,
        "control_wire_bytes":cws.total_bytes,
        "candidate_wire_bytes":kws.total_bytes,
        "control_traffic":control_stats.modeled_memory_traffic_bytes,
        "bulk_traffic":bulk_stats.modeled_memory_traffic_bytes,
        "control_peak_temporary":control_stats.peak_temporary_bytes,
        "bulk_peak_temporary":bulk_stats.peak_temporary_bytes,
    }
    del reference,control_value,scalar_value,bulk_value; gc.collect()
    t=_time_three(control,candidate)
    return {
        "bytes":size,"family":family,**scalars,**t,
        "candidate_over_control_wire":kws.total_bytes/cws.total_bytes,
        "bulk_over_control_traffic":scalars["bulk_traffic"]/scalars["control_traffic"],
        "bulk_over_control_peak_temporary":scalars["bulk_peak_temporary"]/scalars["control_peak_temporary"],
        "bulk_over_control_wall":t["bulk_wall"]/t["control_wall"],
        "bulk_over_control_cpu":t["bulk_cpu"]/t["control_cpu"],
        "bulk_over_scalar_wall":t["bulk_wall"]/t["scalar_wall"],
        "bulk_over_scalar_cpu":t["bulk_cpu"]/t["scalar_cpu"],
        "scalar_over_control_wall":t["scalar_wall"]/t["control_wall"],
        "scalar_over_control_cpu":t["scalar_cpu"]/t["control_cpu"],
    }


def _invoke(size:int,family:str)->dict:
    proc=subprocess.run([sys.executable,"-m","benchmarks.one.one_g02_native_terminal_fill_batch","--child",str(size),family],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    lines=[x for x in proc.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError("native terminal Fill child produced no JSON")
    return json.loads(lines[-1])


def adjudicate(rows:list[dict])->str:
    expected={(size,family) for size in SIZES for family in FAMILIES}
    actual={(int(r["bytes"]),str(r["family"])) for r in rows}
    if len(rows)!=len(expected) or actual!=expected or not all(bool(r["semantic_ok"]) for r in rows):
        return "INVALIDATE_NATIVE_TERMINAL_FILL_BATCH"
    if any(r["candidate_over_control_wire"]>1.0 for r in rows): return "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    if any(r["bulk_over_control_traffic"]>TRAFFIC_MAX or r["bulk_over_control_peak_temporary"]>TEMP_MAX for r in rows): return "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    long_1m=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="long_runs")
    structured_1m=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="structured")
    if long_1m["candidate_over_control_wire"]>LONG_RUNS_1M_WIRE_MAX or structured_1m["candidate_over_control_wire"]>STRUCTURED_1M_WIRE_MAX:
        return "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    if any(r["bulk_over_control_wall"]>CONTROL_MAX or r["bulk_over_control_cpu"]>CONTROL_MAX for r in rows):
        return "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    for r in rows:
        if r["family"]=="long_runs" and (r["bulk_over_scalar_wall"]>LONG_RUNS_OVER_SCALAR_MAX or r["bulk_over_scalar_cpu"]>LONG_RUNS_OVER_SCALAR_MAX):
            return "HOLD_NATIVE_TERMINAL_FILL_BATCH"
    return "ADVANCE_NATIVE_TERMINAL_FILL_BATCH"


def run()->dict:
    rows=[_invoke(size,family) for size in SIZES for family in FAMILIES]
    return {
        "schema":"cmpct-one-g02-native-terminal-fill-batch-v1",
        "experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes":list(SIZES),"families":list(FAMILIES),"repetitions":REPETITIONS,
        "control_max":CONTROL_MAX,"long_runs_over_scalar_max":LONG_RUNS_OVER_SCALAR_MAX,
        "traffic_max":TRAFFIC_MAX,"temp_max":TEMP_MAX,
        "decision":adjudicate(rows),
        "claim_boundary":"same terminal Surprise/Fill/Concat Program; full-root only; native batching changes Fill dispatch only, not representation or selective semantics",
        "rows":rows,
    }


def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--child",nargs=2,metavar=("SIZE","FAMILY")); args=parser.parse_args()
    if args.child:
        size_s,family=args.child; size=int(size_s)
        if size not in SIZES or family not in FAMILIES: return 2
        print(json.dumps(_child(size,family),sort_keys=True)); return 0
    result=run(); print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result["decision"]=="ADVANCE_NATIVE_TERMINAL_FILL_BATCH" else 1


if __name__=="__main__": raise SystemExit(main())
