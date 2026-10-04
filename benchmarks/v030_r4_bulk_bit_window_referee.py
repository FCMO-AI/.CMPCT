from __future__ import annotations

"""Causal referee for bulk bit extraction on the accepted bounded compressed window.

Mission lock
============
The bounded-window referee preserved the exact physical geometry and recovered 63.4% of the dense
source-dispatch speedup, but its bit reader still loops once per requested bit. DEFLATE decoding asks
for many 1-bit Huffman steps plus bounded extra-bit fields, so Python loop traffic remains a plausible
runtime debt. Replace only ``AbsoluteWindowBitReader.read`` with direct little-endian integer loads
from at most four bytes. Keep bit offsets, alignment, page windows, 48-bit guard, pread ranges/calls,
reconstruction and requests identical.

Disproof
========
Any byte/range/call/page mismatch rejects semantics. Timing must improve a majority of probes and the
median bulk/window ratio must be <1.0 to support the runtime hypothesis. No representation or release
credit follows from this synthetic causal test.
"""

import argparse,json,os,statistics,tempfile,time
from pathlib import Path
from benchmarks import v030_r4_bounded_token_guard_pread_referee as G
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC
from benchmarks import v030_r4_window_guard_dispatch_referee as WINDOW

SCHEMA='cmpct-v030-r4-bulk-bit-window-referee-v1';REPS=9;LIMIT=8*G.PAGE

class BulkBitReader(WINDOW.AbsoluteWindowBitReader):
    def read(self,n:int)->int:
        if n==0:return 0
        if n<0 or n>24:raise ValueError('bulk bit read outside validated bound')
        byte_abs=self.bit>>3;shift=self.bit&7;idx=byte_abs-self.base_byte
        need=(shift+n+7)>>3
        if idx<0 or idx+need>len(self.data):raise ValueError('guarded local compressed window exhausted')
        word=self.data[idx]
        if need>1:word|=self.data[idx+1]<<8
        if need>2:word|=self.data[idx+2]<<16
        if need>3:word|=self.data[idx+3]<<24
        v=(word>>shift)&((1<<n)-1);self.bit+=n;return v

class BulkWindowReader(WINDOW.WindowGuardedReader):
    def _decode_page(self,page:int,depth:int)->bytes:
        cached=self.page_cache.get(page)
        if cached is not None:return cached
        anchor=self.anchors[page];self.anchor_frames.add(page);page_base=page*COLD.PAGE;page_end=min(page_base+COLD.PAGE,self.output_bytes)
        out_start=anchor['token_start'];out_pos=out_start;local=bytearray();bid=anchor['block_id'];base,window=self.comp.ensure_page(page)
        br=BulkBitReader(window,base,anchor['bit_start']);segment_start=br.bit;tables=self._tables(bid)
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

def _run(cls,fd,comp,anchors,blocks,raw,a,b):
    src=WINDOW.WindowGuardedSource(fd,len(comp),anchors);t=time.perf_counter();r=cls(src,anchors,blocks,len(raw));got=r.read(a,b);return src,r,got,time.perf_counter()-t

def run()->dict:
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-G.PAGE-17),max(0,len(raw)-G.PAGE)]));rows=[];failures=0
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'payload.deflate';p.write_bytes(comp);fd=os.open(p,os.O_RDONLY)
        try:
            for a in starts:
                b=min(len(raw),a+G.PAGE);wt=[];bt=[];identity=True;bounded=True;last=None
                for _ in range(REPS):
                    ws,wr,wg,w=_run(WINDOW.WindowGuardedReader,fd,comp,anchors,blocks,raw,a,b);bs,br,bg,t=_run(BulkWindowReader,fd,comp,anchors,blocks,raw,a,b)
                    wt.append(w);bt.append(t)
                    identity&=(wg==bg==raw[a:b] and G._merge(ws.ranges)==G._merge(bs.ranges) and ws.calls==bs.calls and ws.pages==bs.pages==wr.anchor_frames==br.anchor_frames and SRC._covers(bs.ranges,br.payload_ranges) and wr.payload_bytes()==br.payload_bytes())
                    bounded&=bs.max_live_window_bytes<=LIMIT;last=(ws,wr,bs,br)
                wm=statistics.median(wt);bm=statistics.median(bt);ws,wr,bs,br=last;ok=identity and bounded
                if not ok:failures+=1
                rows.append({'start':a,'end':b,'physical_identity':identity,'physical_bytes':SRC._bytes(bs.physical_ranges()),'calls':bs.calls,'max_live_window_bytes':bs.max_live_window_bytes,'window_wall_median_s':wm,'bulk_wall_median_s':bm,'bulk_vs_window_wall_ratio':bm/max(wm,1e-12),'timing_improved':bm<wm,'pass':ok})
        finally:os.close(fd)
    ratios=[r['bulk_vs_window_wall_ratio'] for r in rows];improved=sum(r['timing_improved'] for r in rows)
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'anchors':len(anchors),'probes':len(rows),'repetitions':REPS},'failures':failures,'rows':rows,'summary':{'physical_identity_probes':sum(r['physical_identity'] for r in rows),'bounded_window_probes':sum(r['max_live_window_bytes']<=LIMIT for r in rows),'timing_improved_probes':improved,'median_bulk_vs_window_wall_ratio':statistics.median(ratios),'mean_bulk_vs_window_wall_ratio':sum(ratios)/len(ratios),'max_live_window_bytes':max(r['max_live_window_bytes'] for r in rows)},'hypothesis':{'bulk_bit_read_preserves_physical_semantics':failures==0,'bulk_bit_read_reduces_runtime_debt':improved>len(rows)//2 and statistics.median(ratios)<1.0},'contract':{'diagnostic_research_only':True,'release_credit':False,'physical_ranges_and_calls_identical':True,'same_bounded_windows':True,'same_48bit_guard':True,'no_archive_sized_buffer':True,'no_threshold_sweep':True,'remaining_debt':'Office transfer first; then fresh-process CPU/wall/RSS/throughput, serialized auth/root/recovery, native/platform parity'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-bulk-bit-window.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
