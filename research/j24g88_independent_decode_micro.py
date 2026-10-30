#!/usr/bin/env python3
"""Independent J24G88 CPU/control referee. Not installed Reader evidence.

Competing replay and bitmap/gap forms are evaluated after the original base
header was verified by the *independent physical* J24G86 wire parser. This
separates the already-paid root authentication from repeated reconstruction.
"""
import hashlib
import json
from pathlib import Path
import statistics
import struct
import sys
import time
import msgpack
import j24g86_periodic_checkpoint_oracle as wire

def varint(x):
    out=bytearray()
    while x>=128:out.append((x&127)|128);x>>=7
    out.append(x)
    return bytes(out)

def decode_gaps(raw,count,limit):
    output=[];index=0;prev=-1
    for _ in range(count):
        value=shift=0
        while True:
            if index>=len(raw):raise ValueError('truncated')
            b=raw[index];index+=1
            value|=(b&127)<<shift
            if b<128:break
            shift+=7
            if shift>28:raise ValueError('overflow')
        prev+=value+1
        if prev>=limit:raise ValueError('out of bounds')
        output.append(prev)
    if index!=len(raw):raise ValueError('trailing data')
    return output

def timed(fn,reps=101):
    fn();out=[]
    for _ in range(reps):
        st=time.perf_counter_ns();fn();out.append(time.perf_counter_ns()-st)
    return {'raw_ns':out,'median_ns':statistics.median(out)}

def case(directory,name):
    data=(directory/('j24g80-'+name+'-public-valid.cmpct')).read_bytes()
    original,chain=wire.read_wire(data)
    n=len(original['files']);assert n==int(name.split('-')[0])
    pos={r[0]:i for i,r in enumerate(original['files'])}
    removed=set()
    for i in range(1,33):
        op,member=chain[i]['object']['ops'][0]
        assert op=='del';removed.add(pos[member])
    assert len(removed)==32
    bitmap=bytearray([255])*((n+7)//8)
    for i in removed:bitmap[i//8]&=~(1<<(i%8))&255
    sorted_idx=sorted(removed);last=-1;pieces=[]
    for i in sorted_idx:pieces.append(varint(i-last-1));last=i
    gaps=b''.join(pieces)
    rows=original['files']
    def delta_set():
        d=set(removed)
        return [v for i,v in enumerate(rows) if i not in d]
    def bitset():
        return [v for i,v in enumerate(rows) if bitmap[i//8]&(1<<(i%8))]
    def gap_decode():
        d=set(decode_gaps(gaps,32,n))
        return [v for i,v in enumerate(rows) if i not in d]
    assert delta_set()==bitset()==gap_decode()
    results={k:timed(fn) for k,fn in [
        ('32_delta_set_control',delta_set),
        ('survivor_bitmap_preverified_root',bitset),
        ('sparse_deleted_ordinals_preverified_root',gap_decode)]}
    codec={}
    import subprocess
    for typ,raw in [('bitmap',bytes(bitmap)),('gap_vector',gaps)]:
        p=subprocess.run(['zstd','--ultra','-19','--stdout','--no-progress'],
                         input=raw,capture_output=True,check=True)
        inv=subprocess.run(['zstd','--decompress','--stdout','--no-progress'],
                           input=p.stdout,capture_output=True,check=True)
        assert inv.stdout==raw
        codec[typ]={'cli_level19_raw_payload_only_bytes':len(p.stdout),
                    'uncompressed_raw_payload_only_bytes':len(raw)}
    return {'physical_sha256':wire.sha(data),'original_members':n,'control_reconstructed_exactly':True,
            'micro_layer':'in-memory Python list reconstruction, no Reader/open/index decompression',
            'results':results,'cli_codec_raw_payload_only':codec}

def main(path,output):
    src=Path(path)
    report={'schema':'j24g88-preverified-root-independent-cpu-referee-v1',
            'source':'original #12978714378 physical wire, source identities in primary J24G88 artifact',
            'product_benchmark':False,'cases':{}}
    for label in ('8192-middle','32768-tail'):
        report['cases'][label]=case(src,label)
    Path(output).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    for label,x in report['cases'].items():
        print(label, [(k,round(v['median_ns']/1e6,4)) for k,v in x['results'].items()])
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: REF ORIGINAL_ARTIFACT_DIRECTORY OUTPUT_JSON')
    main(sys.argv[1],sys.argv[2])
