"""ONE-G0.2 commitment-width feasibility boundary for fixed authenticated partitions.

Referee freeze before result-bearing execution
==============================================
The fixed-partition leaf/fanout grid is infeasible with the current 32-byte SHA-256-sized
commitments. This experiment asks a diagnostic question only: how small would each persisted
and proof commitment have to become before the SAME fixed-partition geometry enters the frozen
<=3.5% index / <=1.20x median authenticated-touch target?

This is NOT permission to weaken integrity. Commitment widths below the current 32 bytes are
hypothetical economics points. Any future primitive using fewer bytes requires a separate
security analysis and hardening decision. No width is promoted by this experiment.

Frozen grid:
- roots 64 KiB and 256 KiB; request 4 KiB;
- leaves 256..4096 B step 64; fanout 2,4,8,16,32,64,128,256;
- arbitrary alignment every 64 B modulo leaf plus leaf-1;
- commitment widths 32,28,24,20,16 bytes;
- every non-root node commitment is persisted and every proof sibling charged;
- complete intersecting leaf payloads remain charged.

Decision: report the largest commitment width with any feasible geometry. If none exists, the
fixed-partition family is even further from the target. Security acceptability is explicitly
out of scope and cannot be inferred from feasibility.
"""
from __future__ import annotations

import json
import math
import os
from statistics import median

ROOT_SIZES=(65_536,262_144)
REQUEST_BYTES=4096
LEAF_GRID=tuple(range(256,4097,64))
FANOUT_GRID=(2,4,8,16,32,64,128,256)
COMMITMENT_BYTES=(32,28,24,20,16)
ALIGNMENT_STEP=64
MAX_INDEX_FRACTION=0.035
MAX_MEDIAN_TOUCH_AMP=1.20


def _widths(n:int,f:int)->tuple[int,...]:
    out=[n]
    while out[-1]>1:
        out.append(math.ceil(out[-1]/f))
    return tuple(out)


def _proof_count(n:int,f:int,selected:set[int])->int:
    width=n; current=set(selected); total=0
    while width>1:
        parents={i//f for i in current}
        for p in parents:
            lo=p*f; hi=min(width,lo+f)
            total += (hi-lo)-sum(1 for i in current if i//f==p)
        current=parents; width=math.ceil(width/f)
    return total


def _start(root:int,leaf:int,mod:int)->int:
    center=(root-REQUEST_BYTES)//2
    start=center-center%leaf+mod
    if start+REQUEST_BYTES>root: start-=leaf
    if start<0 or start+REQUEST_BYTES>root or start%leaf!=mod:
        raise AssertionError('alignment')
    return start


def _metrics(root:int,leaf:int,fanout:int,commitment:int)->dict[str,float|int]:
    n=math.ceil(root/leaf); widths=_widths(n,fanout)
    index=4+commitment*(sum(widths)-1)
    mods=list(range(0,leaf,ALIGNMENT_STEP))
    if leaf-1 not in mods: mods.append(leaf-1)
    amps=[]
    for mod in mods:
        s=_start(root,leaf,mod); a=s//leaf; b=(s+REQUEST_BYTES-1)//leaf
        selected=set(range(a,b+1))
        payload=sum(min(leaf,root-i*leaf) for i in selected)
        touched=payload+commitment*_proof_count(n,fanout,selected)
        amps.append(touched/REQUEST_BYTES)
    return {'index_fraction':index/root,'median_touch_amplification':median(amps),'max_touch_amplification':max(amps)}


def run()->dict[str,object]:
    by_width={}; all_candidates=[]
    for commitment in COMMITMENT_BYTES:
        candidates=[]; ranked=[]
        for fanout in FANOUT_GRID:
            for leaf in LEAF_GRID:
                per={str(root):_metrics(root,leaf,fanout,commitment) for root in ROOT_SIZES}
                passes=all(m['index_fraction']<=MAX_INDEX_FRACTION and m['median_touch_amplification']<=MAX_MEDIAN_TOUCH_AMP for m in per.values())
                score=max(max(m['index_fraction']/MAX_INDEX_FRACTION,m['median_touch_amplification']/MAX_MEDIAN_TOUCH_AMP) for m in per.values())
                row={'commitment_bytes':commitment,'fanout':fanout,'leaf_bytes':leaf,'per_size':per,'passes':passes,'normalized_worst_score':score}
                ranked.append(row)
                if passes:
                    candidates.append(row); all_candidates.append(row)
        ranked.sort(key=lambda r:r['normalized_worst_score'])
        by_width[str(commitment)]={'candidate_count':len(candidates),'best_candidate':candidates[0] if candidates else None,'best_overall':ranked[0]}
    feasible_widths=[w for w in COMMITMENT_BYTES if by_width[str(w)]['candidate_count']]
    largest=max(feasible_widths) if feasible_widths else None
    return {
        'schema':'cmpct-one-g02-auth-commitment-width-boundary-v1',
        'experimental_version':'ONE-G0.2',
        'source_sha':os.environ.get('EVIDENCE_HEAD') or os.environ.get('GITHUB_SHA') or 'local-unbound',
        'commitment_widths_bytes':list(COMMITMENT_BYTES),
        'target_max_index_fraction':MAX_INDEX_FRACTION,
        'target_max_median_touch_amplification':MAX_MEDIAN_TOUCH_AMP,
        'largest_feasible_commitment_bytes':largest,
        'by_width':by_width,
        'decision':'fixed_partition_requires_sub_sha256_commitments' if largest is not None and largest<32 else ('sha256_width_fixed_partition_feasible' if largest==32 else 'no_tested_commitment_width_feasible'),
        'security_boundary':'hypothetical byte economics only; widths below current 32-byte SHA-256-sized commitments receive no integrity/security promotion authority',
        'claim_boundary':'research cost-model diagnostic only; no canonical wire, security, product or release authority',
    }


if __name__=='__main__':
    print(json.dumps(run(),indent=2,sort_keys=True))
