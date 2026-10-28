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


def positional_owners(rows):
    """Adjacent blocks merge only under exact equal (position,bytes)->member-set."""
    split=[[r[i:i+BLOCK] for i in range(0,len(r),BLOCK)] for r in rows]
    if len(split)!=N or any(len(x)!=CHUNKS for x in split):raise ValueError('geometry')
    incidence=[{} for _ in range(CHUNKS)]
    # Complete bytes as keys, not SHA-only: collision never proves equality.
    for i,blocks in enumerate(split):
        for j,data in enumerate(blocks):
            incidence[j][data]=incidence[j].get(data,0)|(1<<i)
    out=[]
    for i,blocks in enumerate(split):
        runs=[];current=bytearray(blocks[0]);prior=incidence[0][blocks[0]]
        for j in range(1,CHUNKS):
            membership=incidence[j][blocks[j]]
            if membership!=prior:
                runs.append(bytes(current));current.clear()
            current+=blocks[j];prior=membership
        runs.append(bytes(current));out.append(runs)
    return out

def encode(rows,arm):
    if arm=='direct':
        out=bytearray(H.pack(b'D116',N,0,BLOCK))
        for raw in rows:
            frame=zstd(raw);out+=RAW.pack(len(raw),sha(raw),len(frame))+frame
        return bytes(out),[1]*N,0
    grouped=arm in ('segref','posref')
    groups=(positional_owners(rows) if arm=='posref' else owners(rows,grouped));uniques=[];refs=[];lookup={}
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



# A16-O2 prospective source-exact court; retained O0 source is the control.
import argparse, sys, tracemalloc
import a16_o0_sharing_run_court as old

SEEDS=(20261028,20261029)
HOSTILE=(20261030,20261031)
HELDOUT=(20261032,20261033)
REGIMES=('identical','prefix12','suffix12','alternating8','distinct')

