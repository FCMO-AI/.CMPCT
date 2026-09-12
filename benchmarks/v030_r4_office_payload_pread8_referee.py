from __future__ import annotations

"""Exact-head Office payload pread/refill referee for the compact-locator candidate.

Mission Lock / Referee
======================
The v7 candidate is frozen at 5,952,805 B with a 1,221 B density margin and a worst charged 4 KiB read
of 32,746 / 32,768 B, leaving only 22 B physical-read slack. Its logical cold reader currently decodes
from an in-memory compressed stream while charging the exact compressed byte intervals consumed.

This referee changes no representation, metadata group, seed selector, page size, codec, auth tax, or
8x law. It takes the exact existing compressed intervals and executes them through real `os.pread` from
a physical payload file. To avoid the unrealistic one-byte-refill extreme while respecting the tiny
slack, the reader plan is frozen to one native-word-sized **8-byte refill** beginning at each exact
required byte (never rounded backward). The final chunk is clipped only at physical stream EOF. Expanded
intervals are merged before charging. Every read also pays the v7 360 B locator+root cold-read charge.
No refill-size sweep is allowed.

Hypothesis
----------
The fixed 8-byte refill plan must reproduce every requested physical byte exactly and keep every inherited
fixed <=4 KiB Office probe plus every adjacent-page sufficient-condition probe <=32,768 B after charging
whole 644 B metadata groups and the v7 locator/root. If supported, the receipt provides a concrete bounded
bulk-I/O primitive for the next real reader. It does not prove that bit decoding itself is sourced solely
from pread; that remains the next integration step.

Disproof
--------
One pread mismatch or one charged request above 32,768 B falsifies 8-byte refill. Preserve the measured
excess; do not sweep 1/2/4-byte refills or relax 8x.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sparse_superframe_economic_referee as SUPER
from benchmarks import v030_r4_office_gated_seed_superframe_economic_referee as SEEDGROUP
from benchmarks import v030_r4_office_group_charge_locality_referee as GROUP

SCHEMA='cmpct-v030-r4-office-payload-pread8-referee-v1'
PAGE=4096
LIMIT=8*PAGE
REFILL=8
LOCATOR_ROOT_CHARGE=360
EXPECTED_V7_BYTES=5_952_805
EXPECTED_V029_BYTES=5_954_026
EXPECTED_DENSITY_MARGIN=1_221
EXPECTED_V7_WORST=32_746


def _merged(rs):
    if not rs: return []
    out=[list(x) for x in sorted(rs)]
    m=[out[0]]
    for a,b in out[1:]:
        if a<=m[-1][1]: m[-1][1]=max(m[-1][1],b)
        else: m.append([a,b])
    return [(a,b) for a,b in m]


def _expand_refill(rs, n):
    expanded=[]
    for a,b in _merged(rs):
        need=b-a
        end=min(n,a+((need+REFILL-1)//REFILL)*REFILL)
        expanded.append((a,end))
    return _merged(expanded)


def _pread_verify(fd, comp, ranges):
    calls=bytes_read=0
    for a,b in ranges:
        got=os.pread(fd,b-a,a)
        if got!=comp[a:b]:
            raise RuntimeError('payload pread mismatch')
        calls+=1; bytes_read+=len(got)
    return calls,bytes_read


def run(work:Path,v029_checkout:Path,worker:Path)->dict:
    t0=time.perf_counter()
    economic=SEEDGROUP.run(work,v029_checkout,worker)
    if not economic['hypothesis']['exact_selected_seed_records_group_within_same_input_density_margin']:
        raise RuntimeError('gated-seed economics prerequisite unsupported')
    manifest=json.loads((work/'current'/'manifest.json').read_text())
    pool=(work/'current'/'streams.bin').read_bytes()
    hashes=sorted({rec['stream_hash'] for rec in manifest['derived'].values()})

    fixed_requests=pair_requests=0
    exact_failures=locality_failures=pair_failures=pread_failures=0
    pread_calls=pread_bytes=logical_payload_bytes=0
    worst=None; worst_pair=None
    rows=[]
    for si,h in enumerate(hashes):
        s=manifest['stream_index'][h]
        comp=pool[s['o']:s['o']+s['n']]
        parsed=DEP.parse_tokens(comp); raw=zlib.decompress(comp,-15)
        anchors,blocks,_=COLD._build_metadata(parsed)
        seeds,_all_seed,_logical_seed=SEED._build_seeds(parsed,anchors,raw)
        brecs,arecs=SUPER._encoded_records(parsed)
        bmap,bcost,_=GROUP._pack_map([(int(r['key']),r['encoded']) for r in brecs],f's{si}:b')
        amap,acost,_=GROUP._pack_map([(int(r['key']),r['encoded']) for r in arecs],f's{si}:a')
        pages=len(anchors); unsafe=set(); selected=set()
        for p in range(pages):
            a=p*PAGE; b=min(len(raw),min(pages,p+2)*PAGE)
            r=COLD.ColdReader(comp,anchors,blocks,len(raw))
            if r.read(a,b)!=raw[a:b]: raise RuntimeError('classifier exactness drift')
            if r.metadata_bytes()+r.payload_bytes()>LIMIT:
                unsafe.add(p); selected.add(p)
                if p+1<pages:selected.add(p+1)
        seed_records=[]; gated=[None]*pages
        for p in sorted(selected):
            if seeds[p] is None: continue
            enc=GROUP._seed_enc(p,anchors[p],parsed,raw)
            if enc is None or hashlib.sha256(enc).hexdigest()!=seeds[p]['frame_sha256']:
                raise RuntimeError('seed parity drift')
            seed_records.append((p,enc)); gated[p]=seeds[p]
        smap,scost,_=GROUP._pack_map(seed_records,f's{si}:s')
        costs={**bcost,**acost,**scost}
        payload_path=work/f'pread-stream-{si}.deflate'; payload_path.write_bytes(comp)
        fd=os.open(payload_path,os.O_RDONLY)
        try:
            stream_worst=0; stream_max_calls=0
            for p in range(pages):
                a=p*PAGE; b=min(len(raw),min(pages,p+2)*PAGE)
                seed_mode=p in unsafe
                r=SEED.SeedReader(comp,anchors,blocks,gated,len(raw)) if seed_mode else COLD.ColdReader(comp,anchors,blocks,len(raw))
                got=r.read(a,b)
                logical=r.payload_bytes(); rr=_expand_refill(r.payload_ranges,len(comp))
                try: calls,actual=_pread_verify(fd,comp,rr)
                except RuntimeError: pread_failures+=1; calls=actual=0
                meta=GROUP._charge_groups(r,amap,bmap,smap,costs)
                combined=actual+meta+LOCATOR_ROOT_CHARGE
                pair_requests+=1; pread_calls+=calls; pread_bytes+=actual; logical_payload_bytes+=logical
                if got!=raw[a:b] or combined>LIMIT: pair_failures+=1
                q={'stream_sha256':h,'pair_start_page':p,'logical_payload_bytes':logical,'pread_payload_bytes':actual,
                   'payload_overfetch_bytes':actual-logical,'pread_calls':calls,'metadata_bytes':meta,
                   'locator_root_bytes':LOCATOR_ROOT_CHARGE,'combined_bytes':combined,'slack_bytes':LIMIT-combined}
                if worst_pair is None or combined>worst_pair['combined_bytes']: worst_pair=q
            for start in TRANSFER._starts(len(raw)):
                end=min(start+PAGE,len(raw)); p0=start//PAGE; p1=(end-1)//PAGE
                seed_mode=(p0 in unsafe) if p1!=p0 else (p0 in unsafe or (p0>0 and (p0-1) in unsafe))
                r=SEED.SeedReader(comp,anchors,blocks,gated,len(raw)) if seed_mode else COLD.ColdReader(comp,anchors,blocks,len(raw))
                got=r.read(start,end); logical=r.payload_bytes(); rr=_expand_refill(r.payload_ranges,len(comp))
                try: calls,actual=_pread_verify(fd,comp,rr)
                except RuntimeError: pread_failures+=1; calls=actual=0
                meta=GROUP._charge_groups(r,amap,bmap,smap,costs); combined=actual+meta+LOCATOR_ROOT_CHARGE
                fixed_requests+=1; pread_calls+=calls; pread_bytes+=actual; logical_payload_bytes+=logical
                if got!=raw[start:end]: exact_failures+=1
                if combined>LIMIT: locality_failures+=1
                stream_worst=max(stream_worst,combined); stream_max_calls=max(stream_max_calls,calls)
                q={'stream_sha256':h,'start':start,'end':end,'logical_payload_bytes':logical,'pread_payload_bytes':actual,
                   'payload_overfetch_bytes':actual-logical,'pread_calls':calls,'metadata_bytes':meta,
                   'locator_root_bytes':LOCATOR_ROOT_CHARGE,'combined_bytes':combined,'slack_bytes':LIMIT-combined}
                if worst is None or combined>worst['combined_bytes']: worst=q
        finally:
            os.close(fd)
        rows.append({'stream_sha256':h,'compressed_bytes':len(comp),'pages':pages,'worst_fixed_bytes':stream_worst,'max_fixed_pread_calls':stream_max_calls})

    supported=exact_failures==0 and pread_failures==0 and locality_failures==0 and pair_failures==0
    return {
        'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),
        'frozen_v7':{'candidate_bytes':EXPECTED_V7_BYTES,'v029_bytes':EXPECTED_V029_BYTES,'density_margin_bytes':EXPECTED_DENSITY_MARGIN,'prior_worst_bytes':EXPECTED_V7_WORST},
        'physical_refill':{'refill_bytes':REFILL,'locator_root_charge_bytes':LOCATOR_ROOT_CHARGE,'fixed_requests':fixed_requests,'pair_requests':pair_requests,
                           'exact_failures':exact_failures,'pread_failures':pread_failures,'locality_failures':locality_failures,'pair_failures':pair_failures,
                           'total_logical_payload_bytes':logical_payload_bytes,'total_pread_payload_bytes':pread_bytes,'total_payload_overfetch_bytes':pread_bytes-logical_payload_bytes,
                           'total_pread_calls':pread_calls,'worst_fixed_probe':worst,'worst_page_pair':worst_pair,'rows':rows},
        'profile':{'wall_s_including_prerequisites':time.perf_counter()-t0},
        'hypothesis':{'eight_byte_exact_start_pread_refill_preserves_office_8x':supported},
        'contract':{'diagnostic_only':True,'release_credit':False,'representation_bytes_unchanged':True,'same_644b_groups':True,'same_seed_selector':True,
                    'fixed_page_bytes':PAGE,'fixed_limit_bytes':LIMIT,'fixed_refill_bytes':REFILL,'no_refill_sweep':True,'actual_os_pread_for_payload_ranges':True,
                    'decoder_still_discovers_ranges_from_in_memory_comp':True,
                    'remaining_debt':'make bit decoder consume pread source directly; isolated throughput/RSS; archive trust-root integration; hostile transfer; native/platform parity'},
        'next_if_supported':'replace in-memory BitReader source with this bounded pread refill primitive without changing charged ranges; rerun exact probes and fresh-process CPU/RSS',
        'next_if_falsified':'preserve exact overfetch excess; do not sweep refill sizes; use exact-byte physical reads or redesign co-access ownership while keeping 8x',
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-pread8-work')); p.add_argument('--v029-checkout',type=Path,required=True); p.add_argument('--worker',type=Path,default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-pread8.json')); a=p.parse_args()
    d=run(a.work_root,a.v029_checkout,a.worker); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'physical_refill':{k:v for k,v in d['physical_refill'].items() if k!='rows'},'profile':d['profile'],'hypothesis':d['hypothesis']},sort_keys=True))

if __name__=='__main__':main()
