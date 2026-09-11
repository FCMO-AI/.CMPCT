"""ONE-G0.2 falsifier for prepared terminal execution plans.

Separates cold plan compilation from hot replay and compares replay with the current
schedule-on-read bulk terminal evaluator. Precomputation is never treated as free.
"""
from __future__ import annotations

import argparse, gc, json, os, statistics, subprocess, sys, time
from benchmarks.one.one_g02_compact_observer_handoff_writer import FAMILIES, _case
from benchmarks.one.one_g02_native_terminal_fill_batch import _programs
from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.native_terminal_fill import evaluate_terminal_roots_bulk_fill
from experiments.one.prepared_terminal_plan import compile_terminal_plan, execute_prepared_terminal_plan
from experiments.one.vm import evaluate

SIZES=(64<<10,256<<10,1<<20)
REPETITIONS=21
HOT_CONTROL_MAX=1.05
HOT_OVER_BULK_LONG_MAX=0.90
LONG_BREAK_EVEN_REPLAYS_MAX=4.0
TRAFFIC_MAX=1.05
LONG_RUNS_1M_WIRE_MAX=0.55
STRUCTURED_1M_WIRE_MAX=0.90


def _median_ns(fn):
    samples=[]
    for _ in range(REPETITIONS):
        c0=time.process_time_ns(); w0=time.perf_counter_ns(); value=fn(); w1=time.perf_counter_ns(); c1=time.process_time_ns()
        if not value: raise AssertionError("timed operation returned no result")
        samples.append((w1-w0,c1-c0))
    return float(statistics.median(x[0] for x in samples)),float(statistics.median(x[1] for x in samples))


def _child(size:int,family:str)->dict:
    source,target=_case(family,size)
    control,candidate,cws,kws,_=_programs(source,target)
    reference,_=evaluate(candidate)
    control_value,control_stats=evaluate_terminal_roots_fused(control)
    bulk_value,bulk_stats=evaluate_terminal_roots_bulk_fill(candidate)
    plan=compile_terminal_plan(candidate)
    hot_value,hot_stats=execute_prepared_terminal_plan(plan)
    expected={"previous":source,"current":target}
    semantic_ok=reference==control_value==bulk_value==hot_value==expected
    if not semantic_ok: raise AssertionError(f"prepared terminal semantic mismatch: {size=} {family=}")
    if hot_stats.modeled_memory_traffic_bytes!=bulk_stats.modeled_memory_traffic_bytes:
        raise AssertionError("prepared replay changed terminal traffic accounting")
    del reference,control_value,bulk_value,hot_value; gc.collect()
    was=gc.isenabled()
    try:
        if was: gc.disable()
        evaluate_terminal_roots_fused(control); evaluate_terminal_roots_bulk_fill(candidate); execute_prepared_terminal_plan(plan); compile_terminal_plan(candidate)
        control_wall,control_cpu=_median_ns(lambda:evaluate_terminal_roots_fused(control))
        bulk_wall,bulk_cpu=_median_ns(lambda:evaluate_terminal_roots_bulk_fill(candidate))
        hot_wall,hot_cpu=_median_ns(lambda:execute_prepared_terminal_plan(plan))
        compile_wall,compile_cpu=_median_ns(lambda:compile_terminal_plan(candidate))
    finally:
        if was: gc.enable()
    saved_wall=bulk_wall-hot_wall; saved_cpu=bulk_cpu-hot_cpu
    be_wall=compile_wall/saved_wall if saved_wall>0 else float("inf")
    be_cpu=compile_cpu/saved_cpu if saved_cpu>0 else float("inf")
    return {
      "bytes":size,"family":family,"semantic_ok":semantic_ok,
      "control_wire_bytes":cws.total_bytes,"candidate_wire_bytes":kws.total_bytes,
      "candidate_over_control_wire":kws.total_bytes/cws.total_bytes,
      "control_traffic":control_stats.modeled_memory_traffic_bytes,"hot_traffic":hot_stats.modeled_memory_traffic_bytes,
      "hot_over_control_traffic":hot_stats.modeled_memory_traffic_bytes/control_stats.modeled_memory_traffic_bytes,
      "control_wall":control_wall,"control_cpu":control_cpu,"bulk_wall":bulk_wall,"bulk_cpu":bulk_cpu,
      "hot_wall":hot_wall,"hot_cpu":hot_cpu,"compile_wall":compile_wall,"compile_cpu":compile_cpu,
      "hot_over_control_wall":hot_wall/control_wall,"hot_over_control_cpu":hot_cpu/control_cpu,
      "hot_over_bulk_wall":hot_wall/bulk_wall,"hot_over_bulk_cpu":hot_cpu/bulk_cpu,
      "break_even_replays_wall":be_wall,"break_even_replays_cpu":be_cpu,
    }


