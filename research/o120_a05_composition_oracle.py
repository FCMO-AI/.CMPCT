#!/usr/bin/env python3
"""O120: frozen A05 reversible-program oracle; NOT an archive/product benchmark."""
import hashlib, itertools, json, random, shutil, struct, subprocess, sys, time
from pathlib import Path

WIDTH=(2,4,8,16)
LAG=(1,2,4,8,16)
OPS=tuple([("S",w) for w in WIDTH]+[("D",s) for s in LAG]+[("X",s) for s in LAG])
TAG={"S":1,"D":2,"X":3}
INV={v:k for k,v in TAG.items()}
FIXED=45

def forward(data, op):
    t,n=op
    if t=="S":
        assert len(data)%n==0
        return b"".join(data[k::n] for k in range(n))
    if t=="D":
        return bytes(x if i<n else (x-data[i-n])&255 for i,x in enumerate(data))
    return bytes(x if i<n else x^data[i-n] for i,x in enumerate(data))

def backward(data, op):
    t,n=op
    if t=="S":
        assert len(data)%n==0
        k=len(data)//n
        out=bytearray(len(data))
        for j in range(n): out[j::n]=data[j*k:(j+1)*k]
        return bytes(out)
    out=bytearray(data)
    for i in range(n,len(out)):
        out[i]=(out[i]+out[i-n])&255 if t=="D" else out[i]^out[i-n]
    return bytes(out)

def zstd(data, decompress=False):
    cmd=["zstd","-d","-q","-c"] if decompress else ["zstd","-19","-q","-c"]
    return subprocess.run(cmd,input=data,capture_output=True,check=True).stdout

def pack(data, program):
    work=data
    for op in program: work=forward(work,op)
    prefix=b"O120"+struct.pack("<Q",len(data))+hashlib.sha256(data).digest()+bytes([len(program)])
    return prefix+b"".join(bytes([TAG[t],n]) for t,n in program)+zstd(work)

def unpack(blob):
    assert blob[:4]==b"O120" and len(blob)>=FIXED
    n=struct.unpack("<Q",blob[4:12])[0]
    digest=blob[12:44]
    count=blob[44]
    assert count<=2 and len(blob)>=FIXED+2*count
    p=[]
    for i in range(count):
        j=FIXED+2*i
        op=(INV[blob[j]],blob[j+1])
        assert op in OPS
        p.append(op)
    data=zstd(blob[FIXED+2*count:],True)
    for op in reversed(p): data=backward(data,op)
    assert len(data)==n and hashlib.sha256(data).digest()==digest
    return data

def cohorts():
    a=random.Random(12001); pos=[130,19001,45013,61003]; out=bytearray()
    for i in range(4096):
        for j in range(4):
            pos[j]=(pos[j]+(j+1)*3+a.choice((-1,0,1)))&65535
            out+=struct.pack("<H",pos[j])
    A=bytes(out)
    b=random.Random(12002); pos=[0x12345678,0x49382517,0x88abcdef,0xeeee1101];out=bytearray()
    for i in range(3072):
        for j in range(4):
            pos[j]=(pos[j]+(j+2)*17+(i+j)%7+b.randrange(3))&0xffffffff
            out+=struct.pack("<I",pos[j])
    B=bytes(out)
    c=random.Random(12003);out=bytearray();seq=22003
    for i in range(4096):
        seq+=c.randrange(1,4)
        flags=c.randrange(65536) if i%29==0 else (i//64)%4
        out+=struct.pack("<IHH",seq,(i//16)%256,flags)
    C=bytes(out)
    d=random.Random(12004)
    D="".join("2026-10-25T14:%02d:%02dZ service=%s status=%d value=%d\n"%
          (i%60,(i*3)%60,d.choice(("web","api","worker","db")),
           d.choice((200,200,200,201,404,503)),(i*7+d.randrange(11))%10000)
          for i in range(900)).encode()
    e=random.Random(12005)
    E=bytes(e.getrandbits(8) for _ in range(32768))
    return {"A_interleaved_16bit":A,"B_heldout_32bit":B,"C_sparse_shocks":C,
            "D_utf8_logs":D,"E_random":E}

def admissible(n):
    opts=[x for x in OPS if x[0]!="S" or n%x[1]==0]
    yield ()
    for x in opts: yield (x,)
    for x in itertools.product(opts,repeat=2): yield x

def selftest():
    r=random.Random(8801)
    for n in (0,1,2,3,4,8,16,31,32,129,512,1024):
        x=bytes(r.getrandbits(8) for _ in range(n))
        for op in OPS:
            if op[0]!="S" or n%op[1]==0: assert backward(forward(x,op),op)==x
    raw=bytes(range(128))
    for p in ((),(("S",4),),(("D",4),("S",4)),(("S",8),("X",1))):
        assert unpack(pack(raw,p))==raw

def evaluate(name,original):
    best={0:None,1:None,2:None}; n=0;t=time.perf_counter()
    for p in admissible(len(original)):
        x=original
        for op in p: x=forward(x,op)
        for op in reversed(p): x=backward(x,op)
        assert x==original, (name,p)
        container=pack(original,p)
        cand=(len(container),tuple(p),container)
        depth=len(p)
        if best[depth] is None or cand[:2]<best[depth][:2]: best[depth]=cand
        n+=1
    elapsed=time.perf_counter()-t
    for v in best.values(): assert unpack(v[2])==original
    incumbent=min((best[0],best[1]),key=lambda x:x[:2])
    new=best[2]
    delta=incumbent[0]-new[0]
    return dict(name=name,source_bytes=len(original),
        source_sha256=hashlib.sha256(original).hexdigest(),
        candidate_count=n,search_seconds=round(elapsed,6),
        depth_best={str(d):dict(charged_bytes=v[0],program=[list(o) for o in v[1]],
                payload_bytes=v[0]-FIXED-2*len(v[1])) for d,v in best.items()},
        best_depth_le1_bytes=incumbent[0],best_depth2_bytes=new[0],
        two_stage_savings_bytes=delta,two_stage_savings_pct=round(100*delta/incumbent[0],6),
        material_two_stage_win=delta>=64 and delta/incumbent[0]>=.01)

def main():
    if shutil.which("zstd") is None: raise SystemExit("requires actual zstd binary")
    selftest()
    if "--selftest" in sys.argv:
        print("SELFTEST PASS");return
    cases=[evaluate(k,v) for k,v in cohorts().items()]
    a,b=(cases[0]["material_two_stage_win"],cases[1]["material_two_stage_win"])
    decision="BOUNDED_HEADROOM_SEED" if a and b else (
        "GRAMMAR_RETIRED_FOR_STORAGE" if not (a or b) else "REGIME_LIMITED_UNPROMOTED")
    report=dict(schema="o120-a05-composition-v1",source_ref="agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b",
                codec="zstd -19 -q -c",fixed_header_bytes=FIXED,op_descriptor_bytes=2,
                product_credit=False,decision=decision,total_programs=sum(x["candidate_count"] for x in cases),
                cases=cases)
    text=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if "--output" in sys.argv:
        i=sys.argv.index("--output")
        Path(sys.argv[i+1]).write_text(text)
    print(text)

if __name__=="__main__": main()
