from __future__ import annotations

"""Test bounded local compressed windows as the product-shaped successor to dense guarded dispatch.

Mission lock: keep the exact 4 KiB request, 8x locality envelope, RFC-1951 48-bit token guard,
page-triggered pread geometry and recursive reconstruction semantics.  The previous dense referee
proved Python source ``__getitem__`` dispatch is material, but paid O(compressed-stream) resident
memory.  Here each decoded page receives only its exact guarded contiguous pread bytes; the bit reader
indexes those built-in bytes directly and the window dies with the page decode.

Disproof: any byte mismatch, physical range/call/page mismatch, uncovered logical compressed range,
or live compressed window >32,768 B rejects the mechanism. Timing is repeated evidence only.
"""

import argparse,json,os,statistics,tempfile,time
from pathlib import Path
from benchmarks import v030_r4_bounded_token_guard_pread_referee as G
from benchmarks import v030_r4_cached_guard_pread_referee as CACHED
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_dense_guard_dispatch_referee as DENSE
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA='cmpct-v030-r4-window-guard-dispatch-referee-v1';REPS=7;LIMIT=8*G.PAGE

class AbsoluteWindowBitReader:
    def __init__(self,data:bytes,base_byte:int,bit:int):self.data=data;self.base_byte=base_byte;self.bit=bit
    def read(self,n:int)->int:
        if n==0:return 0
        lo=self.bit>>3;hi=(self.bit+n+7)>>3
        if lo<self.base_byte or hi>self.base_byte+len(self.data):raise ValueError('guarded local compressed window exhausted')
        v=0
        for i in range(n):
            idx=(self.bit>>3)-self.base_byte;v|=((self.data[idx]>>(self.bit&7))&1)<<i;self.bit+=1
        return v
    def align(self):self.bit=(self.bit+7)&~7

class WindowGuardedSource:
    def __init__(self,fd:int,size:int,anchors:list[dict]):
        self.fd=fd;self.size=size;self.anchors=anchors;self.pages=set();self.ranges=[];self.calls=0;self.max_live_window_bytes=0
    def ensure_page(self,page:int)->tuple[int,bytes]:
        if page in self.pages:raise RuntimeError('page window requested twice after decoded-page cache')
        a=self.anchors[page];start=a['bit_start']
        if page+1>=len(self.anchors):end=self.size*8
        else:
            n=self.anchors[page+1];boundary=(page+1)*G.PAGE
            if n['token_start']==boundary:end=n['bit_start']
            elif n['token_start']<boundary:end=min(self.size*8,n['bit_start']+G.MAX_TOKEN_BITS)
            else:raise RuntimeError('next anchor starts after page boundary')
        lo=start//8;hi=(end+7)//8;data=os.pread(self.fd,hi-lo,lo)
        if len(data)!=hi-lo:raise RuntimeError('short guarded window pread')
        self.ranges.append((lo,hi));self.pages.add(page);self.calls+=1;self.max_live_window_bytes=max(self.max_live_window_bytes,len(data))
        return lo,data
    def physical_ranges(self):return G._merge(self.ranges)

