#!/usr/bin/env python3
"""O213 independent physical oracle for its archived genuine sparse r24 fixture.

Consumes the untouched GitHub Actions o213-one-original artifact ZIP.
Requires msgpack plus system libzstd; never imports or executes CMPCT product code.
Deliberately scoped to expected one-member S_SPARSE, 4096×4KiB Zstd blocks.
Does NOT implement a general CMPCT parser or independently attest a GitHub signer.
"""
import binascii
import ctypes
import ctypes.util
import hashlib
import json
import struct
import sys
import time
import zipfile
from pathlib import Path

import msgpack

HDR=struct.Struct('<8sHHQQQ32s')
BHDR=struct.Struct('<4sBBHQQII32s')
MIB=1<<20
GIB=1<<30


def sha(value):
    return hashlib.sha256(value).hexdigest()


def decompress_zstd(data, size):
    name=ctypes.util.find_library('zstd')
    if not name:
        raise RuntimeError('Independent oracle needs system libzstd')
    lib=ctypes.CDLL(name)
    lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
    lib.ZSTD_decompress.restype=ctypes.c_size_t
    lib.ZSTD_isError.argtypes=[ctypes.c_size_t]
    lib.ZSTD_isError.restype=ctypes.c_uint
    inp=ctypes.create_string_buffer(data)
    out=ctypes.create_string_buffer(size)
    n=lib.ZSTD_decompress(out,size,inp,len(data))
    if lib.ZSTD_isError(n) or n!=size:
        raise AssertionError(('invalid physical Zstd decoding',n,size))
    return out.raw[:size]


def verify(original_artifact, result_path):
    t0=time.perf_counter()
    with zipfile.ZipFile(original_artifact) as archive:
        assert archive.testzip() is None, 'GitHub artifact outer ZIP CRC failure'
        wire=archive.read('authentic-r24.cmpct')
        manifest=json.loads(archive.read('manifest.json'))
    assert sha(wire)==manifest['archive_sha256']
    magic,version,flags,csize,usize,span,digest=HDR.unpack_from(wire)
    assert (magic,version,flags)==(b'CMPCT24\0',24,0)
    assert csize<10*MIB and usize<20*MIB
    assert HDR.size+csize+span<=len(wire)
    decoded_index=decompress_zstd(wire[HDR.size:HDR.size+csize],usize)
    assert hashlib.sha256(decoded_index).digest()==digest
    index=msgpack.unpackb(decoded_index,raw=False,strict_map_key=False)
    assert index['v']==24 and len(index['files'])==1 and not index['recipes']
    file=index['files'][0]
    assert file[0]=='sparse.bin' and file[4]==4*GIB and file[6][0]==3
    blobs=index['blobs']; extents=file[6][1]
    assert len(blobs)==len(extents)==4096

    decoded_blobs=[]
    record_base=HDR.size+csize
    for j,(offset,usize,csize,codec,flags) in enumerate(blobs):
        assert 0<=offset<=span-BHDR.size
        magic,actual_codec,unused_flags,reserved,logical,compressed,meta_len,crc,checksum=BHDR.unpack_from(wire,record_base+offset)
        assert magic==b'CMA4' and reserved==0 and unused_flags==0
        assert actual_codec==codec==1
        assert logical==usize==4096 and compressed==csize and 0<=meta_len<=256
        assert offset+BHDR.size+meta_len+csize<=span
        payload=wire[record_base+offset+BHDR.size+meta_len:record_base+offset+BHDR.size+meta_len+csize]
        decoded=decompress_zstd(payload,logical)
        assert hashlib.sha256(decoded).digest()==checksum, ('physical SHA',j)
        assert binascii.crc32(decoded)&0xffffffff==crc, ('physical CRC',j)
        decoded_blobs.append(decoded)

    hasher=hashlib.sha256()
    logical_crc=0
    zeros=b'\0'*MIB
    prev_end=0; refs=0; decoded_data=0
    for j,(offset,length,indices) in enumerate(extents):
        assert isinstance(offset,int) and isinstance(length,int) and isinstance(indices,list)
        assert prev_end<=offset<4*GIB and 0<length<=4*GIB-offset
        assert sum(len(decoded_blobs[k]) for k in indices)==length, ('extent length mismatch',j)
        hole=offset-prev_end
        while hole:
            n=min(hole,MIB)
            part=zeros[:n]
            hasher.update(part)
            logical_crc=binascii.crc32(part,logical_crc)
            hole-=n
        for k in indices:
            assert 0<=k<len(decoded_blobs)
            part=decoded_blobs[k]
            hasher.update(part)
            logical_crc=binascii.crc32(part,logical_crc)
            refs+=1
        decoded_data+=length
        prev_end=offset+length
    hole=4*GIB-prev_end
    while hole:
        n=min(hole,MIB)
        part=zeros[:n]
        hasher.update(part)
        logical_crc=binascii.crc32(part,logical_crc)
        hole-=n
    assert hasher.digest()==file[5]
    assert hasher.hexdigest()==manifest['source_sha256']
    result={
        'schema':'cmpct-o213-independent-physical-sparse-oracle-v1',
        'verdict':'PASS_INDEPENDENT_4096_PHYSICAL_BLOB_INTEGRITY_AND_FULL_4GIB_LOGICAL_SHA',
        'archive_bytes':len(wire),'archive_sha256':sha(wire),
        'index_uncompressed_bytes':len(decoded_index),'index_sha256':sha(decoded_index),
        'sparse_extents':len(extents),'blob_count':len(blobs),
        'blob_codecs':{'zstd':len(blobs)},'physical_data_span_bytes':span,
        'physical_reference_count':refs,'decoded_physical_referenced_bytes':decoded_data,
        'full_logical_bytes':4*GIB,'source_sha256':hasher.hexdigest(),
        'full_logical_crc32':logical_crc&0xffffffff,
        'wall_s':time.perf_counter()-t0,
        'scope':'Original O213 GitHub artifact, independent physical validation; not general r24 conformance'}
    result_path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


if __name__=='__main__':
    data=verify(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps(data,sort_keys=True,indent=2))
