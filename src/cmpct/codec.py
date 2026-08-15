#!/usr/bin/env python3
from __future__ import annotations
"""CMPCT v0.24 codec/representation primitives: content-addressed, recursive, codec-aware archive.

Design footnotes are intentionally kept in the code. This implementation is both a working
prototype and executable documentation for a future native implementation.

Core ideas:
  * Logical files are separated from physical blobs, so identical payloads are stored once.
  * ZIP/WHL members can be virtualized losslessly when their Deflate streams are reproducible;
    their container bytes are reconstructed exactly from a skeleton + referenced raw payloads.
  * PCM WAV data uses FLAC internally, while the original WAV prefix/suffix bytes are retained,
    so extraction reproduces the original WAV byte-for-byte.
  * General data uses Zstandard; large logical files are chunked for range reads.
  * The index exists at both the head and tail. Blob records are self-describing and hashed,
    allowing content salvage even when indexes are damaged.
  * A normal Deflate ZIP can be exported on demand for legacy compatibility. Compatibility is
    therefore an endpoint, not permanent storage overhead in every CMPCT archive.
"""
import argparse, base64, binascii, concurrent.futures, ctypes, ctypes.util, hashlib, io, json, os, shutil, stat, struct, sys, tempfile, time, zipfile, zlib, threading, subprocess, mmap
from dataclasses import dataclass
from pathlib import Path
import msgpack

MAGIC=b'CMPCT24\0'; FMAGIC=b'CMPTF24\0'; BMAGIC=b'CMA4'
VERSION=24
# Header: magic, version, flags, primary-index compressed/uncompressed bytes, data span, index SHA.
HDR=struct.Struct('<8sHHQQQ32s')
# Blob record: magic, codec, flags, reserved, usize, csize, meta_len, SHA-256.
BHDR=struct.Struct('<4sBBHQQII32s')
# Footer: magic, tail-index compressed/uncompressed bytes, index SHA. Tail index begins immediately before footer.
FTR=struct.Struct('<8sBBBBQQQ32s')
CODEC_RAW=0; CODEC_ZSTD=1; CODEC_WAVFLAC=2; CODEC_ZSTDDICT=3; CODEC_DEFLATE=4
K_FILE=0; K_DIR=1; K_SYMLINK=2; K_HARDLINK=3
TEXT_EXT={'.py','.md','.json','.txt','.toml','.yaml','.yml','.sh','.example','.ini','.cfg','.csv','.xml','.html','.css','.js','.ts'}
S_BLOB=0; S_CHUNKS=1; S_VZIP=2; S_SPARSE=3; S_PACK=4; S_CDC=5
CHUNK=256*1024
CDC_MIN=128*1024; CDC_AVG=512*1024; CDC_MAX=2*1024*1024

# --- Zstandard through the system library ----------------------------------
_z=ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so')
_sz=ctypes.c_size_t
_z.ZSTD_compressBound.argtypes=[_sz];_z.ZSTD_compressBound.restype=_sz
_z.ZSTD_compress.argtypes=[ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.c_int];_z.ZSTD_compress.restype=_sz
_z.ZSTD_decompress.argtypes=[ctypes.c_void_p,_sz,ctypes.c_void_p,_sz];_z.ZSTD_decompress.restype=_sz
_z.ZSTD_isError.argtypes=[_sz];_z.ZSTD_isError.restype=ctypes.c_uint
_z.ZSTD_getErrorName.argtypes=[_sz];_z.ZSTD_getErrorName.restype=ctypes.c_char_p
_z.ZSTD_createCCtx.argtypes=[];_z.ZSTD_createCCtx.restype=ctypes.c_void_p
_z.ZSTD_freeCCtx.argtypes=[ctypes.c_void_p];_z.ZSTD_freeCCtx.restype=_sz
_z.ZSTD_createDCtx.argtypes=[];_z.ZSTD_createDCtx.restype=ctypes.c_void_p
_z.ZSTD_freeDCtx.argtypes=[ctypes.c_void_p];_z.ZSTD_freeDCtx.restype=_sz
_z.ZSTD_compress_usingDict.argtypes=[ctypes.c_void_p,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.c_int];_z.ZSTD_compress_usingDict.restype=_sz
_z.ZSTD_decompress_usingDict.argtypes=[ctypes.c_void_p,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz];_z.ZSTD_decompress_usingDict.restype=_sz
_z.ZSTD_createDDict.argtypes=[ctypes.c_void_p,_sz];_z.ZSTD_createDDict.restype=ctypes.c_void_p
_z.ZSTD_freeDDict.argtypes=[ctypes.c_void_p];_z.ZSTD_freeDDict.restype=_sz
_z.ZSTD_decompress_usingDDict.argtypes=[ctypes.c_void_p,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.c_void_p];_z.ZSTD_decompress_usingDDict.restype=_sz

