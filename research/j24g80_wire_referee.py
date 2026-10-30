#!/usr/bin/env python3
"""Independent no-CMPCT physical r24 Writer-session wire referee (J24G80)."""
from __future__ import annotations
import copy, ctypes, ctypes.util, hashlib, json, struct, sys, zlib
from pathlib import Path
import msgpack
H=struct.Struct('<8sHHQQQ32s')
F=struct.Struct('<8sBBBBQQQ32s')
B=struct.Struct('<4sBBHQQII32s')
MAX=1<<30
LIB=ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')
LIB.ZSTD_decompress.argtypes=(ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t)
LIB.ZSTD_decompress.restype=ctypes.c_size_t
LIB.ZSTD_isError.argtypes=(ctypes.c_size_t,);LIB.ZSTD_isError.restype=ctypes.c_uint

def sha(b):return hashlib.sha256(b).digest()

def decode(comp,n,codec):
    assert 0<n<MAX and 0<len(comp)<MAX
    if codec==0:
        assert len(comp)==n;return comp
    assert codec==1
    dst=ctypes.create_string_buffer(n);src=ctypes.create_string_buffer(comp)
    sz=LIB.ZSTD_decompress(dst,n,src,len(comp))
    assert not LIB.ZSTD_isError(sz) and sz==n
    return dst.raw[:n]

def parse(raw,corrupt_tail=False):
    assert H.size+F.size<len(raw)<MAX
    magic,rev,fl,clen,ulen,span,digest=H.unpack_from(raw)
    assert magic==b'CMPCT24\0' and rev==24 and fl==0
    base=H.size+clen
    assert base+span<=len(raw)-F.size
    index_raw=decode(raw[H.size:base],ulen,1)
    assert sha(index_raw)==digest
    initial=msgpack.unpackb(index_raw,raw=False)
    pos=len(raw)-F.size;seen=set();foot=[];bad=False
    while True:
        assert base+span<=pos<=len(raw)-F.size and pos not in seen
        seen.add(pos)
        m,kind,codec,flags,res,cs,us,prev,h=F.unpack_from(raw,pos)
        assert m==b'CMPTF24\0' and kind in (0,1) and flags==res==0
        assert 0<cs<MAX and 0<us<MAX and 0<=prev<pos
        payload=decode(raw[pos-cs:pos],us,codec)
        if sha(payload)!=h:
            assert corrupt_tail and not foot and prev>0
            pos=prev;bad=True;continue
        foot.append((pos,kind,prev,msgpack.unpackb(payload,raw=False)))
        if prev==0:break
        pos=prev
    assert foot[-1][3]==initial
    return initial,list(reversed(foot)),bad,base,span

def choose(n,where):
    indices=list(range(n//2-31,n//2+32)) if where=='middle' else list(range(n-63,n))
    indices.append(n//2+32 if where=='middle' else n-64)
    return [f'f{i:05d}.dat' for i in indices]

def delete(idx,name):
    rows=idx['files'];names=[r[0] for r in rows];assert name in names
    idx['files']=[r for r in rows if r[0]!=name]
    new_names=[r[0] for r in idx['files']]
    for field in ('owner_overrides','xattrs'):
        fsmeta=idx.get('fsmeta')
        if not fsmeta or field not in fsmeta:continue
        old_by_name={names[p[0]]:p[1:] for p in fsmeta[field]}
        assert len(old_by_name)==len(fsmeta[field])
        fsmeta[field]=[[new_i,*old_by_name[p]] for new_i,p in enumerate(new_names)
                       if p in old_by_name]

def blobs_validate(archive,idx,base,span,n):
    records=[]
    for off,usize,csize,codec,meta_size in idx['blobs']:
        p=base+off;assert p>=base and p+B.size+meta_size+csize<=base+span
        magic,c,fl,res,u,cs,ml,crc,h=B.unpack_from(archive,p)
        assert magic==b'CMA4' and c==codec and fl==res==0
        assert (u,cs,ml)==(usize,csize,meta_size)
        data=decode(archive[p+B.size+meta_size:p+B.size+meta_size+csize],usize,codec)
        assert sha(data)==h and zlib.crc32(data)&0xffffffff==crc
        records.append(data)
    for row in idx['files']:
        if row[1]!=0:continue
        storage=row[6]
        if storage[0]==0:data=records[storage[1]]
        elif storage[0]==4:
            pack,offset,ln=storage[1:]
            data=records[pack][offset:offset+ln]
            assert len(data)==ln
        else:raise AssertionError(f'unsupported source storage {storage[0]}')
        i=int(row[0][1:6])
        expected=hashlib.sha256(f'j24g80-{n}-{i}'.encode()).digest()
        assert data==expected and row[4]==len(expected)
    return len(records)

def audit_one(archive,receipt,n,where,variant):
    initial,foot,bad,base,span=parse(archive)
    assert not bad and len(foot)==65
    assert foot[0][1]==0 and foot[-1][1]==0
    assert len([x for x in foot if x[1]==1])==63
    assert [x[0] for x in foot]==sorted(x[0] for x in foot)
    assert len(initial['files'])==n
    names=choose(n,where);idx=copy.deepcopy(initial)
    trial=next(r for r in receipt['rows'] if r['variant']==variant)
    assert len(trial['physical'])==64
    blobs=blobs_validate(archive,initial,base,span,n)
    for k,name in enumerate(names,1):
        pos,kind,prev,payload=foot[k]
        assert prev==foot[k-1][0]
        if k<64:
            assert kind==1 and payload=={'blobs':[],'ops':[['del',name]]}
        delete(idx,name)
        if k==64:assert kind==0 and payload==idx
        prefix=archive[:pos+F.size];expected=trial['physical'][k-1]
        assert len(prefix)==expected['bytes'] and sha(prefix).hex()==expected['sha256']
    assert sha(msgpack.packb(idx,use_bin_type=True)).hex()==trial['final_index_sha256']
    return dict(variant=variant,physical_bytes=len(archive),sha256=sha(archive).hex(),
                signed_footers=len(foot),blobs_crc_sha=blobs,
                intermediate_prefix_matches=64,final_index_exact=True)

def main():
    if len(sys.argv)!=6:
        raise SystemExit('usage: referee.py RECEIPT_JSON CASE PUBLIC_ARCHIVE OWNED_ARCHIVE CORRUPT_OWNED')
    receipt=json.loads(Path(sys.argv[1]).read_text());case=sys.argv[2]
    c=receipt['cases'][case];n=int(case.split('-')[0]);where=case.split('-')[1]
    pub=Path(sys.argv[3]).read_bytes();own=Path(sys.argv[4]).read_bytes()
    corrupt=Path(sys.argv[5]).read_bytes()
    a=audit_one(pub,c,n,where,'public');b=audit_one(own,c,n,where,'owned')
    assert pub==own,'candidate not byte-identical to original physical archive'
    assert corrupt[:-1]==own[:-1] and corrupt[-1]!=own[-1]
    _,foot,bad,_,_=parse(own)
    _,prior,was_bad,_,_=parse(corrupt,True)
    assert not bad and was_bad and len(prior)==64
    assert prior[-1][0]==foot[-2][0]
    print(json.dumps(dict(schema='j24g80-detached-no-cmpct-v1',
                          case=case,decision='EXACT_PHYSICAL_AND_CORRUPT_TAIL_PASS',
                          records=[a,b]),indent=2))

if __name__=='__main__':main()
