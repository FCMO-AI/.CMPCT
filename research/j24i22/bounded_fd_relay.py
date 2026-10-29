#!/usr/bin/env python3
"""J24I22 research-only source-FD bounded r24 relay; NOT a secure product compactor.

One physical record is copied and authenticated from the same FD/read. The
source remains mutable by other writers and destination publication is not
protected against a hostile sibling-directory actor. Fail-closed subset only.
"""
from __future__ import annotations
import argparse, binascii, copy, ctypes, ctypes.util, hashlib, json, os, pathlib, stat, tempfile, time, zlib
import msgpack
import physical_relay as pr
import live_blob_relay as live

CHUNK=65536
MAX_INDEX=32*1024*1024
MAX_BLOBS=250000
MAX_DEPTH=128
MAX_ZSTD_WINDOW=8*1024*1024
SHA=pr.sha
DECOMP=pr.zd
PACK=pr.pk
COMP=pr.zc
Z=ctypes.CDLL(ctypes.util.find_library("zstd"))

class InBuf(ctypes.Structure):
    _fields_=[("src",ctypes.c_void_p),("size",ctypes.c_size_t),("pos",ctypes.c_size_t)]
class OutBuf(ctypes.Structure):
    _fields_=[("dst",ctypes.c_void_p),("size",ctypes.c_size_t),("pos",ctypes.c_size_t)]
Z.ZSTD_createDStream.restype=ctypes.c_void_p
Z.ZSTD_freeDStream.argtypes=[ctypes.c_void_p]
Z.ZSTD_freeDStream.restype=ctypes.c_size_t
Z.ZSTD_initDStream.argtypes=[ctypes.c_void_p]
Z.ZSTD_initDStream.restype=ctypes.c_size_t
Z.ZSTD_decompressStream.argtypes=[ctypes.c_void_p,ctypes.POINTER(OutBuf),ctypes.POINTER(InBuf)]
Z.ZSTD_decompressStream.restype=ctypes.c_size_t
Z.ZSTD_DCtx_setMaxWindowSize.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
Z.ZSTD_DCtx_setMaxWindowSize.restype=ctypes.c_size_t
Z.ZSTD_isError.argtypes=[ctypes.c_size_t]
Z.ZSTD_isError.restype=ctypes.c_uint

def exact(fd,n,off):
    if n<0 or off<0:raise ValueError("negative physical coordinate")
    data=os.pread(fd,n,off)
    if len(data)!=n:raise ValueError("truncated physical source")
    return data

def file_sha(fd,size):
    h=hashlib.sha256()
    for p in range(0,size,CHUNK):h.update(exact(fd,min(CHUNK,size-p),p))
    return h.digest()

def output_sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        while part:=f.read(CHUNK):h.update(part)
    return h.digest()

def decode_index(fd,at,base,seen,budget):
    if at in seen or len(seen)>=MAX_DEPTH or at<base or at+pr.FTR.size>os.fstat(fd).st_size:
        raise ValueError("bad index chain")
    m,kind,codec,flags,res,ec,uc,prev,h=pr.FTR.unpack(exact(fd,pr.FTR.size,at))
    if m!=pr.FMAGIC or kind not in (0,1) or codec not in (0,1) or flags or res or ec>MAX_INDEX or uc>MAX_INDEX or ec>at-base:
        raise ValueError("untrusted footer")
    budget[0]-=uc+ec
    if budget[0]<0:raise ValueError("cumulative index budget exceeded")
    encoded=exact(fd,ec,at-ec)
    raw=DECOMP(encoded,uc) if codec else encoded
    if len(raw)!=uc or SHA(raw)!=h:raise ValueError("invalid authenticated index")
    idx=msgpack.unpackb(raw,raw=False,strict_map_key=False)
    if kind==0:return idx,0
    if prev<=0 or prev>=at:raise ValueError("invalid delta parent")
    base_idx,depth=decode_index(fd,prev,base,seen|{at},budget)
    out=copy.deepcopy(base_idx);out["blobs"].extend(idx.get("blobs",[]))
    for op in idx.get("ops",[]):
        if op[0]=="put":out["files"]=[r for r in out["files"] if r[0]!=op[1][0]]+[op[1]]
        elif op[0]=="del":out["files"]=[r for r in out["files"] if r[0]!=op[1]]
        elif op[0]=="ren":
            matches=[r for r in out["files"] if r[0]==op[1]]
            if len(matches)!=1:raise ValueError("missing rename source")
            matches[0][0]=op[2]
        else:raise ValueError("unknown delta operation")
    out["files"].sort(key=lambda r:r[0])
    return out,depth+1

