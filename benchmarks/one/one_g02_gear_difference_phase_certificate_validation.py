"""ONE-G0.2 structural validation of the Gear-difference content-local phase certificate."""
from __future__ import annotations

import heapq
import json
import os

from benchmarks.one.one_g02_bounded_shift_phase_certificate_validation import (
    MODELED_STATE_BYTES as RAW_CERT_STATE_BYTES,
    PER_PHASE_K,
    SOURCE_PHASES,
    STRIDE,
    TARGET_PHASE,
    WORD,
    SIZES,
    SEEDS,
    _build_safe,
    _cases,
    _mix64,
    _safe_result,
)
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR

MASK=(1<<64)-1
MODELED_STATE_BYTES=RAW_CERT_STATE_BYTES + len(SOURCE_PHASES)*8


def _prefix_states(data:bytes):
    out=[]; p=0
    for b in data:
        p=((p<<1)+_GEAR[b])&MASK
        out.append(p)
    return out


def _direct_local_gear8(data:bytes,pos:int)->int:
    p=0
    for b in data[pos:pos+WORD]:
        p=((p<<1)+_GEAR[b])&MASK
    return p


def _difference_local_gear8(states:list[int],pos:int)->int:
    before=states[pos-1] if pos else 0
    end=states[pos+WORD-1]
    return (end-((before<<WORD)&MASK))&MASK


def _token(states:list[int],pos:int)->int:
    return _mix64(_difference_local_gear8(states,pos)^0x9E3779B97F4A7C15)


def _source_certificate(source:bytes):
    states=_prefix_states(source); cert=[]; sampled=0; identity_mismatches=[]
    for phase in SOURCE_PHASES:
        heap=[]
        for pos in range(phase,len(source)-WORD+1,STRIDE):
            sampled+=1
            local=_difference_local_gear8(states,pos)
            direct=_direct_local_gear8(source,pos)
            if local!=direct: identity_mismatches.append(pos)
            h=_mix64(local^0x9E3779B97F4A7C15); item=(-h,-pos,h)
            if len(heap)<PER_PHASE_K: heapq.heappush(heap,item)
            elif h<heap[0][2]: heapq.heapreplace(heap,item)
        cert.extend((entry[2],-entry[1],phase) for entry in heap)
    return cert,sampled,identity_mismatches


def _nominate(source:bytes,target:bytes):
    cert,ss,identity_mismatches=_source_certificate(source); by_hash={}
    for h,pos,phase in cert: by_hash.setdefault(h,[]).append((pos,phase))
    target_states=_prefix_states(target); ts=0; compares=0; target_identity=[]
    for pos in range(TARGET_PHASE,len(target)-WORD+1,STRIDE):
        ts+=1
        local=_difference_local_gear8(target_states,pos)
        direct=_direct_local_gear8(target,pos)
        if local!=direct: target_identity.append(pos)
        h=_mix64(local^0x9E3779B97F4A7C15)
        for source_pos,phase in by_hash.get(h,()):
            compares+=1
            if target[pos:pos+WORD]==source[source_pos:source_pos+WORD]:
                return True,ss,ts,compares,phase,identity_mismatches,target_identity
    return False,ss,ts,compares,None,identity_mismatches,target_identity


def run():
    safe,td=_build_safe(); rows=[]; misses=[]; random_false=[]; identity_failures=[]; max_fraction=0.0
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name,(source,target) in _cases(size,seed).items():
                    enabled,best_shift,proofs=_safe_result(safe,source,target)
                    nominated,ss,ts,compares,phase,src_id,tgt_id=_nominate(source,target)
                    if src_id or tgt_id: identity_failures.append((size,seed,name,len(src_id),len(tgt_id)))
                    frac=(ss+ts)/len(source); max_fraction=max(max_fraction,frac)
                    if enabled and not nominated: misses.append((size,seed,name))
                    if name=="independent_random" and nominated: random_false.append((size,seed,name))
                    rows.append({"relation_bytes":size,"seed":seed,"case":name,"exact_relation_enabled":enabled,"best_shift":best_shift,"exact_proofs":proofs,"gear_difference_nominated":nominated,"matching_source_phase":phase,"source_word_samples":ss,"target_word_samples_until_decision":ts,"sampled_position_fraction":frac,"exact_word_compares":compares,"identity_mismatches_source":len(src_id),"identity_mismatches_target":len(tgt_id)})
        passed=(not identity_failures and not misses and not random_false and max_fraction<=0.19 and MODELED_STATE_BYTES<=280)
        return {"schema":"cmpct-one-g02-gear-difference-phase-certificate-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","frozen_sizes":list(SIZES),"frozen_seeds":list(SEEDS),"stride":STRIDE,"word_bytes":WORD,"source_phases":list(SOURCE_PHASES),"per_phase_witnesses":PER_PHASE_K,"modeled_state_bytes":MODELED_STATE_BYTES,"gear_difference_identity_failures":identity_failures,"required_positive_misses":misses,"independent_random_false_nominations":random_false,"max_sampled_position_fraction":max_fraction,"decision":"advance_gear_difference_certificate_to_native_cost" if passed else "retire_gear_difference_certificate","claim_boundary":"structural writer-side nomination evidence only; no timing/density/reader/format/comparator claim","rows":rows}
    finally:
        td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_gear_difference_certificate_to_native_cost" else 2)
