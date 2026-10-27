#!/usr/bin/env python3
"""O228: standalone research-only virtual reference-run index court (NOT a CMPCT reader).
Every stored owner, chunk length and repeat count is charged to MessagePack+Zstd.
"""
from __future__ import annotations
import argparse, bisect, ctypes, ctypes.util, hashlib, json, random, resource, struct, subprocess, sys, tempfile, time, tracemalloc
from pathlib import Path
import msgpack

LIB=ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so.1")
LIB.ZSTD_compressBound.argtypes=[ctypes.c_size_t]; LIB.ZSTD_compressBound.restype=ctypes.c_size_t
LIB.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]; LIB.ZSTD_compress.restype=ctypes.c_size_t
LIB.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]; LIB.ZSTD_decompress.restype=ctypes.c_size_t
LIB.ZSTD_isError.argtypes=[ctypes.c_size_t]; LIB.ZSTD_isError.restype=ctypes.c_uint
LIB.ZSTD_versionString.restype=ctypes.c_char_p
CASES=("same","run128","run8","run2","alternating","random32","unique32k")
KINDS=("fixed","cdc")
N=262144

def compress(raw):
    output=ctypes.create_string_buffer(LIB.ZSTD_compressBound(len(raw)))
    inp=ctypes.create_string_buffer(raw)
    n=LIB.ZSTD_compress(output,len(output),inp,len(raw),12)
    if LIB.ZSTD_isError(n):raise ValueError("zstd compress failure")
    return output.raw[:n]
def decompress(enc,rawlen):
    buf=ctypes.create_string_buffer(rawlen); inp=ctypes.create_string_buffer(enc)
    n=LIB.ZSTD_decompress(buf,rawlen,inp,len(enc))
    if LIB.ZSTD_isError(n) or n!=rawlen:raise ValueError("zstd decode mismatch")
    return buf.raw[:n]

