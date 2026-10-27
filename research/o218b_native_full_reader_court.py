#!/usr/bin/env python3
"""O218b full installed-Reader C-list admission scientific court (not a product patch)."""
import argparse, hashlib, importlib.util, inspect, json, os, random, statistics, subprocess, sys, tempfile, time
from pathlib import Path
import cmpct.reader as reader_mod
import cmpct.validation as validation
from cmpct.codec import K_FILE, S_CHUNKS
from cmpct.reader import CMPCT
import o216_fixed_chunk_validator_fastpath_oracle as o216
from o218_native_validator_oracle import load_native

READER_BLOB="dbd4ac576a05a47eae97e1e40de89cf1de440516"
VALIDATOR_BLOB="51c2849061f99a4afeddb7666956b24566ce7de0"
C_BLOB="a54f15181d9dbe667b9e8c9d52e927b09c80152f"
PARENT="6372e780be99a31f5ea21b7a3c74fde92cf0bc45"
PREREG="4ad8b7770693832940e766300bcac4a1ea4f0a84"
ORIGINAL=o216.ORIGINAL
METHODS=("original","fast","native","unguarded")
PROFILES=((1,1),(4096,1),(65536,1),(262144,1),(65536,256),(262144,256))

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def source_identity():
    r=git_blob(Path(inspect.getfile(reader_mod)).read_bytes())
    v=git_blob(Path(inspect.getfile(validation)).read_bytes())
    c=git_blob((Path(__file__).parent/"o218_fastscan.c").read_bytes())
    assert (r,v,c)==(READER_BLOB,VALIDATOR_BLOB,C_BLOB),(r,v,c)
    return {"reader":r,"validator":v,"native_c":c}

def load_binary(path):
    spec=importlib.util.spec_from_file_location("_o218_fastscan",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def native_validator(module):
    def checked(path,kind,size,storage,blobs,recipes):
        if kind==K_FILE and isinstance(storage,list) and storage and storage[0]==S_CHUNKS:
            if len(storage)==2 and isinstance(storage[1],list):
                if module.scan_refs(storage[1],blobs,size) is True:
                    return None
        return ORIGINAL(path,kind,size,storage,blobs,recipes)
    return checked

def install(mode,module):
    validation._validate_storage={
       "original":ORIGINAL,"fast":o216.fast_validate,
       "native":native_validator(module),"unguarded":o216.unguarded_oracle
    }[mode]

def outcome(fn,size,storage,blobs,kind=K_FILE):
    try:
        fn("fixed.bin",kind,size,storage,blobs,[])
        return ["ACCEPT"]
    except Exception as e:
        return ["REJECT",type(e).__name__,str(e)]

def semantics(module):
    inherited=o216.semantics_court()  # unchanged O216 19-case control
    blob=[[0,4,4,0,0],[0,7,7,0,0]]
    cases=[
      ("empty",0,[S_CHUNKS,[]]),("one",4,[S_CHUNKS,[0]]),
      ("repeated",8,[S_CHUNKS,[0,0]]),("distinct",11,[S_CHUNKS,[0,1]]),
      ("short",4,[S_CHUNKS,[1]]),("long",8,[S_CHUNKS,[1]]),
      ("bool",4,[S_CHUNKS,[True]]),("false",4,[S_CHUNKS,[False]]),
      ("float",4,[S_CHUNKS,[0.0]]),("negative",4,[S_CHUNKS,[-1]]),
      ("outside",4,[S_CHUNKS,[2]]),("giant",4,[S_CHUNKS,[2**120]]),
      ("text",4,[S_CHUNKS,["0"]]),("none",4,[S_CHUNKS,[None]]),
      ("dict",4,[S_CHUNKS,[{}]]),("sublist",4,[S_CHUNKS,[[0]]]),
      ("late-bool",12,[S_CHUNKS,[0,0,True]]),
      ("late-outside",12,[S_CHUNKS,[0,0,2]]),
      ("empty-storage",4,[]),("missing-list",4,[S_CHUNKS]),
      ("extra",4,[S_CHUNKS,[0],1]),("map",4,[S_CHUNKS,{}]),
      ("large-valid",16384,[S_CHUNKS,[0]*4096]),
      ("large-late-bool",16384,[S_CHUNKS,[0]*4095+[False]])]
    native=native_validator(module)
    rows=[]
    for label,size,storage in cases:
        a=outcome(ORIGINAL,size,storage,blob)
        b=outcome(native,size,storage,blob)
        assert a==b,(label,a,b)
        rows.append({"case":label,"outcome":a})
    rng=random.Random(2182026)
    pool=[0,1,2,-1,True,False,0.,None,"0",2**120,[0],{}]
    for i in range(2500):
        refs=[rng.choice(pool) for _ in range(rng.randrange(8))]
        size=rng.choice((0,4,7,11,15,2**120))
        a=outcome(ORIGINAL,size,[S_CHUNKS,refs],blob)
        b=outcome(native,size,[S_CHUNKS,refs],blob)
        assert a==b,(i,a,b)
    return {"inherited_cases":len(inherited),"named_cases":rows,"fuzz_cases":2500}

def worker(archive,size,mode,lib):
    module=load_binary(lib);source=source_identity();install(mode,module)
    with CMPCT(Path(archive)) as rd:
        assert len(rd.files)==1 and rd.files[0][4]==size
        assert rd.read_range("fixed.bin",0,4)==b"ABCD"
    samples=[]
    for _ in range(5):
        t=time.perf_counter_ns();c=time.process_time_ns()
        with CMPCT(Path(archive)) as rd:
            assert len(rd.files)==1 and rd.files[0][4]==size
        samples.append({"wall_ns":time.perf_counter_ns()-t,"cpu_ns":time.process_time_ns()-c})
    rss=None
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):rss=int(line.split()[1])*1024
    except OSError:pass
    print(json.dumps({"mode":mode,"source":source,"samples":samples,
                      "vmhwm_bytes":rss,"python":sys.version},sort_keys=True))

