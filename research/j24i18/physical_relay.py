#!/usr/bin/env python3
"""J24I18 exact r24 physical-record relay research oracle.

This is NOT a production compactor or secure publisher. It retains all indexed blobs,
including dead ones, authenticates supported physical codecs, and NEVER extracts to
a filesystem tree. Supports only bounded local research archives.
Dependencies: Python 3.11, msgpack, system libzstd.
"""
import binascii, copy, ctypes, ctypes.util, hashlib, json, pathlib, struct, sys, time, zlib
import msgpack

MAGIC=b'CMPCT24\0'; FMAGIC=b'CMPTF24\0'; BMAGIC=b'CMA4'
HDR=struct.Struct('<8sHHQQQ32s'); FTR=struct.Struct('<8sBBBBQQQ32s')
BHDR=struct.Struct('<4sBBHQQII32s')
MAX_INPUT=256*1024*1024; MAX_BLOBS=250000; MAX_INDEX=32*1024*1024
z=ctypes.CDLL(ctypes.util.find_library('zstd'))
z.ZSTD_compressBound.argtypes=[ctypes.c_size_t];z.ZSTD_compressBound.restype=ctypes.c_size_t
z.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
z.ZSTD_compress.restype=ctypes.c_size_t
z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
z.ZSTD_decompress.restype=ctypes.c_size_t
z.ZSTD_isError.argtypes=[ctypes.c_size_t];z.ZSTD_isError.restype=ctypes.c_uint
def sha(data):return hashlib.sha256(data).digest()
def unp(data):return msgpack.unpackb(data,raw=False,strict_map_key=False)
def pk(obj):return msgpack.packb(obj,use_bin_type=True)
def zd(data,size):
    if size<0 or size>MAX_INPUT:raise ValueError('unbounded decoded data')
    out=ctypes.create_string_buffer(max(size,1));n=z.ZSTD_decompress(out,size,data,len(data))
    if z.ZSTD_isError(n) or n!=size:raise ValueError('invalid zstd payload')
    return out.raw[:size]
def zc(data,level=12):
    cap=z.ZSTD_compressBound(len(data));out=ctypes.create_string_buffer(cap)
    n=z.ZSTD_compress(out,cap,data,len(data),level)
    if z.ZSTD_isError(n):raise ValueError('zstd compression error')
    return out.raw[:n]

def read_index(data):
    if len(data)<HDR.size+FTR.size:raise ValueError('short archive')
    magic,version,flags,cs,us,span,ih=HDR.unpack_from(data)
    if magic!=MAGIC or version!=24 or flags!=0 or cs>MAX_INDEX or us>MAX_INDEX or HDR.size+cs>len(data):
        raise ValueError('header/size violation')
    base=HDR.size+cs
    def gen(at,seen):
        if at in seen or len(seen)>=128 or at<base or at+FTR.size>len(data):
            raise ValueError('invalid generation chain')
        m,k,codec,fl,res,ec,uc,prev,h=FTR.unpack_from(data,at)
        if m!=FMAGIC or k not in(0,1) or codec not in(0,1) or fl or res or ec>MAX_INDEX or uc>MAX_INDEX or ec>at-base:
            raise ValueError('invalid generation footer')
        enc=data[at-ec:at];plain=zd(enc,uc) if codec else enc
        if len(plain)!=uc or sha(plain)!=h:raise ValueError('generation digest mismatch')
        idx=unp(plain)
        if k==0:return idx,len(seen)
        if prev<=0 or prev>=at:raise ValueError('invalid parent')
        parent,depth=gen(prev,seen|{at});parent=copy.deepcopy(parent)
        parent['blobs'].extend(idx.get('blobs',[]))
        for op in idx.get('ops',[]):
            if op[0]=='put':
                row=op[1];parent['files']=[r for r in parent['files'] if r[0]!=row[0]]+[row]
            elif op[0]=='del':parent['files']=[r for r in parent['files'] if r[0]!=op[1]]
            elif op[0]=='ren':
                for r in parent['files']:
                    if r[0]==op[1]:r[0]=op[2];break
            else:raise ValueError('unknown update operation')
        parent['files'].sort(key=lambda r:r[0])
        return parent,depth+1
    pos=len(data)
    while True:
        pos=data.rfind(FMAGIC,base,pos)
        if pos<0:break
        try:
            ix,d=gen(pos,set());return ix,base,d
        except (ValueError,KeyError,IndexError,TypeError):pass
    raw=zd(data[HDR.size:base],us)
    if sha(raw)!=ih:raise ValueError('invalid primary index')
    return unp(raw),base,0

