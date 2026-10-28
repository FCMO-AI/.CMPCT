from __future__ import annotations

"""Separate guarded physical-I/O cost from Python per-byte source dispatch.

The cached guarded source preserved exactly the RFC-1951 48-bit page intervals and improved every probe,
but ColdReader still calls a Python `__getitem__` for each compressed byte. This diagnostic keeps the
identical page-triggered `os.pread` calls/ranges, but writes returned bytes into a bytearray so BitReader
uses the built-in C-level byte indexing path. Unread bytes are poison-filled. We run two distinct poison
values and require identical exact output plus post-hoc coverage of every logical compressed range.

This deliberately allocates one compressed-stream-sized bytearray and therefore is NOT a product memory
plan. Its only purpose is causal attribution: if wall time collapses while physical I/O stays identical,
the remaining slowdown belongs to the Python segmented-source dispatch and is a candidate for native bulk
implementation, not more range/metadata tuning.
"""

import argparse,json,os,statistics,tempfile,time
from pathlib import Path
from benchmarks import v030_r4_bounded_token_guard_pread_referee as G
from benchmarks import v030_r4_cached_guard_pread_referee as CACHED
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA='cmpct-v030-r4-dense-guard-dispatch-referee-v1';REPS=5;POISONS=(0x00,0xA5)

class DenseGuardedBuffer(bytearray):
    def __init__(self,fd:int,size:int,anchors:list[dict],poison:int):
        super().__init__([poison] * size)
        self.fd=fd;self.size=size;self.anchors=anchors;self.pages=set();self.ranges=[];self.calls=0;self.poison=poison
    def ensure_page(self,page:int):
        if page in self.pages:return
        a=self.anchors[page];start=a['bit_start']
        if page+1>=len(self.anchors):end=self.size*8
        else:
            n=self.anchors[page+1];boundary=(page+1)*G.PAGE
            if n['token_start']==boundary:end=n['bit_start']
            elif n['token_start']<boundary:end=min(self.size*8,n['bit_start']+G.MAX_TOKEN_BITS)
            else:raise RuntimeError('next anchor starts after page boundary')
        lo=start//8;hi=(end+7)//8;data=os.pread(self.fd,hi-lo,lo)
        if len(data)!=hi-lo:raise RuntimeError('short dense guarded pread')
        self[lo:hi]=data;self.ranges.append((lo,hi));self.pages.add(page);self.calls+=1
    def physical_ranges(self):return G._merge(self.ranges)

class DenseGuardedReader(COLD.ColdReader):
    def _decode_page(self,page,depth):self.comp.ensure_page(page);return super()._decode_page(page,depth)

def _run(reader_cls,src_cls,fd,comp,anchors,blocks,raw,start,end,*args):
    src=src_cls(fd,len(comp),anchors,*args);t=time.perf_counter();r=reader_cls(src,anchors,blocks,len(raw));got=r.read(start,end);return src,r,got,time.perf_counter()-t

def run():
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-G.PAGE-17),max(0,len(raw)-G.PAGE)]));rows=[];fails=0
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'payload.deflate';p.write_bytes(comp);fd=os.open(p,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+G.PAGE);cached_times=[];dense_times=[];identity=True;last=None
                for _ in range(REPS):
                    cs,cr,cg,cw=_run(CACHED.CachedGuardedReader,CACHED.CachedGuardedSource,fd,comp,anchors,blocks,raw,start,end);cached_times.append(cw)
                    poison_results=[]
                    for poison in POISONS:
                        ds,dr,dg,dw=_run(DenseGuardedReader,DenseGuardedBuffer,fd,comp,anchors,blocks,raw,start,end,poison);poison_results.append((ds,dr,dg,dw));dense_times.append(dw)
                    for ds,dr,dg,dw in poison_results:
                        identity &= (dg==cg==raw[start:end] and G._merge(ds.ranges)==G._merge(cs.ranges) and ds.calls==cs.calls and ds.pages==cs.pages==dr.anchor_frames==cr.anchor_frames and SRC._covers(ds.ranges,dr.payload_ranges) and dr.payload_bytes()==cr.payload_bytes())
                    last=(cs,cr,poison_results)
                cm=statistics.median(cached_times);dm=statistics.median(dense_times);improved=dm<cm
                cs,cr,prs=last
                ok=identity
                if not ok:fails+=1
                rows.append({'start':start,'end':end,'physical_identity':identity,'physical_bytes':SRC._bytes(cs.physical_ranges()),'calls':cs.calls,'cached_wall_median_s':cm,'dense_wall_median_s':dm,'dense_vs_cached_wall_ratio':dm/max(cm,1e-12),'dense_timing_improved':improved,'pass':ok})
        finally:os.close(fd)
    ratios=[r['dense_vs_cached_wall_ratio'] for r in rows]
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'anchors':len(anchors),'probes':len(rows),'repetitions':REPS,'poisons':list(POISONS)},'failures':fails,'rows':rows,'summary':{'physical_identity_probes':sum(r['physical_identity'] for r in rows),'timing_improved_probes':sum(r['dense_timing_improved'] for r in rows),'median_dense_vs_cached_wall_ratio':statistics.median(ratios),'mean_dense_vs_cached_wall_ratio':sum(ratios)/len(ratios)},'hypothesis':{'dense_builtin_indexing_preserves_physical_semantics':fails==0,'python_per_byte_dispatch_is_material':sum(r['dense_timing_improved'] for r in rows)>len(rows)//2},'contract':{'diagnostic_only':True,'release_credit':False,'dense_buffer_is_not_product_memory_plan':True,'physical_ranges_and_calls_identical':True,'two_poison_values':True,'same_48bit_guard':True,'remaining_debt':'implement equivalent segmented/bulk access without archive-sized buffer; transfer to Office; auth root; fresh-process RSS/throughput; native/platform parity'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-dense-guard-dispatch.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
