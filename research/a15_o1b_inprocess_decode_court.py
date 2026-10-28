#!/usr/bin/env python3
"""A15-O1b independent in-process Zstd decode-cost counterfactual. Science only."""
from __future__ import annotations
import argparse
import ctypes
import ctypes.util
import hashlib
import json
import statistics
import struct
import time
from pathlib import Path

CHUNK=4096
MEMBER=65536
COUNT=32
TARGETS=(0,17,31)
Z=ctypes.CDLL(ctypes.util.find_library("zstd"))
Z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
Z.ZSTD_decompress.restype=ctypes.c_size_t
Z.ZSTD_isError.argtypes=[ctypes.c_size_t]
Z.ZSTD_isError.restype=ctypes.c_uint

def sha(x):
    return hashlib.sha256(x).digest()

def dec(frame,amount):
    out=ctypes.create_string_buffer(amount)
    n=Z.ZSTD_decompress(out,amount,frame,len(frame))
    if Z.ZSTD_isError(n) or n!=amount:
        raise ValueError("invalid frame or length")
    return out.raw

def a15_frames(blob):
    if len(blob)<12:
        raise ValueError("short A15")
    magic,kind,members,programs=struct.unpack_from("<4sBHH",blob)
    if (magic,kind,members,programs)!=(b"A15O",1,COUNT,1) or blob[9:12]!=b"\x01\x00\x00":
        raise ValueError("invalid A15 grammar")
    pos=12
    frames=[]
    for _ in range(COUNT):
        if pos+42>len(blob):
            raise ValueError("short member")
        pid,n,checksum,sz=struct.unpack_from("<HI32sI",blob,pos)
        pos+=42
        if pid!=0 or n!=MEMBER or sz>1<<21 or pos+sz>len(blob):
            raise ValueError("member bounds")
        frames.append((blob[pos:pos+sz],checksum));pos+=sz
    if pos!=len(blob):
        raise ValueError("A15 trailing")
    return frames

def ref_frames(blob):
    if len(blob)<12:
        raise ValueError("short REF")
    magic,count,nowners,chunksize=struct.unpack_from("<4sHHI",blob)
    if magic!=b"RFO1" or count!=COUNT or nowners>512 or chunksize!=CHUNK:
        raise ValueError("bad REF header")
    pos=12;owners=[]
    for _ in range(nowners):
        if pos+36>len(blob):
            raise ValueError("short owner")
        length=struct.unpack_from("<I",blob,pos)[0]
        checksum=blob[pos+4:pos+36]
        pos+=36
        if length>65536 or pos+length>len(blob):
            raise ValueError("owner bounds")
        owners.append((blob[pos:pos+length],checksum));pos+=length
    frames=[]
    for _ in range(COUNT):
        if pos+38>len(blob):
            raise ValueError("short ref row")
        raw,checksum,nrefs=struct.unpack_from("<I32sH",blob,pos);pos+=38
        if raw!=MEMBER or nrefs!=16 or pos+nrefs*2>len(blob):
            raise ValueError("bad row")
        ids=struct.unpack_from("<"+"H"*nrefs,blob,pos);pos+=nrefs*2
        if any(k>=len(owners) for k in ids):
            raise ValueError("owner index")
        frames.append(([owners[k] for k in ids],checksum))
    if pos!=len(blob):
        raise ValueError("REF trailing")
    return frames

def one_a15(x):
    frame,want=x
    result=dec(frame,MEMBER)
    if sha(result)!=want:
        raise ValueError("member digest")
    return result

def one_ref(x):
    owners,want=x
    result=bytearray()
    for frame,owner_sha in owners:
        block=dec(frame,CHUNK)
        if sha(block)!=owner_sha:
            raise ValueError("owner SHA")
        result+=block
    if len(result)!=MEMBER or sha(result)!=want:
        raise ValueError("member SHA")
    return bytes(result)

