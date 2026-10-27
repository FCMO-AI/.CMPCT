#!/usr/bin/env python3
"""J24S02: CRC32 zero-run algebra; offline/raw-DEFLATE only, not CMPCT product."""
import argparse
import ctypes
import ctypes.util
import hashlib
import io
import json
import os
import statistics
import sys
import time
import zlib
from datetime import datetime, timezone

M=1<<20
ZERO=bytes(M)
BULK=ZERO  # Bulk buffer is allocated inside the timed encoder; no import-time 8-MiB confound.
POLY=0xedb88320


class NativeCRC:
    """C-zlib composition; cold operator generation inside each timed encode."""
    def __init__(self, cached):
        path=ctypes.util.find_library("z")
        if not path:raise RuntimeError("native zlib unavailable (infrastructure, not product loss)")
        self.lib=ctypes.CDLL(path)
        for name in ("crc32_combine","crc32_combine_gen","crc32_combine_op"):
            if not hasattr(self.lib,name):raise RuntimeError("zlib lacks "+name)
        self.lib.crc32_combine.argtypes=(ctypes.c_ulong,ctypes.c_ulong,ctypes.c_longlong)
        self.lib.crc32_combine.restype=ctypes.c_ulong
        self.lib.crc32_combine_gen.argtypes=(ctypes.c_longlong,)
        self.lib.crc32_combine_gen.restype=ctypes.c_ulong
        self.lib.crc32_combine_op.argtypes=(ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong)
        self.lib.crc32_combine_op.restype=ctypes.c_ulong
        self.cached=cached;self.cache={};self.generations=0;self.fallbacks=0
        self.path=path

    def combine(self,a,b,n):
        return self.lib.crc32_combine(a,b,n)&0xffffffff

    def zero_crc(self,n):
        # Binary decomposition of zero runs using a bounded 64-KiB seed.
        q,r=divmod(n,len(SEED));crc=0
        if q:
            power=zlib.crc32(SEED);length=len(SEED)
            while q:
                if q&1:crc=self.combine(crc,power,length)
                q>>=1
                if q:
                    power=self.combine(power,power,length);length*=2
        if r:crc=self.combine(crc,zlib.crc32(SEED[:r]),r)
        return crc

    def advance(self,crc,n):
        if not n:return crc
        if n in self.cache:
            zeros,op=self.cache[n]
        else:
            if self.cached and len(self.cache)>=256:
                self.fallbacks+=1
                return scan_zero(crc,n,ZERO)
            zeros=self.zero_crc(n)
            op=self.lib.crc32_combine_gen(n);self.generations+=1
            if self.cached:self.cache[n]=(zeros,op)
        return self.lib.crc32_combine_op(crc,zeros,op)&0xffffffff

def scan_zero(crc,n,buffer):
    while n:
        take=min(n,len(buffer))
        crc=zlib.crc32(memoryview(buffer)[:take],crc)
        n-=take
    return crc

SESSION={}
SEED=bytes(65536)

def gf2_times(mat, vec):
    value=0
    i=0
    while vec:
        if vec & 1: value ^= mat[i]
        vec >>= 1
        i += 1
    return value

def gf2_square(mat):
    return [gf2_times(mat,mat[i]) for i in range(32)]

def crc_combine(crca,crcb,lenb):
    """Independently implemented zlib crc32_combine polynomial operation."""
    if lenb<=0: return crca & 0xffffffff
    odd=[0]*32
    odd[0]=POLY
    for i in range(1,32):odd[i]=1<<(i-1)
    even=gf2_square(odd)
    odd=gf2_square(even)
    while True:
        even=gf2_square(odd)
        if lenb&1:crca=gf2_times(even,crca)
        lenb >>= 1
        if not lenb:break
        odd=gf2_square(even)
        if lenb&1:crca=gf2_times(odd,crca)
        lenb >>= 1
        if not lenb:break
    return (crca^crcb)&0xffffffff

def zero_crc(n):
    """Return CRC32 of N zeros without a proportional-byte allocation or scan."""
    blocks,rem=divmod(n,M)
    block_crc=zlib.crc32(ZERO)
    block_len=M
    result=0
    while blocks:
        if blocks&1:result=crc_combine(result,block_crc,block_len)
        blocks>>=1
        if blocks:
            block_crc=crc_combine(block_crc,block_crc,block_len)
            block_len <<= 1
    if rem:result=crc_combine(result,zlib.crc32(ZERO[:rem]),rem)
    return result

