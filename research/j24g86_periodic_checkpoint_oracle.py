#!/usr/bin/env python3
"""J24G86: no-CMPCT fully charged r24 checkpoint-density oracle.

Input: original J24G83 detached ZIP (sha pinned). The tool unpacks the
nested original-hosted archive, replays original 63 signed deletes, and
simulates full signed index checkpoints on the same physical source.
No product, benchmark or artifact-compatibility credit.
"""
import ctypes
import ctypes.util
import hashlib
import io
import json
import pathlib
import struct
import sys
import time
import zipfile
import msgpack

ROOT_SHA = '6d0542f0938740a0d82acb0e3f1a57a46fffc9ecafcc6c4bea79187cc607e016'
HEADER = struct.Struct('<8sHHQQQ32s')
FOOTER = struct.Struct('<8sBBBBQQQ32s')
Z = ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')
Z.ZSTD_decompress.argtypes=(ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t)
Z.ZSTD_decompress.restype=ctypes.c_size_t
Z.ZSTD_compressBound.argtypes=(ctypes.c_size_t,)
Z.ZSTD_compressBound.restype=ctypes.c_size_t
Z.ZSTD_compress.argtypes=(ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int)
Z.ZSTD_compress.restype=ctypes.c_size_t
Z.ZSTD_isError.argtypes=(ctypes.c_size_t,)
Z.ZSTD_isError.restype=ctypes.c_uint

def sha(data): return hashlib.sha256(data).hexdigest()

def unpack(payload,plain,codec):
    if codec == 0:
        assert len(payload) == plain
        return payload
    assert codec == 1 and 0 < plain <= 16_000_000
    dst=ctypes.create_string_buffer(plain)
    src=ctypes.create_string_buffer(payload)
    n=Z.ZSTD_decompress(dst,plain,src,len(payload))
    assert not Z.ZSTD_isError(n) and n == plain
    return dst.raw[:plain]

def compress(payload, level):
    cap=Z.ZSTD_compressBound(len(payload))
    dst=ctypes.create_string_buffer(cap)
    src=ctypes.create_string_buffer(payload)
    start=time.perf_counter_ns()
    n=Z.ZSTD_compress(dst,cap,src,len(payload),level)
    elapsed=time.perf_counter_ns()-start
    assert not Z.ZSTD_isError(n)
    out=dst.raw[:n]
    assert unpack(out,len(payload),1)==payload
    return {'level':level,'bytes':len(out),'encode_ns':elapsed}

def read_wire(data):
    magic,rev,flags,cs,us,span,index_sha=HEADER.unpack_from(data)
    assert magic==b'CMPCT24\x00' and rev==24 and flags==0
    body=unpack(data[HEADER.size:HEADER.size+cs],us,1)
    assert hashlib.sha256(body).digest()==index_sha
    original=msgpack.unpackb(body,raw=False)
    off=len(data)-FOOTER.size
    seen=set()
    backward=[]
    while True:
        assert off not in seen and HEADER.size+cs+span <= off <=len(data)-FOOTER.size
        seen.add(off)
        magic,kind,codec,flags,reserved,size,plain,prev,digest=FOOTER.unpack_from(data,off)
        assert magic==b'CMPTF24\x00' and kind in (0,1) and flags==reserved==0
        assert 0 < size <= off and 0 < plain <= 16_000_000 and 0 <= prev < off
        payload=unpack(data[off-size:off],plain,codec)
        assert hashlib.sha256(payload).digest()==digest
        backward.append({'offset':off,'kind':kind,'prev':prev,
                         'body_bytes':size,'object':msgpack.unpackb(payload,raw=False),
                         'raw_sha':sha(payload)})
        if prev==0: break
        off=prev
    chain=list(reversed(backward))
    assert len(chain)==65 and chain[0]['object']==original
    assert chain[0]['kind']==chain[-1]['kind']==0
    assert all(chain[i]['prev']==chain[i-1]['offset'] for i in range(1,65))
    assert all(chain[i]['kind']==1 for i in range(1,64))
    return original,chain

