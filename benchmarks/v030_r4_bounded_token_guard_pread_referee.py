from __future__ import annotations

"""Physical pread with dependency-event page loading and a protocol-derived token-end guard.

Mission Lock
============
The dependency-aware page loader proved that ColdReader's own recursive page events identify the right
physical intervals, but decoding every crossing boundary token with a separate tiny physical source paid
up to 45 endpoint probes and was slower than the 8-byte refill baseline.

RFC-1951 itself provides a bound: a non-stored LZ77 token consumes at most 15 Huffman bits for the
literal/length symbol + 5 length-extra bits + 15 distance-Huffman bits + 13 distance-extra bits = 48 bits.
Literals/EOB are shorter; the stored-block prototype consumes exactly 8 bits per byte. Therefore, when
anchor[p+1] names a token beginning before the next 4 KiB boundary, `anchor.bit_start + 48` is a safe
exclusive upper bound for that token without reading any compressed bytes to discover its actual end.
This is a format theorem, not a swept refill parameter.

Hypothesis
----------
Using that 48-bit guard only on crossing-token boundaries, while loading a page interval exactly when
ColdReader enters that page (including recursive dependencies), will preserve byte-exact output with zero
fallbacks and materially reduce physical calls versus 8-byte pread, with bounded overfetch and no new
persisted metadata or endpoint-probe I/O.

Disproof
--------
Any mismatch, fallback, dependency-page mismatch, uncovered logical payload, or non-reduction in calls
falsifies the mechanism. We record overfetch and timing rather than fitting a threshold to this stream.
Office transfer remains independently gated by its frozen 22-byte locality slack and exact v7 economics.
"""

import argparse,json,os,tempfile,time
from pathlib import Path
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA='cmpct-v030-r4-bounded-token-guard-pread-v1'
PAGE=4096
MAX_TOKEN_BITS=48


def _merge(rs):
    out=[]
    for a,b in sorted(rs):
        if b<=a:continue
        if not out or a>out[-1][1]:out.append([a,b])
        else:out[-1][1]=max(out[-1][1],b)
    return [tuple(x) for x in out]


class GuardedSource:
    __slots__=('fd','size','anchors','ranges','buffers','pages','calls','fallbacks')
    def __init__(self,fd,size,anchors):
        self.fd=fd;self.size=size;self.anchors=anchors;self.ranges=[];self.buffers=[];self.pages=set();self.calls=0;self.fallbacks=0
    def __len__(self):return self.size
    def __getitem__(self,index):
        if index<0:index+=self.size
        if not 0<=index<self.size:raise IndexError(index)
        for (a,b),data in zip(self.ranges,self.buffers):
            if a<=index<b:return data[index-a]
        self.fallbacks+=1;raise RuntimeError(f'compressed byte {index} outside guarded page intervals')
    def ensure_page(self,page):
        if page in self.pages:return
        a=self.anchors[page];start=a['bit_start']
        if page+1>=len(self.anchors):end=self.size*8
        else:
            n=self.anchors[page+1];boundary=(page+1)*PAGE
            if n['token_start']==boundary:end=n['bit_start']
            elif n['token_start']<boundary:end=min(self.size*8,n['bit_start']+MAX_TOKEN_BITS)
            else:raise RuntimeError('next anchor starts after page boundary')
        lo=start//8;hi=(end+7)//8;data=os.pread(self.fd,hi-lo,lo)
        if len(data)!=hi-lo:raise RuntimeError('short guarded pread')
        self.ranges.append((lo,hi));self.buffers.append(data);self.pages.add(page);self.calls+=1
    def physical_ranges(self):return _merge(self.ranges)


class GuardedReader(COLD.ColdReader):
    def _decode_page(self,page,depth):
        self.comp.ensure_page(page)
        return super()._decode_page(page,depth)


def _timed(fn):
    c=time.process_time();w=time.perf_counter();x=fn();return x,time.process_time()-c,time.perf_counter()-w


def run():
    raw,comp=SRC._stream();parsed=DEP.parse_tokens(comp);anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-PAGE-17),max(0,len(raw)-PAGE)]))
    rows=[];fails=0;tot={'resident_wall_s':0.0,'pread8_wall_s':0.0,'guarded_wall_s':0.0,'pread8_calls':0,'guarded_calls':0}
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
                src=GuardedSource(fd,len(comp),anchors);err=None
                try:
                    def gd():
                        r=GuardedReader(src,anchors,blocks,len(raw));return r,r.read(start,end)
                    (gr,gg),_,gw=_timed(gd)
                except Exception as exc:gr=None;gg=b'';gw=0.0;err=repr(exc)
                pr=src.physical_ranges();pb=SRC._bytes(pr);logical=r8.payload_bytes()
                exact=rg==g8==gg==raw[start:end];covered=gr is not None and SRC._covers(pr,gr.payload_ranges)
                acct=gr is not None and gr.payload_bytes()==logical;pages=gr is not None and src.pages==gr.anchor_frames==rr.anchor_frames
                reduced=src.calls<s8.calls;ok=err is None and exact and covered and acct and pages and src.fallbacks==0 and reduced
                if not ok:fails+=1
                tot['resident_wall_s']+=rw;tot['pread8_wall_s']+=w8;tot['guarded_wall_s']+=gw;tot['pread8_calls']+=s8.calls;tot['guarded_calls']+=src.calls
                rows.append({'start':start,'end':end,'exact':exact,'logical_payload_bytes':logical,'physical_bytes':pb,'overfetch_bytes':pb-logical,
                             'pread8_calls':s8.calls,'guarded_calls':src.calls,'fallbacks':src.fallbacks,'touched_pages':sorted(src.pages),'dependency_pages_equal':pages,
                             'physical_covers_logical':covered,'logical_accounting_equal':acct,'call_reduction':reduced,'resident_wall_s':rw,'pread8_wall_s':w8,
                             'guarded_wall_s':gw,'error':err,'pass':ok})
        finally:os.close(fd)
    ratio=tot['guarded_calls']/max(tot['pread8_calls'],1)
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'anchors':len(anchors),'probes':len(rows)},
            'format_bound':{'max_literal_length_huffman_bits':15,'max_length_extra_bits':5,'max_distance_huffman_bits':15,'max_distance_extra_bits':13,'max_copy_token_bits':MAX_TOKEN_BITS},
            'failures':fails,'rows':rows,'summary':{**tot,'guarded_vs_pread8_call_ratio':ratio,'guarded_call_reduction_pct':(1-ratio)*100,
            'guarded_vs_pread8_wall_ratio':tot['guarded_wall_s']/max(tot['pread8_wall_s'],1e-12),'guarded_vs_resident_wall_ratio':tot['guarded_wall_s']/max(tot['resident_wall_s'],1e-12),
            'max_physical_bytes':max(r['physical_bytes'] for r in rows),'max_overfetch_bytes':max(r['overfetch_bytes'] for r in rows),'max_guarded_calls':max(r['guarded_calls'] for r in rows),'max_fallbacks':max(r['fallbacks'] for r in rows)},
            'hypothesis':{'protocol_bounded_guard_pread_supported':fails==0},'contract':{'diagnostic_only':True,'release_credit':False,'no_new_persisted_metadata':True,
            'no_endpoint_probe_io':True,'guard_is_rfc1951_derived_not_swept':True,'timing_is_diagnostic_not_acceptance':True,
            'remaining_debt':'Office transfer under exact v7 644B economics and 22B locality slack; archive-root auth/recovery; fresh-process RSS/throughput; native/platform parity'}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-bounded-token-guard-pread.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'failures':d['failures'],'summary':d['summary'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