def advance_zero(crc,n,mode):
    if mode in ("native_cache","native_uncached"):
        if SESSION["native"] is None:
            SESSION["native"]=NativeCRC(mode=="native_cache")
        return SESSION["native"].advance(crc,n)
    if mode=="bulk":
        if SESSION["bulk"] is None:SESSION["bulk"]=bytes(8*M)
        return scan_zero(crc,n,SESSION["bulk"])
    if mode=="algebra":return crc_combine(crc,zero_crc(n),n)
    if mode=="chunk_algebra":
        while n:
            k=min(n,M)
            crc=crc_combine(crc,zero_crc(k),k)
            n-=k
        return crc
    raise ValueError(mode)

def adversarial():
    lengths=(0,1,2,3,7,31,255,256,257,4095,4096,4097,65535,
             65536,65537,M-1,M,M+1,2*M+3,8*M+13)
    nchecks=0
    for n in lengths:
        for initial in (0,1,0x89abcdef,0xffffffff):
            reference=initial
            todo=n
            while todo:
                k=min(todo,M)
                reference=zlib.crc32(ZERO[:k],reference)
                todo-=k
            for mode in ("algebra","bulk","chunk_algebra"):
                assert advance_zero(initial,n,mode)==reference,(n,initial,mode)
                nchecks+=1
            tail=b"\x01\x00\xfftail"+bytes([n&255])
            assert crc_combine(reference,zlib.crc32(tail),len(tail))==zlib.crc32(tail,reference)
            nchecks+=1
    return nchecks

