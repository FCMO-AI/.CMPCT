#!/usr/bin/env python3
"""J24S01: offline, fully SHA/CRC-charged sparse-hole raw-DEFLATE oracle.

NO CMPCT shipping change, actual ZIP64 product/OS/release claim, or weakened
semantic comparator. Exact input for all three arms; independent stream decode.
"""
import argparse, hashlib, io, json, os, statistics, time, zlib
from datetime import datetime, timezone

M=1<<20
ZERO=bytes(M)

def extents(kind,mib):
    # These are structural span descriptors; the admission path never uses
    # the workload name, file extension, or particular content fingerprint.
    if kind=="zero":
        return [("hole",M,i) for i in range(mib)]
    if kind=="mixed":
        assert mib%16==0
        result=[]
        for p in range(mib//16):
            result.extend(("hole",M,p) for _ in range(15))
            result.append(("hole",M-4096,p))
            result.append(("data",4096,p))
        return result
    return [("data",M,p) for p in range(mib)]

def span_bytes(kind,length,index,source):
    if kind=="hole":
        return ZERO[:length]
    return hashlib.shake_256(("J24S01 "+source+" "+str(index)).encode()).digest(length)

def encode(source,mib,level,arm):
    desc=extents(source,mib)
    sparse=any(k=="hole" for k,n,i in desc)
    engine=("ordinary" if (arm=="template" and not sparse) else arm)
    t0=time.perf_counter(); c0=time.process_time()
    logical_sha=hashlib.sha256(); crc=0; logical=0; calls=0
    writer=io.BytesIO(); memo={}
    stream=zlib.compressobj(level,zlib.DEFLATED,-15) if engine=="ordinary" else None
    for kind,n,index in desc:
        data=span_bytes(kind,n,index,source)
        assert len(data)==n
        logical_sha.update(data); crc=zlib.crc32(data,crc); logical+=n
        if engine=="ordinary":
            writer.write(stream.compress(data)); calls+=1
        elif engine=="template" and kind=="hole":
            if n not in memo:
                c=zlib.compressobj(level,zlib.DEFLATED,-15)
                memo[n]=c.compress(data)+c.flush(zlib.Z_SYNC_FLUSH)
                calls+=1
            writer.write(memo[n])
        else:
            c=zlib.compressobj(level,zlib.DEFLATED,-15)
            writer.write(c.compress(data))
            writer.write(c.flush(zlib.Z_SYNC_FLUSH))
            calls+=1
    if engine=="ordinary":
        writer.write(stream.flush(zlib.Z_FINISH))
    else:
        writer.write(zlib.compressobj(level,zlib.DEFLATED,-15).flush(zlib.Z_FINISH))
        calls+=1
    payload=writer.getvalue()
    wall=time.perf_counter()-t0; cpu=time.process_time()-c0
    return payload,{"family":source,"mib":mib,"level":level,"arm":arm,
      "actual_engine":engine,"wall_s":wall,"cpu_s":cpu,
      "logical_bytes":logical,"deflate_bytes":len(payload),"compress_calls":calls,
      "logical_sha256":logical_sha.hexdigest(),"crc32":f"{crc:08x}",
      "deflate_sha256":hashlib.sha256(payload).hexdigest()}

def verify(wire,expected):
    # Independent raw decoder with bounded one-MiB decoded output.
    d=zlib.decompressobj(-15); sha=hashlib.sha256(); crc=0; total=0
    for p in range(0,len(wire),65536):
        feed=wire[p:p+65536]
        while feed:
            data=d.decompress(feed,M)
            feed=d.unconsumed_tail
            assert not(feed and not data),"no inflater progress"
            sha.update(data); crc=zlib.crc32(data,crc); total+=len(data)
            assert total<=expected["logical_bytes"]
    while True:
        data=d.flush(M)
        if not data: break
        sha.update(data); crc=zlib.crc32(data,crc); total+=len(data)
        assert total<=expected["logical_bytes"]
    assert d.eof and not d.unused_data
    assert total==expected["logical_bytes"]
    assert sha.hexdigest()==expected["logical_sha256"]
    assert f"{crc:08x}"==expected["crc32"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mib",type=int,default=256)
    p.add_argument("--nonhole-mib",type=int,default=64)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--levels",default="1,6")
    p.add_argument("--families",default="zero,mixed,nonhole")
    p.add_argument("--output",default="j24s01-result.json")
    a=p.parse_args()
    assert a.mib>=16 and a.mib%16==0 and 0<a.nonhole_mib<=a.mib
    rows=[]; decisions=[]
    for source in a.families.split(","):
        mib=a.nonhole_mib if source=="nonhole" else a.mib
        for level in map(int,a.levels.split(",")):
            fingerprints={}
            for rep in range(a.repeats):
                arms=("ordinary","framed","template") if rep%2==0 else ("template","framed","ordinary")
                for arm in arms:
                    payload,row=encode(source,mib,level,arm)
                    row["repeat"]=rep; rows.append(row)
                    f=(row["logical_sha256"],row["crc32"],row["deflate_sha256"],row["deflate_bytes"])
                    if arm not in fingerprints:
                        verify(payload,row); fingerprints[arm]=f
                    else:
                        assert f==fingerprints[arm],"nondeterministic stream"
                assert len({f[0:2] for f in fingerprints.values()})==1
            def median(arm,col):
                return statistics.median(r[col] for r in rows if r["family"]==source and r["level"]==level and r["arm"]==arm)
            base=median("ordinary","wall_s"); cand=median("template","wall_s")
            bsz=fingerprints["ordinary"][3]; csz=fingerprints["template"][3]
            d={"family":source,"mib":mib,"level":level,
                "baseline_median_wall_s":base,"candidate_median_wall_s":cand,
                "charged_speedup":base/cand,"baseline_deflate_bytes":bsz,
                "candidate_deflate_bytes":csz,"byte_ratio":csz/bsz}
            if source=="nonhole":
                assert fingerprints["ordinary"]==fingerprints["template"],"no-hole exact fallback failed"
            decisions.append(d)
            print("J24S01_CASE",json.dumps(d,sort_keys=True),flush=True)
    result={"schema":"cmpct-j24s01-v1","utc":datetime.now(timezone.utc).isoformat(),
      "python":os.sys.version,"zlib":zlib.ZLIB_RUNTIME_VERSION,
      "scope":"offline raw-DEFLATE oracle, not real CMPCT or ZIP64 product",
      "source_mode":"validated structural hole-span descriptors only",
      "repeats":a.repeats,"levels":a.levels,"cases":decisions,"raw":rows}
    with open(a.output,"w") as f:json.dump(result,f,indent=2,sort_keys=True)
    print("J24S01_ORACLE_VERIFIED",a.output,flush=True)

if __name__=="__main__":main()