def read_blobs(data,index,base):
    if len(index['blobs'])>MAX_BLOBS:raise ValueError('blob-count limit')
    records=[]
    for off,us,cs,codec,ml in index['blobs']:
        if any(type(v) is not int or v<0 for v in (off,us,cs,codec,ml)):
            raise ValueError('invalid blob coordinates')
        at=base+off
        if at<base or at+BHDR.size>len(data):raise ValueError('blob header outside')
        m,c,fl,res,ru,rc,rm,crc,h=BHDR.unpack_from(data,at)
        if m!=BMAGIC or fl or res or (ru,rc,rm,c)!=(us,cs,ml,codec):
            raise ValueError('blob header/index disagreement')
        end=at+BHDR.size+ml+cs
        if end>len(data):raise ValueError('blob overrun')
        record=data[at:end];comp=data[at+BHDR.size+ml:end]
        if c==0:raw=comp
        elif c==1:raw=zd(comp,us)
        elif c==4:raw=zlib.decompress(comp,-15)
        else:raise ValueError('unverified codec cannot earn oracle credit')
        if len(raw)!=us or sha(raw)!=h or binascii.crc32(raw)&0xffffffff!=crc:
            raise ValueError('blob content integrity')
        records.append(record)
    return records

def relay(source,target):
    start=time.perf_counter_ns();data=pathlib.Path(source).read_bytes()
    if len(data)>MAX_INPUT:raise ValueError('input bound')
    ix,base,depth=read_index(data);records=read_blobs(data,ix,base)
    updated=copy.deepcopy(ix);offset=0
    for b,rec in zip(updated['blobs'],records):
        b[0]=offset;offset+=len(rec)
    raw=pk(updated);packed=zc(raw);h=sha(raw)
    wire=HDR.pack(MAGIC,24,0,len(packed),len(raw),offset,h)+packed+b''.join(records)+packed+FTR.pack(FMAGIC,0,1,0,0,len(packed),len(raw),0,h)
    pathlib.Path(target).write_bytes(wire)
    check,cb,cd=read_index(wire);restored=read_blobs(wire,check,cb)
    def normalized(a):return pk({**a,'blobs':[[0]+list(x[1:]) for x in a['blobs']]})
    assert normalized(ix)==normalized(check) and records==restored and cd==0
    assert sha(pathlib.Path(source).read_bytes())==sha(data)
    return {'source':pathlib.Path(source).name,'before':len(data),'after':len(wire),
            'source_sha256':sha(data).hex(),'output_sha256':sha(wire).hex(),
            'index_semantic_sha256':sha(normalized(ix)).hex(),
            'input_delta_depth':depth,'output_delta_depth':cd,
            'blobs':len(records),'files':len(ix['files']),
            'elapsed_ms':round((time.perf_counter_ns()-start)/1e6,3)}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);p.add_argument('inputs',nargs='+')
    a=p.parse_args();dst=pathlib.Path(a.output_dir);dst.mkdir(parents=True,exist_ok=True)
    for x in a.inputs:
        try:print(json.dumps(relay(x,dst/pathlib.Path(x).name),sort_keys=True))
        except Exception as e:print(json.dumps({'source':x,'failure':str(e)},sort_keys=True))
