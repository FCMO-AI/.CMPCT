"""ONE-G0.2 falsifier: one native mixed replay for an unchanged prepared terminal Program.

Mission lock: test whether Python Surprise scatter remains the material hot-path tax after
prepared-plan promotion failed. Native lowering is measured separately and must amortize;
root SHA-256 and output freezing stay inside every hot replay.
"""
from __future__ import annotations
import argparse,gc,json,os,statistics,subprocess,sys,time
from benchmarks.one.one_g02_compact_observer_handoff_writer import FAMILIES,_case
from benchmarks.one.one_g02_native_terminal_fill_batch import _programs
from experiments.one.fused_terminal_reader import evaluate_terminal_roots_fused
from experiments.one.prepared_terminal_plan import compile_terminal_plan,execute_prepared_terminal_plan
from experiments.one.native_mixed_terminal_plan import compile_native_mixed_terminal_plan,execute_native_mixed_terminal_plan
from experiments.one.vm import evaluate

SIZES=(64<<10,256<<10,1<<20); REPETITIONS=21
HOT_CONTROL_MAX=1.05; TRAFFIC_MAX=1.05; NO_REGRESS_PREPARED_MAX=1.05
LONG_1M_OVER_PREPARED_MAX=0.90; STRUCTURED_1M_OVER_PREPARED_MAX=0.95
BREAK_EVEN_REPLAYS_MAX=4.0; LONG_RUNS_1M_WIRE_MAX=0.55; STRUCTURED_1M_WIRE_MAX=0.90

def _median_ns(fn):
    xs=[]
    for _ in range(REPETITIONS):
        c0=time.process_time_ns();w0=time.perf_counter_ns();v=fn();w1=time.perf_counter_ns();c1=time.process_time_ns()
        if not v: raise AssertionError("timed operation returned no result")
        xs.append((w1-w0,c1-c0))
    return float(statistics.median(x[0] for x in xs)),float(statistics.median(x[1] for x in xs))

def _child(size:int,family:str)->dict:
    source,target=_case(family,size);control,candidate,cws,kws,_=_programs(source,target)
    reference,_=evaluate(candidate); literal,lstats=evaluate_terminal_roots_fused(control)
    prepared=compile_terminal_plan(candidate); pval,pstats=execute_prepared_terminal_plan(prepared)
    mixed=compile_native_mixed_terminal_plan(prepared); mval,mstats=execute_native_mixed_terminal_plan(mixed)
    expected={"previous":source,"current":target}; semantic_ok=reference==literal==pval==mval==expected
    if not semantic_ok: raise AssertionError(f"mixed terminal semantic mismatch {size=} {family=}")
    if mstats.modeled_memory_traffic_bytes!=pstats.modeled_memory_traffic_bytes: raise AssertionError("mixed replay changed traffic accounting")
    del reference,literal,pval,mval;gc.collect();was=gc.isenabled()
    try:
        if was:gc.disable()
        evaluate_terminal_roots_fused(control);execute_prepared_terminal_plan(prepared);execute_native_mixed_terminal_plan(mixed);compile_native_mixed_terminal_plan(prepared)
        lw,lc=_median_ns(lambda:evaluate_terminal_roots_fused(control));pw,pc=_median_ns(lambda:execute_prepared_terminal_plan(prepared));mw,mc=_median_ns(lambda:execute_native_mixed_terminal_plan(mixed));cw,cc=_median_ns(lambda:compile_native_mixed_terminal_plan(prepared))
    finally:
        if was:gc.enable()
    sw=pw-mw;sc=pc-mc
    return {"bytes":size,"family":family,"semantic_ok":semantic_ok,"control_wire_bytes":cws.total_bytes,"candidate_wire_bytes":kws.total_bytes,"candidate_over_control_wire":kws.total_bytes/cws.total_bytes,"literal_traffic":lstats.modeled_memory_traffic_bytes,"mixed_traffic":mstats.modeled_memory_traffic_bytes,"mixed_over_literal_traffic":mstats.modeled_memory_traffic_bytes/lstats.modeled_memory_traffic_bytes,"literal_wall":lw,"literal_cpu":lc,"prepared_wall":pw,"prepared_cpu":pc,"mixed_wall":mw,"mixed_cpu":mc,"mixed_compile_wall":cw,"mixed_compile_cpu":cc,"mixed_over_literal_wall":mw/lw,"mixed_over_literal_cpu":mc/lc,"mixed_over_prepared_wall":mw/pw,"mixed_over_prepared_cpu":mc/pc,"incremental_break_even_wall":cw/sw if sw>0 else float("inf"),"incremental_break_even_cpu":cc/sc if sc>0 else float("inf")}

