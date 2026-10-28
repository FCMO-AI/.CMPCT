#!/usr/bin/env python3
"""A14-O1b: source-exact PNG/GZIP checksum-erasure oracle, NOT CMPCT product.
Preregistration: docs/v031-research/2026-10-28-a14-o1b-natural-checksum-prereg.md.
No source-file content or user pathname is emitted into the durable result.
"""
from __future__ import annotations
import argparse
import brotli
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time
import zlib

SIG=b'\x89PNG\r\n\x1a\n'
MAGIC=b'A14CRC01'
HEADER=struct.Struct('<8sBQQ32s')
LIMIT=8*1024*1024

class Unsupported(ValueError):
    pass

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def zstd(raw:bytes, decode:bool=False)->bytes:
    cmd=['zstd','-q','-c'] if decode else ['zstd','-q','-19','-c']
    if decode:cmd.insert(1,'-d')
    return subprocess.run(cmd,input=raw,capture_output=True,check=True).stdout

def png_parse(raw:bytes, *, strip:bool)->tuple[bytes,int]:
    if not raw.startswith(SIG):raise Unsupported('bad PNG signature')
    out=bytearray(SIG);p=len(SIG);chunks=0;ended=False
    while p<len(raw):
        if len(raw)-p<12:raise Unsupported('truncated chunk')
        n=struct.unpack_from('>I',raw,p)[0]
        if n>len(raw)-p-12:raise Unsupported('chunk bound')
        end=p+12+n
        ctype=raw[p+4:p+8]
        if len(ctype)!=4 or not all(65<=x<=90 or 97<=x<=122 for x in ctype):raise Unsupported('chunk type')
        chunk=raw[p+8:p+8+n]
        stored=raw[p+8+n:end]
        expected=struct.pack('>I',zlib.crc32(ctype+chunk))
        if stored!=expected:raise Unsupported('CRC mismatch')
        if ctype==b'IEND' and n!=0:raise Unsupported('IEND length')
        out.extend(raw[p:end-4] if strip else raw[p:end]);p=end;chunks+=1
        if ctype==b'IEND':ended=True;break
    if not ended:raise Unsupported('missing IEND')
    out.extend(raw[p:])  # faithfully preserve nonstandard trailing bytes, not synthesize them
    return bytes(out),chunks

def png_restore(body:bytes)->bytes:
    if not body.startswith(SIG):raise ValueError('bad PNG stripped signature')
    out=bytearray(SIG);p=len(SIG);ended=False
    while p<len(body):
        if len(body)-p<8:raise ValueError('truncated PNG stripped chunk')
        n=struct.unpack_from('>I',body,p)[0]
        if n>len(body)-p-8:raise ValueError('bad PNG stripped chunk bound')
        ctype=body[p+4:p+8];payload=body[p+8:p+8+n]
        if not all(65<=x<=90 or 97<=x<=122 for x in ctype):raise ValueError('invalid chunk type')
        out.extend(body[p:p+8+n]);out.extend(struct.pack('>I',zlib.crc32(ctype+payload)))
        p+=8+n
        if ctype==b'IEND':
            if n!=0:raise ValueError('bad IEND')
            ended=True;break
    if not ended:raise ValueError('missing IEND')
    out.extend(body[p:]);return bytes(out)

def gzip_payload_start(raw:bytes)->int:
    if len(raw)<18 or raw[:3]!=b'\x1f\x8b\x08':raise Unsupported('bad gzip header')
    flags=raw[3];p=10
    if flags&0xe0:raise Unsupported('reserved flags')
    if flags&4:
        if p+2>len(raw)-8:raise Unsupported('extra bound')
        n=struct.unpack_from('<H',raw,p)[0];p+=2+n
        if p>len(raw)-8:raise Unsupported('extra truncated')
    for mask in (8,16):
        if flags&mask:
            stop=raw.find(b'\0',p,len(raw)-8)
            if stop<0:raise Unsupported('unclosed gzip filename/comment')
            p=stop+1
    if flags&2:p+=2
    if p>len(raw)-8:raise Unsupported('gzip header overrun')
    return p

def raw_inflate(raw:bytes)->bytes:
    obj=zlib.decompressobj(wbits=-15)
    out=obj.decompress(raw,LIMIT+1)
    if len(out)>LIMIT or not obj.eof or obj.unused_data or obj.unconsumed_tail:raise Unsupported('raw Deflate invalid or expansion limit')
    out+=obj.flush()
    if len(out)>LIMIT:raise Unsupported('expansion limit')
    return out

