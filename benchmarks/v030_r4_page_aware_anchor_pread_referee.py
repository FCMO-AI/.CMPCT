from __future__ import annotations

"""Dependency-aware physical pread using only existing page anchors and block state.

Mission Lock
============
Two simpler policies were falsified on the same frozen mixed DEFLATE stream:
(1) 8-byte direct pread was exact but paid up to 2,100 syscalls/request;
(2) lazy whole-anchor intervals cut calls but fetched unrelated next-page intervals; and
(3) preplanning only the user-requested output pages failed 5/8 probes because LZ77 recursively needs
prior pages that cannot be known from the request alone.

ColdReader itself already discovers that dependency closure causally while decoding. This referee attaches
physical range planning to that exact event: immediately before `_decode_page(page)`, load only the interval
owned by *that logical page*. Recursive prior-page reads therefore trigger their own interval, but unrelated
physical-neighbour pages do not. Existing anchor/block metadata is unchanged.

Most interval ends are the next anchor bit. If the next anchor sits inside a token crossing a page boundary,
we decode only that one token's Huffman/length/distance bits through the physical byte source to obtain its
end. Those probe bytes and calls are charged; no resident compressed payload is consulted for planning.

Hypothesis
----------
This event-coupled policy will preserve exact output and logical payload accounting, require zero fallback
reads, cover the same dependency pages as ColdReader, reduce syscall count materially versus 8-byte pread,
and keep unique physical bytes within logical consumed payload + 2 B per touched page on the frozen stream.

Disproof
--------
Any mismatch, fallback, uncovered logical payload, bound violation, dependency-page mismatch, or failure to
reduce calls falsifies the mechanism. Timing is diagnostic only. Office transfer remains independently gated.
"""

import argparse
import bisect
import json
import os
import tempfile
import time
from pathlib import Path

from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA = "cmpct-v030-r4-page-aware-anchor-pread-referee-v1"
PAGE = 4096


def _merge(rs: list[tuple[int,int]]) -> list[tuple[int,int]]:
    out: list[list[int]]=[]
    for a,b in sorted(rs):
        if b<=a: continue
        if not out or a>out[-1][1]: out.append([a,b])
        else: out[-1][1]=max(out[-1][1],b)
    return [(a,b) for a,b in out]


class PageAwareSource:
    __slots__=("fd","size","anchors","blocks","ranges","buffers","calls","fallbacks","pages","probe_ranges","probe_calls")
    def __init__(self,fd:int,size:int,anchors:list[dict],blocks:list[dict]):
        self.fd=fd; self.size=size; self.anchors=anchors; self.blocks=blocks
        self.ranges:list[tuple[int,int]]=[]; self.buffers:list[bytes]=[]
        self.calls=0; self.fallbacks=0; self.pages:set[int]=set(); self.probe_ranges:list[tuple[int,int]]=[]; self.probe_calls=0
    def __len__(self): return self.size
    def _byte_from_loaded(self,index:int):
        for (a,b),data in zip(self.ranges,self.buffers):
            if a<=index<b: return data[index-a]
        return None
    def __getitem__(self,index:int)->int:
        if index<0:index+=self.size
        if not 0<=index<self.size: raise IndexError(index)
        v=self._byte_from_loaded(index)
        if v is None:
            self.fallbacks+=1
            raise RuntimeError(f"compressed byte {index} outside dependency-aware page intervals")
        return v
    def _probe_token_end(self,anchor:dict)->int:
        # A tiny direct source is used only to derive the end of one boundary-crossing token.
        probe=SRC.PreadByteSource(self.fd,self.size)
        bid=anchor['block_id']; b=self.blocks[bid]; br=CONE.BitReader(probe); br.bit=anchor['bit_start']
        if b['type']==0: br.read(8)
        else:
            if b['type']==1: ll,dd=CONE.FIXED
            elif b['type']==2: ll,dd=CONE._table(b['ll_lengths']),CONE._table(b['dd_lengths'])
            else: raise RuntimeError('unsupported block type')
            sym=CONE._decode(br,ll)
            if 257<=sym<=285:
                li=sym-257; br.read(CONE.LEN_EXTRA[li]); ds=CONE._decode(br,dd)
                if ds>=len(CONE.DIST_BASE): raise RuntimeError('invalid distance symbol')
                br.read(CONE.DIST_EXTRA[ds])
            elif sym>285: raise RuntimeError('reserved literal/length symbol')
        self.probe_ranges.extend(probe.ranges); self.probe_calls+=probe.calls
        return br.bit
    def ensure_page(self,page:int)->None:
        if page in self.pages:return
        a=self.anchors[page]; start_bit=a['bit_start']
        if page+1>=len(self.anchors): end_bit=self.size*8
        else:
            n=self.anchors[page+1]; boundary=(page+1)*PAGE
            if n['token_start']==boundary:end_bit=n['bit_start']
            elif n['token_start']<boundary:end_bit=self._probe_token_end(n)
            else:raise RuntimeError('next anchor starts after boundary')
        lo=start_bit//8; hi=(end_bit+7)//8
        data=os.pread(self.fd,hi-lo,lo)
        if len(data)!=hi-lo:raise RuntimeError('short page interval pread')
        self.ranges.append((lo,hi));self.buffers.append(data);self.calls+=1;self.pages.add(page)
    def physical_ranges(self):return _merge(self.ranges+self.probe_ranges)
    def physical_calls(self):return self.calls+self.probe_calls


