#!/usr/bin/env python3
"""J24I45: independent held-out stereo PCM16 Builder admission; never force codec."""
import argparse
import hashlib
import json
import wave
from pathlib import Path

import numpy as np
from cmpct.builder import Builder
from cmpct.reader import CMPCT

SIZES_KIB=(2048,8192)
SEED=24145
def sha(b): return hashlib.sha256(b).hexdigest()

def write_wav(path, kib):
    rng=np.random.default_rng(SEED+kib)
    left=0
    offset=0
    remain=kib*1024//4
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        while remain:
            n=min(32768,remain)
            steps=rng.integers(-80,81,size=n,dtype=np.int16).astype(np.int64)
            cum=np.cumsum(steps,dtype=np.int64)
            lhs=((cum+left)&65535).astype('<u2').view('<i2')
            left=(left+int(cum[-1]))&65535
            ix=np.arange(offset,offset+n,dtype=np.int64)
            noise=rng.integers(-40,41,size=n,dtype=np.int16).astype(np.int64)
            rhs=((((ix*19)%8192)-4096+noise)&65535).astype('<u2').view('<i2')
            pcm=np.empty((n,2),dtype='<i2')
            pcm[:,0]=lhs
            pcm[:,1]=rhs
            wav.writeframesraw(pcm.tobytes(order='C'))
            offset+=n
            remain-=n

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,required=True)
    root=ap.parse_args().output
    root.mkdir(parents=True,exist_ok=True)
    records={}
    for kib in SIZES_KIB:
        tree=root/f'source-{kib}k'
        tree.mkdir(exist_ok=True)
        wav=tree/'capture.wav'
        write_wav(wav,kib)
        original=wav.read_bytes()
        assert len(original)==kib*1024+44
        archive=root/f'builder-wav-{kib}k.cmpct'
        details=Builder(tree,workers=1,reproducible=True).build(archive)
        encoded=archive.read_bytes()
        with CMPCT(archive) as reader:
            assert len(reader.files)==1
            row=reader.by['capture.wav']
            assert row[4]==len(original)
            assert reader.read_range('capture.wav',0,len(original))==original
            assert reader.verify()==1
            direct=row[6]==[0,0] and len(reader.blobs)==1
            codec=int(reader.blobs[0][3]) if direct else None
        selected=bool(direct and codec==2)
        records[str(kib)]=dict(pcm_kib=kib,logical_bytes=len(original),logical_sha256=sha(original),
            archive_bytes=len(encoded),archive_sha256=sha(encoded),direct=direct,codec=codec,
            selected_flac=selected,builder_summary=details)
        print('J24I45_ADMISSION',kib,codec,selected,flush=True)
    manifest=dict(schema='j24i45-stereo-heldout-v1',pcm_kib=list(SIZES_KIB),seed=SEED,
        channels=2,rate=48000,bits=16,selection_unmodified=True,records=records)
    (root/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    count=sum(int(r['selected_flac']) for r in records.values())
    print('J24I45_ADMISSION_TOTAL',count,flush=True)
    assert count>0,'Builder selected no direct FLAC: record admission failure, no forcing'

if __name__=='__main__': main()