def latest(fd,size):
    if size<pr.HDR.size+pr.FTR.size:raise ValueError("small archive")
    m,v,flags,cs,us,span,h=pr.HDR.unpack(exact(fd,pr.HDR.size,0))
    if m!=pr.MAGIC or v!=24 or flags or cs>MAX_INDEX or us>MAX_INDEX or pr.HDR.size+cs>=size:
        raise ValueError("invalid primary header")
    base=pr.HDR.size+cs
    budget=[MAX_INDEX-cs-us]
    if budget[0]<0:raise ValueError("primary index budget exceeded")
    primary=DECOMP(exact(fd,cs,pr.HDR.size),us)
    if len(primary)!=us or SHA(primary)!=h:raise ValueError("invalid primary index")
    # Unlike the product Reader, research intentionally refuses an uncommitted tail.
    idx,depth=decode_index(fd,size-pr.FTR.size,base,set(),budget)
    if type(idx) is not dict or type(idx.get("blobs")) is not list or type(idx.get("files")) is not list:
        raise ValueError("invalid index tables")
    if len(idx["blobs"])>MAX_BLOBS:raise ValueError("blob count bound")
    return idx,base,depth

def verify_record(fd,b,base,size,outfd=None):
    if type(b) is not list or len(b)!=5 or any(type(v) is not int or v<0 for v in b):
        raise ValueError("invalid blob declaration")
    offset,uncompressed,compressed,codec,metalength=b
    pos=base+offset;end=pos+pr.BHDR.size+metalength+compressed
    if pos<base or end>size-pr.FTR.size or end<pos:raise ValueError("blob out of range")
    header=exact(fd,pr.BHDR.size,pos)
    magic,c,flags,res,rawlen,complen,metalen,crc,digest=pr.BHDR.unpack(header)
    if magic!=pr.BMAGIC or flags or res or (c,rawlen,complen,metalen)!=(codec,uncompressed,compressed,metalength):
        raise ValueError("physical header/declaration mismatch")
    metadata=exact(fd,metalength,pos+pr.BHDR.size)
    if codec not in (0,1,4):raise ValueError("unsupported physical codec")
    if outfd is not None:outfd.write(header);outfd.write(metadata)
    sha=hashlib.sha256();rolling_crc=0;total=0;remaining=compressed
    zstream=Z.ZSTD_createDStream() if codec==1 else None
    if zstream and (Z.ZSTD_isError(Z.ZSTD_initDStream(zstream)) or Z.ZSTD_isError(Z.ZSTD_DCtx_setMaxWindowSize(zstream,MAX_ZSTD_WINDOW))):
        Z.ZSTD_freeDStream(zstream);raise ValueError("zstd decoder bound not established")
    inflater=zlib.decompressobj(-15) if codec==4 else None
    # Reuse this buffer: allocating one ctypes buffer per decoded chunk caused
    # ~70MiB apparent Python/FFI RSS growth on a 128MiB zero-stream oracle.
    out_buffer=ctypes.create_string_buffer(CHUNK) if codec==1 else None
    out_pointer=ctypes.cast(out_buffer,ctypes.c_void_p) if out_buffer is not None else None
    completed=False
    def accept(raw):
        nonlocal rolling_crc,total
        total+=len(raw)
        if total>uncompressed:raise ValueError("decoded length overflow")
        sha.update(raw);rolling_crc=binascii.crc32(raw,rolling_crc)
    try:
        position=pos+pr.BHDR.size+metalength
        while remaining:
            chunk=exact(fd,min(CHUNK,remaining),position)
            position+=len(chunk);remaining-=len(chunk)
            if outfd is not None:outfd.write(chunk)
            if codec==0:accept(chunk)
            elif codec==4:
                buffered=chunk
                while buffered:
                    try:raw=inflater.decompress(buffered,CHUNK)
                    except zlib.error as e:raise ValueError("malformed deflate content") from e
                    accept(raw)
                    if inflater.unused_data:raise ValueError("trailing deflate input")
                    buffered=inflater.unconsumed_tail
                if inflater.eof and remaining:raise ValueError("trailing deflate bytes")
            else:
                ib=ctypes.create_string_buffer(chunk)
                ins=InBuf(ctypes.cast(ib,ctypes.c_void_p),len(chunk),0)
                while ins.pos<ins.size:
                    outs=OutBuf(out_pointer,CHUNK,0)
                    prior=ins.pos
                    rv=Z.ZSTD_decompressStream(zstream,ctypes.byref(outs),ctypes.byref(ins))
                    if Z.ZSTD_isError(rv):raise ValueError("invalid zstd content")
                    accept(out_buffer.raw[:outs.pos])
                    if rv==0:
                        completed=True
                        if ins.pos<ins.size or remaining:raise ValueError("trailing zstd bytes")
                    if ins.pos==prior and outs.pos==0:raise ValueError("no decompression progress")
        if codec==4:
            while True:
                final=inflater.flush(CHUNK)
                if not final:break
                accept(final)
            if not inflater.eof:raise ValueError("truncated deflate stream")
        if codec==1 and not completed:raise ValueError("truncated zstd stream")
        if total!=uncompressed or sha.digest()!=digest or rolling_crc&0xffffffff!=crc:
            raise ValueError("blob SHA256/CRC32/length failure")
    finally:
        if zstream:Z.ZSTD_freeDStream(zstream)
    return end-pos