class PageAwareReader(COLD.ColdReader):
    def _decode_page(self,page:int,depth:int)->bytes:
        self.comp.ensure_page(page)
        return super()._decode_page(page,depth)


def _timed(fn):
    c=time.process_time();w=time.perf_counter();x=fn();return x,time.process_time()-c,time.perf_counter()-w


def run()->dict:
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-PAGE-17),max(0,len(raw)-PAGE)]))
    rows=[];failures=0;tot={"resident_wall_s":0.0,"pread8_wall_s":0.0,"aware_wall_s":0.0,"pread8_calls":0,"aware_calls":0}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'payload.deflate';path.write_bytes(comp);fd=os.open(path,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+PAGE)
                def res():
                    r=COLD.ColdReader(comp,anchors,blocks,len(raw));return r,r.read(start,end)
                (rr,rg),_,rw=_timed(res)
                s8=SRC.PreadByteSource(fd,len(comp))
                def p8():
                    r=COLD.ColdReader(s8,anchors,blocks,len(raw));return r,r.read(start,end)
                (r8,g8),_,w8=_timed(p8)
                src=PageAwareSource(fd,len(comp),anchors,blocks)
                err=None
                try:
                    def aware():
                        r=PageAwareReader(src,anchors,blocks,len(raw));return r,r.read(start,end)
                    (ra,ga),_,wa=_timed(aware)
                except Exception as exc:
                    ra=None;ga=b'';wa=0.0;err=repr(exc)
                pr=src.physical_ranges();pb=SRC._bytes(pr);logical=r8.payload_bytes();touched=len(rr.anchor_frames)
                exact=rg==g8==ga==raw[start:end]
                covered=ra is not None and SRC._covers(pr,ra.payload_ranges)
                accounting=ra is not None and ra.payload_bytes()==logical
                pages_equal=ra is not None and src.pages==ra.anchor_frames==rr.anchor_frames
                bound=pb<=logical+2*touched
                calls=src.physical_calls();reduce=calls<s8.calls
                ok=err is None and exact and covered and accounting and pages_equal and bound and src.fallbacks==0 and reduce
                if not ok:failures+=1
                tot['resident_wall_s']+=rw;tot['pread8_wall_s']+=w8;tot['aware_wall_s']+=wa;tot['pread8_calls']+=s8.calls;tot['aware_calls']+=calls
                rows.append({"start":start,"end":end,"exact":exact,"logical_payload_bytes":logical,"physical_bytes":pb,"physical_calls":calls,
                             "interval_calls":src.calls,"boundary_probe_calls":src.probe_calls,"fallbacks":src.fallbacks,"touched_pages":sorted(src.pages),
                             "dependency_pages_equal":pages_equal,"physical_covers_logical":covered,"logical_accounting_equal":accounting,"physical_bound_ok":bound,
                             "call_reduction":reduce,"resident_wall_s":rw,"pread8_wall_s":w8,"aware_wall_s":wa,"error":err,"pass":ok})
        finally:os.close(fd)
    ratio=tot['aware_calls']/max(tot['pread8_calls'],1)
    return {"schema":SCHEMA,"source_commit":os.environ.get('EVIDENCE_HEAD'),"input":{"raw_bytes":len(raw),"compressed_bytes":len(comp),"anchors":len(anchors),"probes":len(rows)},
            "failures":failures,"rows":rows,"summary":{**tot,"aware_vs_pread8_call_ratio":ratio,"aware_call_reduction_pct":(1-ratio)*100,
            "aware_vs_pread8_wall_ratio":tot['aware_wall_s']/max(tot['pread8_wall_s'],1e-12),"aware_vs_resident_wall_ratio":tot['aware_wall_s']/max(tot['resident_wall_s'],1e-12),
            "max_physical_bytes":max(r['physical_bytes'] for r in rows),"max_overfetch_bytes":max(r['physical_bytes']-r['logical_payload_bytes'] for r in rows),
            "max_physical_calls":max(r['physical_calls'] for r in rows),"max_boundary_probe_calls":max(r['boundary_probe_calls'] for r in rows),"max_fallbacks":max(r['fallbacks'] for r in rows)},
            "hypothesis":{"dependency_event_coupled_anchor_pread_supported":failures==0},
            "contract":{"diagnostic_only":True,"release_credit":False,"no_new_persisted_metadata":True,"coldreader_semantics_unchanged":True,"boundary_probe_io_charged":True,
            "timing_is_diagnostic_not_acceptance":True,"remaining_debt":"Office transfer under exact v7 economics and 22B locality slack; archive-root auth/recovery; fresh-process RSS/throughput; native/platform parity"}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-page-aware-anchor-pread.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
