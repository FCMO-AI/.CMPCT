#!/usr/bin/env python3
"""J24G99 detached O0: one immutable original root and a rewritten immutable tail pack.
No CMPCT product import, installed Reader, real crash, or product claim.
"""
import argparse,hashlib,io,json,os,pathlib,statistics,tempfile,time,zipfile
from contextlib import ExitStack
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,require
READS=120;ROUNDS=15
def sha(b):return hashlib.sha256(b).hexdigest()
def write(path,buf):
    with open(path,"xb",buffering=0) as f:
        f.write(buf);f.flush();os.fsync(f.fileno())
def fsync_dir(p):
    fd=os.open(p,os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
    try:os.fsync(fd)
    finally:os.close(fd)
def verify(p,expected):
    data=p.read_bytes()
    require(sha(data)==sha(expected) and len(data)==len(expected),"segment identity")
    return data
def read_trial(root,raw,root_bytes,tailname):
    times={"contiguous":[],"tailpack":[]}
    offs=[];rng=0x13579bdf
    for _ in range(READS*ROUNDS):
        rng^=(rng<<13)&0xffffffff;rng^=rng>>17;rng^=(rng<<5)&0xffffffff
        offs.append(rng%max(1,len(raw)-4096+1))
    with ExitStack() as stack:
        f0=stack.enter_context(open(root/"contig","rb",buffering=0))
        f1=stack.enter_context(open(root/"base.bin","rb",buffering=0))
        f2=stack.enter_context(open(root/tailname,"rb",buffering=0))
        for i in range(ROUNDS):
            batch=offs[i*READS:(i+1)*READS]
            order=["contiguous","tailpack"] if i%2==0 else ["tailpack","contiguous"]
            for variant in order:
                t=time.perf_counter_ns()
                for off in batch:
                    n=min(4096,len(raw)-off)
                    if variant=="contiguous":got=os.pread(f0.fileno(),n,off)
                    elif off+n<=root_bytes:got=os.pread(f1.fileno(),n,off)
                    elif off>=root_bytes:got=os.pread(f2.fileno(),n,off-root_bytes)
                    else:
                        got=os.pread(f1.fileno(),root_bytes-off,off)
                        got+=os.pread(f2.fileno(),off+n-root_bytes,0)
                    require(got==raw[off:off+n],"selective exact bytes")
                times[variant].append((time.perf_counter_ns()-t)/1e6/READS)
    med={k:statistics.median(v) for k,v in times.items()}
    return {"raw_ms_per_read":times,"medians_ms_per_read":med,
            "ratio":med["tailpack"]/med["contiguous"],
            "read_bytes":4096,"rounds":ROUNDS,"reads_per_round":READS,"active_fd_count":3}
def run(raw,origin):
    chain=parse_chain(raw);ends=[x["pos"]+68 for x in chain]
    require(len(ends) in (4,64) and ends[-1]==len(raw),"original depth/tail")
    base=raw[:ends[0]];root_bytes=len(base);written=0;json_written=0
    born_tail_blocks=0;born_manifest_blocks=0;file_syncs=1;dir_syncs=0
    with tempfile.TemporaryDirectory(prefix="j24g99-") as dirname:
        root=pathlib.Path(dirname)
        write(root/"contig",raw);write(root/"base.bin",base)
        os.chmod(root/"base.bin",0o444)
        cumulative=[]
        for i,end in enumerate(ends[1:],1):
            tail=raw[root_bytes:end];name=f"tail-{i:03d}.bin"
            write(root/name,tail);os.chmod(root/name,0o444)
            written+=len(tail);file_syncs+=1
            born_tail_blocks+=(root/name).stat().st_blocks*512
            manifest={"schema":"J24G99-O0","generation":i,"length":end,
                      "base":{"name":"base.bin","size":root_bytes,"sha256":sha(base)},
                      "tail":{"name":name,"size":len(tail),"sha256":sha(tail)}}
            mb=(json.dumps(manifest,separators=(",",":"),sort_keys=True)+"\n").encode()
            write(root/"HEAD.tmp",mb);file_syncs+=1
            born_manifest_blocks+=(root/"HEAD.tmp").stat().st_blocks*512
            json_written+=len(mb)
            os.replace(root/"HEAD.tmp",root/"HEAD");fsync_dir(root);dir_syncs+=1
            require(json.loads((root/"HEAD").read_text())==manifest,"manifest switch")
            require(verify(root/"base.bin",base)+verify(root/name,tail)==raw[:end],
                    "historical physical prefix")
            if i>=2:
                oldname=f"tail-{i-1:03d}.bin"
                require(verify(root/oldname,raw[root_bytes:ends[i-1]])==
                        raw[root_bytes:ends[i-1]],"prior snapshot changed")
            # GC is a research assumption: only safe once no old reader owns this epoch.
            if i>=3:(root/f"tail-{i-2:03d}.bin").unlink()
            cumulative.append({"generation":i,"end":end,"tail_bytes":len(tail)})
        latest=f"tail-{len(ends)-1:03d}.bin"
        tail=raw[root_bytes:];last_path=root/latest
        os.chmod(last_path,0o644)
        last_path.write_bytes(tail[:-1]+bytes([tail[-1]^1]))
        reject=(sha(last_path.read_bytes())!=sha(tail))
        last_path.write_bytes(tail);os.chmod(last_path,0o444)
        require(reject,"tamper not detected on reverify")
        latency=read_trial(root,raw,root_bytes,latest)
        fbytes=(root/"contig").stat().st_blocks*512
        bbytes=(root/"base.bin").stat().st_blocks*512
        tbytes=(root/latest).stat().st_blocks*512
        hbytes=(root/"HEAD").stat().st_blocks*512
        ratio=(bbytes+tbytes+hbytes)/fbytes
        direct=len(raw)-root_bytes;full_copy=sum(ends[1:])
        passed=(ratio<=1.05 and written<=40*direct
                and written<=0.10*full_copy and latency["ratio"]<=2)
        return {"origin":origin,"sha256":sha(raw),"archive_bytes":len(raw),
                "footers":len(ends),"footer_ends":ends,"root_bytes":root_bytes,
                "last_append_bytes":ends[-1]-ends[-2],"total_append_bytes":direct,
                "tail_copy_bytes_cumulative":written,"head_json_bytes_cumulative":json_written,
                "full_archive_copy_bytes_cumulative":full_copy,
                "tail_copy_vs_direct":written/direct,"tail_copy_vs_full":written/full_copy,
                "contiguous_allocated":fbytes,"base_allocated":bbytes,
                "latest_tail_allocated":tbytes,"head_allocated":hbytes,"active_allocation_ratio":ratio,
                "new_tail_allocated_cumulative":born_tail_blocks,
                "new_head_allocated_cumulative":born_manifest_blocks,
                "cumulative_allocated_vs_direct":(born_tail_blocks+born_manifest_blocks)/direct,
                "fsync_file_count":file_syncs,"fsync_directory_count":dir_syncs,
                "timeline":cumulative,"mutation_rejected_on_reverify":reject,
                "read":latency,"local_filter_pass":passed}
def main():
    p=argparse.ArgumentParser()
    for key in ZIP_CASES:p.add_argument("--"+key,required=True,type=pathlib.Path)
    p.add_argument("--output",required=True,type=pathlib.Path)
    a=p.parse_args();out={}
    for key,(zsha,source,filenames) in ZIP_CASES.items():
        b=getattr(a,key.replace("-","_")).read_bytes()
        require(sha(b)==zsha,"original ZIP SHA")
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            require(z.read("checkout-head.txt").decode().strip()==source,"source SHA")
            for n in filenames:out[key+"/"+n]=run(z.read(n),key+"/"+n)
    require(len(out)==8,"source count")
    deep=[v for v in out.values() if v["footers"]==64]
    verdict=("O0_ROLLING_TAILPACK_LOCAL_SCREEN_PASS" if all(v["local_filter_pass"] for v in deep)
             else "ROLLING_TAILPACK_SCREEN_FAIL")
    report={"schema":"j24g99-rolling-tailpack-O0-v1","decision":verdict,"cases":out,
            "limitations":["No installed CMPCT Reader/Writer, format mutation or release credit",
                           "No issuer trust, actual immutability, power cut or multiwriter CAS",
                           "GC depends on external reader lifetime; dir/inode overhead not fully charged",
                           "Original Windows source ZIPs are evaluated on one Linux host"]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":verdict,"cases":len(out),
       "deep_ratios":{k:round(v["active_allocation_ratio"],4) for k,v in out.items() if v["footers"]==64},
       "raw_report_sha256":sha(a.output.read_bytes())},sort_keys=True))
if __name__=="__main__":main()