class WindowGuardedReader(COLD.ColdReader):
    def _decode_page(self,page:int,depth:int)->bytes:
        cached=self.page_cache.get(page)
        if cached is not None:return cached
        anchor=self.anchors[page];self.anchor_frames.add(page);page_base=page*COLD.PAGE;page_end=min(page_base+COLD.PAGE,self.output_bytes)
        out_start=anchor['token_start'];out_pos=out_start;local=bytearray();bid=anchor['block_id'];base,window=self.comp.ensure_page(page)
        br=AbsoluteWindowBitReader(window,base,anchor['bit_start']);segment_start=br.bit;tables=self._tables(bid)
        def finish_segment():
            nonlocal segment_start
            a=segment_start//8;b=(br.bit+7)//8
            if b>a:self.payload_ranges.append((a,b))
            segment_start=br.bit
        while out_pos<page_end:
            block=self.blocks[bid]
            if out_pos>=block['out_end']:
                finish_segment();bid+=1
                if bid>=len(self.blocks):raise RuntimeError('ran beyond final DEFLATE block')
                block=self.blocks[bid];br.bit=block['first_token_bit'];segment_start=br.bit;tables=self._tables(bid)
            token_start=out_pos
            if block['type']==0:
                sym=br.read(8);self.symbols_decoded+=1;token=bytes([sym])
            else:
                ll,dd=tables;sym=CONE._decode(br,ll);self.symbols_decoded+=1
                if sym<256:token=bytes([sym])
                elif sym==256:
                    if out_pos!=block['out_end']:raise RuntimeError('early EOB relative to persisted block state')
                    continue
                elif 257<=sym<=285:
                    li=sym-257;length=CONE.LEN_BASE[li]+br.read(CONE.LEN_EXTRA[li]);ds=CONE._decode(br,dd)
                    if ds>=len(CONE.DIST_BASE):raise RuntimeError('invalid distance symbol')
                    distance=CONE.DIST_BASE[ds]+br.read(CONE.DIST_EXTRA[ds])
                    if distance>out_pos:raise RuntimeError('distance beyond output')
                    seed_len=min(distance,length);src0=out_pos-distance;src1=src0+seed_len;seed=bytearray()
                    if src0<out_start:
                        prior_end=min(src1,out_start);seed+=self.read(src0,prior_end,depth+1);src0=prior_end
                    if src0<src1:
                        lo=src0-out_start;hi=src1-out_start
                        if lo<0 or hi>len(local):raise RuntimeError('local LZ77 history unavailable')
                        seed+=local[lo:hi]
                    if len(seed)!=seed_len or not seed:raise RuntimeError('failed to reconstruct LZ77 seed')
                    token=bytes((seed*((length+len(seed)-1)//len(seed)))[:length])
                else:raise RuntimeError('reserved literal/length symbol')
            local+=token;out_pos=token_start+len(token)
        finish_segment();begin=page_base-out_start
        if begin<0 or page_end-out_start>len(local):raise RuntimeError('page reconstruction bounds mismatch')
        page_bytes=bytes(local[begin:page_end-out_start])
        if len(page_bytes)!=page_end-page_base:raise RuntimeError('short page reconstruction')
        self.page_cache[page]=page_bytes;return page_bytes

def _run(kind,fd,comp,anchors,blocks,raw,start,end):
    if kind=='cached':src=CACHED.CachedGuardedSource(fd,len(comp),anchors);cls=CACHED.CachedGuardedReader
    elif kind=='dense':src=DENSE.DenseGuardedBuffer(fd,len(comp),anchors,0xA5);cls=DENSE.DenseGuardedReader
    else:src=WindowGuardedSource(fd,len(comp),anchors);cls=WindowGuardedReader
    t=time.perf_counter();r=cls(src,anchors,blocks,len(raw));got=r.read(start,end);return src,r,got,time.perf_counter()-t

def run()->dict:
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-G.PAGE-17),max(0,len(raw)-G.PAGE)]));rows=[];failures=0
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'payload.deflate';p.write_bytes(comp);fd=os.open(p,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+G.PAGE);ct=[];dt=[];wt=[];identity=True;bounded=True;last=None
                for _ in range(REPS):
                    cs,cr,cg,cw=_run('cached',fd,comp,anchors,blocks,raw,start,end);ds,dr,dg,dw=_run('dense',fd,comp,anchors,blocks,raw,start,end);ws,wr,wg,ww=_run('window',fd,comp,anchors,blocks,raw,start,end)
                    ct.append(cw);dt.append(dw);wt.append(ww)
                    identity&=(wg==dg==cg==raw[start:end] and G._merge(ws.ranges)==G._merge(cs.ranges)==G._merge(ds.ranges) and ws.calls==cs.calls==ds.calls and ws.pages==cs.pages==ds.pages==wr.anchor_frames==cr.anchor_frames==dr.anchor_frames and SRC._covers(ws.ranges,wr.payload_ranges) and wr.payload_bytes()==cr.payload_bytes()==dr.payload_bytes())
                    bounded&=ws.max_live_window_bytes<=LIMIT;last=(ws,wr)
                cm=statistics.median(ct);dm=statistics.median(dt);wm=statistics.median(wt);ws,wr=last;ok=identity and bounded
                if not ok:failures+=1
                gain=max(0.0,cm-dm);recovered=(cm-wm)/gain if gain>1e-12 else 0.0
                rows.append({'start':start,'end':end,'physical_identity':identity,'physical_bytes':SRC._bytes(ws.physical_ranges()),'calls':ws.calls,'max_live_window_bytes':ws.max_live_window_bytes,'cached_wall_median_s':cm,'dense_wall_median_s':dm,'window_wall_median_s':wm,'window_vs_cached_wall_ratio':wm/max(cm,1e-12),'window_vs_dense_wall_ratio':wm/max(dm,1e-12),'dense_speedup_recovered_fraction':recovered,'window_timing_improved':wm<cm,'pass':ok})
        finally:os.close(fd)
    ratios=[r['window_vs_cached_wall_ratio'] for r in rows];drat=[r['window_vs_dense_wall_ratio'] for r in rows];rec=[r['dense_speedup_recovered_fraction'] for r in rows];improved=sum(r['window_timing_improved'] for r in rows)
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'anchors':len(anchors),'probes':len(rows),'repetitions':REPS},'failures':failures,'rows':rows,'summary':{'physical_identity_probes':sum(r['physical_identity'] for r in rows),'bounded_window_probes':sum(r['max_live_window_bytes']<=LIMIT for r in rows),'timing_improved_probes':improved,'median_window_vs_cached_wall_ratio':statistics.median(ratios),'mean_window_vs_cached_wall_ratio':sum(ratios)/len(ratios),'median_window_vs_dense_wall_ratio':statistics.median(drat),'median_dense_speedup_recovered_fraction':statistics.median(rec),'max_live_window_bytes':max(r['max_live_window_bytes'] for r in rows)},'hypothesis':{'bounded_window_preserves_physical_semantics':failures==0,'bounded_window_removes_material_dispatch_debt':improved>len(rows)//2 and statistics.median(ratios)<1.0,'recovers_at_least_half_dense_speedup_median':statistics.median(rec)>=0.5},'contract':{'diagnostic_research_only':True,'release_credit':False,'same_48bit_guard':True,'physical_ranges_and_calls_identical':True,'no_archive_sized_compressed_buffer':True,'max_live_window_bound_bytes':LIMIT,'timing_does_not_override_semantic_failure':True,'remaining_debt':'transfer to full Office probes; serialize/root/authenticate locator+metadata; fresh-process CPU/RSS/throughput; hostile corruption/recovery; native/platform parity'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-window-guard-dispatch.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
