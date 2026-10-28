#!/usr/bin/env python3
"""A15-O0: bounded exact reconstruction IR oracle; research-only, NOT CMPCT format."""
from __future__ import annotations
import argparse, ctypes, ctypes.util, hashlib, json, random, struct, time
from pathlib import Path

MAG=b"A15O"; HD=struct.Struct("<4sBHH"); REC=struct.Struct("<HI32sI")
OP={"stripe2":(1,2),"stripe4":(1,4),"delta":(2,0),"xor":(3,0),"zero":(4,0)}
PIPES=((),("stripe2",),("stripe4",),("delta",),("xor",),("zero",),
       ("stripe2","delta"),("stripe4","delta"),("stripe2","xor"),
       ("stripe4","xor"),("delta","stripe2"))
lib=ctypes.CDLL(ctypes.util.find_library("zstd"))
lib.ZSTD_compressBound.argtypes=[ctypes.c_size_t];lib.ZSTD_compressBound.restype=ctypes.c_size_t
lib.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];lib.ZSTD_compress.restype=ctypes.c_size_t
lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];lib.ZSTD_decompress.restype=ctypes.c_size_t
lib.ZSTD_getFrameContentSize.argtypes=[ctypes.c_void_p,ctypes.c_size_t];lib.ZSTD_getFrameContentSize.restype=ctypes.c_ulonglong
lib.ZSTD_isError.argtypes=[ctypes.c_size_t];lib.ZSTD_isError.restype=ctypes.c_uint
def pack(data):
    cap=lib.ZSTD_compressBound(len(data));dest=ctypes.create_string_buffer(cap)
    n=lib.ZSTD_compress(dest,cap,data,len(data),19)
    if lib.ZSTD_isError(n):raise ValueError("compress error")
    return dest.raw[:n]
def unpack(data):
    size=lib.ZSTD_getFrameContentSize(data,len(data))
    if size>1<<22:raise ValueError("unbounded zstd frame")
    out=ctypes.create_string_buffer(size);n=lib.ZSTD_decompress(out,size,data,len(data))
    if lib.ZSTD_isError(n) or n!=size:raise ValueError("zstd decode failure")
    return out.raw[:n]
def forward(b,op):
    if op.startswith("stripe"):
        w=OP[op][1]
        if len(b)%w:raise ValueError("unaligned")
        return b"".join(b[k::w] for k in range(w))
    if op=="delta":return bytes((b[0],))+bytes((b[i]-b[i-1])&255 for i in range(1,len(b))) if b else b
    if op=="xor":return bytes((b[0],))+bytes(b[i]^b[i-1] for i in range(1,len(b))) if b else b
    if op=="zero":
        out=bytearray();i=0
        while i<len(b):
            z=0
            while i<len(b) and b[i]==0 and z<65535:z+=1;i+=1
            start=i
            while i<len(b) and b[i]!=0 and i-start<65535:i+=1
            out+=struct.pack("<HH",z,i-start)+b[start:i]
        return bytes(out)
    raise ValueError("operator")
def reverse(b,op,size):
    if op.startswith("stripe"):
        w=OP[op][1]
        if len(b)!=size or size%w:raise ValueError("stripe bounds")
        n=size//w;out=bytearray(size)
        for k in range(w):out[k::w]=b[k*n:(k+1)*n]
        return bytes(out)
    if op in ("delta","xor"):
        if len(b)!=size:raise ValueError("predictor bounds")
        out=bytearray(b)
        for i in range(1,len(out)):out[i]=((out[i-1]+b[i])&255) if op=="delta" else (out[i-1]^b[i])
        return bytes(out)
    if op=="zero":
        out=bytearray();i=0
        while i<len(b):
            if i+4>len(b):raise ValueError("truncated zero")
            z,n=struct.unpack_from("<HH",b,i);i+=4
            if z+n==0 or i+n>len(b) or len(out)+z+n>size:raise ValueError("zero overflow")
            out+=bytes(z)+b[i:i+n];i+=n
        if len(out)!=size:raise ValueError("zero length")
        return bytes(out)
    raise ValueError("illegal operator")
def code(pipe,kind):
    if len(pipe)>2 or ("zero" in pipe and len(pipe)>1):raise ValueError("bad pipeline")
    return bytes((len(pipe),))+b"".join(bytes(OP[x])+ (b"\1" if kind else b"") for x in pipe)
def decode_code(b,kind):
    if not b or b[0]>2 or len(b)!=1+b[0]*(3 if kind else 2):raise ValueError("code shape")
    out=[]
    for j in range(b[0]):
        k=1+j*(3 if kind else 2)
        if kind and b[k+2]!=1:raise ValueError("type tag")
        op=next((name for name,pair in OP.items() if pair==tuple(b[k:k+2])),None)
        if op is None:raise ValueError("illegal code")
        out.append(op)
    if "zero" in out and len(out)!=1:raise ValueError("bad zero composition")
    return tuple(out)
def transform(b,pipe):
    for op in pipe:b=forward(b,op)
    return b
def reconstruct(b,pipe,size):
    for op in reversed(pipe):b=reverse(b,op,size if op=="zero" else len(b))
    if len(b)!=size:raise ValueError("size")
    return b