# libdeflate is used only as a faster decoder for exact Deflate streams inherited from ZIP.
# The stored bytes remain ordinary raw Deflate, so this is an implementation acceleration, not a new codec.
# libdeflate is an accelerator, not a format dependency. Readers fall back to Python/zlib when it
# is absent so a CMPCT archive never becomes unreadable merely because an optional native library
# was not installed on a new machine.
_ld=None
try:
    _ld_path=ctypes.util.find_library('deflate')
    if _ld_path:
        _ld=ctypes.CDLL(_ld_path)
        _ld.libdeflate_alloc_decompressor.argtypes=[];_ld.libdeflate_alloc_decompressor.restype=ctypes.c_void_p
        _ld.libdeflate_free_decompressor.argtypes=[ctypes.c_void_p];_ld.libdeflate_free_decompressor.restype=None
        _ld.libdeflate_deflate_decompress.argtypes=[ctypes.c_void_p,ctypes.c_void_p,_sz,ctypes.c_void_p,_sz,ctypes.POINTER(_sz)];_ld.libdeflate_deflate_decompress.restype=ctypes.c_int
except OSError:
    _ld=None

def _zck(n:int)->int:
    if _z.ZSTD_isError(n): raise RuntimeError(_z.ZSTD_getErrorName(n).decode())
    return int(n)
def zc(data:bytes, level:int)->bytes:
    if not data:return b''
    src=ctypes.create_string_buffer(data);cap=int(_z.ZSTD_compressBound(len(data)));dst=ctypes.create_string_buffer(cap)
    n=_zck(_z.ZSTD_compress(dst,cap,src,len(data),level));return dst.raw[:n]
def zd(data:bytes, usize:int)->bytes:
    if usize==0:return b''
    src=ctypes.create_string_buffer(data);dst=ctypes.create_string_buffer(usize)
    n=_zck(_z.ZSTD_decompress(dst,usize,src,len(data)))
    if n!=usize:raise IOError(f'Zstd size mismatch: {n} != {usize}')
    return dst.raw[:n]

def sha(b:bytes)->bytes:return hashlib.sha256(b).digest()

# --- Content-defined chunking ----------------------------------------------
# A tiny native helper keeps creation throughput high on multi-gigabyte files. The *format* does not
# depend on this helper: every CDC file records explicit [logical_length, blob_ref] pairs, so a reader
# never needs to know how boundaries were chosen. If the helper is absent we fall back to fixed chunks
# rather than making an archive unreadable or refusing to run on an unfamiliar platform.
_cdc=None
try:
    _cdc_path=Path(__file__).with_name('libcmpct_cdc.so')
    if _cdc_path.exists():
        _cdc=ctypes.CDLL(str(_cdc_path))
        _cdc.cmpct_cdc_cut.argtypes=[ctypes.c_void_p,_sz,_sz,_sz,_sz,ctypes.POINTER(ctypes.c_uint64),_sz]
        _cdc.cmpct_cdc_cut.restype=_sz
except OSError:
    _cdc=None

