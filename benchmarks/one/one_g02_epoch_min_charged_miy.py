"""ONE-G0.2 fully charged marginal-information-yield comparison.

Referee freeze before result-bearing execution
==============================================
Structural transfer now supports replacing the mature sliding minimizer *as discovery
knowledge* on the tested shifted/versioned families, but the candidate has not yet paid for
its sparse/rescue indexes, proof traffic and incremental native signal work in one symmetric
ledger. This experiment closes that debt on the pre-existing minimizer MIY corpus.

Baseline common work (fixed observer / shared source semantics) is not claimed as candidate
savings. Native selector cost is measured as candidate-minus-Gear and mature-minus-Gear on the
same runner. Candidate modeled state is native epoch signal state plus exact retained sparse +
epoch index entries at 16 B/entry, matching the mature MIY entry accounting convention.
Opportunity is byte-verified headroom, never stored-byte savings.

Frozen advancement gate on every mature-positive marginal row:
- candidate total opportunity >= mature full-minimizer opportunity individually;
- candidate modeled discovery state <=0.60x mature modeled discovery state;
- candidate incremental selector elapsed <=0.65x mature incremental selector elapsed;
- candidate marginal opportunity / incremental selector ms >=1.50x mature;
- candidate verification+extension reads <= mature verification+extension reads;
- no candidate exact opportunity on a row where both fixed and mature report zero.
Any row failure blocks replacement/promotion; aggregate wins cannot hide it.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes,json,os,random
from pathlib import Path
import statistics,subprocess,tempfile,time

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,_U64_MASK,ANCHOR_MASK,WINDOW,MIN_RUN,FIXED_MAX_INDEX_ENTRIES,GEAR_MAX_INDEX_ENTRIES,
    _extend_left,_extend_right,_cases,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe,MINIMIZER_SPAN
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_mature,_dispatch_call,_gear_call
from benchmarks.one.one_g02_starvation_epoch_min_native_ab import _bind_epoch,_call_epoch
from experiments.one.observe import observe

ROUNDS=13
INDEX_BYTES_PER_ENTRY=16

@dataclass(frozen=True)
class Candidate:
    reuse:int; sparse_entries:int; rescue_entries:int; verify:int; extension:int; pulses:int


def _candidate(data:bytes)->Candidate:
    if not data:return Candidate(0,0,0,0,0,0)
    sparse_index={};rescue_index={};h=0;last_sparse=None;active=False
    min_signal=(1<<64)-1;min_pos=-1;epoch_count=0;pulses=0
    reuse=verify=extension=0;covered=0;run_value=data[0];run_length=0
    def audition(start,signal,index):
        nonlocal reuse,verify,extension,covered
        if start<0 or start<covered:return
        source=index.get(signal)
        if source is None:
            if len(index)<GEAR_MAX_INDEX_ENTRIES:index[signal]=start
            return
        verify+=2*WINDOW
        if data[source:source+WINDOW]!=data[start:start+WINDOW]:return
        left,lr=_extend_left(data,source,start,covered);right,rr=_extend_right(data,source,start)
        extension+=lr+rr;a=max(start-left,covered);b=start+right
        if b>a:reuse+=b-a;covered=b
    def reset():
        nonlocal min_signal,min_pos,epoch_count
        min_signal=(1<<64)-1;min_pos=-1;epoch_count=0
    def pulse():
        nonlocal pulses
        if min_pos<0:return
        pulses+=1;audition(min_pos+1-WINDOW,min_signal,rescue_index);reset()
    for position,value in enumerate(data):
        if not run_length:run_value=value;run_length=1
        elif value==run_value:run_length+=1
        else:run_value=value;run_length=1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW:continue
        rd=run_length>=max(MIN_RUN,WINDOW);sparse=not(h&ANCHOR_MASK) and not rd
        if sparse:
            if active:pulse()
            audition(position+1-WINDOW,h,sparse_index);last_sparse=position;active=False;reset();continue
        if rd:continue
        epoch_count+=1
        if h<=min_signal:min_signal=h;min_pos=position
        gap=position-last_sparse if last_sparse is not None else position+1-WINDOW
        if not active and gap>=MINIMIZER_SPAN:pulse();active=True
        elif active and epoch_count>=MINIMIZER_SPAN:pulse()
    if active:pulse()
    return Candidate(reuse,len(sparse_index),len(rescue_index),verify,extension,pulses)


def _build():
    here=Path(__file__).parent;td=tempfile.TemporaryDirectory(prefix="cmpct-one-g02-epoch-charged-");lib=Path(td.name)/"lib.so"
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-fPIC","-shared",
        str(here/"one_g02_minimizer_kernel.c"),str(here/"one_g02_minimizer_segmented_counter_kernel.c"),
        str(here/"one_g02_minimizer_offset_only_kernel.c"),str(here/"one_g02_minimizer_size_dispatch_tail_kernel.c"),
        str(here/"one_g02_starvation_epoch_min_kernel.c"),"-o",str(lib)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)),td

def _time(fn):
    t=time.perf_counter_ns();fn();return time.perf_counter_ns()-t

def _paired_increment(gear_fn,selector_fn):
    gear_fn();selector_fn();vals=[];gs=[];ss=[]
    for _ in range(ROUNDS):
        g1=_time(gear_fn);s1=_time(selector_fn);s2=_time(selector_fn);g2=_time(gear_fn)
        g=(g1+g2)*.5;s=(s1+s2)*.5;gs.append(g);ss.append(s);vals.append(s-g)
    return float(statistics.median(gs)),float(statistics.median(ss)),float(statistics.median(vals))

def run():
    cases=_cases();starved=random.Random(4876).randbytes(8*1024)
    cases["starved_repeat_basis_8k_16k"]=starved*2;cases["starved_shifted_basis_8k_insert1"]=starved+b"X"+starved
    lib,td=_build()
    try:
        mature_fn,gear_fn=_bind_mature(lib);epoch_fn=_bind_epoch(lib);gear=(ctypes.c_uint64*256)(*_GEAR)
        rows=[];positive=[];failures=[]
        for name,data in cases.items():
            fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            mature=_minimizer_observe(data);cand=_candidate(data);f=fixed.stats.reuse_opportunity_bytes;m=mature.reuse_opportunity_bytes
            marginal=max(0,m-f);candidate_total=max(f,cand.reuse)
            arr=(ctypes.c_uint8*len(data)).from_buffer_copy(data);once_m=_dispatch_call(mature_fn,gear,arr,len(data));once_e=_call_epoch(epoch_fn,gear,arr,len(data))
            g1,mtotal,mincr=_paired_increment(lambda:_gear_call(gear_fn,gear,arr,len(data)),lambda:_dispatch_call(mature_fn,gear,arr,len(data)))
            g2,etotal,eincr=_paired_increment(lambda:_gear_call(gear_fn,gear,arr,len(data)),lambda:_call_epoch(epoch_fn,gear,arr,len(data)))
            if mincr<=0 or eincr<=0:raise AssertionError((name,"non-positive incremental cost",mincr,eincr))
            mature_index=(mature.global_entries+mature.local_entries)*INDEX_BYTES_PER_ENTRY
            candidate_index=(cand.sparse_entries+cand.rescue_entries)*INDEX_BYTES_PER_ENTRY
            mature_state=int(once_m.reserved_state_bytes)+mature_index;candidate_state=int(once_e.reserved_state_bytes)+candidate_index
            mature_proof=mature.verification_read_bytes+mature.extension_read_bytes;candidate_proof=cand.verify+cand.extension
            mature_yield=marginal/(mincr/1e6) if marginal else 0.0;candidate_marginal=max(0,candidate_total-f)
            candidate_yield=candidate_marginal/(eincr/1e6) if candidate_marginal else 0.0
            row={"case":name,"input_bytes":len(data),"fixed_opportunity_bytes":f,"mature_opportunity_bytes":m,
                "candidate_opportunity_bytes":cand.reuse,"mature_marginal_bytes":marginal,"candidate_marginal_bytes":candidate_marginal,
                "mature_incremental_selector_ns":mincr,"candidate_incremental_selector_ns":eincr,"incremental_cost_ratio":eincr/mincr,
                "mature_modeled_state_bytes":mature_state,"candidate_modeled_state_bytes":candidate_state,"state_ratio":candidate_state/mature_state if mature_state else 0,
                "mature_proof_read_bytes":mature_proof,"candidate_proof_read_bytes":candidate_proof,"proof_ratio":candidate_proof/mature_proof if mature_proof else 0,
                "mature_marginal_bytes_per_incremental_ms":mature_yield,"candidate_marginal_bytes_per_incremental_ms":candidate_yield,
                "yield_ratio":candidate_yield/mature_yield if mature_yield else 0,"candidate_sparse_entries":cand.sparse_entries,"candidate_rescue_entries":cand.rescue_entries,"candidate_pulses":cand.pulses}
            if marginal:
                positive.append(name);reasons=[]
                if candidate_total<m:reasons.append("opportunity")
                if row["state_ratio"]>.60:reasons.append("state")
                if row["incremental_cost_ratio"]>.65:reasons.append("elapsed")
                if row["yield_ratio"]<1.50:reasons.append("yield")
                if candidate_proof>mature_proof:reasons.append("proof")
                if reasons:failures.append({"case":name,"reasons":reasons})
            if f==0 and m==0 and cand.reuse!=0:failures.append({"case":name,"reasons":["candidate_false_exact_opportunity"]})
            rows.append(row)
        decision="advance_epoch_candidate_economics" if positive and not failures else "block_epoch_replacement_on_charged_economics"
        return {"schema":"cmpct-one-g02-epoch-min-charged-miy-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","rounds":ROUNDS,
            "positive_marginal_cases":positive,"gate_failures":failures,"decision":decision,
            "claim_boundary":"fully charged O1 encoder-discovery economics; no stored-byte/reader/product/comparator/release authority","rows":rows}
    finally:td.cleanup()

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
