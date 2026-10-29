#!/usr/bin/env python3
"""A06-O0: lower-rung exact off-boundary copy oracle. NOT a CMPCT encoder."""
import ctypes, hashlib, json, os, pathlib, platform, random, resource, sys, time
from collections import defaultdict

W=64; BASE=257; MASK=(1<<64)-1; LOW=(1<<9)-1; MAX_BUCKET=4
POWER=pow(BASE,W-1,1<<64)

class Zstd:
    def __init__(self):
        self.z=ctypes.CDLL("libzstd.so.1")
        self.z.ZSTD_compressBound.argtypes=[ctypes.c_size_t]
        self.z.ZSTD_compressBound.restype=ctypes.c_size_t
        self.z.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
        self.z.ZSTD_compress.restype=ctypes.c_size_t
        self.z.ZSTD_isError.argtypes=[ctypes.c_size_t]
        self.z.ZSTD_isError.restype=ctypes.c_uint
    def size(self,b):
        if not b:return 0
        src=ctypes.create_string_buffer(bytes(b))
        dst=ctypes.create_string_buffer(self.z.ZSTD_compressBound(len(b)))
        n=self.z.ZSTD_compress(dst,len(dst),src,len(b),19)
        assert not self.z.ZSTD_isError(n)
        return int(n)

def anchors(b):
    if len(b)<W:return
    h=0
    for x in b[:W]:h=(h*BASE+x)&MASK
    if not(h&LOW):yield (0,h)
    for i in range(1,len(b)-W+1):
        h=(((h-b[i-1]*POWER)&MASK)*BASE+b[i+W-1])&MASK
        if not(h&LOW):yield (i,h)

def cohorts():
    groups=[
       ("other_h", "/usr/include", lambda p:p.suffix==".h" and not str(p).startswith(("/usr/include/c++/","/usr/include/boost/"))),
       ("cxx_h", "/usr/include/c++", lambda p:p.suffix==".h"),
       ("boost_hpp", "/usr/include/boost", lambda p:p.suffix==".hpp")]
    for name,root,predicate in groups:
        paths=[]
        for p in pathlib.Path(root).rglob("*"):
            try:
                if not p.is_file() or p.is_symlink() or not predicate(p):continue
                if 2048<=p.stat().st_size<=262144:paths.append(p)
            except OSError:pass
        paths.sort(key=lambda p:(hashlib.sha256(str(p).encode()).digest(),str(p)))
        if len(paths)<32:raise RuntimeError("missing cohort "+name)
        yield name,paths[:32],len(paths)