def gzip_strip(raw:bytes)->tuple[bytes,int]:
    p=gzip_payload_start(raw)
    decoded=raw_inflate(raw[p:-8])
    correct=struct.pack('<II',zlib.crc32(decoded),len(decoded)&0xffffffff)
    if raw[-8:]!=correct:raise Unsupported('gzip footer mismatch')
    # independent gzip decoder checks header and complete member framing
    obj=zlib.decompressobj(wbits=31)
    independently=obj.decompress(raw,LIMIT+1)
    if len(independently)>LIMIT or not obj.eof or obj.unused_data or obj.unconsumed_tail or independently!=decoded:
        raise Unsupported('invalid or concatenated gzip')
    return raw[:-8],1

def gzip_restore(body:bytes)->bytes:
    p=gzip_payload_start(body+b'\0'*8)
    decoded=raw_inflate(body[p:])
    return body+struct.pack('<II',zlib.crc32(decoded),len(decoded)&0xffffffff)

def pack(raw:bytes,kind:int)->tuple[bytes,int]:
    if kind==1:body,count=png_parse(raw,strip=True)
    elif kind==2:body,count=gzip_strip(raw)
    else:raise ValueError('format')
    compressed=zstd(body)
    return HEADER.pack(MAGIC,kind,len(raw),len(compressed),hashlib.sha256(raw).digest())+compressed,count

def unpack(blob:bytes)->bytes:
    if len(blob)<HEADER.size:raise ValueError('truncated header')
    magic,kind,origsize,clen,digest=HEADER.unpack_from(blob)
    if magic!=MAGIC or kind not in (1,2) or clen!=len(blob)-HEADER.size or origsize>1_048_576:
        raise ValueError('invalid header')
    b=zstd(blob[HEADER.size:],decode=True)
    if kind==1:restored=png_restore(b)
    else:restored=gzip_restore(b)
    if len(restored)!=origsize or hashlib.sha256(restored).digest()!=digest:raise ValueError('digest/length mismatch')
    return restored

def selected_paths(suffix:str)->list[Path]:
    c=[]
    for root in (Path('/usr'),Path('/opt')):
        for dirname, dirs, files in os.walk(root,followlinks=False):
            dirs[:]=[n for n in dirs if not (Path(dirname)/n).is_symlink()]
            for f in files:
                if not f.lower().endswith(suffix):continue
                p=Path(dirname)/f
                try:
                    if p.is_symlink() or not p.is_file() or not 256<=p.stat().st_size<=1_048_576:continue
                except OSError:continue
                c.append(p)
    c.sort(key=lambda p:hashlib.sha256(str(p).encode('utf8',errors='surrogateescape')).digest())
    out=[];seen=set()
    for p in c:
        try:raw=p.read_bytes()
        except OSError:continue
        if not 256<=len(raw)<=1_048_576:continue
        digest=sha(raw)
        if digest in seen:continue
        seen.add(digest);out.append(p)
        if len(out)==64:break
    return out