def fixture(family,seed,n):
    r=random.Random(seed);out=bytearray()
    if family=="lane16":
        for j in range(n//2):out.extend((r.randrange(256),(j//512+seed)%4))
    elif family=="lane32":
        for j in range(n//4):out+=struct.pack("<I",(j*65537+seed*4099+r.randrange(8))&0xffffffff)
    elif family=="diff":
        v=r.randrange(256)
        for j in range(n):v=(v+r.choice((-1,0,0,1)))&255;out.append(v)
    elif family=="zeros":
        while len(out)<n:
            span=r.randrange(20,240)
            out+=bytes(span) if r.random()<.65 else r.randbytes(span)
    else:out+=r.randbytes(n)
    return bytes(out[:n])
def build(src,kind):
    choices=[]
    for b in src:
        candidates=[]
        for p in PIPES:
            try:payload=pack(transform(b,p));candidates.append((len(payload)+len(code(p,0)),p,payload))
            except ValueError:pass
        _,p,encoded=min(candidates,key=lambda x:(x[0],x[1]))
        choices.append((p,encoded))
    names=sorted({p for p,_ in choices});ids={p:i for i,p in enumerate(names)}
    out=bytearray(HD.pack(MAG,kind,len(src),len(names)))
    for p in names:raw=code(p,kind);out+=struct.pack("<H",len(raw))+raw
    for b,(p,enc) in zip(src,choices):out+=REC.pack(ids[p],len(b),hashlib.sha256(b).digest(),len(enc))+enc
    return bytes(out),[("+".join(p) or "direct") for p,_ in choices]
def read(blob):
    if len(blob)<HD.size:raise ValueError("header truncated")
    magic,kind,count,program_count=HD.unpack_from(blob)
    if magic!=MAG or kind not in (0,1) or count>64 or program_count>64:raise ValueError("bad header")
    pos=HD.size;programs=[]
    for _ in range(program_count):
        if pos+2>len(blob):raise ValueError("program truncated")
        n=struct.unpack_from("<H",blob,pos)[0];pos+=2
        if n>16 or pos+n>len(blob):raise ValueError("bad program")
        programs.append(decode_code(blob[pos:pos+n],kind));pos+=n
    result=[]
    for _ in range(count):
        if pos+REC.size>len(blob):raise ValueError("member truncated")
        pid,n,sha,size=REC.unpack_from(blob,pos);pos+=REC.size
        if pid>=len(programs) or n>1<<22 or size>1<<22 or pos+size>len(blob):raise ValueError("member bounds")
        body=reconstruct(unpack(blob[pos:pos+size]),programs[pid],n);pos+=size
        if hashlib.sha256(body).digest()!=sha:raise ValueError("SHA mismatch")
        result.append(body)
    if pos!=len(blob):raise ValueError("trailing bytes")
    return result
def measure(blob):
    samples=[]
    for _ in range(7):
        t=time.perf_counter_ns();cpu=time.process_time_ns();read(blob)
        samples.append((time.perf_counter_ns()-t,time.process_time_ns()-cpu))
    return {"wall_median_ns":sorted(x[0] for x in samples)[3],
            "cpu_median_ns":sorted(x[1] for x in samples)[3],"raw":samples}
def hostile(blob):
    checks={}
    tests={"bad_magic":(0,127),"bad_kind":(4,7),"bad_program_count":(7,255),"truncated":None}
    for label,alter in tests.items():
        b=bytearray(blob)
        if alter is None:b=b[:-1]
        else:b[alter[0]]=alter[1]
        try:read(bytes(b));checks[label]=False
        except ValueError:checks[label]=True
    return checks
def run(out):
    out.mkdir(parents=True,exist_ok=True);cases=[];bad=[]
    for family in ("lane16","lane32","diff","zeros","opaque"):
        for count in (1,8,32):
            held=count==32;n=4096 if count>1 else 65536
            src=[fixture(family,2026102800+(100000 if held else 0)+i*7919+len(family),n) for i in range(count)]
            a,p=build(src,0);b,q=build(src,1)
            if p!=q or read(a)!=src or read(b)!=src:raise AssertionError("exact reconstruction")
            name=f"{family}_{count}_{'heldout' if held else 'seen'}"
            (out/(name+".source.bin")).write_bytes(b"".join(src))
            (out/(name+".bespoke.bin")).write_bytes(a);(out/(name+".ir.bin")).write_bytes(b)
            cases.append({"family":family,"members":count,"heldout":held,
                 "source_sha256":hashlib.sha256(b"".join(src)).hexdigest(),"source_lengths":[len(x) for x in src],
                 "bespoke_sha256":hashlib.sha256(a).hexdigest(),"ir_sha256":hashlib.sha256(b).hexdigest(),
                 "bespoke_bytes":len(a),"ir_bytes":len(b),"chosen_programs":p,
                 "bespoke_timing":measure(a),"ir_timing":measure(b)})
            if count==1:bad.append({"case":name,"tested":hostile(b)})
    if not all(all(x["tested"].values()) for x in bad):raise AssertionError("hostile control")
    result={"schema":"a15-o0-unified-reconstruction-v1","source_base":"80c358f8824ec1b20d349c92ed94c898090969b0",
            "claim_level":"scientific_oracle_only","cases":cases,"adversarial":bad,"passed":True}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"cases":len(cases),"adversarial":sum(len(x["tested"]) for x in bad),"passed":True}))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True)
    run(ap.parse_args().out)
