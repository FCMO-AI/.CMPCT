"""ONE-G0.2 epoch-min rescue transfer falsifier.

Mission lock
============
Exact full-span replay at starvation edges preserves 35/35 hard shifted opportunities but
is too expensive on ~8 KiB inputs. A continuously maintained 64-position hierarchy is also
retired because its always-on bookkeeping roughly doubles large-path elapsed.

This Builder asks a narrower causal question: does the hard transfer require an *exact sliding
4096-position minimizer*, or only a stable rightmost minimum over consecutive starvation
epochs? Before rescue activates, maintain one scalar rightmost minimum for the starvation
epoch. At activation (fixed 4096 gap), emit it and reset. While active, maintain one scalar
minimum; emit/reset every 4096 active positions and emit the final partial epoch at exit/EOF.
There is no queue, history replay, block hierarchy, or changed threshold.

The scalar epoch candidate is discovery-only and may nominate a different subset than the
mature sliding minimizer. It advances only if it preserves every previously frozen hard row.

Frozen disproof:
- same first 12 zero-sparse-anchor 4096-byte seed bases and insertion lengths 1/8/31;
- every row where full minimizer owns opportunity beyond fixed+sparse must retain 100% of
  full-minimizer opportunity under epoch-min rescue;
- any loss rejects epoch-min as the small-case rescue seed; zero hard rows is inconclusive.
"""
from __future__ import annotations

from dataclasses import dataclass
import json, os

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,_U64_MASK,ANCHOR_MASK,WINDOW,MIN_RUN,FIXED_MAX_INDEX_ENTRIES,GEAR_MAX_INDEX_ENTRIES,
    _extend_left,_extend_right,_gear_observe,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe, MINIMIZER_SPAN
from benchmarks.one.one_g02_late_rescue_transfer import _starved_bases, INSERTIONS
from experiments.one.observe import observe

@dataclass(frozen=True)
class EpochResult:
    reuse_opportunity_bytes:int; pulses:int; sparse_anchors:int
    verification_read_bytes:int; extension_read_bytes:int


def _epoch_observe(data:bytes)->EpochResult:
    if not data: return EpochResult(0,0,0,0,0)
    sparse_index={}; rescue_index={}; h=0; last_sparse=None; active=False
    min_signal=(1<<64)-1; min_pos=-1; epoch_count=0; pulses=anchors=0
    reuse=verify=ext=0; covered=0; run_value=data[0]; run_length=0
    def audition(start,signal,index):
        nonlocal reuse,verify,ext,covered
        if start<0 or start<covered: return
        source=index.get(signal)
        if source is None:
            if len(index)<GEAR_MAX_INDEX_ENTRIES:index[signal]=start
            return
        verify+=2*WINDOW
        if data[source:source+WINDOW]!=data[start:start+WINDOW]:return
        left,lr=_extend_left(data,source,start,covered); right,rr=_extend_right(data,source,start)
        ext+=lr+rr; a=max(start-left,covered); b=start+right
        if b>a: reuse+=b-a; covered=b
    def reset_epoch():
        nonlocal min_signal,min_pos,epoch_count
        min_signal=(1<<64)-1; min_pos=-1; epoch_count=0
    def update(signal,pos):
        nonlocal min_signal,min_pos,epoch_count
        epoch_count+=1
        if signal<=min_signal:min_signal=signal;min_pos=pos
    def pulse():
        nonlocal pulses
        if min_pos<0:return
        pulses+=1; audition(min_pos+1-WINDOW,min_signal,rescue_index); reset_epoch()
    for position,value in enumerate(data):
        if not run_length:run_value=value;run_length=1
        elif value==run_value:run_length+=1
        else:run_value=value;run_length=1
        h=((h<<1)+_GEAR[value])&_U64_MASK
        if position+1<WINDOW:continue
        rd=run_length>=max(MIN_RUN,WINDOW); sparse=not(h&ANCHOR_MASK) and not rd
        if sparse:
            if active:pulse()
            anchors+=1; audition(position+1-WINDOW,h,sparse_index); last_sparse=position; active=False; reset_epoch(); continue
        if rd:continue
        gap=position-last_sparse if last_sparse is not None else position+1-WINDOW
        update(h,position)
        if not active and gap>=MINIMIZER_SPAN:
            pulse(); active=True
        elif active and epoch_count>=MINIMIZER_SPAN:
            pulse()
    if active:pulse()
    return EpochResult(reuse,pulses,anchors,verify,ext)


def run():
    rows=[]; hard=0; losses=[]
    for seed,basis in _starved_bases():
        for ins in INSERTIONS:
            data=basis+ins+basis
            fixed=observe(data,min_run=MIN_RUN,chunk_size=WINDOW,max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            sparse=_gear_observe(data); full=_minimizer_observe(data); epoch=_epoch_observe(data)
            cheap=max(fixed.stats.reuse_opportunity_bytes,sparse.reuse_opportunity_bytes)
            need=full.reuse_opportunity_bytes>cheap
            if need:
                hard+=1
                if epoch.reuse_opportunity_bytes<full.reuse_opportunity_bytes: losses.append(f"seed={seed}/insert={len(ins)}")
            rows.append({"seed":seed,"insertion_bytes":len(ins),"input_bytes":len(data),
                "fixed_reuse_opportunity_bytes":fixed.stats.reuse_opportunity_bytes,
                "sparse_reuse_opportunity_bytes":sparse.reuse_opportunity_bytes,
                "full_minimizer_reuse_opportunity_bytes":full.reuse_opportunity_bytes,
                "epoch_min_reuse_opportunity_bytes":epoch.reuse_opportunity_bytes,"hard_rescue_needed":need,
                "epoch_minus_full_opportunity_bytes":epoch.reuse_opportunity_bytes-full.reuse_opportunity_bytes,
                "pulses":epoch.pulses,"verification_read_bytes":epoch.verification_read_bytes,"extension_read_bytes":epoch.extension_read_bytes})
    decision="epoch_min_transfer_survives" if hard and not losses else "inconclusive_no_hard_rows" if not hard else "reject_epoch_min_rescue"
    return {"schema":"cmpct-one-g02-starvation-epoch-min-transfer-v1","experimental_version":"ONE-G0.2",
        "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "hard_rescue_rows":hard,"hard_rescue_loss_cases":losses,"decision":decision,
        "claim_boundary":"generator-distinct encoder-discovery transfer only; not native/product/release authority","rows":rows}

if __name__=="__main__":print(json.dumps(run(),indent=2,sort_keys=True))