def ids_for(name):
    n=32768 if name=="unique32k" else N
    if name=="same":return [0]*n
    if name.startswith("run"):return [(i//int(name[3:]))%64 for i in range(n)]
    if name=="alternating":return [i%2 for i in range(n)]
    if name=="unique32k":return list(range(n))
    r=random.Random(20261027);return [r.randrange(32) for _ in range(n)]

def payload(idx,kind):
    seed=hashlib.sha256(b"O228 physical"+struct.pack("<I",idx)).digest()
    return (seed*3)[:64+(8*(idx%4) if kind=="cdc" else 0)]

def build(name,kind):
    ids=ids_for(name); blob=[payload(i,kind) for i in range(max(ids)+1)]
    lengths=[len(blob[i]) for i in ids]
    runs=[]
    for owner,ln in zip(ids,lengths):
        if runs and runs[-1][1:]==[ln,owner]:runs[-1][0]+=1
        else:runs.append([1,ln,owner])
    logical=hashlib.sha256()
    for i in ids:logical.update(blob[i])
    total=sum(lengths); checksum=logical.digest()
    refs=ids if kind=="fixed" else [[lengths[j],i] for j,i in enumerate(ids)]
    table=[[j*128,len(b),len(b),0,0] for j,b in enumerate(blob)]
    def ix(storage):
        return {"v":24,"files":[["f.bin",0,420,0,total,checksum,storage]],
                "blobs":table,"recipes":[],"dict_blob":None,
                "fsmeta":{"owner":[0,0],"owner_overrides":[],"xattrs":[]},"features":[]}
    baseline=ix([1 if kind=="fixed" else 5,refs])
    candidate=ix([101 if kind=="fixed" else 105,runs])
    return baseline,candidate,blob,len(ids),len(runs)

def validate(storage,blob,declared,kind,cap=1000000):
    if not isinstance(storage,list) or len(storage)!=2 or type(storage[0]) is not int or storage[0]!=(101 if kind=="fixed" else 105):raise ValueError("tag")
    n=0; total=0
    for entry in storage[1]:
        if not isinstance(entry,list) or len(entry)!=3 or any(type(x) is not int for x in entry):raise ValueError("entry/type")
        count,length,owner=entry
        if count<=0 or count>cap-n or owner<0 or owner>=len(blob) or length<=0 or length!=len(blob[owner]):raise ValueError("bounds")
        n+=count;total+=count*length
        if total>declared or total>2**63-1:raise ValueError("overflow")
    if total!=declared:raise ValueError("declared logical geometry")
    return n,total

def digest_semantics(storage,kind,blob):
    sha=hashlib.sha256()
    if storage[0] in (1,5):
        for row in storage[1]:
            ln,owner=(len(blob[row]),row) if kind=="fixed" else row
            sha.update(struct.pack("<QI",ln,owner))
    else:
        for count,ln,owner in storage[1]:
            item=struct.pack("<QI",ln,owner)
            for _ in range(count):sha.update(item)
    return sha.hexdigest()

def samples(storage,kind,blob,declared):
    if storage[0] in (1,5):
        entries=[(len(blob[i]),i) if kind=="fixed" else tuple(i) for i in storage[1]]
        prefixes=[0]
        for length,_ in entries:prefixes.append(prefixes[-1]+length)
        def byte_at(offset):
            i=bisect.bisect_right(prefixes,offset)-1
            return blob[entries[i][1]][offset-prefixes[i]]
    else:
        entries=storage[1];prefixes=[0]
        for count,length,_ in entries:prefixes.append(prefixes[-1]+count*length)
        def byte_at(offset):
            i=bisect.bisect_right(prefixes,offset)-1
            count,length,owner=entries[i]
            return blob[owner][(offset-prefixes[i])%length]
    r=random.Random(1032)
    offsets=[0,declared//2,declared-1]+[r.randrange(declared) for _ in range(24)]
    return [hashlib.sha256(bytes(byte_at(x) for x in range(offset,min(declared,offset+16)))).hexdigest() for offset in offsets]

def attacks(storage,blob,declared,kind):
    base=storage[1][0]; rejected=0
    variations=[(0,base[1],base[2]),(-1,base[1],base[2]),(True,base[1],base[2]),
                (10**30,base[1],base[2]),(base[0],0,base[2]),(base[0],-1,base[2]),
                (base[0],base[1],-1),(base[0],base[1],len(blob)),
                (base[0],base[1]+1,base[2])]
    for first in variations:
        bad=[storage[0],[list(first)]+storage[1][1:]]
        try:validate(bad,blob,declared,kind)
        except ValueError:rejected+=1
    for wrong in (declared-1,declared+1):
        try:validate(storage,blob,wrong,kind)
        except ValueError:rejected+=1
    if rejected!=11:raise AssertionError(f"adversarial admission only {rejected}/11")
    return rejected

def child(path):
    data=msgpack.unpackb(Path(path).read_bytes(),raw=False)
    t=time.perf_counter_ns();cpu=time.process_time_ns()
    raw=decompress(data["compressed"],data["raw_size"])
    full_wall=time.perf_counter_ns()-t;full_cpu=time.process_time_ns()-cpu
    tracemalloc.start()
    t=time.perf_counter_ns();cpu=time.process_time_ns()
    obj=msgpack.unpackb(raw,raw=False)
    unpack_wall=time.perf_counter_ns()-t;unpack_cpu=time.process_time_ns()-cpu
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    print(json.dumps({"decompress_wall_ns":full_wall,"decompress_cpu_ns":full_cpu,
                      "unpack_wall_ns":unpack_wall,"unpack_cpu_ns":unpack_cpu,
                      "unpack_heap_peak":peak,"unpack_heap_current":current,
                      "resident_peak_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      "materialized_storage_entries":len(obj["files"][0][6][1])},sort_keys=True))

def main(out):
    rows=[]; failures=0
    with tempfile.TemporaryDirectory(prefix="o228-") as d:
        for kind in KINDS:
            for case in CASES:
                literal,run,blob,n,nruns=build(case,kind)
                declared=literal["files"][0][4]
                assert validate(run["files"][0][6],blob,declared,kind)[0]==n
                assert digest_semantics(literal["files"][0][6],kind,blob)==digest_semantics(run["files"][0][6],kind,blob)
                assert samples(literal["files"][0][6],kind,blob,declared)==samples(run["files"][0][6],kind,blob,declared)
                rejects=attacks(run["files"][0][6],blob,declared,kind)
                arms={}
                for label,index in (("literal",literal),("runs",run)):
                    start=time.perf_counter_ns();cpu=time.process_time_ns()
                    wire=msgpack.packb(index,use_bin_type=True);packed=compress(wire)
                    encode_wall=time.perf_counter_ns()-start;encode_cpu=time.process_time_ns()-cpu
                    testfile=Path(d)/(kind+"-"+case+"-"+label+".msgpack")
                    testfile.write_bytes(msgpack.packb({"compressed":packed,"raw_size":len(wire)},use_bin_type=True))
                    trials=[]
                    for repetition in range(3):
                        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--child",str(testfile)],
                                         capture_output=True,text=True,timeout=60,check=True)
                        trials.append(json.loads(p.stdout))
                    arms[label]={"index_raw":len(wire),"index_zstd":len(packed),
                                 "dual_index_zstd":2*len(packed),"encode_wall_ns":encode_wall,
                                 "encode_cpu_ns":encode_cpu,
                                 "raw_index_sha256":hashlib.sha256(wire).hexdigest(),"trials":trials}
                physical=sum(64+len(b) for b in blob)
                best=min(arms,key=lambda x:arms[x]["dual_index_zstd"])
                rows.append({"case":case,"kind":kind,"logical_refs":n,"logical_size":declared,
                             "run_count":nruns,"physical_record_bytes_proxy":physical,
                             "semantic_sha_equal":True,"selective_byte_equal":True,
                             "hostile_rejects":rejects,"best_full_index_oracle":best,"arms":arms})
                print(f"{kind}/{case}: {n} refs {nruns} runs; bytes {arms['literal']['index_zstd']} vs {arms['runs']['index_zstd']}",file=sys.stderr,flush=True)
    data={"schema":"cmpct-o228-oracle-v1","source_kind":"synthetic-r24-index-shape-not-CMPCT-archive",
          "release_control":"main@80c358f8824ec1b20d349c92ed94c898090969b0",
          "environment":{"python":sys.version,"msgpack":str(msgpack.version),
                         "zstd":LIB.ZSTD_versionString().decode(),"platform":sys.platform},
          "rows":rows}
    Path(out).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    assert len(rows)==14
    assert all(len(a["trials"])==3 for row in rows for a in row["arms"].values())
    print(json.dumps({"cases":len(rows),"fresh_process_observations":84,"output":out}))

def audit(path):
    doc=json.loads(Path(path).read_text())
    assert doc["schema"]=="cmpct-o228-oracle-v1" and len(doc["rows"])==14
    import statistics
    report=[]
    for row in doc["rows"]:
        a,b=row["arms"]["literal"],row["arms"]["runs"]
        assert row["semantic_sha_equal"] and row["selective_byte_equal"] and row["hostile_rejects"]==11
        assert len(a["trials"])==len(b["trials"])==3
        assert row["best_full_index_oracle"]==min(row["arms"],key=lambda x:row["arms"][x]["dual_index_zstd"])
        m=lambda arm:statistics.median(t["unpack_heap_peak"] for t in arm["trials"])
        report.append({"case":row["case"],"kind":row["kind"],"raw_refs":row["logical_refs"],
                       "runs":row["run_count"],"zstd_bytes_literal":a["index_zstd"],
                       "zstd_bytes_runs":b["index_zstd"],
                       "decode_heap_ratio":round(m(a)/max(1,m(b)),3),
                       "best":row["best_full_index_oracle"]})
    print(json.dumps({"audit":"PASS","observations":84,"table":report},indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--child");p.add_argument("--output");p.add_argument("--audit")
    args=p.parse_args()
    if args.child:child(args.child)
    elif args.output:main(args.output)
    elif args.audit:audit(args.audit)
    else:p.error("specify child, output or audit")