def extents(family,mib):
    if family=="zero":return [("hole",M,i) for i in range(mib)]
    if family=="mixed":
        assert mib%16==0
        items=[]
        for p in range(mib//16):
            items.extend(("hole",M,p) for _ in range(15))
            items.append(("hole",M-4096,p))
            items.append(("data",4096,p))
        return items
    if family=="irregular":
        # 256 distinct structurally discovered hole lengths at 256MiB.
        items=[]
        for p in range(mib):
            length=4096+((p*647)%61440)
            items.extend((("hole",M-length,p),("data",length,p)))
        return items
    if family=="nonhole":return [("data",M,i) for i in range(mib)]
    raise ValueError(family)

def span(kind,n,i,family):
    if kind=="hole":return ZERO[:n]
    # Same deterministic source identity and generation as inherited J24S01.
    return hashlib.shake_256(("J24S01 "+family+" "+str(i)).encode()).digest(n)

def encode(family,mib,level,mode):
    global SESSION
    start=time.perf_counter()
    SESSION={"native":None,"bulk":None}
    cpu=time.process_time()
    sha=hashlib.sha256()
    crc=0
    pending=0
    writer=io.BytesIO()
    template={}
    for kind,n,i in extents(family,mib):
        data=span(kind,n,i,family)
        sha.update(data)  # Never eliminate or sample complete logical SHA256.
        if mode=="chunk":
            crc=zlib.crc32(data,crc)
        elif kind=="hole":
            pending+=n
            if mode=="chunk_algebra":
                crc=advance_zero(crc,pending,mode)
                pending=0
        else:
            if pending:
                crc=advance_zero(crc,pending,mode)
                pending=0
            crc=zlib.crc32(data,crc)
        # Every mode emits the *identical* J24S01 reusable-hole DEFLATE bytes.
        if kind=="hole":
            if n not in template:
                obj=zlib.compressobj(level,zlib.DEFLATED,-15)
                template[n]=obj.compress(data)+obj.flush(zlib.Z_SYNC_FLUSH)
            writer.write(template[n])
        else:
            obj=zlib.compressobj(level,zlib.DEFLATED,-15)
            writer.write(obj.compress(data))
            writer.write(obj.flush(zlib.Z_SYNC_FLUSH))
    if pending:crc=advance_zero(crc,pending,mode)
    writer.write(zlib.compressobj(level,zlib.DEFLATED,-15).flush(zlib.Z_FINISH))
    wire=writer.getvalue()
    return wire,dict(family=family,mib=mib,level=level,mode=mode,
        sha256=sha.hexdigest(),crc32=f"{crc:08x}",wire_sha256=hashlib.sha256(wire).hexdigest(),
        wire_bytes=len(wire),wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu,
        op_generations=0 if SESSION["native"] is None else SESSION["native"].generations,
        cache_entries=0 if SESSION["native"] is None else len(SESSION["native"].cache),
        cache_fallbacks=0 if SESSION["native"] is None else SESSION["native"].fallbacks,
        bulk_buffer_bytes=0 if SESSION["bulk"] is None else len(SESSION["bulk"]))

def verify_decoder(wire,expected):
    """Separately inflate and SHA/CRC full logical plaintext, bounded to 1MiB output."""
    dec=zlib.decompressobj(-15)
    sha=hashlib.sha256()
    crc=0
    size=0
    for offset in range(0,len(wire),65536):
        feed=wire[offset:offset+65536]
        while feed:
            data=dec.decompress(feed,M)
            feed=dec.unconsumed_tail
            assert not(feed and not data),"stalled decoder"
            sha.update(data)
            crc=zlib.crc32(data,crc)
            size+=len(data)
    while True:
        data=dec.flush(M)
        if not data:break
        sha.update(data)
        crc=zlib.crc32(data,crc)
        size+=len(data)
    assert dec.eof and not dec.unused_data
    assert size==expected["mib"]*M
    assert sha.hexdigest()==expected["sha256"]
    assert f"{crc:08x}"==expected["crc32"]

def adversarial_native():
    c=NativeCRC(True);count=0
    for n in (0,1,2,3,7,31,255,256,257,4095,4096,4097,65535,65536,65537,
              M-1,M,M+1,2*M+3,8*M+13,64*M+7):
        for initial in (0,1,0x89abcdef,0xffffffff):
            expected=scan_zero(initial,n,ZERO)
            observed=c.advance(initial,n)
            assert observed==expected,(n,initial,observed,expected)
            suffix=bytes((1,0,255,n&255,27,47,125))
            assert c.combine(observed,zlib.crc32(suffix),len(suffix))==zlib.crc32(suffix,observed)
            count+=2
    return count

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sparse-mib",type=int,default=256)
    p.add_argument("--nonhole-mib",type=int,default=64)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--levels",default="1,6")
    p.add_argument("--families",default="zero,mixed,irregular,nonhole")
    p.add_argument("--output",default="j24s03-result.json")
    a=p.parse_args()
    assert a.repeats>=3 and a.sparse_mib>=16 and a.sparse_mib%16==0
    nchecks=adversarial_native()
    print("J24S03_NATIVE_ADVERSARIAL_PASS",nchecks,flush=True)
    rows=[]
    cases=[]
    for family in a.families.split(","):
        mib=a.nonhole_mib if family=="nonhole" else a.sparse_mib
        for level in map(int,a.levels.split(",")):
            expected=None
            for rep in range(a.repeats):
                modes=("chunk","bulk","native_uncached","native_cache")
                if rep%2:modes=modes[::-1]
                for mode in modes:
                    wire,row=encode(family,mib,level,mode)
                    row["repeat"]=rep
                    rows.append(row)
                    fingerprint=(row["sha256"],row["crc32"],row["wire_sha256"],row["wire_bytes"])
                    if expected is None:
                        verify_decoder(wire,row)
                        expected=fingerprint
                    assert fingerprint==expected,(family,level,rep,mode)
            def med(mode,key):
                return statistics.median(r[key] for r in rows if r["family"]==family and r["level"]==level and r["mode"]==mode)
            base=med("chunk","wall_s")
            cand=med("native_cache","wall_s")
            bulk=med("bulk","wall_s")
            case=dict(family=family,mib=mib,level=level,
                baseline_wall_s=base,native_cache_wall_s=cand,bulk_wall_s=bulk,
                native_uncached_wall_s=med("native_uncached","wall_s"),
                native_cache_speedup=base/cand,bulk_speedup=base/bulk,
                native_uncached_speedup=base/med("native_uncached","wall_s"),
                native_cache_cpu_speedup=med("chunk","cpu_s")/med("native_cache","cpu_s"),
                cache_entries_max=max(r["cache_entries"] for r in rows if r["family"]==family and r["level"]==level and r["mode"]=="native_cache"),
                wire_bytes=expected[3],same_sha_crc_deflate=True)
            cases.append(case)
            print("J24S03_CASE",json.dumps(case,sort_keys=True),flush=True)
    complete={x["family"] for x in cases}=={"zero","mixed","irregular","nonhole"}
    positive=all(any(x["family"]==family and x["native_cache_speedup"]>=1/0.95 for x in cases) for family in ("zero","mixed"))
    irregular_ok=all(x["native_cache_speedup"]>=1/1.02 for x in cases if x["family"]=="irregular")
    nohole_ok=all(x["native_cache_speedup"]>=1/1.02 for x in cases if x["family"]=="nonhole")
    terminal=("CONTINUE_ORACLE_ONLY" if positive and irregular_ok and nohole_ok and complete else
              "RETIRE_AS_GENERAL_OPTIMIZATION" if complete else "INCOMPLETE_COURT")
    result=dict(schema="cmpct-j24s03-v1",utc=datetime.now(timezone.utc).isoformat(),
                scope="offline C-zlib CRC composition/raw-DEFLATE; NOT real CMPCT/ZIP64 product",
                parent="J24S02 #547",platform=sys.platform,python=sys.version,
                zlib=zlib.ZLIB_RUNTIME_VERSION,adversarial_checks=nchecks,raw=rows,cases=cases,
                sparse_wall_threshold=0.05,irregular_nohole_regression_limit=0.02,
                terminal=terminal)
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("J24S03_TERMINAL",terminal,a.output,flush=True)

if __name__=="__main__":main()
