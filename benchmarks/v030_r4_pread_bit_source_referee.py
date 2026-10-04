from __future__ import annotations

"""Direct `os.pread` byte-source compatibility + timing referee for the sparse DEFLATE reader.

Mission Lock / Referee
======================
ColdReader/BitReader grammar is unchanged. `BitReader` requires only `len(data)` and byte indexing. This
referee supplies those operations from a file descriptor with the preregistered 8-byte exact-start refill
policy instead of resident compressed bytes. Builder metadata is identical. The same probe is also decoded
from resident bytes to expose syscall cost; timing is diagnostic and cannot change the correctness verdict.

Hypothesis
----------
Every deterministic 4 KiB probe must reconstruct byte-exactly from the pread-backed source. No source read
may exceed 8 bytes; physical ranges must cover every logical compressed interval; physical bytes must be
bounded by logical unique payload bytes + 7 bytes per pread call. Resident-vs-pread CPU/wall is measured as
a hidden-cost signal, not a promotion threshold.
"""

import argparse,json,os,tempfile,time,zlib
from pathlib import Path
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP

SCHEMA='cmpct-v030-r4-pread-bit-source-referee-v2';REFILL=8;PAGE=4096

def _merge(rs):
    out=[]
    for a,b in sorted(rs):
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
        else:out.append((a,b))
    return out

def _bytes(rs):return sum(b-a for a,b in _merge(rs))

class PreadByteSource:
    __slots__=('fd','size','base','cache','ranges','calls','max_call')
    def __init__(self,fd,size):self.fd=fd;self.size=size;self.base=-1;self.cache=b'';self.ranges=[];self.calls=0;self.max_call=0
    def __len__(self):return self.size
    def __getitem__(self,index):
        if index<0:index+=self.size
        if not 0<=index<self.size:raise IndexError(index)
        if not (self.base<=index<self.base+len(self.cache)):
            n=min(REFILL,self.size-index);data=os.pread(self.fd,n,index)
            if len(data)!=n:raise RuntimeError('short pread')
            self.base=index;self.cache=data;self.ranges.append((index,index+n));self.calls+=1;self.max_call=max(self.max_call,n)
        return self.cache[index-self.base]

def _covers(physical,logical):
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

def _stream():
    raw=bytearray()
    for i in range(2048):
        raw+=(b'cmpct-v030-pread-boundary|'+(i%97).to_bytes(2,'little'))*(1+(i%5));raw+=bytes(((i*17+j*31)&255) for j in range(i%23))
    c=zlib.compressobj(level=6,wbits=-15);return bytes(raw),c.compress(bytes(raw))+c.flush()

def _timed(fn):
    c=time.process_time();w=time.perf_counter();out=fn();return out,time.process_time()-c,time.perf_counter()-w

def run():
    raw,comp=_stream();parsed=DEP.parse_tokens(comp)
    if parsed['output_bytes']!=len(raw) or zlib.decompress(comp,-15)!=raw:raise RuntimeError('builder parse drift')
    anchors,blocks,_=COLD._build_metadata(parsed);starts=sorted(set([0,1,4095,4096,max(0,len(raw)//3-37),len(raw)//2,max(0,len(raw)-PAGE-17),max(0,len(raw)-PAGE)]));rows=[];failures=0
    total_base_cpu=total_base_wall=total_pread_cpu=total_pread_wall=0.0
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'payload.deflate';p.write_bytes(comp);fd=os.open(p,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+PAGE)
                def resident():
                    r=COLD.ColdReader(comp,anchors,blocks,len(raw));return r,r.read(start,end)
                (rb,basegot),bcpu,bwall=_timed(resident)
                src=PreadByteSource(fd,len(comp))
                def physical():
                    r=COLD.ColdReader(src,anchors,blocks,len(raw));return r,r.read(start,end)
                (r,got),pcpu,pwall=_timed(physical)
                logical=r.payload_bytes();physical_bytes=_bytes(src.ranges);exact=got==raw[start:end] and basegot==got;covered=_covers(src.ranges,r.payload_ranges);bound=physical_bytes<=logical+7*src.calls;call_ok=src.max_call<=REFILL;ok=exact and covered and bound and call_ok
                if not ok:failures+=1
                total_base_cpu+=bcpu;total_base_wall+=bwall;total_pread_cpu+=pcpu;total_pread_wall+=pwall
                rows.append({'start':start,'end':end,'exact':exact,'logical_payload_bytes':logical,'physical_pread_bytes':physical_bytes,'pread_calls':src.calls,'max_pread_bytes':src.max_call,'logical_ranges_covered':covered,'accounting_bound_ok':bound,'resident_cpu_s':bcpu,'resident_wall_s':bwall,'pread_cpu_s':pcpu,'pread_wall_s':pwall,'pass':ok})
        finally:os.close(fd)
    supported=failures==0
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'input':{'raw_bytes':len(raw),'compressed_bytes':len(comp),'probes':len(rows)},'policy':{'refill_bytes':REFILL,'exact_start':True,'backward_alignment':False},'rows':rows,'failures':failures,
            'summary':{'max_physical_payload_bytes':max(x['physical_pread_bytes'] for x in rows),'max_pread_calls':max(x['pread_calls'] for x in rows),'max_call_bytes':max(x['max_pread_bytes'] for x in rows),'resident_total_cpu_s':total_base_cpu,'resident_total_wall_s':total_base_wall,'pread_total_cpu_s':total_pread_cpu,'pread_total_wall_s':total_pread_wall,'pread_vs_resident_wall_ratio':total_pread_wall/max(total_base_wall,1e-12),'pread_vs_resident_cpu_ratio':total_pread_cpu/max(total_base_cpu,1e-12)},
            'hypothesis':{'unchanged_bitreader_consumes_direct_pread_source_exactly':supported},'contract':{'diagnostic_only':True,'release_credit':False,'coldreader_code_unchanged':True,'builder_runtime_separated':True,'no_refill_sweep':True,'timing_is_diagnostic_not_acceptance':True,'remaining_debt':'replace syscall-heavy byte cache with anchor-derived bulk reads; Office v7 exact metadata/auth/locality; fresh-process RSS; native/platform parity'}}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-pread-bit-source.json'));a=p.parse_args();d=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'input':d['input'],'summary':d['summary'],'failures':d['failures'],'hypothesis':d['hypothesis']},sort_keys=True))
if __name__=='__main__':main()
