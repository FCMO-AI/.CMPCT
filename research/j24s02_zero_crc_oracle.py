#!/usr/bin/env python3
"""J24S02: CRC32 zero-run algebra; offline/raw-DEFLATE only, not CMPCT product."""
import argparse
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
BULK=ZERO*8  # Conventional larger-read control: charges +8 MiB memory.
POLY=0xedb88320

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
    if mode=="algebra":return crc_combine(crc,zero_crc(n),n)
    if mode=="bulk":
        while n:
            k=min(n,len(BULK))
            crc=zlib.crc32(memoryview(BULK)[:k],crc)
            n-=k
        return crc
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
    if family=="nonhole":return [("data",M,i) for i in range(mib)]
    raise ValueError(family)

def span(kind,n,i,family):
    if kind=="hole":return ZERO[:n]
    # Same deterministic source identity and generation as inherited J24S01.
    return hashlib.shake_256(("J24S01 "+family+" "+str(i)).encode()).digest(n)

def encode(family,mib,level,mode):
    start=time.perf_counter()
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
        wire_bytes=len(wire),wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu)

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

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sparse-mib",type=int,default=256)
    p.add_argument("--nonhole-mib",type=int,default=64)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--levels",default="1,6")
    p.add_argument("--families",default="zero,mixed,nonhole")
    p.add_argument("--output",default="j24s02-result.json")
    a=p.parse_args()
    assert a.repeats>=3 and a.sparse_mib>=16 and a.sparse_mib%16==0
    nchecks=adversarial()
    print("J24S02_GF2_ADVERSARIAL_PASS",nchecks,flush=True)
    rows=[]
    cases=[]
    for family in a.families.split(","):
        mib=a.nonhole_mib if family=="nonhole" else a.sparse_mib
        for level in map(int,a.levels.split(",")):
            expected=None
            for rep in range(a.repeats):
                modes=("chunk","bulk","algebra","chunk_algebra")
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
            cand=med("algebra","wall_s")
            bulk=med("bulk","wall_s")
            case=dict(family=family,mib=mib,level=level,baseline_wall_s=base,
                      algebra_wall_s=cand,bulk_wall_s=bulk,
                      algebra_speedup=base/cand,bulk_speedup=base/bulk,
                      algebra_cpu_speedup=med("chunk","cpu_s")/med("algebra","cpu_s"),
                      wire_bytes=expected[3],same_sha_crc_deflate=True)
            cases.append(case)
            print("J24S02_CASE",json.dumps(case,sort_keys=True),flush=True)
    positive=all(any(x["family"]==family and x["algebra_speedup"]>=1/0.95 for x in cases) for family in ("zero","mixed"))
    nohole=all(x["algebra_wall_s"]<=1.02*x["baseline_wall_s"] for x in cases if x["family"]=="nonhole")
    # Promote no result without every required family being covered.
    complete={x["family"] for x in cases}=={"zero","mixed","nonhole"}
    terminal=("CONTINUE_ORACLE_ONLY" if positive and nohole and complete else
              "RETIRE_AS_FULL_PRODUCT_PRIORITY" if complete else "INCOMPLETE_COURT")
    result=dict(schema="cmpct-j24s02-v1",utc=datetime.now(timezone.utc).isoformat(),
                scope="offline CRC algebra/raw-DEFLATE oracle, NOT real CMPCT/ZIP64 product",
                platform=sys.platform,python=sys.version,zlib=zlib.ZLIB_RUNTIME_VERSION,
                adversarial_checks=nchecks,raw=rows,cases=cases,
                full_oracle_threshold=0.05,nohole_slowdown_limit=0.02,terminal=terminal)
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("J24S02_TERMINAL",terminal,a.output,flush=True)

if __name__=="__main__":main()