def profile(label,inputs,z):
    blobs=[p.read_bytes() if isinstance(p,pathlib.Path) else p for p in inputs]
    seen=defaultdict(list);all_matches=[];confirmed=0
    for i,b in enumerate(blobs):
        choices=set()
        for off,h in anchors(b):
            for source,soff in seen.get(h,()):
                prev=blobs[source]
                if prev[soff:soff+W]!=b[off:off+W]:continue
                a=off; s=soff;end=off+W;send=soff+W
                while a>0 and s>0 and off-a<65536 and b[a-1]==prev[s-1]:
                    a-=1;s-=1
                while end<len(b) and send<len(prev) and end-a<65536 and b[end]==prev[send]:
                    end+=1;send+=1
                if end-a>=128:choices.add((a,end,source,s))
        chosen=[]
        for a,end,src,offset in sorted(choices,key=lambda x:(x[0]-x[1],x)):
            if all(end<=x or a>=y for x,y,*_ in chosen):chosen.append((a,end,src,offset))
        chosen.sort();all_matches.append(chosen);confirmed+=len(chosen)
        for off,h in anchors(b):
            if len(seen[h])<MAX_BUCKET:seen[h].append((i,off))
    base_ids={src for group in all_matches for _,_,src,_ in group}
    per=[];charged=0;actual_matched=0;copy_count=0;ampl=[];independent=0
    base_sizes=[z.size(b) for b in blobs]
    independent=sum(base_sizes)+16*len(blobs)
    for i,(b,matches) in enumerate(zip(blobs,all_matches)):
        meta={"path":str(inputs[i]) if isinstance(inputs[i],pathlib.Path) else "fixture-"+str(i),
              "sha256":hashlib.sha256(b).hexdigest(),"size":len(b)}
        if i in base_ids:
            charged+=base_sizes[i]+16
            meta.update({"root":True,"reference_count":0,"copy_bytes":0})
            per.append(meta);continue
        literal=bytearray();rebuild=bytearray();position=0
        for a,end,src,s in matches:
            literal+=b[position:a];rebuild+=b[position:a]
            chunk=blobs[src][s:s+end-a]
            assert chunk==b[a:end]
            rebuild+=chunk;copy_count+=1;actual_matched+=len(chunk)
            ampl.append(len(blobs[src])/len(chunk))
            position=end
        literal+=b[position:];rebuild+=b[position:]
        assert rebuild==b, "reconstruction mismatch"
        charged+=z.size(literal)+16+16*len(matches)
        meta.update({"root":False,"reference_count":len(matches),"copy_bytes":sum(end-a for a,end,_,_ in matches)})
        per.append(meta)
    full_seen=set();whole_dup=0;blocks={};fixed4=0
    for i,b in enumerate(blobs):
        sha=hashlib.sha256(b).digest()
        if sha in full_seen:whole_dup+=len(b)
        full_seen.add(sha)
        for off in range(0,len(b)-4095,4096):
            key=(off,hashlib.sha256(b[off:off+4096]).digest())
            if key in blocks and blocks[key]!=i:fixed4+=4096
            else:blocks.setdefault(key,i)
    gifted=sum(end-a for group in all_matches for a,end,_,_ in group)
    n=sum(map(len,blobs));solid=z.size(b"".join(blobs))
    return {"cohort":label,"file_count":len(blobs),"logical_bytes":n,
      "gifted_coverage_bytes":gifted,"gifted_coverage_fraction":gifted/n,
      "charged_copy_bytes":actual_matched,"charged_reference_count":copy_count,"root_files":len(base_ids),
      "complete_candidate_bytes_lower_bound":charged,"independent_zstd19_plus_16B_per_file":independent,
      "solid_zstd19_bytes":solid,"candidate_delta_vs_independent":charged-independent,
      "candidate_delta_vs_solid":charged-solid,
      "whole_file_duplicate_bytes":whole_dup,"same_position_4k_bytes":fixed4,
      "max_source_file_to_ref_decode_ratio":max(ampl or [0]),
      "correct_exact_reconstruction":True,"files":per}

def controls(z):
    rng=random.Random(4471)
    b=bytes(rng.getrandbits(8) for _ in range(8192))
    shift=profile("shifted",[b,b"offset-shift!!!"+b+b"extra!!"],z)
    noises=[]
    for i in range(3):
        r=random.Random(i+30)
        noises.append(bytes(r.getrandbits(8) for _ in range(8192)))
    neg=profile("independent_random",noises,z)
    assert shift["gifted_coverage_bytes"]>=8192
    assert neg["gifted_coverage_bytes"]==0
    return {"shifted":shift,"random_negative":neg}

def main():
    start=time.monotonic();z=Zstd()
    output={"experiment":"A06-O0","evidence_class":"incomplete research oracle, not CMPCT product",
      "prereg_sha":"c2b4f7efa0f8e7e1fd193c7b3e5de12fd5d1cb88",
      "published_main":"80c358f8824ec1b20d349c92ed94c898090969b0",
      "environment":{"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "python":sys.version,"host":platform.platform()},
      "controls":controls(z),"cohorts":[]}
    if "--controls-only" not in sys.argv:
        for name,paths,eligible in cohorts():
            x=profile(name,paths,z);x["eligible_files"]=eligible
            output["cohorts"].append(x)
    output["wall_seconds"]=time.monotonic()-start
    output["peak_rss_kib"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with open("a06_o0_results.json","w") as fp:json.dump(output,fp,sort_keys=True,indent=2)
    print(json.dumps({x["cohort"]:{"gifted_coverage_fraction":x["gifted_coverage_fraction"],
        "candidate_delta_vs_solid":x["candidate_delta_vs_solid"],
        "candidate_delta_vs_independent":x["candidate_delta_vs_independent"]}
        for x in output["cohorts"]},sort_keys=True))
    print("control PASS",flush=True)

if __name__=="__main__":main()
