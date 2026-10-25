#!/usr/bin/env python3
"""O129 A12 charged cross-wrapper RFC1951 root oracle; NOT a CMPCT product test."""
import hashlib, json, random, struct, subprocess, zlib
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
SEEDS=(41,101,2026,4096)
FAMILIES=('telemetry','records','entropy','mixed','unrelated','multi_level')
COUNTS=(1,2,4,8)
CAP=1_000_000
@lru_cache(maxsize=512)
def zstd(b):
    return subprocess.run(['zstd','-19','-q','-c'],input=b,stdout=subprocess.PIPE,check=True).stdout
def rawzip(b,level=9):
    c=zlib.compressobj(level,zlib.DEFLATED,-15)
    return c.compress(b)+c.flush()
def corpus(f,s,i):
    r=random.Random(s+111*(i if f=='unrelated' else 0))
    if f=='entropy': return r.randbytes(160000)
    if f=='telemetry': return b''.join(f'{k:06d},rack={k%17},pressure={r.randrange(40,100):03d},ok\n'.encode() for k in range(3000))
    if f=='records': return b''.join(f'{{"id":{k%31},"region":{k%7},"latency":{r.randrange(1000)},"valid":true}}\n'.encode() for k in range(2400))
    if f=='mixed': return b''.join(b'@SOURCE='+str(k%29).encode()+b'|'+r.randbytes(18)+b'|COMMIT|'+str(k).encode()+b'\n' for k in range(3200))
    if f=='unrelated': return b''.join(f'{k:06d},{r.randrange(10000000):07d}\n'.encode() for k in range(8000))
    return b''.join(b'blob:'+r.randbytes(24)+b';'*((k%5)+2)+b'\n' for k in range(2500))
def frame(b,kind,s,j,level):
    d=rawzip(b,level)
    if kind=='gzip':
        head=b'\x1f\x8b\x08\x08'+struct.pack('<I',100000+s+j)+b'\x02\xff'+f'host-{s}-{j}.log'.encode()+b'\0'
        tail=struct.pack('<II',zlib.crc32(b),len(b)&0xffffffff)
    elif kind=='zlib':
        z=zlib.compress(b,level); assert z[2:-4]==d
        head,tail=z[:2],z[-4:]
    else: head=tail=b''
    return head+d+tail
def parse(v):
    if len(v)>CAP: raise ValueError('bounded input')
    if len(v)>=18 and v[:3]==b'\x1f\x8b\x08':
        flags=v[3]
        if flags&0xe0: raise ValueError('reserved gzip flags')
        p=10
        if flags&4: p+=2+int.from_bytes(v[p:p+2],'little')
        if flags&8: p=v.index(0,p)+1
        if flags&16: p=v.index(0,p)+1
        if flags&2: p+=2
        if p>=len(v)-8: raise ValueError('short gzip')
        pre,root,post,codec=v[:p],v[p:-8],v[-8:],31
    elif len(v)>=6 and v[0]&15==8 and (v[0]*256+v[1])%31==0:
        if v[1]&32: raise ValueError('zlib dictionary')
        pre,root,post,codec=v[:2],v[2:-4],v[-4:],15
    else: pre,root,post,codec=b'',v,b'',-15
    for source,w in ((v,codec),(root,-15)):
        d=zlib.decompressobj(w)
        clear=d.decompress(source,CAP+1)+d.flush()
        if len(clear)>CAP or not d.eof or d.unused_data or d.unconsumed_tail:
            raise ValueError('invalid or trailing compressed stream')
        if w==codec: plain=clear
        else: assert clear==plain
    assert pre+root+post==v
    return pre,root,post,plain
def run_one(job):
    f,s,n=job
    entries=[]
    for j in range(n):
        b=corpus(f,s,j); level=(1 if j%2 else 9) if f=='multi_level' else 9
        kind=('gzip','zlib','raw')[j%3]; v=frame(b,kind,s,j,level)
        pre,root,post,plain=parse(v)
        assert plain==b and pre+root+post==v
        entries.append((f'dir/file_{j:03d}.{kind}',v,pre,root,post))
    roots=list(dict.fromkeys(e[3] for e in entries))
    common=sum(2+len(name.encode())+8+8+32 for name,*_ in entries)
    own=sum(min(len(x),len(zstd(x))) for x in roots)
    proposal=48+common+40*len(roots)+own+sum(len(pre)+len(post)+12 for _,_,pre,_,post in entries)
    solid=48+common+len(zstd(b''.join(e[1] for e in entries)))
    indep=48+common+sum(min(len(e[1]),len(zstd(e[1]))) for e in entries)
    amp=max((len(root)+len(pre)+len(post)+12)/len(v) for _,v,pre,root,post in entries)
    return dict(family=f,seed=s,views=n,roots=len(roots),proposal=proposal,solid=solid,
                independent=indep,strongest=min(solid,indep),delta=proposal-min(solid,indep),
                read_amp=round(amp,5),sha256=hashlib.sha256(b''.join(e[1] for e in entries)).hexdigest())
def main():
    sample=frame(b'ABCD'*128,'gzip',41,0,9)
    hostile=[b'not a deflate stream',sample+sample,sample[:-1]+bytes([sample[-1]^1]),sample[:3]+bytes([sample[3]|32])+sample[4:],rawzip(b'ABCD'*128)+b'extra']
    for b in hostile:
        try: parse(b)
        except (ValueError,zlib.error,IndexError): continue
        raise AssertionError('hostile input accepted')
    jobs=[(f,s,n) for f in FAMILIES for s in SEEDS for n in COUNTS]
    with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(run_one,jobs))
    positives=[r for r in rows if r['family'] not in ('unrelated','multi_level') and r['views']>=2]
    print(json.dumps(dict(schema='cmpct-o129-a12-framed-view-oracle-v1',product_credit=False,
          material_wins=sum(r['proposal']<r['strongest']*.99 for r in positives),
          positive_wins=sum(r['delta']<0 for r in positives),negative_cases=len(rows)-len(positives),
          adversarial_rejections=len(hostile),max_amplification=max(r['read_amp'] for r in rows),
          physical_charge='index:2+utf8(path)+8+8+32/member,global:48,root:40,view:12',
          zstd=subprocess.run(['zstd','--version'],capture_output=True,text=True).stdout.strip(),
          cases=rows),sort_keys=True,indent=2))
if __name__=='__main__': main()
