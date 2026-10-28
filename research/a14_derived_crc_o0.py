#!/usr/bin/env python3
"""A14 O0 research-only: exact fixed-stride derived CRC32 fields, NOT CMPCT product.

Frozen question: docs/v031-research/2026-10-28-a14-derived-crc-o0-prereg.md.
Never treat checksum equality as authentication or content identity.
"""
from __future__ import annotations
import hashlib
import json
import lzma
import random
import shutil
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

MAGIC=b'CFOLD001'
HEADER=struct.Struct('<8sHHBQQ32s')
WIDTHS=range(16,257,4)
MAX_RECORDS=2_000_000


def run_zstd(data:bytes, *, decompress:bool=False)->bytes:
    command=['zstd','-q','-c']
    if decompress:command.insert(1,'-d')
    else:command.insert(1,'-19')
    out=subprocess.run(command,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    return out.stdout


def field_positions(width:int):
    return sorted({0,4,width-4})


def crc_bytes(payload:bytes,endian:int)->bytes:
    return int(zlib.crc32(payload)).to_bytes(4,'little' if endian==0 else 'big')


def bytes_for(seed:int, n:int)->bytes:
    # SHA256 deterministic test vectors: independent of filesystem, OS, Python PRNG internals.
    out=bytearray(); i=0
    while len(out)<n:
        out.extend(hashlib.sha256(struct.pack('<QQ',seed,i)).digest());i+=1
    return bytes(out[:n])


def make_case(seed:int,width:int,count:int,offset:int,endian:int,*,kind:str)->bytes:
    out=bytearray()
    for i in range(count):
        if kind=='random':body=bytes_for(seed*10_000+i,width-4)
        elif kind=='structured':
            prefix=(b'log-field-row:')+(i%512).to_bytes(4,'little')
            body=(prefix+bytes_for(seed+(i%8),8))*((width//len(prefix))+2)
            body=body[:width-4]
        elif kind=='none':body=bytes_for(seed*10_000+i,width)
        else:raise ValueError(kind)
        if kind=='none':out.extend(body);continue
        pos=offset if kind!='varying' else (0 if i%2==0 else width-4)
        checksum=crc_bytes(body,endian)
        out.extend(body[:pos]+checksum+body[pos:])
    return bytes(out)


def discover(raw:bytes)->tuple[tuple[int,int,int]|None,dict]:
    checks=0; candidates=0; full_validations=0
    for width in WIDTHS:
        if len(raw)%width:continue
        count=len(raw)//width
        if not count or count>MAX_RECORDS:continue
        for offset in field_positions(width):
            if offset+4>width:continue
            for endian in (0,1):
                candidates+=1
                matched=True
                for i in range(min(count,32)):
                    rec=raw[i*width:(i+1)*width]
                    checks+=1
                    if rec[offset:offset+4]!=crc_bytes(rec[:offset]+rec[offset+4:],endian):
                        matched=False;break
                if not matched:continue
                full_validations+=1
                for i in range(32,count):
                    rec=raw[i*width:(i+1)*width]
                    checks+=1
                    if rec[offset:offset+4]!=crc_bytes(rec[:offset]+rec[offset+4:],endian):
                        matched=False;break
                if matched:return (width,offset,endian),{'candidates_considered':candidates,'crc_checks':checks,'full_validations':full_validations}
    return None,{'candidates_considered':candidates,'crc_checks':checks,'full_validations':full_validations}


def pack(raw:bytes, params:tuple[int,int,int])->bytes:
    width,offset,endian=params
    if width not in WIDTHS or offset not in field_positions(width) or endian not in (0,1):raise ValueError('layout')
    if len(raw)%width:raise ValueError('stride')
    count=len(raw)//width
    if count<1 or count>MAX_RECORDS:raise ValueError('count')
    bod=bytearray()
    for i in range(count):
        rec=raw[i*width:(i+1)*width]
        prefix=rec[:offset]+rec[offset+4:]
        if rec[offset:offset+4]!=crc_bytes(prefix,endian):raise ValueError('crc mismatch')
        bod.extend(prefix)
    enc=run_zstd(bytes(bod))
    hdr=HEADER.pack(MAGIC,width,offset,endian,count,len(enc),hashlib.sha256(raw).digest())
    return hdr+enc


def unpack(artifact:bytes)->bytes:
    if len(artifact)<HEADER.size:raise ValueError('truncated header')
    magic,width,offset,endian,count,enc_len,digest=HEADER.unpack_from(artifact)
    if magic!=MAGIC or width not in WIDTHS or offset not in field_positions(width) or endian not in (0,1) or not 1<=count<=MAX_RECORDS:
        raise ValueError('header')
    if enc_len!=len(artifact)-HEADER.size:raise ValueError('compressed-length mismatch')
    raw_body=run_zstd(artifact[HEADER.size:],decompress=True)
    if len(raw_body)!=count*(width-4):raise ValueError('decompressed-length mismatch')
    out=bytearray()
    for i in range(count):
        body=raw_body[i*(width-4):(i+1)*(width-4)]
        out.extend(body[:offset]+crc_bytes(body,endian)+body[offset:])
    if hashlib.sha256(out).digest()!=digest:raise ValueError('strong digest mismatch')
    return bytes(out)


def transpose(raw:bytes,width:int)->bytes:
    if len(raw)%width:raise ValueError('width')
    count=len(raw)//width
    return bytes(raw[r*width+c] for c in range(width) for r in range(count))


def detranspose(raw:bytes,width:int)->bytes:
    if len(raw)%width:raise ValueError('width')
    count=len(raw)//width
    return bytes(raw[c*count+r] for r in range(count) for c in range(width))


def benchmark(name:str, raw:bytes, width:int, *, positive:bool):
    t0=time.perf_counter_ns();params,stats=discover(raw); discovery_ms=(time.perf_counter_ns()-t0)/1e6
    row={'case':name,'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),
         'expected_positive':positive,'detected':list(params) if params else None,'discovery_ms':discovery_ms,**stats}
    if (params is not None)!=positive:raise AssertionError(f'bad admission {name}: {params}')
    if not positive:return row
    # Complete source exactness and independent stdlib CRC checks on all records.
    w,off,end=params
    assert len(raw)%w==0
    for r in range(len(raw)//w):
        seg=raw[r*w:(r+1)*w]
        assert seg[off:off+4]==crc_bytes(seg[:off]+seg[off+4:],end)
    t0=time.perf_counter_ns();encoded=pack(raw,params);row['fold_compress_ms']=(time.perf_counter_ns()-t0)/1e6
    t0=time.perf_counter_ns();decoded=unpack(encoded);row['fold_decode_ms']=(time.perf_counter_ns()-t0)/1e6
    assert decoded==raw
    t0=time.perf_counter_ns();zstd=run_zstd(raw);row['solid_zstd19_ms']=(time.perf_counter_ns()-t0)/1e6
    t0=time.perf_counter_ns();xz=lzma.compress(raw,format=lzma.FORMAT_XZ,preset=9);row['solid_xz9_ms']=(time.perf_counter_ns()-t0)/1e6
    t0=time.perf_counter_ns();trans=transpose(raw,width);zt=run_zstd(trans);row['transpose_zstd19_ms']=(time.perf_counter_ns()-t0)/1e6
    assert run_zstd(zstd,decompress=True)==raw
    assert lzma.decompress(xz)==raw
    assert detranspose(run_zstd(zt,decompress=True),width)==raw
    zt_size=len(zt)+12  # charge width and count, no metadata supplied for free
    options={'solid_zstd19':len(zstd),'solid_xz9':len(xz),'transposed_zstd19_charged':zt_size}
    best=min(options.values())
    row.update(fold_artifact_bytes=len(encoded),fold_header_bytes=HEADER.size,compressed_body_bytes=len(encoded)-HEADER.size,
               solid_zstd19_bytes=len(zstd),solid_xz9_bytes=len(xz),transpose_zstd19_charged_bytes=zt_size,
               best_control_bytes=best,best_control=min(options,key=options.get),fold_gain_bytes=best-len(encoded),
               fold_gain_percent=round((best-len(encoded))/best*100,6),
               artifact_sha256=hashlib.sha256(encoded).hexdigest(),reconstructed_sha256=hashlib.sha256(decoded).hexdigest())
    # Hardening controls: do not accept a valid-looking but forged artifact.
    tamper=[]
    def must_fail(label,mut):
        try:unpack(mut)
        except (ValueError, subprocess.CalledProcessError):tamper.append(label)
        else:raise AssertionError(f'tamper accepted: {name}/{label}')
    z=bytearray(encoded);z[0]^=1;must_fail('bad_magic',bytes(z))
    z=bytearray(encoded);z[10:12]=b'\xff\xff';must_fail('bad_offset',bytes(z))
    z=bytearray(encoded);z[21]^=1;must_fail('encoded_length_mismatch',bytes(z))
    z=bytearray(encoded);z[HEADER.size-1]^=1;must_fail('digest_mismatch',bytes(z))
    must_fail('truncate',encoded[:-1])
    z=bytearray(encoded);z[-1]^=1;must_fail('altered_payload',bytes(z))
    row['tamper_rejected']=tamper
    return row


def main():
    if shutil.which('zstd') is None:raise SystemExit('UNMEASURED: zstd CLI unavailable')
    specs=[('high_entropy_head_36',1401,36,8192,0,0,'random',True),
           ('high_entropy_tail_68',1402,68,4096,64,1,'random',True),
           ('high_entropy_internal_132',1403,132,2048,4,0,'random',True),
           ('structured_tail_68',1404,68,4096,64,0,'structured',True),
           ('no_crc_random_36',1405,36,8192,0,0,'none',False),
           ('late_corrupt_36',1406,36,8192,0,0,'random',False),
           ('variable_offset_68',1407,68,4096,0,0,'random',False)]
    result=[];t_start=time.perf_counter_ns()
    for name,seed,width,count,offset,endian,kind,positive in specs:
        raw=make_case(seed,width,count,offset,endian,kind=kind)
        if name=='late_corrupt_36':
            modified=bytearray(raw);modified[-width]^=1;raw=bytes(modified)
        if name=='variable_offset_68':
            # Recreate without changing payload content: even records CRC at head, odd at tail.
            raw=bytearray()
            for i in range(count):
                body=bytes_for(seed*10_000+i,width-4);pos=0 if i%2==0 else width-4
                raw+=body[:pos]+crc_bytes(body,endian)+body[pos:]
            raw=bytes(raw)
        row=benchmark(name,raw,width,positive=positive)
        result.append(row)
        print(f'{name}: '+(f"{row['fold_gain_percent']:+.3f}% vs {row['best_control']}" if positive else 'correctly rejected'),flush=True)
    positive=[r for r in result if r['expected_positive']]
    major=[r for r in positive if r['fold_gain_percent']>=5]
    decision='O0_STRUCTURAL_HEADROOM_ONLY' if len({(r['detected'][0],r['detected'][1]) for r in major})>=2 and any(r['case'].startswith('high_entropy') for r in major) else 'O0_HYPOTHESIS_FALSIFIED'
    version=subprocess.run(['zstd','--version'],capture_output=True,text=True,check=True).stdout.strip()
    record={'schema':'cmpct-a14-derived-crc-o0-v1','court':'local deterministic research oracle; no CMPCT product',
            'python':sys.version.split()[0], 'zstd_version':version, 'lzma_version':'Python stdlib liblzma',
            'header_struct':HEADER.format,'instrument_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sha256_algorithm':'sha256','crc_algorithm':'zlib.crc32',
            'search_widths':'16..256 step 4','sample_budget_per_candidate':32,
            'decision':decision,'total_elapsed_ms':(time.perf_counter_ns()-t_start)/1e6,'cases':result,
            'note':'O0 synthetic, search grammar predefined, no real held-out corpus; no released Reader, ZIP parity, or release claim'}
    out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('a14_derived_crc_o0_result.json')
    out.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('DECISION',decision,'OUTPUT',out)
if __name__=='__main__':main()