def build_case(n,owners):
    blobs=tuple(bytes([65+i%23,66,67,68]) for i in range(owners))
    refs=[i%owners for i in range(n)]
    logical=b"".join(blobs[idx] for idx in refs)
    return refs,logical,blobs

def controller(output):
    source=source_identity()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
    from test_o215_fixed_chunk_admission import _make_archive
    with tempfile.TemporaryDirectory(prefix="o218b-") as td:
        native,compiler=load_native(td)
        contract=semantics(native)
        lib=str(Path(td)/("_o218_fastscan"+__import__("sysconfig").get_config_var("EXT_SUFFIX")))
        rows=[];manifests=[];rng=random.Random(21822026)
        for n,owners in PROFILES:
            refs,logical,blobs=build_case(n,owners)
            wire=_make_archive(refs,logical,blobs=blobs)
            file=Path(td)/f"refs-{n}-{owners}.cmpct";file.write_bytes(wire)
            if n<=4096:
                with CMPCT(file) as rd:
                    assert rd.read("fixed.bin")==logical and rd.verify()==1
                    assert rd.read_range("fixed.bin",len(logical)-4,4)==logical[-4:]
            manifests.append({"count":n,"owners":owners,"archive_bytes":len(wire),
              "archive_sha256":hashlib.sha256(wire).hexdigest(),
              "logical_sha256":hashlib.sha256(logical).hexdigest(),
              "full_read_verified":n<=4096})
            for cycle in range(3):
                arms=list(METHODS)*2;rng.shuffle(arms)
                for mode in arms:
                    cmd=[sys.executable,str(Path(__file__).resolve()),"--worker",
                         str(file),str(len(logical)),mode,lib]
                    p=subprocess.run(cmd,capture_output=True,text=True,check=True,cwd=td,timeout=120)
                    result=json.loads(p.stdout)
                    assert result["mode"]==mode and result["source"]==source
                    result.update(count=n,owners=owners,cycle=cycle)
                    rows.append(result)
            print(f"O218B_PROFILE count={n} owners={owners} workers=24",flush=True)
        summary=[]
        for n,owners in PROFILES:
            timings={m:[statistics.median(x["wall_ns"] for x in r["samples"])
               for r in rows if r["count"]==n and r["owners"]==owners and r["mode"]==m]
               for m in METHODS}
            med={m:statistics.median(timings[m])/1e6 for m in METHODS}
            summary.append({"count":n,"owners":owners,"median_wall_ms":med,
              "fast_over_native":med["fast"]/med["native"],
              "native_over_unguarded":med["native"]/med["unguarded"],
              "native_extra_ms":med["native"]-med["unguarded"]})
        focus=[s for s in summary if s["owners"]==1 and s["count"] in (65536,262144)]
        passed=all(s["fast_over_native"]>=2.5 and s["native_over_unguarded"]<2 and
              s["native_extra_ms"]<=(5 if s["count"]==65536 else 20) for s in focus)
        result={"tier":"whole_installed_reader_science_not_product",
          "decision":"NATIVE_READER_ROUTE_WORTH_PRODUCTIZATION" if passed else
                     "NATIVE_READER_ROUTE_INSUFFICIENT",
          "source":source,"parent":PARENT,"prereg":PREREG,
          "semantics":contract,"manifests":manifests,
          "compiler_argv":compiler,"native_binary_bytes":Path(lib).stat().st_size,
          "raw_workers":rows,"summary":summary,
          "limitations":["Linux CPython only","C extension research injection only",
             "compiler and process startup excluded from timed constructor",
             "high-reference complete read/verify not exercised due futures RSS risk",
             "native package/wheel/ABI, release parity and portability unmeasured"]}
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(result,sort_keys=True,indent=2))
        print("O218B_DECISION="+result["decision"],flush=True)
        print("O218B_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output");p.add_argument("--worker",nargs=4)
    a=p.parse_args()
    if a.worker:
        archive,size,mode,lib=a.worker;worker(archive,int(size),mode,lib)
    else:
        if not a.output:p.error("--output required")
        controller(a.output)
