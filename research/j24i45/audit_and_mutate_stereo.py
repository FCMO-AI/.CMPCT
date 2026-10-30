#!/usr/bin/env python3
"""J24I45 detached r24/FLAC verification and one-byte mutants; NO CMPCT imports."""
import argparse
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path
import msgpack
import numpy as np
import soundfile as sf
import zstandard

H=struct.Struct('<8sHHQQQ32s')
B=struct.Struct('<4sBBHQQII32s')
F=struct.Struct('<8sBBBBQQQ32s')
def sha(b): return hashlib.sha256(b).digest()

def main(root):
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['schema']=='j24i45-stereo-heldout-v1'
    result={}
    for kib in manifest['pcm_kib']:
        entry=manifest['records'][str(kib)]
        original=(root/f'source-{kib}k'/'capture.wav').read_bytes()
        raw=(root/f'builder-wav-{kib}k.cmpct').read_bytes()
        assert sha(original).hex()==entry['logical_sha256']
        assert sha(raw).hex()==entry['archive_sha256']
        magic,rev,flags,cs,us,span,ihash=H.unpack_from(raw)
        assert (magic,rev,flags)==(b'CMPCT24\0',24,0)
        index_bytes=zstandard.ZstdDecompressor().decompress(raw[H.size:H.size+cs],max_output_size=us)
        assert len(index_bytes)==us and sha(index_bytes)==ihash
        index=msgpack.unpackb(index_bytes,raw=False)
        assert len(index['files'])==1
        row=index['files'][0]
        assert row[0]=='capture.wav' and row[4]==len(original)
        tail=H.size+cs+span
        assert raw[tail:tail+cs]==raw[H.size:H.size+cs]
        assert len(raw)==tail+cs+F.size
        assert F.unpack_from(raw,tail+cs)==(b'CMPTF24\0',0,1,0,0,cs,us,0,ihash)
        if not entry['selected_flac']:
            result[str(kib)]={'selected_flac':False,'physical_authenticated':True}
            continue
        assert row[6]==[0,0] and len(index['blobs'])==1
        off,usize,csize,codec,meta_len=index['blobs'][0]
        assert (off,usize,codec)==(0,len(original),2)
        rec=H.size+cs
        bm,bc,bf,reserved,bu,bcsize,bm_len,crc,digest=B.unpack_from(raw,rec)
        assert (bm,bc,bf,reserved)==(b'CMA4',2,0,0)
        assert (bu,bcsize,bm_len)==(usize,csize,meta_len)
        assert span==B.size+meta_len+csize
        meta_start=rec+B.size
        prefix,suffix,channels,rate,bits=msgpack.unpackb(raw[meta_start:meta_start+meta_len],raw=False)
        assert (channels,rate,bits)==(2,48000,16)
        flac_start=meta_start+meta_len
        flac=raw[flac_start:flac_start+csize]
        assert len(flac)==csize and flac[:4]==b'fLaC'
        samples,sample_rate=sf.read(io.BytesIO(flac),dtype='int16',always_2d=True)
        assert sample_rate==48000 and samples.ndim==2 and samples.shape[1]==2
        decoded=bytes(prefix)+np.asarray(samples,dtype='<i2').tobytes(order='C')+bytes(suffix)
        assert decoded==original
        assert digest==sha(original) and crc==(zlib.crc32(original)&0xffffffff)
        mutants={}
        mdir=root/'mutants'
        mdir.mkdir(exist_ok=True)
        for name,pos in [('crc',rec+28),('magic',flac_start),('frame',flac_start+csize//2)]:
            altered=bytearray(raw)
            altered[pos]^=1
            assert len(altered)==len(raw)
            assert sum(a!=b for a,b in zip(altered,raw))==1
            output=mdir/f'{kib}-{name}.cmpct'
            output.write_bytes(altered)
            mutants[name]={'offset':pos,'sha256':sha(altered).hex()}
        result[str(kib)]={'selected_flac':True,'sha256':sha(decoded).hex(),
            'encoded_bytes':csize,'logical_bytes':len(original),'mutants':mutants}
    assert any(x['selected_flac'] for x in result.values())
    out={'schema':'j24i45-detached-physical-audit-v1','result':'PASS',
        'independent_of_cmpct_import':True,'cases':result}
    (root/'detached-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('J24I45_DETACHED_PASS',sum(x['selected_flac'] for x in result.values()),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--case-dir',required=True,type=Path)
    main(ap.parse_args().case_dir)
