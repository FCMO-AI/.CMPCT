#!/usr/bin/env python3
"""O218 lower-rung CPython direct-list admission oracle; never product credit.
Preregistered at 94a7eaf09ba18131a4eab7111e3f0ce6a70e8047.
All encoded fixtures are generic deterministic msgpack structure, not workload IDs.
"""
import argparse
import hashlib
import importlib.util
import json
import random
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time
from pathlib import Path
import msgpack

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"o218_fastscan.c"

def load_native(tmp):
    out=Path(tmp)/("_o218_fastscan"+sysconfig.get_config_var("EXT_SUFFIX"))
    cmd=["gcc","-O3","-fPIC","-shared","-Wall","-Wextra","-Werror",
         "-I"+sysconfig.get_config_var("INCLUDEPY"),str(SOURCE),"-o",str(out)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    spec=importlib.util.spec_from_file_location("_o218_fastscan",out)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module,cmd

def strong_python(refs,blobs,size):
    if type(refs) is not list or type(blobs) is not list or type(size) is not int or size<0:
        return False
    count=len(blobs)
    total=0
    for idx in refs:
        if type(idx) is not int or idx<0 or idx>=count:return False
        row=blobs[idx]
        if type(row) is not list or len(row)!=5:return False
        length=row[1]
        if type(length) is not int or length<0:return False
        total+=length
    return total==size

def o216_like_python(refs,blobs,size):
    """Safe on prevalidated blob rows. Not a replacement for original source validator."""
    if type(refs) is not list or type(blobs) is not list or type(size) is not int or size<0:
        return False
    count=len(blobs);total=0
    for idx in refs:
        if type(idx) is not int or idx<0 or idx>=count:return False
        total+=blobs[idx][1]
    return total==size

def fixture(n,unique):
    rng=random.Random(218+n+unique)
    owners=min(n,unique)
    blobs=[[i*37,17+i%7,33,0,0] for i in range(owners)]
    ids=([0]*n if unique==1 else list(range(n)) if unique==n
         else [rng.randrange(owners) for _ in range(n)])
    payload=msgpack.packb({"r":ids,"b":blobs},use_bin_type=True)
    record=msgpack.unpackb(payload,raw=False)
    ids,blobs=record["r"],record["b"]
    declared=sum(blobs[idx][1] for idx in ids)
    return ids,blobs,declared,len(payload),hashlib.sha256(payload).hexdigest()

def attack(native):
    blob=[[0,3,3,0,0],[3,5,5,0,0]]
    cases=[
      ("valid", [0,1,0],blob,11), ("empty",[],blob,0),
      ("bool",[0,True],blob,8), ("float",[0,0.0],blob,6),
      ("negative",[0,-1],blob,6), ("out_of_range",[0,2],blob,6),
      ("gigantic_ref",[0,2**120],blob,6), ("wrong_size",[0,1],blob,9),
      ("negative_size",[0,1],blob,-1), ("bool_size",[0,1],blob,True),
      ("huge_size",[0,1],blob,2**120), ("tuple_refs",(0,1),blob,8),
      ("bad_blob_length",[0],[[0,-1,3,0,0]],0),
      ("bool_blob_length",[0],[[0,True,3,0,0]],1),
      ("short_row",[0],[[0,3]],3),
      ("too_large_blob",[0],[[0,2**120,3,0,0]],2**120)
    ]
    outcome=[]
    for label,refs,blobs,size in cases:
        expected=strong_python(refs,blobs,size)
        proposed=bool(native.scan_refs(refs,blobs,size))
        if proposed and not expected:
            raise AssertionError("NATIVE_FALSE_ACCEPT "+label)
        # Expected true can safely return False: mandatory original-validator fallback.
        outcome.append({"case":label,"reference":expected,"native":proposed,
                        "fallback":not proposed})
    # Adversarial stochastic fuzz, deterministic seed, no after-the-fact selection.
    rng=random.Random(9218)
    pool=[0,1,2,3,-1,True,False,1.0,None,"0",2**120,[],(1,),{"a":1}]
    for i in range(5000):
        refs=[rng.choice(pool) for _ in range(rng.randrange(0,7))]
        try:
            expected=strong_python(refs,blob,rng.choice([0,3,5,8,11,2**120]))
            proposed=bool(native.scan_refs(refs,blob,rng.choice([0,3,5,8,11,2**120])))
        except Exception as exc:
            raise AssertionError("native unexpected exception at "+str(i)) from exc
        # Different declared sizes above mean no value comparison; test safety on SAME input below.
        size=rng.choice([0,3,5,8,11,2**120])
        if bool(native.scan_refs(refs,blob,size)) and not strong_python(refs,blob,size):
            raise AssertionError("fuzz false accept "+str(i))
    return outcome

def run(output,rounds):
    with tempfile.TemporaryDirectory(prefix="o218-native-") as tmp:
        mod,compiler=load_native(tmp)
        hostile=attack(mod)
        profiles=[(4096,1),(4096,4096),(65536,1),(65536,4096),
                  (65536,65536),(262144,1),(262144,4096),(262144,262144)]
        samples=[]
        for n,d in profiles:
            refs,blobs,declared,payload_len,digest=fixture(n,d)
            ops={"strong_py":strong_python,"o216_like":o216_like_python,"native":mod.scan_refs}
            for op in ops.values():
                assert op(refs,blobs,declared) is True
            rng=random.Random(n+d+218)
            for rep in range(rounds):
                names=list(ops)
                rng.shuffle(names)
                for name in names:
                    f=ops[name]
                    start_cpu=time.process_time_ns();start=time.perf_counter_ns()
                    value=f(refs,blobs,declared)
                    elapsed=time.perf_counter_ns()-start
                    elapsed_cpu=time.process_time_ns()-start_cpu
                    assert value is True
                    samples.append({"n":n,"unique":d,"rep":rep,"method":name,
                                    "wall_ns":elapsed,"cpu_ns":elapsed_cpu,
                                    "wire_bytes":payload_len,"wire_sha256":digest})
        summary=[]
        for n,d in profiles:
            times={k:[r["wall_ns"] for r in samples if r["n"]==n and
                       r["unique"]==d and r["method"]==k]
                   for k in ("strong_py","o216_like","native")}
            med={k:statistics.median(v)/1e6 for k,v in times.items()}
            summary.append({"n":n,"unique":d,"median_wall_ms":med,
                "o216_over_native":round(med["o216_like"]/med["native"],4)})
        decisive=[r for r in summary if r["n"] in (65536,262144)
                  and r["unique"] in (1,r["n"])]
        decision=("MICRO_NATIVE_HEADROOM" if all(r["o216_over_native"]>=3 for r in decisive)
                  else "MICRO_NATIVE_INSUFFICIENT")
        result={"evidence_tier":"detached_micro_not_product","decision":decision,
                "source_parent":"6989b25640be2c82436bb77ec545dd15816f698b",
                "prereg_sha":"94a7eaf09ba18131a4eab7111e3f0ce6a70e8047",
                "python":sys.version,"platform":sys.platform,"compiler_argv":compiler,
                "c_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "hostile":hostile,"fuzz_cases":5000,"summary":summary,"samples":samples}
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        Path(output).write_text(json.dumps(result,indent=2,sort_keys=True))
        print(json.dumps({"decision":decision,"summary":summary,
                          "hostile_cases":len(hostile),"fuzz_cases":5000,
                          "samples":len(samples)},sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    ap.add_argument("--rounds",type=int,default=11)
    args=ap.parse_args()
    run(args.output,args.rounds)