def _invoke(size:int,family:str)->dict:
    p=subprocess.run([sys.executable,"-m","benchmarks.one.one_g02_prepared_terminal_plan","--child",str(size),family],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])


def adjudicate(rows:list[dict])->str:
    expected={(s,f) for s in SIZES for f in FAMILIES}; actual={(int(r["bytes"]),str(r["family"])) for r in rows}
    if len(rows)!=len(expected) or actual!=expected or not all(r["semantic_ok"] for r in rows): return "INVALIDATE_PREPARED_TERMINAL_PLAN"
    if any(r["candidate_over_control_wire"]>1.0 or r["hot_over_control_traffic"]>TRAFFIC_MAX for r in rows): return "HOLD_PREPARED_TERMINAL_PLAN"
    l1=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="long_runs"); s1=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="structured")
    if l1["candidate_over_control_wire"]>LONG_RUNS_1M_WIRE_MAX or s1["candidate_over_control_wire"]>STRUCTURED_1M_WIRE_MAX: return "HOLD_PREPARED_TERMINAL_PLAN"
    if any(r["hot_over_control_wall"]>HOT_CONTROL_MAX or r["hot_over_control_cpu"]>HOT_CONTROL_MAX for r in rows): return "HOLD_PREPARED_TERMINAL_PLAN"
    for r in rows:
        if r["family"]=="long_runs":
            if r["hot_over_bulk_wall"]>HOT_OVER_BULK_LONG_MAX or r["hot_over_bulk_cpu"]>HOT_OVER_BULK_LONG_MAX: return "HOLD_PREPARED_TERMINAL_PLAN"
            if r["break_even_replays_wall"]>LONG_BREAK_EVEN_REPLAYS_MAX or r["break_even_replays_cpu"]>LONG_BREAK_EVEN_REPLAYS_MAX: return "HOLD_PREPARED_TERMINAL_PLAN"
    return "ADVANCE_REUSABLE_PREPARED_TERMINAL_PLAN"


def run()->dict:
    rows=[_invoke(s,f) for s in SIZES for f in FAMILIES]
    return {"schema":"cmpct-one-g02-prepared-terminal-plan-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","sizes":list(SIZES),"families":list(FAMILIES),"repetitions":REPETITIONS,"hot_control_max":HOT_CONTROL_MAX,"hot_over_bulk_long_max":HOT_OVER_BULK_LONG_MAX,"long_break_even_replays_max":LONG_BREAK_EVEN_REPLAYS_MAX,"decision":adjudicate(rows),"claim_boundary":"same terminal Surprise/Fill/Concat Program; plan compilation charged separately; promotion is reusable-reader execution evidence, not one-shot cold-read authority or selective-range authority","rows":rows}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--child",nargs=2); a=ap.parse_args()
    if a.child:
        s,f=int(a.child[0]),a.child[1]
        if s not in SIZES or f not in FAMILIES:return 2
        print(json.dumps(_child(s,f),sort_keys=True));return 0
    result=run();print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["decision"]=="ADVANCE_REUSABLE_PREPARED_TERMINAL_PLAN" else 1
if __name__=="__main__": raise SystemExit(main())