def hostile(seed):
    rng=random.Random(seed);out=[bytearray() for _ in range(N)]
    for j in range(CHUNKS):
        pool=[rng.randbytes(BLOCK) for _ in range(4)]
        order=[k for k in range(4) for _ in range(N//4)]
        rng.shuffle(order)
        for i,k in enumerate(order):out[i]+=pool[k]
    return list(map(bytes,out))

def shifted(seed):
    rng=random.Random(seed);pool=[rng.randbytes(BLOCK) for _ in range(6)]
    out=[]
    for i in range(N):
        parts=[pool[(i%6+j)%6] if j%3!=2 else rng.randbytes(BLOCK)
               for j in range(CHUNKS)]
        out.append(b''.join(parts))
    return out

def permuted(seed):
    rng=random.Random(seed);out=[bytearray() for _ in range(N)]
    groups=[list(range(N)) for _ in range(4)]
    for g in groups:rng.shuffle(g)
    for j in range(CHUNKS):
        pool=[rng.randbytes(BLOCK) for _ in range(4)]
        for k,idx in enumerate(groups[j//4]):out[idx]+=pool[k//8]
    return list(map(bytes,out))

def source_o2(regime,seed):
    if regime in REGIMES:return old.source(seed,regime)
    if regime=='hostile':return hostile(seed)
    if regime=='shifted':return shifted(seed)
    if regime=='permuted':return permuted(seed)
    raise ValueError('regime')

def read_index(blob):
    tag,n,owners,gran=H.unpack_from(blob)
    if n!=N or gran!=BLOCK or tag not in (b'D116',b'CR16',b'SR16'):
        raise ValueError('bad header')
    p=H.size; frames=[];records=[]
    for _ in range(owners):
        if tag==b'CR16':
            width,want=FIX.unpack_from(blob,p);p+=FIX.size;length=BLOCK
        else:
            length,width,want=VAR.unpack_from(blob,p);p+=VAR.size
        if not 0<length<=BLOCK*CHUNKS or not 0<width<=1<<22 or p+width>len(blob):
            raise ValueError('frame bounds')
        frames.append((blob[p:p+width],length,want));p+=width
    for _ in range(n):
        if tag==b'D116':
            length,want,width=RAW.unpack_from(blob,p);p+=RAW.size
            if length!=BLOCK*CHUNKS or not 0<width<=1<<22 or p+width>len(blob):
                raise ValueError('direct bounds')
            records.append(([(blob[p:p+width],length,want)],want))
            p+=width
        else:
            length,want,nref=ROW.unpack_from(blob,p);p+=ROW.size
            if length!=BLOCK*CHUNKS or not 0<nref<=CHUNKS or p+2*nref>len(blob):
                raise ValueError('refs bounds')
            indices=struct.unpack_from('<'+'H'*nref,blob,p);p+=2*nref
            if any(k>=len(frames) for k in indices):raise ValueError('owner id')
            records.append(([frames[k] for k in indices],want))
    if p!=len(blob):raise ValueError('trailing')
    return records

Z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
Z.ZSTD_decompress.restype=ctypes.c_size_t

def member_read(rec):
    frames,want=rec
    output=bytearray()
    for frame,rawlen,hsh in frames:
        buf=ctypes.create_string_buffer(rawlen)
        got=Z.ZSTD_decompress(buf,rawlen,frame,len(frame))
        if Z.ZSTD_isError(got) or got!=rawlen:raise ValueError('decode')
        part=buf.raw[:rawlen]
        if sha(part)!=hsh:raise ValueError('physical sha')
        output+=part
    raw=bytes(output)
    if len(raw)!=BLOCK*CHUNKS or sha(raw)!=want:raise ValueError('member sha')
    return raw

def time_reads(blob):
    items=read_index(blob);q1=[];whole=[]
    for _ in range(7):
        t=time.perf_counter_ns()
        member_read(items[-1])
        q1.append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns()
        for rec in items:member_read(rec)
        whole.append((time.perf_counter_ns()-t)/1e6)
    return {'q1_ms':q1,'whole_ms':whole,
            'median_q1_ms':statistics.median(q1),'median_whole_ms':statistics.median(whole)}

def run_o2(root):
    root.mkdir(parents=True,exist_ok=True)
    cases=[]
    schedule=([(regime,seed) for regime in REGIMES for seed in SEEDS]
              + [('hostile',seed) for seed in HOSTILE]
              + [(regime,seed) for regime in ('shifted','permuted') for seed in HELDOUT])
    for regime,seed in schedule:
        rows=source_o2(regime,seed)
        folder=root/(regime+'_'+str(seed));folder.mkdir(exist_ok=True)
        (folder/'source.bin').write_bytes(b''.join(rows))
        packed={};geometry={};create={}
        for arm in ('direct','chunkref','binary_segref','positional_coowner'):
            begin=time.perf_counter_ns()
            if arm=='positional_coowner':
                blob,units,n=encode(rows,'posref')
            else:
                blob,units,n=old.encode(rows,{'binary_segref':'segref'}.get(arm,arm))
            create[arm]=(time.perf_counter_ns()-begin)/1e6
            if old.independent_parse(blob)!=rows:raise AssertionError('exact member mismatch')
            (folder/(arm+'.bin')).write_bytes(blob)
            packed[arm]=blob;geometry[arm]={'units':units,'owners':n}
        # Separate memory probe: never charge tracing overhead as fair creation wall.
        tracemalloc.start()
        positional_owners(rows)
        _,peak=tracemalloc.get_traced_memory()
        tracemalloc.stop()
        sizes={k:len(v) for k,v in packed.items()}
        reads={arm:time_reads(packed[arm])
               for arm in ('direct','chunkref','positional_coowner')}
        selected=min(('direct','chunkref','positional_coowner'),key=sizes.get)
        case={'regime':regime,'seed':seed,'source_sha256':sha(b''.join(rows)).hex(),
              'complete_bytes':sizes,'geometry':geometry,'create_wall_ms':create,
              'positional_membership_peak_tracemalloc_bytes':peak,
              'read_wall_ms':reads,'portfolio_baseline_bytes':min(sizes['direct'],sizes['chunkref'])+1,
              'portfolio_candidate_bytes':min(sizes['direct'],sizes['chunkref'],sizes['positional_coowner'])+1,
              'portfolio_selected':selected,
              'ratio_positional_over_fixed':sizes['positional_coowner']/sizes['chunkref'],
              'read_speedup_fixed_over_positional':reads['chunkref']['median_whole_ms']/reads['positional_coowner']['median_whole_ms']}
        cases.append(case)
        (folder/'result.json').write_text(json.dumps(case,sort_keys=True,indent=2)+'\n')
        print(regime,seed,sizes,'units',min(geometry['positional_coowner']['units']),
              max(geometry['positional_coowner']['units']),flush=True)
    hostile_rows=[x for x in cases if x['regime']=='hostile']
    partial=[x for x in cases if x['regime'] in ('prefix12','suffix12')]
    hostile_pass=all(x['ratio_positional_over_fixed']<=1.01
                     and x['geometry']['positional_coowner']['units']==[16]*N
                     for x in hostile_rows)
    transfer=all(x['geometry']['positional_coowner']['units']==[2]*N
                 and x['complete_bytes']['positional_coowner']<=1.005*x['complete_bytes']['binary_segref']
                 for x in partial)
    joint=all(x['ratio_positional_over_fixed']<=.99
              and x['read_speedup_fixed_over_positional']>=1.5 for x in partial)
    receipt={'schema':'a16-o2-positional-coowner-hosted-v1',
             'source_parent':'acaa48a74c2e8859e476c629bf1debab25e89f37',
             'prereg_sha':'a0b75a33f17c67c749c467227266092ba799c224',
             'hostile_containment':hostile_pass,'positive_transfer':transfer,
             'inherited_joint_byte_wall_pass':joint,
             'cases':cases,'scope':'research only; not CMPCT product'}
    (root/'result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('hostile_containment','positive_transfer',
                                             'inherited_joint_byte_wall_pass')}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    run_o2(p.parse_args().out)
