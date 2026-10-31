#!/usr/bin/env python3
"""J24G98: detached physical segment experiment, research only; no CMPCT import."""
import argparse,bisect,hashlib,io,json,os,pathlib,statistics,tempfile,time,zipfile
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,sha,require

READS=120;ROUNDS=15
def digest(b):return hashlib.sha256(b).hexdigest()
def sync_dir(d):
    fd=os.open(d,os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
    try:os.fsync(fd)
    finally:os.close(fd)
def read_segments(fds,starts,sizes,off,n):
    out=bytearray(); end=off+n
    while off<end:
        i=bisect.bisect_right(starts,off)-1
        require(0<=i<len(fds),"segment index")
        local=off-starts[i];qty=min(end-off,sizes[i]-local)
        part=os.pread(fds[i],qty,local)
        require(len(part)==qty,"short segment read")
        out.extend(part);off+=qty
    return bytes(out)
def sample_reads(root,raw,entries):
    starts=[];offset=0
    for e in entries:starts.append(offset);offset+=e["size"]
    require(offset==len(raw),"length mismatch")
    from contextlib import ExitStack
    times={"one":[],"seg":[]};state=0x13579bdf
    offsets=[]
    for _ in range(READS*ROUNDS):
        state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff
        offsets.append(state%max(1,len(raw)-4096+1))
    with ExitStack() as stack:
        fd=stack.enter_context(open(root/"contig","rb",buffering=0)).fileno()
        fds=[stack.enter_context(open(root/e["name"],"rb",buffering=0)).fileno() for e in entries]
        for r in range(ROUNDS):
            order=["seg","one"] if r%2 else ["one","seg"]
            batch=offsets[r*READS:(r+1)*READS]
            for method in order:
                t0=time.perf_counter_ns()
                for off in batch:
                    count=min(4096,len(raw)-off)
                    got=(os.pread(fd,count,off) if method=="one" else
                         read_segments(fds,starts,[e["size"] for e in entries],off,count))
                    require(got==raw[off:off+count],"selective payload")
                times[method].append((time.perf_counter_ns()-t0)/1e6/READS)
    med={k:statistics.median(v) for k,v in times.items()}
    return {"raw_ms_per_read":times,"medians_ms_per_read":med,"ratio":med["seg"]/med["one"],
            "cached_open_fds":len(entries)+1,"read_size":4096,"reads_each":READS*ROUNDS}
def run_archive(raw,source):
    chain=parse_chain(raw)
    require(len(chain) in (4,64),"footer count")
    ends=[x["pos"]+68 for x in chain]
    require(ends[-1]==len(raw),"footer tail")
    starts=[0]+ends[:-1];chunks=[raw[a:b] for a,b in zip(starts,ends)]
    require(all(chunks) and b"".join(chunks)==raw,"physical cut")
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g98-") as dirname:
        root=pathlib.Path(dirname)
        with open(root/"contig","xb",buffering=0) as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        entries=[]
        for i,chunk in enumerate(chunks):
            name=f"seg-{i:03d}.bin"
            with open(root/name,"xb",buffering=0) as f:
                f.write(chunk);f.flush();os.fsync(f.fileno())
            os.chmod(root/name,0o444)
            entries.append({"name":name,"size":len(chunk),"sha256":digest(chunk)})
        manifest={"schema":"j24g98-v1","length":len(raw),"segments":entries}
        payload=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()
        with open(root/"HEAD.tmp","xb",buffering=0) as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        os.replace(root/"HEAD.tmp",root/"HEAD");sync_dir(root)
        decoded=json.loads((root/"HEAD").read_text())
        require(decoded==manifest,"manifest publication mismatch")
        require(len(entries)<=128 and len({e["name"] for e in entries})==len(entries),"manifest cardinality")
        for i,e in enumerate(decoded["segments"]):
            require(e["name"]==f"seg-{i:03d}.bin","canonical manifest name")
            assert digest((root/e["name"]).read_bytes())==e["sha256"]
        require(b"".join((root/e["name"]).read_bytes() for e in entries)==raw,"reconstruction")
        for k,end in enumerate(ends):
            assert b"".join(chunks[:k+1])==raw[:end]
        old=b"".join((root/e["name"]).read_bytes() for e in entries[:-1])
        require(old==raw[:ends[-2]],"retained old generation")
        # Mutation after validation is not prevented by mode 0444 for same-UID owner.
        last=root/entries[-1]["name"];original=last.read_bytes()
        os.chmod(last,0o644);last.write_bytes(original[:-1]+bytes([original[-1]^1]))
        changed=digest(last.read_bytes())!=entries[-1]["sha256"]
        os.chmod(last,0o644);last.write_bytes(original);os.chmod(last,0o444)
        require(changed,"corruption negative")
        latency=sample_reads(root,raw,entries)
        logical_size=len(raw)
        allocated_file=(root/"contig").stat().st_blocks*512
        allocated_parts=sum((root/e["name"]).stat().st_blocks*512 for e in entries)
        allocated_head=(root/"HEAD").stat().st_blocks*512
        ratio=(allocated_parts+allocated_head)/allocated_file
        return {"source":source,"sha256":digest(raw),"bytes":logical_size,
                "footer_count":len(chain),"ends":ends,"segments":entries,
                "full_copy_retained_generation_bytes":sum(ends),
                "last_append_bytes":len(chunks[-1]),"manifest_bytes":len(payload),
                "allocated_contiguous":allocated_file,"allocated_segments":allocated_parts,
                "allocated_manifest":allocated_head,"allocated_ratio":ratio,
                "corrupt_segment_hash_rejected_on_reverify":changed,
                "read":latency,"passes_local_o1_filter":ratio<=1.05 and latency["ratio"]<=2}
def main():
    p=argparse.ArgumentParser()
    for name in ZIP_CASES:p.add_argument("--"+name,type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args();out={}
    for name,(zsha,head,files) in ZIP_CASES.items():
        raw=getattr(a,name.replace("-","_")).read_bytes()
        require(digest(raw)==zsha,"provider ZIP SHA")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            require(z.read("checkout-head.txt").decode().strip()==head,"original source")
            for f in files:out[name+"/"+f]=run_archive(z.read(f),name+"/"+f)
    deep=[v for v in out.values() if v["footer_count"]==64]
    decision=("SEGMENT_PER_FOOTER_O1_ADMISSION_FAIL" if any(not v["passes_local_o1_filter"] for v in deep)
              else "O0_LOCAL_FILTER_SURVIVES")
    report={"schema":"j24g98-immutable-segment-science-v1","decision":decision,"cases":out,
            "limitations":["Research-only Linux filesystem, no CMPCT Reader integration",
                           "No true crash or multiwriter CAS, not authenticated issuer or robust immutability",
                           "Source ZIPs are Windows/Ubuntu-produced; the court runs on current host only",
                           "Physical directory and inode overhead not fully captured by stat.st_blocks"]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,"cases":len(out),
        "deep_alloc_ratios":{k:round(v["allocated_ratio"],3) for k,v in out.items() if v["footer_count"]==64},
        "result_sha256":digest(a.output.read_bytes())},sort_keys=True))
if __name__=="__main__":main()