def measure(data,n):
    original,chain=read_wire(data)
    assert len(original['files'])==n and len(set(r[0] for r in original['files']))==n
    original_names=set(r[0] for r in original['files'])
    deleted=set()
    costs={}
    for g in range(1,65):
        if g<64:
            delta=chain[g]['object']
            assert set(delta)=={'blobs','ops'} and delta['blobs']==[]
            assert len(delta['ops'])==1 and delta['ops'][0][0]=='del'
            name=delta['ops'][0][1]
            assert name in original_names and name not in deleted
            deleted.add(name)
        else:
            target=set(r[0] for r in chain[g]['object']['files'])
            newly_removed=original_names-target-deleted
            assert len(newly_removed)==1
            deleted.update(newly_removed)
        index=dict(original)
        index['files']=[row for row in original['files'] if row[0] not in deleted]
        assert len(index['files'])==n-g
        if g==64:
            assert index==chain[g]['object']
            assert sha(msgpack.packb(index,use_bin_type=True))==chain[g]['raw_sha']
        if g in (8,16,24,32,40,48,56):
            packed=msgpack.packb(index,use_bin_type=True)
            values=[compress(packed,level) for level in (1,3,19)]
            best=min(values,key=lambda v:v['bytes'])
            costs[str(g)]={'index_members':len(index['files']),
                'full_index_decoded_bytes':len(packed),'codec_trials':values,
                'best_level':best['level'],'full_index_plus_footer_bytes':best['bytes']+FOOTER.size,
                'displaced_delta_plus_footer_bytes':chain[g]['body_bytes']+FOOTER.size,
                'net_added_bytes':best['bytes']-chain[g]['body_bytes']}
            assert costs[str(g)]['net_added_bytes']>0
    baseline=range(1,64)
    schedules={}
    for k in (8,16,32):
        selected=[g for g in range(k,64,k)]
        extra=sum(costs[str(g)]['net_added_bytes'] for g in selected)
        depth=[g%k for g in baseline]
        schedules[str(k)]={'checkpoints':selected,'extra_bytes':extra,
            'charged_complete_archive_bytes':len(data)+extra,
            'extra_percent':100*extra/len(data),
            'worst_remaining_deltas':max(depth),'mean_remaining_deltas':sum(depth)/len(depth),
            'relative_worst_delta_work':max(baseline)/max(depth),
            'research_gate':extra/len(data)<=0.05 and max(baseline)/max(depth)>=2}
    corrupt=bytearray(data)
    corrupt[chain[63]['offset']-1]^=0x40
    hostile_rejected=False
    try:read_wire(bytes(corrupt))
    except (AssertionError,ValueError,struct.error,msgpack.ExtraData):
        hostile_rejected=True
    assert hostile_rejected
    return {'sha256':sha(data),'archive_bytes':len(data),'initial_members':n,
        'footers_authenticated':len(chain),'final_full_checkpoint_matches':True,
        'signed_corruption_rejected':True,'periodic_index_cost':costs,
        'baseline_worst_deltas':63,'schedules':schedules}

def run(source):
    raw=pathlib.Path(source).read_bytes()
    assert sha(raw)==ROOT_SHA
    result={'schema':'j24g86-periodic-checkpoint-cost-o0','source_zip_sha256':ROOT_SHA,
            'classification':'research_oracle_only','cases':{}}
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read('j24g83_original_hosted_evidence.zip'))) as z:
            for case in ('8192-middle','32768-tail'):
                n=int(case.split('-')[0])
                data=z.read('j24g80-'+case+'-public-valid.cmpct')
                assert data==z.read('j24g80-'+case+'-owned-valid.cmpct')
                assert data==z.read('j24g83-'+case+'-fresh-valid.cmpct')
                result['cases'][case]=measure(data,n)
    result['decision']='AT_LEAST_ONE_CADENCE_SURVIVES' if any(
        all(result['cases'][case]['schedules'][k]['research_gate'] for case in result['cases'])
        for k in ('8','16','32')) else 'DENSE_FULL_CHECKPOINTS_TRIAGE_FAIL'
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__': run(sys.argv[1])
