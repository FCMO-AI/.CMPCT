#!/usr/bin/env python3
"""Independent A15-O0 referee; never imports the candidate encoder/decoder."""
from __future__ import annotations
import argparse,hashlib,json,statistics,struct,subprocess
from pathlib import Path
H=struct.Struct("<4sBHH");R=struct.Struct("<HI32sI")
NAMES={(1,2):"stripe2",(1,4):"stripe4",(2,0):"delta",(3,0):"xor",(4,0):"zero"}
FAMILIES={"lane16","lane32","diff","zeros","opaque"}
def digest(b):return hashlib.sha256(b).hexdigest()
def inflate(b):
    p=subprocess.run(["zstd","--decompress","--stdout","--quiet"],input=b,capture_output=True)
    if p.returncode:raise ValueError("independent Zstd frame failure")
    return p.stdout
def undo(buf,op,expected):
    if op.startswith("stripe"):
        w=2 if op=="stripe2" else 4
        if len(buf)!=expected or len(buf)%w:raise ValueError("stripe geometry")
        out=bytearray(len(buf));n=len(buf)//w
        for i in range(w):out[i::w]=buf[i*n:(i+1)*n]
        return bytes(out)
    if op=="delta":
        if len(buf)!=expected:raise ValueError("delta length")
        out=bytearray(buf)
        for i in range(1,len(out)):out[i]=(out[i-1]+buf[i])&255
        return bytes(out)
    if op=="xor":
        if len(buf)!=expected:raise ValueError("xor length")
        out=bytearray(buf)
        for i in range(1,len(out)):out[i]=out[i-1]^buf[i]
        return bytes(out)
    if op=="zero":
        out=bytearray();p=0
        while p<len(buf):
            if p+4>len(buf):raise ValueError("zero truncated")
            z,l=struct.unpack_from("<HH",buf,p);p+=4
            if z+l==0 or p+l>len(buf) or len(out)+z+l>expected:raise ValueError("zero bounds")
            out+=bytes(z)+buf[p:p+l];p+=l
        if len(out)!=expected:raise ValueError("zero output size")
        return bytes(out)
    raise ValueError("unknown operation")
def independent_decode(archive):
    if len(archive)<H.size:raise ValueError("header missing")
    magic,kind,count,nprogram=H.unpack_from(archive)
    if magic!=b"A15O" or kind not in (0,1) or count>64 or nprogram>64:raise ValueError("header")
    pos=H.size;programs=[]
    for _ in range(nprogram):
        if pos+2>len(archive):raise ValueError("truncated program length")
        clen=struct.unpack_from("<H",archive,pos)[0];pos+=2
        if clen<1 or clen>16 or pos+clen>len(archive):raise ValueError("program bytes")
        code=archive[pos:pos+clen];pos+=clen
        depth=code[0]
        if depth>2 or len(code)!=1+depth*(3 if kind else 2):raise ValueError("depth")
        pipe=[]
        for j in range(depth):
            a=1+j*(3 if kind else 2)
            if kind and code[a+2]!=1:raise ValueError("type tag")
            op=NAMES.get((code[a],code[a+1]))
            if op is None:raise ValueError("unknown op")
            pipe.append(op)
        if "zero" in pipe and len(pipe)!=1:raise ValueError("zero composition")
        programs.append(tuple(pipe))
    out=[]
    for _ in range(count):
        if pos+R.size>len(archive):raise ValueError("member descriptor")
        pid,rawlen,sha,compressed_len=R.unpack_from(archive,pos);pos+=R.size
        if pid>=len(programs) or rawlen>1<<22 or compressed_len>1<<22 or pos+compressed_len>len(archive):raise ValueError("member framing")
        data=inflate(archive[pos:pos+compressed_len]);pos+=compressed_len
        for op in reversed(programs[pid]):data=undo(data,op,rawlen if op=="zero" else len(data))
        if len(data)!=rawlen or hashlib.sha256(data).digest()!=sha:raise ValueError("member integrity")
        out.append(data)
    if pos!=len(archive):raise ValueError("trailing bytes")
    return out