def cdc_chunks(data:bytes,min_size:int=CDC_MIN,avg_size:int=CDC_AVG,max_size:int=CDC_MAX):
    """Return byte slices using stable content-defined boundaries.

    Footnote: content-defined boundaries preserve deduplication after insertions/deletions because the
    next boundary is rediscovered from nearby content rather than from an absolute file offset. This is
    especially useful for VM images, databases, source bundles and successive file versions. The native
    helper is an encoder optimization only; fixed chunks remain a fully compatible fallback.
    """
    if len(data)<=max_size or _cdc is None:
        return [data[i:i+CHUNK] for i in range(0,len(data),CHUNK)]
    cap=max(4,len(data)//max(1,min_size)+4);ends=(ctypes.c_uint64*cap)();buf=ctypes.create_string_buffer(data)
    n=int(_cdc.cmpct_cdc_cut(buf,len(data),min_size,avg_size,max_size,ends,cap))
    if n<=0:return [data[i:i+CHUNK] for i in range(0,len(data),CHUNK)]
    out=[];p=0
    for i in range(n):
        q=int(ends[i])
        if q<=p or q>len(data):return [data[j:j+CHUNK] for j in range(0,len(data),CHUNK)]
        out.append(data[p:q]);p=q
    if p!=len(data):out.append(data[p:])
    return out


def zcd(data:bytes, dictionary:bytes, level:int)->bytes:
    if not data:return b''
    src=ctypes.create_string_buffer(data);db=ctypes.create_string_buffer(dictionary);cap=int(_z.ZSTD_compressBound(len(data)));dst=ctypes.create_string_buffer(cap);ctx=_z.ZSTD_createCCtx()
    try:n=_zck(_z.ZSTD_compress_usingDict(ctx,dst,cap,src,len(data),db,len(dictionary),level));return dst.raw[:n]
    finally:_z.ZSTD_freeCCtx(ctx)
def zdd(data:bytes, usize:int, dictionary:bytes)->bytes:
    if usize==0:return b''
    src=ctypes.create_string_buffer(data);db=ctypes.create_string_buffer(dictionary);dst=ctypes.create_string_buffer(usize);ctx=_z.ZSTD_createDCtx()
    try:
        n=_zck(_z.ZSTD_decompress_usingDict(ctx,dst,usize,src,len(data),db,len(dictionary)))
        if n!=usize:raise IOError(f'Zstd-dict size mismatch: {n} != {usize}')
        return dst.raw[:n]
    finally:_z.ZSTD_freeDCtx(ctx)

def _audio_modules():
    # Heavy scientific/audio modules are imported only when a file actually selects the FLAC codec.
    # Fast profiles with reusable Deflate WAV streams pay zero heavy-module import cost.
    import numpy as np
    import soundfile as sf
    return np,sf

def _wav_parts(raw:bytes):
    # We preserve all non-audio bytes verbatim rather than trusting a WAV writer to recreate them.
    if len(raw)<44 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':return None
    p=12;fmt=None;data=None
    while p+8<=len(raw):
        cid=raw[p:p+4];n=struct.unpack_from('<I',raw,p+4)[0];start=p+8;end=start+n
        if end>len(raw):return None
        if cid==b'fmt ':fmt=raw[start:end]
        if cid==b'data':data=(start,end);break
        p=end+(n&1)
    if not fmt or data is None or len(fmt)<16:return None
    af,ch,rate,br,ba,bits=struct.unpack_from('<HHIIHH',fmt,0)
    if af!=1 or bits not in (8,16,24,32):return None
    start,end=data;return raw[:start],raw[start:end],raw[end:],ch,rate,bits

def wavflac_compress(raw:bytes):
    np,sf=_audio_modules();parts=_wav_parts(raw)
    if not parts:return None
    prefix,pcm,suffix,ch,rate,bits=parts
    if bits==16:arr=np.frombuffer(pcm,dtype='<i2');sub='PCM_16'
    elif bits==32:arr=np.frombuffer(pcm,dtype='<i4');sub='PCM_32'
    elif bits==8:
        # WAV PCM8 is unsigned while libsndfile integer arrays are signed; not enabled by the current exact WAV-FLAC path.
        return None
    else:
        # 24-bit exact handling is deliberately deferred rather than silently risking altered bytes.
        return None
    if ch>1:arr=arr.reshape(-1,ch)
    bio=io.BytesIO();sf.write(bio,arr,rate,format='FLAC',subtype=sub,compression_level=1.0)
    meta=msgpack.packb([prefix,suffix,ch,rate,bits],use_bin_type=True)
    return bio.getvalue(),meta
def wavflac_decompress(comp:bytes, meta:bytes)->bytes:
    np,sf=_audio_modules();prefix,suffix,ch,rate,bits=msgpack.unpackb(meta,raw=False)
    dtype='int16' if bits==16 else 'int32'
    arr,r=sf.read(io.BytesIO(comp),dtype=dtype,always_2d=(ch>1))
    if r!=rate:raise IOError('FLAC sample-rate mismatch')
    pcm=np.asarray(arr,dtype='<i2' if bits==16 else '<i4').tobytes()
    return bytes(prefix)+pcm+bytes(suffix)

# --- Exact nested ZIP virtualization --------------------------------------
LFH=struct.Struct('<IHHHHHIIIHH'); LFHS=0x04034B50
ZCDH=struct.Struct('<IHHHHHHIIIHHHHHII'); ZEOCD=struct.Struct('<IHHHHIIH')

def _compressed_payload(ap:Path, zi:zipfile.ZipInfo)->bytes:
    with open(ap,'rb') as f:
        f.seek(zi.header_offset);v=LFH.unpack(f.read(LFH.size));nl,xl=v[-2],v[-1];f.seek(nl+xl,1);return f.read(zi.compress_size)

def deflate_level_for(raw:bytes, target:bytes):
    for level in range(10):
        co=zlib.compressobj(level,zlib.DEFLATED,-15);got=co.compress(raw)+co.flush()
        if got==target:return level
    return None

def make_vzip_recipe(ap:Path, add_content):
    original=ap.read_bytes(); infos=[]
    with zipfile.ZipFile(ap) as z:
        infos=sorted([i for i in z.infolist() if not i.is_dir()],key=lambda x:x.header_offset)
        payloads=[]; spans=[]
        with open(ap,'rb') as f:
            for zi in infos:
                f.seek(zi.header_offset);v=LFH.unpack(f.read(LFH.size));nl,xl=v[-2],v[-1];start=zi.header_offset+LFH.size+nl+xl;end=start+zi.compress_size
                raw=z.read(zi);stream=original[start:end]
                if zi.compress_type==zipfile.ZIP_STORED:
                    cref=add_content(raw,Path(zi.filename).suffix.lower());stream_hash=b'';level=-1
                elif zi.compress_type==zipfile.ZIP_DEFLATED:
                    # v0.18 records the deterministic zlib level even when it also retains the exact stream.
                    # This lets the builder drop cold/small Deflate streams without losing byte-exact ZIP rebuilds.
                    level=deflate_level_for(raw,stream)
                    if level is None:return None
                    cref=add_content(raw,Path(zi.filename).suffix.lower(),stream);stream_hash=sha(stream)
                else:return None
                spans.append((start,end));payloads.append([cref,zi.compress_type,stream_hash,len(stream),level])
    literals=[];cursor=0
    for start,end in spans:literals.append(original[cursor:start]);cursor=end
    literals.append(original[cursor:])
    skeleton=b''.join(literals);lens=[len(x) for x in literals]
    skref=add_content(skeleton,'.cmpct-skeleton')
    return [skref,lens,payloads,sha(original),len(original),binascii.crc32(original)&0xffffffff]

def rebuild_vzip(recipe,get_content,get_stream)->bytes:
    skref,lens,payloads,want_sha,want_size,want_crc=recipe;sk=get_content(skref)
    cps=[]
    for rawref,method,stream_mode,streamref,csize,level in payloads:
        if method==zipfile.ZIP_STORED:cps.append(get_content(rawref))
        else:
            cp=get_stream(stream_mode,streamref,level)
            if len(cp)!=csize:raise IOError('virtual ZIP compressed-stream size mismatch')
            cps.append(cp)
    out=[];p=0
    for i,cp in enumerate(cps):n=lens[i];out.append(sk[p:p+n]);p+=n;out.append(cp)
    n=lens[-1];out.append(sk[p:p+n]);res=b''.join(out)
    if len(res)!=want_size or (binascii.crc32(res)&0xffffffff)!=want_crc:raise IOError('virtual ZIP reconstruction mismatch')
    return res

def range_vzip(recipe,get_content,get_stream,start:int,length:int)->bytes:
    """Return an exact byte range from a virtual ZIP without rebuilding the whole nested archive."""
    skref,lens,payloads,want_sha,want_size,want_crc=recipe;end=start+length
    if start<0 or length<0 or end>want_size:raise ValueError('range outside virtual ZIP')
    sk=get_content(skref);out=[];outpos=0;skpos=0
    for i,pr in enumerate(payloads):
        ln=lens[i]
        if outpos+ln>start and outpos<end:
            a=max(start,outpos)-outpos;b=min(end,outpos+ln)-outpos;out.append(sk[skpos+a:skpos+b])
        outpos+=ln;skpos+=ln
        rawref,method,stream_mode,streamref,csize,level=pr
        if outpos+csize>start and outpos<end:
            seg=get_content(rawref) if method==zipfile.ZIP_STORED else get_stream(stream_mode,streamref,level)
            a=max(start,outpos)-outpos;b=min(end,outpos+csize)-outpos;out.append(seg[a:b])
        outpos+=csize
        if outpos>=end:return b''.join(out)
    ln=lens[-1]
    if outpos+ln>start and outpos<end:
        a=max(start,outpos)-outpos;b=min(end,outpos+ln)-outpos;out.append(sk[skpos+a:skpos+b])
    return b''.join(out)

def _sparse_data_extents(path:Path, size:int):
    """Return [(offset, bytes), ...] when a regular file is meaningfully sparse.

    Footnote: SEEK_DATA/SEEK_HOLE report allocated data extents without reading holes. We use
    ``st_blocks`` as a cheap prefilter and fall back cleanly on filesystems that do not implement
    the seek operations. A sparse representation is chosen only when it avoids at least 25% of
    logical bytes, so ordinary files never pay sparse-map metadata for no reason.
    """
    if size < 1024*1024 or not hasattr(os,'SEEK_DATA') or not hasattr(os,'SEEK_HOLE'):return None
    st=path.stat()
    allocated=getattr(st,'st_blocks',0)*512
    if not allocated or allocated >= size*0.75:return None
    fd=os.open(path,os.O_RDONLY);ext=[];pos=0
    try:
        while pos<size:
            try:data_off=os.lseek(fd,pos,os.SEEK_DATA)
            except OSError as e:
                if e.errno in (6,19,22,95):break  # ENXIO/ENODEV/EINVAL/ENOTSUP-ish portability fallback.
                raise
            if data_off>=size:break
            try:hole=os.lseek(fd,data_off,os.SEEK_HOLE)
            except OSError:return None
            hole=min(hole,size);left=hole-data_off;buf=[];q=data_off
            while left:
                n=min(left,4*1024*1024);b=os.pread(fd,n,q)
                if not b:break
                buf.append(b);q+=len(b);left-=len(b)
            ext.append((data_off,b''.join(buf)));pos=max(hole,data_off+1)
    finally:os.close(fd)
    data_bytes=sum(len(b) for _,b in ext)
    return ext if data_bytes < size*0.75 else None

def _hash_sparse(size:int, extents):
    """SHA-256 the logical sparse byte stream without ever materializing its holes."""
    h=hashlib.sha256();zero=b'\0'*(1024*1024);pos=0
    def zeros(n):
        while n:
            q=min(n,len(zero));h.update(zero[:q]);n-=q
    for off,b in extents:
        if off>pos:zeros(off-pos)
        h.update(b);pos=off+len(b)
    if pos<size:zeros(size-pos)
    return h.digest()

# --- Builder ---------------------------------------------------------------