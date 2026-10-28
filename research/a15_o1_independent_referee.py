#!/usr/bin/env python3
"""Independent A15-O1 referee: no imports from the research producer."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import struct
import subprocess
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def decode_frame(data):
    p = subprocess.run(["zstd","-q","-d","-c"], input=data,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode:
        raise ValueError("bad independent zstd frame")
    return p.stdout

def a15_read_all(data):
    if len(data)<9:
        raise ValueError("short A15")
    magic, kind, count, plans=struct.unpack_from("<4sBHH",data)
    if (magic,kind,count,plans)!=(b"A15O",1,32,1) or data[9:12]!=b"\x01\x00\x00":
        raise ValueError("A15 grammar unsupported")
    pos=12
    out=[]
    for _ in range(count):
        if pos+42>len(data):
            raise ValueError("bad A15 descriptor")
        plan,n,checksum,length=struct.unpack_from("<HI32sI",data,pos)
        pos+=42
        if plan or n!=65536 or length>1<<21 or pos+length>len(data):
            raise ValueError("bad A15 member bounds")
        member=decode_frame(data[pos:pos+length])
        if len(member)!=n or hashlib.sha256(member).digest()!=checksum:
            raise ValueError("bad A15 digest")
        out.append(member);pos+=length
    if pos!=len(data):
        raise ValueError("A15 trailing bytes")
    return out

def ref_read_all(data):
    if len(data)<12:
        raise ValueError("short REF")
    magic,count,owners,chunkbytes=struct.unpack_from("<4sHHI",data)
    if magic!=b"RFO1" or count!=32 or owners>512 or chunkbytes!=4096:
        raise ValueError("REF header")
    pos=12
    chunks=[]
    for _ in range(owners):
        if pos+36>len(data):
            raise ValueError("REF owner length")
        length=struct.unpack_from("<I",data,pos)[0]
        checksum=data[pos+4:pos+36]
        pos+=36
        if length>65536 or pos+length>len(data):
            raise ValueError("REF owner frame bounds")
        chunk=decode_frame(data[pos:pos+length])
        if len(chunk)!=chunkbytes or hashlib.sha256(chunk).digest()!=checksum:
            raise ValueError("REF owner digest")
        chunks.append(chunk)
        pos+=length
    members=[]
    for _ in range(count):
        if pos+38>len(data):
            raise ValueError("REF member length")
        n,checksum,refcount=struct.unpack_from("<I32sH",data,pos)
        pos+=38
        if n!=65536 or refcount!=16 or pos+refcount*2>len(data):
            raise ValueError("REF member bounds")
        refs=struct.unpack_from("<"+"H"*refcount,data,pos)
        if any(i>=owners for i in refs):
            raise ValueError("REF bad ref")
        pos+=2*refcount
        member=b"".join(chunks[i] for i in refs)
        if len(member)!=n or hashlib.sha256(member).digest()!=checksum:
            raise ValueError("REF member SHA")
        members.append(member)
    if pos!=len(data):
        raise ValueError("REF trailing bytes")
    return members,owners

def audit_case(root,row):
    case=root/row["label"]
    a=(case/"a15.bin").read_bytes()
    b=(case/"chunkref.bin").read_bytes()
    source=(case/"source.bin").read_bytes()
    if len(source)!=32*65536:
        raise ValueError("wrong source member length")
    if (sha(source),sha(a),sha(b))!=(
        row["source_sha256"],row["a15_sha256"],row["chunkref_sha256"]):
        raise ValueError("source or encoded identity")
    x=a15_read_all(a);y,owners=ref_read_all(b)
    if b"".join(x)!=source or x!=y:
        raise ValueError("different reconstructed bytes")
    if owners!=row["unique_owners"] or len(a)!=row["a15_bytes"] or len(b)!=row["chunkref_bytes"]:
        raise ValueError("recorded physical amounts")
    if abs(len(b)/len(a)-row["chunkref_to_a15"])>1e-12:
        raise ValueError("mismatched ratio")
    for arm,key in (("a15_bench","a15_sha256"),("chunkref_bench","chunkref_sha256")):
        samples=row[arm]["raw"]
        if len(samples)!=6 or sorted(z["wall_ns"] for z in samples)[3]!=row[arm]["wall_median_ns"]:
            raise ValueError("forged median")
        if any(z["target"] not in (0,17,31) or z["wall_ns"]<0 or z["parent_cpu_ns"]<0 or
               z["sha256"]!=sha(x[z["target"]]) for z in samples):
            raise ValueError("forged sample")
    if sorted(row["hostile"])!=sorted(("invalid_ref","owner_corrupted","member_sha",
                                   "wrong_raw_size","truncated_owner_frame","truncated","trailing")):
        raise ValueError("missing adversarial case")
    if not all(row["hostile"].values()):
        raise ValueError("adversarial miss")
    return len(x),owners

def evaluate(root,receipt):
    if receipt.get("schema")!="a15-o1-cross-owner-transfer-v1" or receipt.get("claim_level")!="scientific_oracle_only":
        raise ValueError("schema or claim drift")
    cases=receipt.get("cases")
    if not isinstance(cases,list) or len(cases)!=6:
        raise ValueError("missing cases")
    expected={(r,s) for r in ("identical","partial","distinct") for s in (20261028,20261029)}
    if {(r.get("regime"),r.get("seed")) for r in cases}!=expected:
        raise ValueError("unexpected samples")
    member_total=0
    for row in cases:
        if row["label"]!=f'{row["regime"]}_{row["seed"]}' or row["members"]!=32 or row["member_bytes"]!=65536 or row["chunk_bytes"]!=4096:
            raise ValueError("wrong case metadata")
        n,_=audit_case(root,row)
        member_total+=n
    verdict=all((r["chunkref_to_a15"]<=.70 if r["regime"]!="distinct"
                 else r["chunkref_to_a15"]>=.95) for r in cases)
    if receipt.get("prediction_met") is not verdict:
        raise ValueError("prediction drift")
    return member_total,verdict

def main(root):
    receipt=json.loads((root/"result.json").read_text())
    n,verdict=evaluate(root,receipt)
    forged=0
    def reject(changer):
        nonlocal forged
        r=copy.deepcopy(receipt)
        changer(r)
        try:evaluate(root,r)
        except (ValueError,KeyError,TypeError,IndexError,AssertionError):
            forged+=1
            return
        raise AssertionError("forged receipt accepted")
    reject(lambda r:r["cases"][0].update({"source_sha256":"0"*64}))
    reject(lambda r:r["cases"][0].update({"a15_bytes":0}))
    reject(lambda r:r["cases"][0].update({"unique_owners":999}))
    reject(lambda r:r["cases"][0]["a15_bench"].update({"wall_median_ns":1}))
    reject(lambda r:r["cases"][0]["hostile"].update({"invalid_ref":False}))
    reject(lambda r:r.update({"prediction_met":not verdict}))
    report={"schema":"a15-o1-independent-referee-v1","member_decodes":n,
            "cases":len(receipt["cases"]),"forged_rejected":forged,
            "prediction_met":verdict,"source_result_sha256":sha((root/"result.json").read_bytes()),
            "verdict":"PASS_INDEPENDENT_BYTE_EXACT"}
    (root/"referee.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    main(ap.parse_args().root)