def bench(frames_a,frames_b,source):
    raw=[]
    # Exact balanced ABBA, with A and B meaning the two fully charged
    # in-process inverse routines; no process launch, no cross-read cache.
    for target in TARGETS:
        truth=source[target*MEMBER:(target+1)*MEMBER]
        if one_a15(frames_a[target])!=truth or one_ref(frames_b[target])!=truth:
            raise AssertionError("wrong bytes")
        for repetition in range(12):
            order=("a15","ref","ref","a15") if repetition%2==0 else ("ref","a15","a15","ref")
            for arm in order:
                fn=one_a15 if arm=="a15" else one_ref
                frame=frames_a[target] if arm=="a15" else frames_b[target]
                t=time.perf_counter_ns()
                cpu=time.process_time_ns()
                actual=fn(frame)
                raw.append({"target":target,"repetition":repetition,"arm":arm,
                            "wall_ns":time.perf_counter_ns()-t,
                            "cpu_ns":time.process_time_ns()-cpu,
                            "sha256":sha(actual).hex()})
                if actual!=truth:
                    raise AssertionError("wrong sampled output")
    arms={}
    for arm in ("a15","ref"):
        observations=[x for x in raw if x["arm"]==arm]
        arms[arm]={"count":len(observations),
                   "wall_median_ns":statistics.median(x["wall_ns"] for x in observations),
                   "cpu_median_ns":statistics.median(x["cpu_ns"] for x in observations)}
    return raw,arms

def main(root):
    source_receipt=json.loads((root/"result.json").read_text())
    rows=[]
    for parent in source_receipt["cases"]:
        sub=root/parent["label"]
        raw=(sub/"source.bin").read_bytes()
        if len(raw)!=COUNT*MEMBER or sha(raw).hex()!=parent["source_sha256"]:
            raise ValueError("source misbound")
        encoded_a=(sub/"a15.bin").read_bytes()
        encoded_b=(sub/"chunkref.bin").read_bytes()
        if sha(encoded_a).hex()!=parent["a15_sha256"] or sha(encoded_b).hex()!=parent["chunkref_sha256"]:
            raise ValueError("encoded misbound")
        frames_a=a15_frames(encoded_a)
        frames_b=ref_frames(encoded_b)
        sampled,medians=bench(frames_a,frames_b,raw)
        ratio_wall=medians["ref"]["wall_median_ns"]/medians["a15"]["wall_median_ns"]
        ratio_cpu=medians["ref"]["cpu_median_ns"]/medians["a15"]["cpu_median_ns"]
        rows.append({"label":parent["label"],"source_sha256":parent["source_sha256"],
                     "a15_sha256":parent["a15_sha256"],"ref_sha256":parent["chunkref_sha256"],
                     "arms":medians,"ref_over_a15_wall":ratio_wall,
                     "ref_over_a15_cpu":ratio_cpu,"raw":sampled})
        print(f'{parent["label"]} wall ref/a15={ratio_wall:.3f} CPU={ratio_cpu:.3f}',flush=True)
    prediction=all(x["ref_over_a15_wall"]>=1.5 and x["ref_over_a15_cpu"]>=1.5 for x in rows)
    result={"schema":"a15-o1b-inprocess-inversion-v1",
            "source_receipt_sha256":sha((root/"result.json").read_bytes()).hex(),
            "source_court":"A15-O1 original six-case byte oracle",
            "platform":"local system libzstd via ctypes",
            "claim_level":"scientific_inprocess_component_only",
            "prediction_met":prediction,"cases":rows,
            "limitations":["No installed CMPCT Reader or per-member index/cold open cost",
                           "No process startup; libzstd decompression and ctypes/Python loops included",
                           "No cross-query decoded cache, which requires source lifetime proof",
                           "Full RSS, native zero-copy, selective physical bytes, real I/O unmeasured"]}
    (root/"inprocess.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"cases":len(rows),"prediction_met":prediction,
                      "raw_observations":sum(len(x["raw"]) for x in rows)}))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True)
    main(p.parse_args().root)
