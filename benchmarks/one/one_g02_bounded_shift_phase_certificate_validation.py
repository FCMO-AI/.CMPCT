"""ONE-G0.2 frozen structural validation of the sparse bounded-shift phase certificate."""
from __future__ import annotations

import heapq
import json
import os
import random

from benchmarks.one.one_g02_relation_shared_observer_validation import (
    _build_safe,
    _hostile_band_break,
    _safe_result,
    _shifted,
)
from benchmarks.one.one_g02_local_gear_certificate_validation import _certificate_targeted

SIZES=(4*1024,8*1024,16*1024,64*1024,256*1024)
SEEDS=(11,37,59)
STRIDE=32
WORD=8
TARGET_PHASE=0
SOURCE_PHASES=(0,1,2,30,31)
PER_PHASE_K=4
MODELED_STATE_BYTES=len(SOURCE_PHASES)*PER_PHASE_K*(8+4)
MASK=(1<<64)-1


def _mix64(x:int)->int:
    x ^= x>>30; x=(x*0xBF58476D1CE4E5B9)&MASK
    x ^= x>>27; x=(x*0x94D049BB133111EB)&MASK
    x ^= x>>31
    return x


def _word_hash(data:bytes,pos:int)->int:
    return _mix64(int.from_bytes(data[pos:pos+WORD],"little") ^ 0x9E3779B97F4A7C15)


def _source_certificate(source:bytes):
    cert=[]; sampled=0
    for phase in SOURCE_PHASES:
        heap=[]
        for pos in range(phase,len(source)-WORD+1,STRIDE):
            sampled += 1
            h=_word_hash(source,pos); item=(-h,-pos,h)
            if len(heap)<PER_PHASE_K: heapq.heappush(heap,item)
            elif h<heap[0][2]: heapq.heapreplace(heap,item)
        cert.extend((entry[2],-entry[1],phase) for entry in heap)
    return cert,sampled


def _nominate(source:bytes,target:bytes):
    cert,source_samples=_source_certificate(source)
    by_hash={}
    for h,pos,phase in cert: by_hash.setdefault(h,[]).append((pos,phase))
    target_samples=0; exact_compares=0
    for pos in range(TARGET_PHASE,len(target)-WORD+1,STRIDE):
        target_samples += 1; h=_word_hash(target,pos)
        for source_pos,phase in by_hash.get(h,()):
            exact_compares += 1
            if target[pos:pos+WORD]==source[source_pos:source_pos+WORD]:
                return True,source_samples,target_samples,exact_compares,phase
    return False,source_samples,target_samples,exact_compares,None


def _cases(size:int,seed:int):
    source=random.Random(71000+size*43+seed*1031).randbytes(size)
    return {
        "shift_plus1":(source,_shifted(source)),
        "damage_quarter":(source,_shifted(source,damage_quarter=True)),
        "fragmented_every96":(source,_shifted(source,spacing=96)),
        "hostile_fixed_bands":(source,_hostile_band_break(source)),
        "prior_certificate_targeted":(source,_certificate_targeted(source)),
        "fragmented_every32":(source,_shifted(source,spacing=32)),
        "independent_random":(source,random.Random(72000+size*47+seed*1033).randbytes(size)),
    }


def run():
    safe,td=_build_safe(); rows=[]; misses=[]; random_false=[]; max_fraction=0.0
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name,(source,target) in _cases(size,seed).items():
                    enabled,best_shift,proofs=_safe_result(safe,source,target)
                    nominated,ss,ts,compares,phase=_nominate(source,target)
                    frac=(ss+ts)/len(source); max_fraction=max(max_fraction,frac)
                    if enabled and not nominated: misses.append((size,seed,name))
                    if name=="independent_random" and nominated: random_false.append((size,seed,name))
                    rows.append({"relation_bytes":size,"seed":seed,"case":name,"exact_relation_enabled":enabled,"best_shift":best_shift,"exact_proofs":proofs,"phase_certificate_nominated":nominated,"matching_source_phase":phase,"source_word_samples":ss,"target_word_samples_until_decision":ts,"sampled_position_fraction":frac,"exact_word_compares":compares})
        passed=not misses and not random_false and max_fraction<=0.19 and MODELED_STATE_BYTES==240
        return {"schema":"cmpct-one-g02-bounded-shift-phase-certificate-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","frozen_sizes":list(SIZES),"frozen_seeds":list(SEEDS),"stride":STRIDE,"word_bytes":WORD,"source_phases":list(SOURCE_PHASES),"per_phase_witnesses":PER_PHASE_K,"modeled_state_bytes":MODELED_STATE_BYTES,"required_positive_misses":misses,"independent_random_false_nominations":random_false,"max_sampled_position_fraction":max_fraction,"decision":"advance_phase_certificate_to_native_cascade_cost" if passed else "reject_bounded_shift_phase_certificate","claim_boundary":"structural writer-side nomination evidence only; fragmented_every32 false nominations are allowed here but must be charged through the sparse falsifier at the next gate","rows":rows}
    finally: td.cleanup()


if __name__=="__main__":
    result=run(); print(json.dumps(result,indent=2,sort_keys=True)); raise SystemExit(0 if result["decision"]=="advance_phase_certificate_to_native_cascade_cost" else 1)
