from __future__ import annotations

"""Token-anchor physical-range oracle for Analytics Mode2.

The block-prefix physical oracle found a 40,933 B / 9.99x worst case: sparse decoded dependencies are
small, but restarting at a DEFLATE block header reads irrelevant prefix payload. DEFLATE symbol parsing
has no cross-symbol entropy state beyond the active Huffman tables, so a plausible compact index can
store a token-boundary bit anchor per 4 KiB decoded page plus the block's active code tables. This oracle
charges compressed payload from each needed page's token anchor through the furthest actually-needed
producing symbol, then unions overlapping byte ranges. It also charges a deliberately conservative
metadata envelope of 320 bytes of Huffman lengths/state for every block plus 16 bytes per page anchor.

Pre-registered support: every fixed 4 KiB request must have <=32,768 unique decoded dependencies,
<=32,768 unique compressed payload bytes after range union, and <=8 merged physical ranges; the
metadata envelope must fit the 1,681,984 B auxiliary budget required to remain below v0.29 Analytics.
No page/request/threshold sweep. A pass still does not claim a shipping reader: authentication, exact
serialized tables, actual pread syscalls, arbitrary unaligned requests, CPU and hostile-index bounds remain.
"""

import argparse
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
from benchmarks import v030_r4_deflate_physical_range_oracle as PHYS

SCHEMA='cmpct-v030-r4-deflate-token-anchor-physical-oracle-v1'
PAGE=4096
LIMIT=8*PAGE
LIMIT_RANGES=8
DUAL_OWNER_BYTES=4_453_188
ACCEPTED_V029_ANALYTICS=DUAL.ACCEPTED_V029_ANALYTICS
ANCHOR_BYTES=16
HUFFMAN_STATE_ENVELOPE_PER_BLOCK=320
BLOCK_RECORD_BYTES=16


def closure(parents,start,end):
    seen=set();stack=list(range(start,end))
    while stack:
        n=stack.pop()
        if n in seen:continue
        seen.add(n);p=parents[n]
        if p>=0 and p not in seen:stack.append(p)
    return seen


def page_anchor_bit(parsed,page:int,n:int)->int:
    pos=min(page*PAGE,n-1)
    # The producing token may start before the page boundary (copy token spanning it); starting at that
    # token is sufficient and costs at most one token of extra compressed payload.
    return int(parsed['starts'][pos])


def merge_ranges(ranges:list[tuple[int,int]])->list[tuple[int,int]]:
    if not ranges:return []
    ranges=sorted(ranges);out=[ranges[0]]
    for s,e in ranges[1:]:
        ps,pe=out[-1]
        if s<=pe:out[-1]=(ps,max(pe,e))
        else:out.append((s,e))
    return out


