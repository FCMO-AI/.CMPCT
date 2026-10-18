"""Independently frame r24 chunk/CDC fixtures without Builder.

A 1-MiB physical object may be referenced repeatedly to represent a >4-GiB
logical member. Exact physical and logical hashes are charged, not gifted.
"""
import binascii
import hashlib
import json
import sys
from pathlib import Path
import msgpack
from cmpct.codec import HDR, BHDR, BMAGIC, MAGIC, CODEC_RAW, K_FILE, K_HARDLINK, S_CHUNKS, S_CDC, zc

PAYLOAD = bytes(range(256)) * 4096
assert len(PAYLOAD)==1 << 20

def make(path, kind, count, *, mutation=None, hardlink=False):
    n=len(PAYLOAD)
    h=hashlib.sha256()
    for _ in range(count):h.update(PAYLOAD)
    ph=hashlib.sha256(PAYLOAD).digest()
    if mutation=='physical':ph=bytes([ph[0]^1])+ph[1:]
    packed=BHDR.pack(BMAGIC,CODEC_RAW,0,0,n,n,0,binascii.crc32(PAYLOAD)&0xffffffff,ph)+PAYLOAD
    if kind=='chunks': storage=[S_CHUNKS,[0]*count]
    elif kind=='cdc': storage=[S_CDC,[[n,0] for _ in range(count)]]
    else:raise ValueError(kind)
    if mutation=='declared':
        assert kind=='cdc';storage[1][count//2][0]=n-1
    want=h.digest()
    if mutation=='logical':want=bytes([want[0]^1])+want[1:]
    if mutation=='no_commit':want=None
    rows=[['member.dat',K_FILE,0o644,0,n*count,want,storage]]
    if hardlink:
        rows.append(['member.link',K_HARDLINK,0o644,0,n*count,None,['member.dat']])
    rows.sort(key=lambda x:x[0])
    index={'v':24,'blobs':[[0,n,n,CODEC_RAW,0]],'files':rows,'recipes':[],
           'dict_blob':None,'fsmeta':{},'features':[]}
    b=msgpack.packb(index,use_bin_type=True)
    bc=zc(b,3)
    path=Path(path);path.write_bytes(HDR.pack(MAGIC,24,0,len(bc),len(b),len(packed),hashlib.sha256(b).digest())+bc+packed)
    return {'archive':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'logical_sha256':h.hexdigest(),'logical_bytes':n*count,'physical_bytes':path.stat().st_size,
            'storage':kind,'count':count,'mutation':mutation,'hardlink':hardlink}

if __name__=='__main__':
    _,dst,kind,count,*args=sys.argv
    mutation=args[0] if args else None
    print(json.dumps(make(dst,kind,int(count),mutation=mutation)))

def make_cdc_cross_boundary(path):
    # Distinct adjacent frames expose the inconsistency between full-read identity
    # and the declared-length-addressed random-access projection.
    a=b'A'*(256*1024)
    b=b'B'*(256*1024)
    bodies=[];blobs=[];pos=0
    for payload in (a,b):
        n=len(payload)
        record=BHDR.pack(BMAGIC,CODEC_RAW,0,0,n,n,0,
                         binascii.crc32(payload)&0xffffffff,
                         hashlib.sha256(payload).digest())+payload
        bodies.append(record);blobs.append([pos,n,n,CODEC_RAW,0]);pos+=len(record)
    full=a+b
    index={'v':24,'blobs':blobs,
           'files':[['pair.bin',K_FILE,0o644,0,len(full),hashlib.sha256(full).digest(),
                     [S_CDC,[[len(a)-1,0],[len(b)+1,1]]]]],
           'recipes':[],'dict_blob':None,'fsmeta':{},'features':[]}
    ib=msgpack.packb(index,use_bin_type=True); ic=zc(ib,3)
    path=Path(path)
    path.write_bytes(HDR.pack(MAGIC,24,0,len(ic),len(ib),pos,
                              hashlib.sha256(ib).digest())+ic+b''.join(bodies))
    return full

def make_alternating(path, kind, count=4097, *, mutation=None):
    # Held-out second physical-ownership regime, alternating distinct one-MiB objects.
    a=PAYLOAD
    b=PAYLOAD[::-1]
    h=hashlib.sha256()
    rec=[];refs=[];base=0;blobs=[]
    for payload in (a,b):
        n=len(payload)
        r=BHDR.pack(BMAGIC,CODEC_RAW,0,0,n,n,0,
                    binascii.crc32(payload)&0xffffffff,
                    hashlib.sha256(payload).digest())+payload
        rec.append(r);blobs.append([base,n,n,CODEC_RAW,0]);base+=len(r)
    for i in range(count):
        idx=i%2
        h.update((a,b)[idx])
        refs.append(idx if kind=='chunks' else [len(a),idx])
    want=h.digest()
    if mutation=='logical':want=bytes([want[0]^1])+want[1:]
    index={'v':24,'blobs':blobs,
           'files':[['heldout.bin',K_FILE,0o644,0,len(a)*count,want,
                     [S_CHUNKS if kind=='chunks' else S_CDC,refs]]],
           'recipes':[],'dict_blob':None,'fsmeta':{},'features':[]}
    ib=msgpack.packb(index,use_bin_type=True);ic=zc(ib,3)
    path=Path(path)
    path.write_bytes(HDR.pack(MAGIC,24,0,len(ic),len(ib),base,
                              hashlib.sha256(ib).digest())+ic+b''.join(rec))
    return {'archive':str(path),'archive_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'logical_sha256':h.hexdigest(),'bytes':len(a)*count,'kind':kind,
            'count':count,'mutation':mutation}
