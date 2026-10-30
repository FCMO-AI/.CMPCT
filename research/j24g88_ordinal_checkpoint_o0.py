#!/usr/bin/env python3
"""J24G88: charged ordinal-survivor checkpoint O0, not a legal r24 archive.

Uses the existing independent r24 wire referee from J24G86, not CMPCT.
The input directory is the ORIGINAL J24G83 Actions artifact #12978714378
(source SHA pinned per physical archive). A hypothetical future Writer
*substitutes* a new-format checkpoint for generation32's existing delta;
nothing in this program rewrites or mutates original physical evidence.
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

SOURCE_SHA = {
    '8192-middle': '5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a',
    '32768-tail': '8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81',
}
ROOT_PTR = struct.pack('<Q', wire.HEADER.size)
BMP_TAG, GAP_TAG = b'ordinal-map-v1!!', b'ordinal-gaps-v1!'
assert len(BMP_TAG) == len(GAP_TAG) == 16

def sha(data):
    return hashlib.sha256(data).digest()

def varint(value):
    if value < 0: raise ValueError('negative gap')
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)

def unvarints(raw, count, limit):
    offsets=[]; prev=-1; pos=0
    for _ in range(count):
        val=shift=0
        for k in range(5):
            if pos>=len(raw): raise ValueError('truncated gap')
            byte=raw[pos]; pos+=1
            val |= (byte & 127) << shift
            if byte < 128: break
            shift+=7
        else: raise ValueError('overlong gap')
        if varint(val)!=raw[pos-k-1:pos]: raise ValueError('noncanonical gap')
        prev+=val+1
        if prev>=limit: raise ValueError('out-of-range ordinal')
        offsets.append(prev)
    if pos!=len(raw): raise ValueError('trailing bytes')
    return offsets

def descriptor(base, deleted, generation, typ):
    count=len(base['files'])
    assert len(deleted)==generation and all(0<=x<count for x in deleted)
    if typ=='bitmap':
        bits=bytearray([255])*((count+7)//8)
        for i in deleted: bits[i//8]&=~(1<<(i%8))&255
        if count%8: bits[-1]&=(1<<(count%8))-1
        field='survival_bitmap'; value=bytes(bits);tag=BMP_TAG
    elif typ=='gaps':
        prev=-1;chunks=[]
        for i in sorted(deleted):
            chunks.append(varint(i-prev-1)); prev=i
        field='deleted_ordinal_gaps';value=b''.join(chunks);tag=GAP_TAG
    else: raise ValueError('unknown descriptor')
    return {'type':tag,'base_index_sha256':sha(msgpack.packb(base,use_bin_type=True)),
            'base_index_offset_le64':ROOT_PTR,
            'base_file_count':count,'generation':generation,field:value}

def materialize(base, desc, body_sha=None):
    payload=msgpack.packb(desc,use_bin_type=True)
    if body_sha is not None and sha(payload)!=body_sha:
        raise ValueError('body SHA mismatch')
    n=len(base['files']); g=desc.get('generation')
    if not isinstance(g,int) or g<0 or g>n: raise ValueError('generation')
    if desc.get('base_index_sha256')!=sha(msgpack.packb(base,use_bin_type=True)):
        raise ValueError('base root SHA')
    if desc.get('base_index_offset_le64')!=ROOT_PTR or desc.get('base_file_count')!=n:
        raise ValueError('base count or physical offset')
    if desc.get('type')==BMP_TAG:
        if set(desc)!={'type','base_index_sha256','base_index_offset_le64',
                       'base_file_count','generation','survival_bitmap'}:
            raise ValueError('bitmap keys')
        bits=desc['survival_bitmap']
        if not isinstance(bits,bytes) or len(bits)!=(n+7)//8: raise ValueError('bitmap length')
        if n%8 and bits[-1]>> (n%8):raise ValueError('trailing bits')
        rows=[r for i,r in enumerate(base['files']) if bits[i//8]&(1<<(i%8))]
    elif desc.get('type')==GAP_TAG:
        if set(desc)!={'type','base_index_sha256','base_index_offset_le64',
                       'base_file_count','generation','deleted_ordinal_gaps'}:
            raise ValueError('gap keys')
        deleted=set(unvarints(desc['deleted_ordinal_gaps'],g,n))
        rows=[r for i,r in enumerate(base['files']) if i not in deleted]
    else: raise ValueError('unknown grammar tag')
    if len(rows)!=n-g: raise ValueError('survivor cardinality')
    return {**base,'files':rows}

def rejects(base, desc, digest=None):
    try: materialize(base,desc,digest)
    except ValueError: return True
    return False

def micros(fn):
    fn()
    samples=[]
    for i in range(17):
        t=time.perf_counter_ns();fn();samples.append(time.perf_counter_ns()-t)
    return {'median_ns':statistics.median(samples),'raw_ns':samples}

def trial(path,kind):
    data=path.read_bytes()
    assert wire.sha(data)==SOURCE_SHA[kind], 'source content mismatch'
    base,chain=wire.read_wire(data)
    n=len(base['files'])
    assert n==int(kind.split('-')[0]) and len(chain)==65
    assert chain[0]['object']==base and chain[0]['raw_sha']==sha(msgpack.packb(base,use_bin_type=True)).hex()
    assert all(chain[i]['kind']==1 for i in range(1,64))
    assert chain[64]['kind']==0
    assert {k:v for k,v in base.items() if k!='files'}=={k:v for k,v in chain[64]['object'].items() if k!='files'}
    names=[r[0] for r in base['files']]; assert len(set(names))==n
    pos={name:i for i,name in enumerate(names)}
    deleted=set();ordered=[]
    for step in range(1,64):
        obj=chain[step]['object']
        assert set(obj)=={'ops','blobs'} and obj['blobs']==[] and len(obj['ops'])==1
        action,name=obj['ops'][0]
        assert action=='del' and name in pos and pos[name] not in deleted
        deleted.add(pos[name]);ordered.append(pos[name])
        if step==32: deleted32=set(deleted)
    final_names={r[0] for r in chain[64]['object']['files']}
    assert len([x for x in base['files'] if x[0] not in final_names])==64
    expected={**base,'files':[r for i,r in enumerate(base['files']) if i not in deleted32]}
    report={'archive_sha256':wire.sha(data),'archive_bytes':len(data),
            'initial_members':n,'verified_footer_count':len(chain),
            'original_generation32_delta_bytes':chain[32]['body_bytes'],
            'nonfile_fields_immutable':True}
    for typ in ('bitmap','gaps'):
        d=descriptor(base,deleted32,32,typ)
        payload=msgpack.packb(d,use_bin_type=True)
        assert materialize(base,d,sha(payload))==expected
        codecs=[wire.compress(payload,level) for level in (1,3,19)]
        extra=codecs[0]['bytes']-chain[32]['body_bytes']
        report[typ]={'raw_descriptor_bytes':len(payload),
                     'payload_data_bytes':len(d['survival_bitmap'] if typ=='bitmap' else d['deleted_ordinal_gaps']),
                     'codec_trials':codecs,'extra_physical_bytes':extra,
                     'whole_archive_overhead_percent':100*extra/len(data),
                     'exact_generation32_index':True}
        if typ=='bitmap':
            changes=[]
            a=dict(d);a['base_index_sha256']=b'\0'*32;changes.append(a)
            a=dict(d);a['base_index_offset_le64']=b'\0'*8;changes.append(a)
            a=dict(d);a['base_file_count']+=1;changes.append(a)
            a=dict(d);a['survival_bitmap']+=b'\xff';changes.append(a)
            a=dict(d);b=bytearray(a['survival_bitmap']);b[0]^=1;b[1]^=1;a['survival_bitmap']=bytes(b);changes.append(a)
            assert all(rejects(base,c,sha(payload)) for c in changes)
            # Padding-bit rejection must also hold for a non-byte-aligned root.
            small={**base,'files':base['files'][:10]}
            test=descriptor(small,{1,3},2,'bitmap')
            changed=dict(test); bits=bytearray(test['survival_bitmap']);bits[-1]|=0x80
            changed['survival_bitmap']=bytes(bits)
            assert rejects(small,changed)
            report['hostile_cases_rejected']=6
    bm=descriptor(base,deleted32,32,'bitmap')
    gaps=descriptor(base,deleted32,32,'gaps')
    def replay():
        seen=set(ordered[:32])
        return [r for i,r in enumerate(base['files']) if i not in seen]
    assert replay()==materialize(base,bm)['files']==materialize(base,gaps)['files']
    report['python_micro_no_product_credit']={
        'original_32_op_replay':micros(replay),
        'bitmap_with_reauthenticated_root':micros(lambda:materialize(base,bm)),
        'gaps_with_reauthenticated_root':micros(lambda:materialize(base,gaps))}
    hostile={'first32':list(range(32)),'last32':list(range(n-32,n)),
             'alternating32':list(range(0,64,2)),
             'sha256_ranked32':sorted(range(n),key=lambda i:sha(b'j24g88-hostile-v1'+struct.pack('<I',i)))[:32]}
    report['synthetic_hostile_controls']={}
    for label,ordinals in hostile.items():
        b=descriptor(base,set(ordinals),32,'bitmap')
        g=descriptor(base,set(ordinals),32,'gaps')
        assert materialize(base,b)==materialize(base,g)
        report['synthetic_hostile_controls'][label]={
            'genuine_physical_history':False,
            'bitmap_zstd1_bytes':wire.compress(msgpack.packb(b,use_bin_type=True),1)['bytes'],
            'gaps_zstd1_bytes':wire.compress(msgpack.packb(g,use_bin_type=True),1)['bytes']}
    report['frozen_k32_gate_pass']=(report['bitmap']['whole_archive_overhead_percent']<=5 and 63/31>=2)
    return report

def main(directory,output):
    root=Path(directory)
    result={'schema':'j24g88-source-verified-ordinal-o0-v1',
            'research_only':True,'new_reader_grammar_required':True,
            'physical_compatibility_claim':False,'product_speed_claim':False,
            'hypothetical_substitution_not_retrofit':True,
            'source_artifact': 'J24G83 #12978714378',
            'source_sha256':SOURCE_SHA,'cases':{}}
    for kind in ('8192-middle','32768-tail'):
        path=root/('j24g80-'+kind+'-public-valid.cmpct')
        # Historical A/B/C physical identity is independently asserted.
        data=path.read_bytes()
        assert data==(root/('j24g80-'+kind+'-owned-valid.cmpct')).read_bytes()
        assert data==(root/('j24g83-'+kind+'-fresh-valid.cmpct')).read_bytes()
        result['cases'][kind]=trial(path,kind)
    result['decision']='SURVIVOR_BITMAP_O0_BYTES_PASS' if all(
        x['frozen_k32_gate_pass'] for x in result['cases'].values()) else 'SURVIVOR_BITMAP_O0_FAIL'
    result['productization']='UNPROVEN: optimized signed-delta Reader and Writer session are stronger controls; no real Reader wall/CPU/RSS/recovery measurements.'
    Path(output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['decision'])
    for case,v in result['cases'].items():
        print(case,'bitmap',v['bitmap']['extra_physical_bytes'],
              'gaps',v['gaps']['extra_physical_bytes'],
              'archive',v['archive_bytes'],
              'micro_ns',v['python_micro_no_product_credit']['bitmap_with_reauthenticated_root']['median_ns'])

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: SCRIPT ORIGINAL_J24G83_ARTIFACT_DIRECTORY RESULT_JSON')
    main(sys.argv[1],sys.argv[2])
