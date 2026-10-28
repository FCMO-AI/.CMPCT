#!/usr/bin/env python3
"""A16-O0: preregistered sharing-class segment coalescing falsifier.

Standalone scientific envelopes, not CMPCT r24 archives or product code.
"""
from __future__ import annotations
import ctypes, ctypes.util, hashlib, json, random, statistics, struct, subprocess, time
from pathlib import Path

BLOCK=4096; N=32; CHUNKS=16; SEEDS=(20261028,20261029)
REGIMES=('identical','prefix12','suffix12','alternating8','distinct')
H=struct.Struct('<4sHHI'); RAW=struct.Struct('<I32sI'); FIX=struct.Struct('<I32s')
VAR=struct.Struct('<II32s'); ROW=struct.Struct('<I32sH')
Z=ctypes.CDLL(ctypes.util.find_library('zstd'))
Z.ZSTD_compressBound.argtypes=[ctypes.c_size_t]; Z.ZSTD_compressBound.restype=ctypes.c_size_t
Z.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
Z.ZSTD_compress.restype=ctypes.c_size_t
Z.ZSTD_isError.argtypes=[ctypes.c_size_t]; Z.ZSTD_isError.restype=ctypes.c_uint

def sha(data): return hashlib.sha256(data).digest()
def zstd(data):
    out=ctypes.create_string_buffer(Z.ZSTD_compressBound(len(data)))
    size=Z.ZSTD_compress(out,len(out),data,len(data),19)
    if Z.ZSTD_isError(size): raise ValueError('zstd encode failed')
    return out.raw[:size]
def source(seed,regime):
    rng=random.Random(seed);common=[rng.randbytes(BLOCK) for _ in range(CHUNKS)];all=[]
    for _ in range(N):
        if regime=='identical': parts=common
        elif regime=='prefix12':parts=common[:12]+[rng.randbytes(BLOCK) for _ in range(4)]
        elif regime=='suffix12':parts=[rng.randbytes(BLOCK) for _ in range(4)]+common[4:]
        elif regime=='alternating8':parts=[common[i] if i%2==0 else rng.randbytes(BLOCK) for i in range(CHUNKS)]
        else:parts=[rng.randbytes(BLOCK) for _ in range(CHUNKS)]
        all.append(b''.join(parts))
    return all

def owners(rows,grouped):
    split=[[r[i:i+BLOCK] for i in range(0,len(r),BLOCK)] for r in rows]
    memberships={}
    for member,blocks in enumerate(split):
        for part in blocks: memberships.setdefault(sha(part),set()).add(member)
    out=[]
    for blocks in split:
        if not grouped: out.append(blocks); continue
        row=[];acc=bytearray();old=None
        for part in blocks:
            shared=len(memberships[sha(part)])>1
            if old is not None and shared!=old:row.append(bytes(acc));acc.clear()
            acc+=part;old=shared
        row.append(bytes(acc));out.append(row)
    return out

def encode(rows,arm):
    if arm=='direct':
        out=bytearray(H.pack(b'D116',N,0,BLOCK))
        for raw in rows:
            frame=zstd(raw);out+=RAW.pack(len(raw),sha(raw),len(frame))+frame
        return bytes(out),[1]*N,0
    grouped=arm=='segref'
    groups=owners(rows,grouped);uniques=[];refs=[];lookup={}
    for row in groups:
        indices=[]
        for data in row:
            key=sha(data);hit=next((idx for idx in lookup.get(key,()) if uniques[idx]==data),None)
            if hit is None:
                hit=len(uniques);lookup.setdefault(key,[]).append(hit);uniques.append(data)
            indices.append(hit)
        refs.append(indices)
    out=bytearray(H.pack(b'SR16' if grouped else b'CR16',N,len(uniques),BLOCK))
    for data in uniques:
        frame=zstd(data)
        # The stronger fixed-size control does NOT pay a redundant raw-length word.
        out+=(VAR.pack(len(data),len(frame),sha(data)) if grouped
              else FIX.pack(len(frame),sha(data)))+frame
    for raw,indices in zip(rows,refs):
        out+=ROW.pack(len(raw),sha(raw),len(indices))
        out+=struct.pack('<'+'H'*len(indices),*indices)
    return bytes(out),list(map(len,refs)),len(uniques)

