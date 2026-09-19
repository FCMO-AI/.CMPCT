from __future__ import annotations

"""Physical compressed-range lower bound for the Analytics Mode2 DEFLATE member.

The exact sparse byte closure passes (~1.01x) and a 4 KiB anchor localization model passes (~3.90x),
while whole-page dependency ownership fails catastrophically. This oracle removes the next major gift:
compressed payload I/O. It parses the exact frozen raw-DEFLATE member and records, for every decoded byte,
its immediate LZ77 parent plus the producing symbol's bit interval and DEFLATE block. For each fixed 4 KiB
request it computes the exact sparse decoded closure, then charges the physical compressed prefix of every
touched block from that block's header byte through the furthest producing symbol needed in that block.
Block ranges are disjoint, so their byte lengths sum directly.

Pre-registered support requires, for every request: <=32,768 unique decoded closure bytes, <=32,768
compressed physical bytes touched, and <=8 touched block ranges. No request-size, page-size or threshold
sweep. This remains a lower bound because it gifts compact output->symbol anchors, cached/encoded Huffman
state, authentication metadata, syscall overhead and CPU parsing cost.
"""

import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE

SCHEMA='cmpct-v030-r4-deflate-physical-range-oracle-v1'
REQUEST=4096
LIMIT_DECODED=8*REQUEST
LIMIT_COMPRESSED=8*REQUEST
LIMIT_RANGES=8
DUAL_OWNER_BYTES=4_453_188
ACCEPTED_V029_ANALYTICS=DUAL.ACCEPTED_V029_ANALYTICS


def parse_physical(raw:bytes)->dict:
    br=CONE.BitReader(raw)
    parents=array('i');starts=array('I');ends=array('I');block_ids=array('I');blocks=[];token_count=literal_tokens=copy_tokens=0;bid=0
    while True:
        header=br.bit;final=br.read(1);btype=br.read(2);out0=len(parents)
        if btype==0:
            br.align();n=br.read(16);nn=br.read(16)
            if (n^0xFFFF)!=nn:raise ValueError('stored LEN/NLEN mismatch')
            for _ in range(n):
                s=br.bit;br.read(8);e=br.bit;parents.append(-1);starts.append(s);ends.append(e);block_ids.append(bid);token_count+=1;literal_tokens+=1
        elif btype in (1,2):
            ll,dd=CONE.FIXED if btype==1 else CONE._dynamic(br)
            while True:
                s=br.bit;sym=CONE._decode(br,ll)
                if sym<256:
                    e=br.bit;parents.append(-1);starts.append(s);ends.append(e);block_ids.append(bid);token_count+=1;literal_tokens+=1
                elif sym==256:break
                elif 257<=sym<=285:
                    li=sym-257
                    if li>=len(CONE.LEN_BASE):raise ValueError('invalid length')
                    length=CONE.LEN_BASE[li]+br.read(CONE.LEN_EXTRA[li]);ds=CONE._decode(br,dd)
                    if ds>=len(CONE.DIST_BASE):raise ValueError('invalid distance')
                    distance=CONE.DIST_BASE[ds]+br.read(CONE.DIST_EXTRA[ds])
                    if distance>len(parents):raise ValueError('distance beyond output')
                    e=br.bit;token_count+=1;copy_tokens+=1
                    for _ in range(length):
                        parents.append(len(parents)-distance);starts.append(s);ends.append(e);block_ids.append(bid)
                else:raise ValueError('reserved symbol')
        else:raise ValueError('reserved block type')
        blocks.append({'id':bid,'header_bit':header,'end_bit':br.bit,'out_start':out0,'out_end':len(parents),'type':btype});bid+=1
        if final:break
    return {'parents':parents,'starts':starts,'ends':ends,'block_ids':block_ids,'blocks':blocks,'tokens':token_count,'literal_tokens':literal_tokens,'copy_tokens':copy_tokens,'consumed_bits':br.bit}


def closure(parents:array,start:int,end:int)->set[int]:
    seen=set();stack=list(range(start,end))
    while stack:
        n=stack.pop()
        if n in seen:continue
        seen.add(n);p=parents[n]
        if p>=0 and p not in seen:stack.append(p)
    return seen


def charge(parsed:dict,nodes:set[int])->dict:
    furthest={}
    for n in nodes:
        bid=int(parsed['block_ids'][n]);furthest[bid]=max(furthest.get(bid,0),int(parsed['ends'][n]))
    ranges=[];total=0
    for bid,end_bit in sorted(furthest.items()):
        block=parsed['blocks'][bid];start_byte=block['header_bit']//8;end_byte=(end_bit+7)//8
        size=max(0,end_byte-start_byte);total+=size;ranges.append({'block':bid,'start_byte':start_byte,'end_byte':end_byte,'bytes':size})
    return {'compressed_ranges':len(ranges),'compressed_bytes_touched':total,'ranges':ranges}