def measure():
    output={'schema':'cmpct-a14-o1b-natural-crc-v1','tier':'format-aware held-out natural-data oracle, not product',
            'platform':platform.platform(),'python':platform.python_version(),'format_spec':'PNG chunk CRC32 and single-member GZIP CRC32/ISIZE',
            'header_bytes':HEADER.size,'results':[], 'selection':{},'t0_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    for kind,suffix in ((1,'.png'),(2,'.gz')):
        paths=selected_paths(suffix)
        output['selection'][suffix]={'selected':len(paths),'selection_manifest_sha256':sha(('\n'.join(sha(p.read_bytes()) for p in paths)).encode())}
        for idx,path in enumerate(paths):
            raw=path.read_bytes();start=time.perf_counter_ns()
            item={'family':'png' if kind==1 else 'gzip','id':f'{kind}:{idx:03d}','raw_sha256':sha(raw),'raw_bytes':len(raw)}
            try:
                artifact,count=pack(raw,kind)
                restored=unpack(artifact)
                if restored!=raw:raise AssertionError('roundtrip mismatch')
                item.update(status='admitted',field_count=count,crc_bytes_saved=(4*count if kind==1 else 8),
                    candidate_bytes=len(artifact),artifact_sha256=sha(artifact),roundtrip_sha256=sha(restored),
                    candidate_encode_ms=(time.perf_counter_ns()-start)/1e6)
                t=time.perf_counter_ns();q=unpack(artifact);item['candidate_decode_ms']=(time.perf_counter_ns()-t)/1e6
                if q!=raw:raise AssertionError('decode mismatch')
                controls={}
                for label,func in (('zstd19',zstd),('xz9',lambda x:lzma.compress(x,preset=9)),('brotli11',lambda x:brotli.compress(x,quality=11))):
                    t=time.perf_counter_ns();data=func(raw)
                    controls[label]={'bytes':len(data),'encode_ms':(time.perf_counter_ns()-t)/1e6,'sha256':sha(data)}
                winner=min(controls,key=lambda x:controls[x]['bytes'])
                base=controls[winner]['bytes']
                item.update(controls=controls,best_control=winner,best_control_bytes=base,
                     gain_bytes=base-len(artifact),gain_pct=100*(base-len(artifact))/base,
                     no_header_upper_bound_pct=100*(base-(len(artifact)-HEADER.size))/base,
                     raw_crc_opportunity_pct=100*item['crc_bytes_saved']/len(raw),
                     ratio_raw_crc_to_header=item['crc_bytes_saved']/HEADER.size)
            except (Unsupported, ValueError, subprocess.CalledProcessError) as exc:
                item.update(status='refused',reason=type(exc).__name__+': '+str(exc)[:90])
            output['results'].append(item)
    output['summary']={}
    for fam in ('png','gzip'):
        rows=[r for r in output['results'] if r['family']==fam]
        valid=[r for r in rows if r['status']=='admitted']
        positives=[r for r in valid if r['gain_pct']>=5]
        output['summary'][fam]={'selected':len(rows),'valid':len(valid),'refused':len(rows)-len(valid),
          'positive5_files':len(positives),'total_raw_bytes':sum(r['raw_bytes'] for r in valid),
          'total_crc_bytes':sum(r['crc_bytes_saved'] for r in valid),
          'total_candidate_bytes':sum(r['candidate_bytes'] for r in valid),
          'total_best_control_bytes':sum(r['best_control_bytes'] for r in valid),
          'sum_candidate_encode_ms':sum(r['candidate_encode_ms'] for r in valid),
          'sum_candidate_decode_ms':sum(r['candidate_decode_ms'] for r in valid),
          'no_header_crc_frac_percent':(100*sum(r['crc_bytes_saved'] for r in valid)/sum(r['raw_bytes'] for r in valid) if valid else None)}
        s=output['summary'][fam]
        s['aggregate_gain_pct']=(100*(s['total_best_control_bytes']-s['total_candidate_bytes'])/s['total_best_control_bytes'] if s['total_best_control_bytes'] else None)
    output['decision']='INSUFFICIENT_CORPUS' if any(z['valid']<16 for z in output['summary'].values()) else ('ADVANCE_O1B' if all(z['positive5_files']>=2 and z['aggregate_gain_pct']>=1 for z in output['summary'].values()) else 'PARK_FORMAT_CHECKSUM_FAMILY')
    output['t_end_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    output['instrument_sha256']=sha(Path(__file__).read_bytes())
    return output

def selftest():
    # Valid, exact positive controls generated for test only (not held-out corpus wins).
    png=SIG
    for kind,body in ((b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0)),(b'IDAT',zlib.compress(b'abc')),(b'IEND',b'')):
        png+=struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body))
    gz=gzip.compress(b'abc'*100,mtime=0)
    for kind,src in ((1,png),(2,gz)):
        blob,n=pack(src,kind);assert unpack(blob)==src
        mutations=[blob[:-1],b'Z'+blob[1:],blob[:18]+b'\xff'+blob[19:]]
        for bad in mutations:
            try:unpack(bad)
            except (ValueError,subprocess.CalledProcessError):pass
            else:raise AssertionError('tampered archive accepted')
    bad_png=bytearray(png);bad_png[31]^=1
    try:pack(bytes(bad_png),1)
    except Unsupported:pass
    else:raise AssertionError('corrupt PNG admitted')
    for bad in (gz[:-1],gz+b'bad',gz[:-8]+b'\0'*8):
        try:pack(bad,2)
        except (Unsupported,ValueError,zlib.error):pass
        else:raise AssertionError('invalid GZIP admitted')
    print('SELFTEST PASS: 2 exact roundtrips, 6 candidate mutations rejected, malformed PNG and GZIP rejected')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--selftest',action='store_true');parser.add_argument('--output',default='a14_o1b_result.json');a=parser.parse_args()
    if a.selftest:selftest()
    else:
        result=measure();Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'decision':result['decision'],'summary':result['summary']},indent=2))