def independent_parse(blob):
    """Independent wire reparse and external CLI Zstd concatenated-frame decoder."""
    tag,n,owner_count,gran=H.unpack_from(blob)
    if n!=N or gran!=BLOCK or tag not in (b'D116',b'CR16',b'SR16'):raise ValueError('bad header')
    p=H.size;fr=[];owners=[];rows=[]
    if tag!=b'D116':
        for _ in range(owner_count):
            if tag==b'CR16':
                length=BLOCK;size,want=FIX.unpack_from(blob,p);p+=FIX.size
            else:
                length,size,want=VAR.unpack_from(blob,p);p+=VAR.size
            if not 0<length<=1<<22 or not 0<size<=1<<22 or p+size>len(blob):raise ValueError('owner bounds')
            fr.append((blob[p:p+size],length,want));p+=size
    for _ in range(n):
        if tag==b'D116':
            length,want,size=RAW.unpack_from(blob,p);p+=RAW.size
            if length!=BLOCK*CHUNKS or not 0<size<=1<<22 or p+size>len(blob):raise ValueError('raw bounds')
            fr.append((blob[p:p+size],length,want));rows.append(None);p+=size
        else:
            length,want,num=ROW.unpack_from(blob,p);p+=ROW.size
            if length!=BLOCK*CHUNKS or num>16 or p+num*2>len(blob):raise ValueError('row bounds')
            ids=struct.unpack_from('<'+'H'*num,blob,p);p+=num*2
            if any(i>=owner_count for i in ids):raise ValueError('bad ref')
            rows.append((want,ids))
    if p!=len(blob):raise ValueError('trailing bytes')
    out=subprocess.run(['zstd','-q','-dc'],input=b''.join(x[0] for x in fr),capture_output=True,check=True).stdout
    if len(out)!=sum(x[1] for x in fr):raise ValueError('zstd output bounds')
    pieces=[];pos=0
    for frame,length,want in fr:
        part=out[pos:pos+length];pos+=length
        if sha(part)!=want:raise ValueError('physical SHA')
        pieces.append(part)
    if tag==b'D116':return pieces
    owners=pieces;result=[]
    for want,ids in rows:
        member=b''.join(owners[i] for i in ids)
        if len(member)!=BLOCK*CHUNKS or sha(member)!=want:raise ValueError('member SHA')
        result.append(member)
    return result

def run(root):
    root.mkdir(parents=True,exist_ok=True);results=[]
    for seed in SEEDS:
        for regime in REGIMES:
            rows=source(seed,regime);out={};geometry={};
            for arm in ('direct','chunkref','segref'):
                data,units,count=encode(rows,arm)
                if independent_parse(data)!=rows:raise ValueError('lossy '+arm)
                out[arm]=data;geometry[arm]={'owners':count,'units':units}
            sizes={k:len(x) for k,x in out.items()}
            prefix=regime=='prefix12';ratio=sizes['segref']/sizes['chunkref']
            row={'regime':regime,'seed':seed,'source_sha256':sha(b''.join(rows)).hex(),
                 'sizes':sizes,'segment_over_fixed_bytes':ratio,
                 'owners':{k:v['owners'] for k,v in geometry.items()},
                 'units':{k:v['units'] for k,v in geometry.items()},
                 'baseline_portfolio_bytes':min(sizes['direct'],sizes['chunkref'])+1,
                 'candidate_portfolio_bytes':min(sizes.values())+1,
                 'positive_size_criterion':ratio<=.99,
                 'candidate_selector':min(sizes,key=sizes.get)}
            results.append(row)
            (root/f'{regime}_{seed}.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
            print(regime,seed,sizes,'segment/fixed',round(ratio,6),flush=True)
    primary_bytes=all(r['positive_size_criterion'] for r in results if r['regime']=='prefix12')
    distinct_fallback=all(r['candidate_portfolio_bytes']<=1.01*r['baseline_portfolio_bytes'] for r in results if r['regime']=='distinct')
    receipt={'schema':'a16-o0-hosted-v1','primary_size_pass':primary_bytes,
             'distinct_fallback_pass':distinct_fallback,'cases':results,
             'scope':'byte-bound and member-exact scientific envelope only; no Reader/product credit'}
    (root/'result.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'primary_size_pass':primary_bytes,'fallback':distinct_fallback},sort_keys=True))
    return receipt

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.out)
