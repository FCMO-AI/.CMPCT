from __future__ import annotations

"""Hostile review of the RFC-1951 guarded physical source: isolate Python lookup overhead.

The bounded-token-guard referee established exact physical semantics with 0 fallbacks, <=4 B overfetch and
97.81% fewer syscalls than 8-byte pread, but was ~2x slower. Its byte source linearly scans every previously
loaded page interval on *every compressed byte access*. This experiment changes no physical range, guard,
metadata, reader grammar, or I/O policy. It adds only an in-memory last-hit cache plus bisect lookup on a
miss, then requires byte/call/range identity against the slow guarded source.

Hypothesis: lookup acceleration preserves identical physical behavior and reduces repeated hosted wall time
relative to the slow guarded source. Timing is evidence about implementation overhead, not release credit.
"""

import argparse,bisect,json,os,statistics,tempfile,time
from pathlib import Path
from benchmarks import v030_r4_bounded_token_guard_pread_referee as G
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA='cmpct-v030-r4-cached-guard-pread-referee-v1';REPS=5

class CachedGuardedSource(G.GuardedSource):
    __slots__=('sorted_starts','sorted_ranges','sorted_buffers','hot_base','hot_end','hot_buf')
    def __init__(self,fd,size,anchors):
        super().__init__(fd,size,anchors);self.sorted_starts=[];self.sorted_ranges=[];self.sorted_buffers=[];self.hot_base=-1;self.hot_end=-1;self.hot_buf=b''
    def ensure_page(self,page):
        before=len(self.ranges);super().ensure_page(page)
        if len(self.ranges)==before:return
        r=self.ranges[-1];buf=self.buffers[-1];i=bisect.bisect_left(self.sorted_starts,r[0]);self.sorted_starts.insert(i,r[0]);self.sorted_ranges.insert(i,r);self.sorted_buffers.insert(i,buf)
        self.hot_base,self.hot_end=r;self.hot_buf=buf
    def __getitem__(self,index):
        if index<0:index+=self.size
        if not 0<=index<self.size:raise IndexError(index)
        if self.hot_base<=index<self.hot_end:return self.hot_buf[index-self.hot_base]
        i=bisect.bisect_right(self.sorted_starts,index)-1
        while i>=0:
            a,b=self.sorted_ranges[i]
            if a<=index<b:
                self.hot_base,self.hot_end=a,b;self.hot_buf=self.sorted_buffers[i];return self.hot_buf[index-a]
            if b<=index:break
            i-=1
        self.fallbacks+=1;raise RuntimeError(f'compressed byte {index} outside cached guarded intervals')

class CachedGuardedReader(COLD.ColdReader):
    def _decode_page(self,page,depth):self.comp.ensure_page(page);return super()._decode_page(page,depth)

def _one(reader_cls,source_cls,fd,comp,anchors,blocks,raw,start,end):
    src=source_cls(fd,len(comp),anchors);t=time.perf_counter();r=reader_cls(src,anchors,blocks,len(raw));got=r.read(start,end);wall=time.perf_counter()-t
    return src,r,got,wall

def run():
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-G.PAGE-17),max(0,len(raw)-G.PAGE)]));rows=[];fails=0
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'payload.deflate';path.write_bytes(comp);fd=os.open(path,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+G.PAGE);slow=[];fast=[];last=None
                for _ in range(REPS):
                    ss,sr,sg,sw=_one(G.GuardedReader,G.GuardedSource,fd,comp,anchors,blocks,raw,start,end);slow.append(sw)
                    fs,fr,fg,fw=_one(CachedGuardedReader,CachedGuardedSource,fd,comp,anchors,blocks,raw,start,end);fast.append(fw);last=(ss,sr,sg,fs,fr,fg)
                ss,sr,sg,fs,fr,fg=last
                same=(sg==fg==raw[start:end] and G._merge(ss.ranges)==G._merge(fs.ranges) and ss.calls==fs.calls and ss.pages==fs.pages==sr.anchor_frames==fr.anchor_frames and ss.fallbacks==fs.fallbacks==0)
                sm=statistics.median(slow);fm=statistics.median(fast);improved=fm<sm;ok=same
                if not ok:fails+=1
                rows.append({'start':start,'end':end,'physical_identity':same,'physical_bytes':SRC._bytes(fs.physical_ranges()),'calls':fs.calls,'slow_wall_median_s':sm,'cached_wall_median_s':fm,'cached_vs_slow_wall_ratio':fm/max(sm,1e-12),'timing_improved':improved,'pass':ok})
        finally:os.close(fd)
    ratios=[r['cached_vs_slow_wall_ratio'] for r in rows]
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'anchors':len(anchors),'probes':len(rows),'repetitions':REPS},'failures':fails,'rows':rows,
            'summary':{'median_cached_vs_slow_wall_ratio':statistics.median(ratios),'mean_cached_vs_slow_wall_ratio':sum(ratios)/len(ratios),'timing_improved_probes':sum(r['timing_improved'] for r in rows),'physical_identity_probes':sum(r['physical_identity'] for r in rows)},
            'hypothesis':{'lookup_cache_preserves_physical_semantics':fails==0,'lookup_cache_reduces_median_wall_on_majority':sum(r['timing_improved'] for r in rows)>len(rows)//2},
            'contract':{'diagnostic_only':True,'release_credit':False,'physical_ranges_must_be_identical':True,'same_48bit_guard':True,'no_new_persisted_metadata':True,'timing_repetitions':REPS,'remaining_debt':'Office transfer, <=8x including archive-root auth, fresh-process RSS/throughput, native/platform parity'}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-cached-guard-pread.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
