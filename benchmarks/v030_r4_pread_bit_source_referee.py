from __future__ import annotations

"""Direct `os.pread` byte-source compatibility referee for the existing sparse DEFLATE reader.

Mission Lock / Referee
======================
The existing ColdReader/BitReader grammar is unchanged. `BitReader` requires only `len(data)` and byte
indexing. This referee supplies those operations from a file descriptor with the already-preregistered
8-byte exact-start refill policy instead of a resident compressed `bytes` object. Builder metadata is
constructed from the ordinary source bytes, then runtime receives only the pread source, persisted
anchor/block records and output length.

Hypothesis
----------
Without modifying ColdReader, every deterministic 4 KiB probe over a mixed literal/copy raw-DEFLATE
stream must reconstruct byte-exactly from the pread-backed source. No source read may exceed 8 bytes;
merged physical ranges must cover every logical compressed interval reported by the unchanged reader;
and physical payload bytes must be bounded by logical unique payload bytes + 7 bytes per pread call.

Disproof
--------
Any byte mismatch, out-of-policy pread, uncovered logical compressed byte, or accounting-bound violation
falsifies the adapter. PASS proves only that the current bit decoder can consume physical I/O directly;
Office locality/auth/RSS/throughput/native integration remain separate gates.
"""

import argparse
import json
import os
from pathlib import Path
import tempfile
import zlib

from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP

SCHEMA='cmpct-v030-r4-pread-bit-source-referee-v1'
REFILL=8
PAGE=4096


def _merge(rs:list[tuple[int,int]])->list[tuple[int,int]]:
    if not rs:return []
    out=[]
    for a,b in sorted(rs):
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
        else:out.append((a,b))
    return out


def _bytes(rs:list[tuple[int,int]])->int:
    return sum(b-a for a,b in _merge(rs))


class PreadByteSource:
    __slots__=('fd','size','base','cache','ranges','calls','max_call')
    def __init__(self,fd:int,size:int):
        self.fd=fd;self.size=size;self.base=-1;self.cache=b'';self.ranges=[];self.calls=0;self.max_call=0
    def __len__(self):return self.size
    def __getitem__(self,index:int)->int:
        if index<0:index+=self.size
        if not 0<=index<self.size:raise IndexError(index)
        if not (self.base<=index<self.base+len(self.cache)):
            n=min(REFILL,self.size-index);data=os.pread(self.fd,n,index)
            if len(data)!=n:raise RuntimeError('short pread')
            self.base=index;self.cache=data;self.ranges.append((index,index+n));self.calls+=1;self.max_call=max(self.max_call,n)
        return self.cache[index-self.base]


def _covers(physical:list[tuple[int,int]],logical:list[tuple[int,int]])->bool:
    ps=_merge(physical)
    for a,b in _merge(logical):
        pos=a
        for x,y in ps:
            if y<=pos:continue
            if x>pos:break
            pos=max(pos,y)
            if pos>=b:break
        if pos<b:return False
    return True


def _stream()->tuple[bytes,bytes]:
    # Deterministic heterogeneous body: repeated structure exercises distances; changing counters/literal
    # islands prevent a trivial one-token stream.
    raw=bytearray()
    for i in range(2048):
        raw += (b'cmpct-v030-pread-boundary|' + (i%97).to_bytes(2,'little')) * (1+(i%5))
        raw += bytes(((i*17+j*31)&255) for j in range(i%23))
    c=zlib.compressobj(level=6,wbits=-15)
    return bytes(raw),c.compress(bytes(raw))+c.flush()


def run()->dict:
    raw,comp=_stream();parsed=DEP.parse_tokens(comp)
    if parsed['output_bytes']!=len(raw) or zlib.decompress(comp,-15)!=raw:raise RuntimeError('builder parse drift')
    anchors,blocks,_=COLD._build_metadata(parsed)
    starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-PAGE-17),max(0,len(raw)-PAGE)]))
    rows=[];failures=0
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'payload.deflate';p.write_bytes(comp);fd=os.open(p,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+PAGE);src=PreadByteSource(fd,len(comp));r=COLD.ColdReader(src,anchors,blocks,len(raw))
                got=r.read(start,end);logical=r.payload_bytes();physical=_bytes(src.ranges)
                exact=got==raw[start:end];covered=_covers(src.ranges,r.payload_ranges);bound=physical<=logical+7*src.calls;call_ok=src.max_call<=REFILL
                ok=exact and covered and bound and call_ok
                if not ok:failures+=1
                rows.append({'start':start,'end':end,'exact':exact,'logical_payload_bytes':logical,'physical_pread_bytes':physical,
                             'pread_calls':src.calls,'max_pread_bytes':src.max_call,'logical_ranges_covered':covered,'accounting_bound_ok':bound,'pass':ok})
        finally:os.close(fd)
    supported=failures==0
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'probes':len(rows)},
            'policy':{'refill_bytes':REFILL,'exact_start':True,'backward_alignment':False},'rows':rows,'failures':failures,
            'summary':{'max_physical_payload_bytes':max(x['physical_pread_bytes'] for x in rows),'max_pread_calls':max(x['pread_calls'] for x in rows),'max_call_bytes':max(x['max_pread_bytes'] for x in rows)},
            'hypothesis':{'unchanged_bitreader_consumes_direct_pread_source_exactly':supported},
            'contract':{'diagnostic_only':True,'release_credit':False,'coldreader_code_unchanged':True,'builder_runtime_separated':True,'no_refill_sweep':True,
                        'remaining_debt':'Office v7 exact metadata/auth/locality; cold and repeated throughput; fresh-process RSS; native/platform parity'}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-pread-bit-source.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'summary':d['summary'],'failures':d['failures'],'hypothesis':d['hypothesis']},sort_keys=True))

if __name__=='__main__':main()