def relay(source,destination,after_admit=None):
    started=time.perf_counter_ns();source=pathlib.Path(source);destination=pathlib.Path(destination)
    if not hasattr(os,"O_NOFOLLOW"):raise RuntimeError("POSIX O_NOFOLLOW required")
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    tmp=None
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):raise ValueError("source not regular")
        size=st.st_size;old_digest=file_sha(fd,size)
        idx,base,depth=latest(fd,size)
        keep=live.live_ids(idx);new=live.map_index(idx,keep)
        mapping={old:i for i,old in enumerate(keep)}
        offsets={};cursor=0
        for old in keep:
            b=idx["blobs"][old]
            if type(b) is not list or len(b)!=5:raise ValueError("bad blob descriptor")
            offsets[old]=cursor;cursor+=pr.BHDR.size+b[4]+b[2]
        for old,i in mapping.items():new["blobs"][i][0]=offsets[old]
        encoded_raw=PACK(new);enc=COMP(encoded_raw);h=SHA(encoded_raw)
        if len(enc)>MAX_INDEX or len(encoded_raw)>MAX_INDEX:raise ValueError("output index bound")
        if after_admit:after_admit()
        with tempfile.NamedTemporaryFile(mode="w+b",dir=destination.parent,prefix=".j24i22-",delete=False) as out:
            tmp=pathlib.Path(out.name)
            out.write(pr.HDR.pack(pr.MAGIC,24,0,len(enc),len(encoded_raw),cursor,h));out.write(enc)
            for i,b in enumerate(idx["blobs"]):
                verify_record(fd,b,base,size,out if i in mapping else None)
            out.write(enc);out.write(pr.FTR.pack(pr.FMAGIC,0,1,0,0,len(enc),len(encoded_raw),0,h))
            out.flush();os.fsync(out.fileno())
        now=os.fstat(fd)
        if (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)!=(now.st_dev,now.st_ino,now.st_size,now.st_mtime_ns,now.st_ctime_ns):
            raise ValueError("source changed during relay")
        if file_sha(fd,size)!=old_digest:raise ValueError("source fingerprint changed")
        if destination.exists():raise FileExistsError("research output must be new")
        os.replace(tmp,destination);tmp=None
        return {"source_sha256":old_digest.hex(),"destination_sha256":output_sha(destination).hex(),
                "old_bytes":size,"new_bytes":destination.stat().st_size,
                "live":len(keep),"dead":len(idx["blobs"])-len(keep),"depth":depth,
                "physical_read_bytes_estimate":3*size+sum(pr.BHDR.size+b[4]+b[2] for b in idx["blobs"]),
                "elapsed_ms":round((time.perf_counter_ns()-started)/1e6,3)}
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)
        os.close(fd)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source");p.add_argument("destination");a=p.parse_args()
    print(json.dumps(relay(a.source,a.destination),sort_keys=True))