def verdict(rows):
    by_fam={}
    for x in rows:
        if not x["heldout"]:continue
        wall=x["ir_timing"]["wall_median_ns"]/max(1,x["bespoke_timing"]["wall_median_ns"])
        cpu=x["ir_timing"]["cpu_median_ns"]/max(1,x["bespoke_timing"]["cpu_median_ns"])
        overhead=x["ir_bytes"]-x["bespoke_bytes"]
        by_fam[x["family"]]={"overhead":overhead,"wall_ratio":wall,"cpu_ratio":cpu,
           "pass":overhead<=128 and overhead/max(1,x["bespoke_bytes"])<=0.02 and wall<=1.15 and cpu<=1.15}
    wins=sum(x["pass"] for x in by_fam.values())
    return {"per_family":by_fam,"passing_families":wins,"decision":"FEASIBLE_RESEARCH_SEED" if wins>=4 else "IR_COST_OR_CORRECTNESS_NEGATIVE"}
def validate_receipt(receipt,directory):
    if receipt.get("schema")!="a15-o0-unified-reconstruction-v1" or receipt.get("passed") is not True:raise ValueError("schema")
    cases=receipt["cases"]
    if len(cases)!=15 or set(x["family"] for x in cases)!=FAMILIES:raise ValueError("case family")
    expected_names={(f,n) for f in FAMILIES for n in (1,8,32)}
    if {(x["family"],x["members"]) for x in cases}!=expected_names:raise ValueError("case cells")
    for x in cases:
        ident=f'{x["family"]}_{x["members"]}_{"heldout" if x["members"]==32 else "seen"}'
        if bool(x["heldout"])!=(x["members"]==32):raise ValueError("heldout")
        src=(directory/(ident+".source.bin")).read_bytes()
        if digest(src)!=x["source_sha256"] or sum(x["source_lengths"])!=len(src):raise ValueError("source ownership")
        members=[];p=0
        for n in x["source_lengths"]:members.append(src[p:p+n]);p+=n
        if len(members)!=x["members"]:raise ValueError("member count")
        for kind in ("bespoke","ir"):
            archive=(directory/(ident+"."+kind+".bin")).read_bytes()
            if digest(archive)!=x[kind+"_sha256"] or len(archive)!=x[kind+"_bytes"]:raise ValueError("artifact custody")
            if independent_decode(archive)!=members:raise ValueError("not exact")
            samples=x[kind+"_timing"]["raw"]
            if len(samples)!=7 or any(len(t)!=2 or min(t)<=0 for t in samples):raise ValueError("timing provenance")
            if statistics.median(v[0] for v in samples)!=x[kind+"_timing"]["wall_median_ns"]:raise ValueError("wall median")
            if statistics.median(v[1] for v in samples)!=x[kind+"_timing"]["cpu_median_ns"]:raise ValueError("CPU median")
    adversarial=receipt["adversarial"]
    if len(adversarial)!=5 or any(len(a["tested"])!=12 or not all(a["tested"].values()) for a in adversarial):raise ValueError("hostile controls")
    return verdict(cases)
def main():
    a=argparse.ArgumentParser();a.add_argument("--dir",type=Path,required=True);args=a.parse_args()
    root=args.dir;receipt=json.loads((root/"result.json").read_text())
    result=validate_receipt(receipt,root)
    import copy
    mutated=[]
    def forge(k,fn):
        candidate=copy.deepcopy(receipt);fn(candidate)
        try:validate_receipt(candidate,root);mutated.append({"case":k,"rejected":False})
        except (ValueError,KeyError,TypeError,IndexError):mutated.append({"case":k,"rejected":True})
    forge("schema",lambda x:x.update(schema="bogus"))
    forge("result_status",lambda x:x.update(passed=False))
    forge("source_sha",lambda x:x["cases"][0].update(source_sha256="0"*64))
    forge("archive_sha",lambda x:x["cases"][0].update(ir_sha256="f"*64))
    forge("archive_bytes",lambda x:x["cases"][0].update(ir_bytes=3))
    forge("case_count",lambda x:x["cases"].pop())
    forge("duplicate_cell",lambda x:x["cases"][1].update(family=x["cases"][0]["family"],members=x["cases"][0]["members"]))
    forge("timing_wall",lambda x:x["cases"][0]["ir_timing"].update(wall_median_ns=1))
    forge("timing_cpu",lambda x:x["cases"][0]["ir_timing"].update(cpu_median_ns=1))
    forge("hostile",lambda x:x["adversarial"][0]["tested"].update(bad_magic=False))
    if not all(x["rejected"] for x in mutated):raise AssertionError(mutated)
    result.update(schema="a15-o0-independent-referee-v1",cases_checked=15,members_checked=205,mutations=mutated,passed=True)
    (root/"referee.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"passed":True,"cells":15,"forged_rejected":len(mutated),"decision":result["decision"],"passing_families":result["passing_families"]}))
if __name__=="__main__":main()