def starts(n:int)->list[int]:
    if n<=REQUEST:return [0]
    out=list(range(0,n-REQUEST+1,REQUEST));tail=n-REQUEST
    if out[-1]!=tail:out.append(tail)
    return out


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_physical_neutral');repair=V029._load(V029.REPAIR_PATH,'r4_physical_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus);source=corpus/'04_analytics_and_database'
    rel=DUAL._npz_relation(source)['accepted'];npz=source.joinpath(*Path(rel['npz_path']).parts);info,comp,expected,method=CONE._raw_zip_member(npz,rel['member'])
    if method!=zipfile.ZIP_DEFLATED:raise RuntimeError('expected DEFLATE')
    t0=time.perf_counter();parsed=parse_physical(comp);parse_wall=time.perf_counter()-t0;actual=zlib.decompress(comp,-15)
    if actual!=expected or len(parsed['parents'])!=len(actual):raise RuntimeError('physical parser mismatch')
    worst_dec=worst_comp=worst_ranges=None;total_dec=total_comp=total_ranges=0;reqs=starts(len(actual));t0=time.perf_counter()
    for s in reqs:
        e=min(s+REQUEST,len(actual));nodes=closure(parsed['parents'],s,e);phys=charge(parsed,nodes);row={'start':s,'end':e,'request_bytes':e-s,'unique_decoded_closure_bytes':len(nodes),'decoded_amplification':len(nodes)/max(1,e-s),**phys,'compressed_amplification':phys['compressed_bytes_touched']/max(1,e-s)}
        total_dec+=len(nodes);total_comp+=phys['compressed_bytes_touched'];total_ranges+=phys['compressed_ranges']
        if worst_dec is None or row['unique_decoded_closure_bytes']>worst_dec['unique_decoded_closure_bytes']:worst_dec=row
        if worst_comp is None or row['compressed_bytes_touched']>worst_comp['compressed_bytes_touched']:worst_comp=row
        if worst_ranges is None or row['compressed_ranges']>worst_ranges['compressed_ranges']:worst_ranges=row
    probe_wall=time.perf_counter()-t0;assert worst_dec and worst_comp and worst_ranges
    passes=worst_dec['unique_decoded_closure_bytes']<=LIMIT_DECODED and worst_comp['compressed_bytes_touched']<=LIMIT_COMPRESSED and worst_ranges['compressed_ranges']<=LIMIT_RANGES
    aux=ACCEPTED_V029_ANALYTICS-DUAL_OWNER_BYTES;block_state=len(parsed['blocks'])*64;page_anchor=math.ceil(len(actual)/REQUEST)*16;index_env=block_state+page_anchor
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'workload':'04_analytics_and_database','relation':rel,'member':{'compressed_bytes':len(comp),'compressed_sha256':hashlib.sha256(comp).hexdigest(),'raw_bytes':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'crc32':info.CRC,'compress_type':info.compress_type},'parser':{'blocks':len(parsed['blocks']),'tokens':parsed['tokens'],'literal_tokens':parsed['literal_tokens'],'copy_tokens':parsed['copy_tokens'],'consumed_bits':parsed['consumed_bits'],'stream_bits':len(comp)*8,'parse_wall_s':parse_wall,'exact_raw_match':True},'physical_dependency':{'request_bytes':REQUEST,'requests':len(reqs),'limits':{'decoded_bytes':LIMIT_DECODED,'compressed_bytes':LIMIT_COMPRESSED,'ranges':LIMIT_RANGES},'mean_decoded_closure_bytes':total_dec/len(reqs),'mean_compressed_bytes_touched':total_comp/len(reqs),'mean_compressed_ranges':total_ranges/len(reqs),'worst_decoded':worst_dec,'worst_compressed':worst_comp,'worst_ranges':worst_ranges,'passes_physical_payload_floor':passes,'probe_wall_s':probe_wall},'economics':{'dual_owner_bytes':DUAL_OWNER_BYTES,'accepted_v029_bytes':ACCEPTED_V029_ANALYTICS,'max_auxiliary_bytes_to_beat_v029':aux,'illustrative_page_anchor_plus_block_state_bytes':index_env,'illustrative_index_within_budget':index_env<=aux},'hypothesis':{'physical_sparse_DEFLATE_payload_can_meet_8x_lower_bound':passes},'contract':{'diagnostic_only':True,'release_credit':False,'lower_bound_only':True,'no_threshold_sweep':True,'no_request_size_sweep':True,'no_product_format_change':True,'important_limitation':'charges compressed block-prefix payload ranges but gifts compact output-to-symbol anchors, encoded Huffman state, authentication metadata, syscall/seek overhead and parsing CPU'},'next_if_supported':'build a real authenticated sidecar/index reader and issue measured pread ranges against the frozen NPZ member; require exact arbitrary-offset reads and total stored bytes below v0.29 Analytics','next_if_falsified':'preserve negative and change owner boundary; compressed physical locality itself exceeds the 8x envelope'}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-physical-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-physical.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'member':d['member'],'parser':d['parser'],'physical_dependency':d['physical_dependency'],'economics':d['economics'],'hypothesis':d['hypothesis']},indent=2))
if __name__=='__main__':main()