def charge(parsed,nodes:set[int],n:int)->dict:
    by_page={}
    for node in nodes:
        page=node//PAGE;by_page[page]=max(by_page.get(page,0),int(parsed['ends'][node]))
    raw=[]
    for page,end_bit in sorted(by_page.items()):
        start_bit=page_anchor_bit(parsed,page,n);raw.append((start_bit//8,(end_bit+7)//8))
    merged=merge_ranges(raw);total=sum(e-s for s,e in merged)
    return {'anchor_pages':len(by_page),'merged_ranges':len(merged),'compressed_bytes_touched':total,'compressed_amplification':total/PAGE,'ranges':[{'start_byte':s,'end_byte':e,'bytes':e-s} for s,e in merged]}


def starts(n:int)->list[int]:
    if n<=PAGE:return [0]
    s=list(range(0,n-PAGE+1,PAGE));tail=n-PAGE
    if s[-1]!=tail:s.append(tail)
    return s


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_token_anchor_neutral');repair=V029._load(V029.REPAIR_PATH,'r4_token_anchor_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus);source=corpus/'04_analytics_and_database'
    rel=DUAL._npz_relation(source)['accepted'];npz=source.joinpath(*Path(rel['npz_path']).parts);info,comp,expected,method=CONE._raw_zip_member(npz,rel['member'])
    if method!=zipfile.ZIP_DEFLATED:raise RuntimeError('expected DEFLATE')
    t0=time.perf_counter();parsed=PHYS.parse_physical(comp);parse_wall=time.perf_counter()-t0;actual=zlib.decompress(comp,-15)
    if actual!=expected or len(parsed['parents'])!=len(actual):raise RuntimeError('parser mismatch')
    worst_dec=worst_comp=worst_ranges=None;total_dec=total_comp=total_ranges=0;reqs=starts(len(actual));t0=time.perf_counter()
    for s in reqs:
        e=min(s+PAGE,len(actual));nodes=closure(parsed['parents'],s,e);phys=charge(parsed,nodes,len(actual));row={'start':s,'end':e,'request_bytes':e-s,'unique_decoded_closure_bytes':len(nodes),'decoded_amplification':len(nodes)/max(1,e-s),**phys};total_dec+=len(nodes);total_comp+=phys['compressed_bytes_touched'];total_ranges+=phys['merged_ranges']
        if worst_dec is None or row['unique_decoded_closure_bytes']>worst_dec['unique_decoded_closure_bytes']:worst_dec=row
        if worst_comp is None or row['compressed_bytes_touched']>worst_comp['compressed_bytes_touched']:worst_comp=row
        if worst_ranges is None or row['merged_ranges']>worst_ranges['merged_ranges']:worst_ranges=row
    probe_wall=time.perf_counter()-t0;assert worst_dec and worst_comp and worst_ranges
    pages=math.ceil(len(actual)/PAGE);metadata=pages*ANCHOR_BYTES+len(parsed['blocks'])*(HUFFMAN_STATE_ENVELOPE_PER_BLOCK+BLOCK_RECORD_BYTES);aux=ACCEPTED_V029_ANALYTICS-DUAL_OWNER_BYTES
    passes=worst_dec['unique_decoded_closure_bytes']<=LIMIT and worst_comp['compressed_bytes_touched']<=LIMIT and worst_ranges['merged_ranges']<=LIMIT_RANGES and metadata<=aux
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'workload':'04_analytics_and_database','member':{'compressed_bytes':len(comp),'compressed_sha256':hashlib.sha256(comp).hexdigest(),'raw_bytes':len(actual),'raw_sha256':hashlib.sha256(actual).hexdigest(),'crc32':info.CRC},'parser':{'blocks':len(parsed['blocks']),'tokens':parsed['tokens'],'literal_tokens':parsed['literal_tokens'],'copy_tokens':parsed['copy_tokens'],'exact_raw_match':True,'parse_wall_s':parse_wall},'token_anchor_physical':{'page_bytes':PAGE,'requests':len(reqs),'limits':{'decoded_bytes':LIMIT,'compressed_bytes':LIMIT,'ranges':LIMIT_RANGES},'mean_decoded_closure_bytes':total_dec/len(reqs),'mean_compressed_bytes_touched':total_comp/len(reqs),'mean_merged_ranges':total_ranges/len(reqs),'worst_decoded':worst_dec,'worst_compressed':worst_comp,'worst_ranges':worst_ranges,'passes_payload_and_range_floor':passes,'probe_wall_s':probe_wall},'economics':{'dual_owner_bytes':DUAL_OWNER_BYTES,'accepted_v029_bytes':ACCEPTED_V029_ANALYTICS,'max_auxiliary_bytes_to_beat_v029':aux,'page_anchors':pages,'anchor_bytes':pages*ANCHOR_BYTES,'blocks':len(parsed['blocks']),'huffman_state_envelope_bytes':len(parsed['blocks'])*HUFFMAN_STATE_ENVELOPE_PER_BLOCK,'block_record_bytes':len(parsed['blocks'])*BLOCK_RECORD_BYTES,'total_metadata_envelope_bytes':metadata,'metadata_within_budget':metadata<=aux,'remaining_aux_budget_after_envelope':aux-metadata},'hypothesis':{'token_anchor_sparse_reader_has_physical_8x_path':passes},'contract':{'diagnostic_only':True,'release_credit':False,'lower_bound_only':True,'no_threshold_sweep':True,'no_page_size_sweep':True,'no_request_size_sweep':True,'no_product_format_change':True,'important_limitation':'compressed payload and conservative index envelope are charged, but exact serialized Huffman tables, authentication/Merkle data, actual pread syscall granularity, parsing CPU, unaligned requests and hostile-index bounds remain'},'next_if_supported':'implement an authenticated serialized token-anchor index + actual os.pread reader; test arbitrary offsets and held-out/hostile NPY relations before integration','next_if_falsified':'preserve negative and change owner boundary; token anchors cannot recover physical locality within 8x'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-token-anchor-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-token-anchor.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'member':d['member'],'parser':d['parser'],'token_anchor_physical':d['token_anchor_physical'],'economics':d['economics'],'hypothesis':d['hypothesis']},indent=2))
if __name__=='__main__':main()