def _invoke(size,family):
    p=subprocess.run([sys.executable,"-m","benchmarks.one.one_g02_native_mixed_terminal_plan","--child",str(size),family],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def adjudicate(rows):
    expected={(s,f) for s in SIZES for f in FAMILIES};actual={(int(r["bytes"]),str(r["family"])) for r in rows}
    if len(rows)!=len(expected) or actual!=expected or not all(r["semantic_ok"] for r in rows):return "INVALIDATE_NATIVE_MIXED_TERMINAL_PLAN"
    if any(r["candidate_over_control_wire"]>1.0 or r["mixed_over_literal_traffic"]>TRAFFIC_MAX for r in rows):return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    l1=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="long_runs");s1=next(r for r in rows if r["bytes"]==(1<<20) and r["family"]=="structured")
    if l1["candidate_over_control_wire"]>LONG_RUNS_1M_WIRE_MAX or s1["candidate_over_control_wire"]>STRUCTURED_1M_WIRE_MAX:return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    if any(r["mixed_over_literal_wall"]>HOT_CONTROL_MAX or r["mixed_over_literal_cpu"]>HOT_CONTROL_MAX for r in rows):return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    if any(r["mixed_over_prepared_wall"]>NO_REGRESS_PREPARED_MAX or r["mixed_over_prepared_cpu"]>NO_REGRESS_PREPARED_MAX for r in rows):return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    if l1["mixed_over_prepared_wall"]>LONG_1M_OVER_PREPARED_MAX or l1["mixed_over_prepared_cpu"]>LONG_1M_OVER_PREPARED_MAX:return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    if s1["mixed_over_prepared_wall"]>STRUCTURED_1M_OVER_PREPARED_MAX or s1["mixed_over_prepared_cpu"]>STRUCTURED_1M_OVER_PREPARED_MAX:return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    for r in (l1,s1):
        if r["incremental_break_even_wall"]>BREAK_EVEN_REPLAYS_MAX or r["incremental_break_even_cpu"]>BREAK_EVEN_REPLAYS_MAX:return "HOLD_NATIVE_MIXED_TERMINAL_PLAN"
    return "ADVANCE_NATIVE_MIXED_TERMINAL_PLAN"

def run():
    rows=[_invoke(s,f) for s in SIZES for f in FAMILIES]
    return {"schema":"cmpct-one-g02-native-mixed-terminal-plan-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","repetitions":REPETITIONS,"decision":adjudicate(rows),"claim_boundary":"unchanged terminal Surprise/Fill/Concat Program; generic plan already validated; native mixed lowering charged separately; root hashing and output freeze charged; full-root execution evidence only","rows":rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--child",nargs=2);a=ap.parse_args()
    if a.child:
        s,f=int(a.child[0]),a.child[1]
        if s not in SIZES or f not in FAMILIES:return 2
        print(json.dumps(_child(s,f),sort_keys=True));return 0
    result=run();print(json.dumps(result,indent=2,sort_keys=True));return 0 if result["decision"]=="ADVANCE_NATIVE_MIXED_TERMINAL_PLAN" else 1
if __name__=="__main__":raise SystemExit(main())
