from __future__ import annotations

"""Can existing page anchors predict bulk compressed ranges without new persisted metadata?

Mission Lock / Referee
======================
The sparse reader already persists, for each 4 KiB output page, the compressed bit start of the token
containing that page boundary plus DEFLATE block Huffman state. The direct-pread adapter proved byte-exact
physical decoding but required thousands of 8-byte syscalls. This referee asks whether those *existing*
anchors are enough to precompute a small number of bulk compressed reads for every page the unchanged
reader actually touches, including recursively requested dependency pages.

For touched page p, the predicted interval starts at anchor[p].bit_start. If anchor[p+1]'s token starts
exactly at the next page boundary, its bit start is the exclusive end. If that token begins before the
boundary and crosses it, decode exactly that one token (using already-persisted Huffman state) to learn
its end bit. The last page uses compressed EOF as a conservative end. No new archive metadata is introduced.

Hypothesis
----------
On a deterministic mixed literal/copy stream, the union of anchor-derived intervals for every page touched
by ColdReader must cover every compressed byte actually consumed. Range count is measured as the number
of touched pages rather than falsely assuming one range/request. Overfetch is measured, not threshold-
tuned; Office's frozen 22-byte slack will decide transfer separately.

Disproof
--------
One uncovered byte or inability to derive an endpoint falsifies this no-new-metadata bulk-prefetch idea.
PASS is only a mechanism prerequisite; it gives no Office/locality/release credit.
"""

import argparse,json,os
from pathlib import Path
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA='cmpct-v030-r4-anchor-bulk-prefetch-referee-v2'
PAGE=4096


def _token_end(comp:bytes,anchor:dict,blocks:list[dict])->int:
    bid=anchor['block_id'];b=blocks[bid];br=CONE.BitReader(comp);br.bit=anchor['bit_start']
    if b['type']==0:br.read(8);return br.bit
    if b['type']==1:ll,dd=CONE.FIXED
    elif b['type']==2:ll,dd=CONE._table(b['ll_lengths']),CONE._table(b['dd_lengths'])
    else:raise RuntimeError('unsupported block type')
    sym=CONE._decode(br,ll)
    if sym<256 or sym==256:return br.bit
    if 257<=sym<=285:
        li=sym-257;br.read(CONE.LEN_EXTRA[li]);ds=CONE._decode(br,dd)
        if ds>=len(CONE.DIST_BASE):raise RuntimeError('invalid distance symbol')
        br.read(CONE.DIST_EXTRA[ds]);return br.bit
    raise RuntimeError('reserved symbol')


def _predict(comp:bytes,anchors:list[dict],blocks:list[dict],page:int)->tuple[int,int]:
    start_bit=anchors[page]['bit_start']
    if page+1>=len(anchors):end_bit=len(comp)*8
    else:
        nexta=anchors[page+1];boundary=(page+1)*PAGE
        if nexta['token_start']==boundary:end_bit=nexta['bit_start']
        elif nexta['token_start']<boundary:end_bit=_token_end(comp,nexta,blocks)
        else:raise RuntimeError('next anchor starts after page boundary')
    return start_bit//8,(end_bit+7)//8


def _covers(predicted,actual)->bool:
    ps=SRC._merge(predicted)
    for a,b in SRC._merge(actual):
        pos=a
        for x,y in ps:
            if y<=pos:continue
            if x>pos:break
            pos=max(pos,y)
            if pos>=b:break
        if pos<b:return False
    return True


def run()->dict:
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    rows=[];failures=0
    for p in range(len(anchors)):
        base=p*PAGE;end=min(len(raw),base+PAGE);r=COLD.ColdReader(comp,anchors,blocks,len(raw));got=r.read(base,end)
        touched=sorted(r.anchor_frames);pred=[_predict(comp,anchors,blocks,q) for q in touched]
        logical=SRC._bytes(r.payload_ranges);pred_bytes=SRC._bytes(pred);covered=_covers(pred,r.payload_ranges);exact=got==raw[base:end];ok=covered and exact
        if not ok:failures+=1
        rows.append({'page':p,'touched_pages':touched,'predicted_ranges':pred,'predicted_range_count':len(pred),'predicted_unique_bytes':pred_bytes,'logical_payload_bytes':logical,'overfetch_bytes':pred_bytes-logical,'covered':covered,'exact':exact})
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'pages':len(anchors)},'failures':failures,
            'summary':{'max_overfetch_bytes':max(x['overfetch_bytes'] for x in rows),'mean_overfetch_bytes':sum(x['overfetch_bytes'] for x in rows)/len(rows),'max_predicted_bytes':max(x['predicted_unique_bytes'] for x in rows),'max_ranges_per_request':max(x['predicted_range_count'] for x in rows),'mean_ranges_per_request':sum(x['predicted_range_count'] for x in rows)/len(rows)},
            'rows':rows,'hypothesis':{'existing_anchors_predict_covering_bulk_payload_ranges':failures==0},
            'contract':{'diagnostic_only':True,'release_credit':False,'no_new_persisted_metadata':True,'page_bytes':PAGE,'coldreader_unchanged':True,'recursive_touched_pages_charged':True,'office_22b_slack_not_assumed':True,
                        'remaining_debt':'Office transfer with 644B groups+locator/root; physical pread verification; throughput/RSS; auth/recovery; native parity'}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-anchor-bulk-prefetch.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
