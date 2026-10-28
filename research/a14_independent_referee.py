#!/usr/bin/env python3
"""Independent A14 O0 receipt referee. Does NOT import candidate research module."""
from __future__ import annotations
import binascii,copy,hashlib,json,lzma,struct,subprocess,sys
from pathlib import Path

SPECS=[('high_entropy_head_36',1401,36,8192,0,0,'random',True),
       ('high_entropy_tail_68',1402,68,4096,64,1,'random',True),
       ('high_entropy_internal_132',1403,132,2048,4,0,'random',True),
       ('structured_tail_68',1404,68,4096,64,0,'structured',True),
       ('no_crc_random_36',1405,36,8192,0,0,'none',False),
       ('late_corrupt_36',1406,36,8192,0,0,'random',False),
       ('variable_offset_68',1407,68,4096,0,0,'random',False)]
HEADER='<8sHHBQQ32s'; HEADSZ=struct.calcsize(HEADER)

def expand(seed,n):
    b=b'';counter=0
    while len(b)<n:
        b+=hashlib.sha256(seed.to_bytes(8,'little')+counter.to_bytes(8,'little')).digest()
        counter+=1
    return b[:n]

def expected_bytes(row):
    name,seed,w,n,offset,endian,kind,pos=row
    v=bytearray()
    for i in range(n):
        if kind=='none':v.extend(expand(seed*10000+i,w));continue
        if kind=='structured':
            part=b'log-field-row:'+(i%512).to_bytes(4,'little')+expand(seed+i%8,8)
            payload=(part*(w//(len(part)-8)+2))[:w-4]
        else:payload=expand(seed*10000+i,w-4)
        off=offset if name!='variable_offset_68' else (0 if i%2==0 else w-4)
        c=binascii.crc32(payload).to_bytes(4,'little' if endian==0 else 'big')
        v.extend(payload[:off]);v.extend(c);v.extend(payload[off:])
    if name=='late_corrupt_36':v[-w]^=1
    return bytes(v)

def zstd(data,decomp=False):
    cmd=['zstd','-q','-c']
    cmd.insert(1,'-d' if decomp else '-19')
    return subprocess.run(cmd,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout

def refuse(msg):raise ValueError(msg)

def audit(receipt):
    if receipt.get('schema')!='cmpct-a14-derived-crc-o0-v1':refuse('schema')
    if receipt.get('instrument_sha256')!=hashlib.sha256(Path(__file__).with_name('a14_derived_crc_o0.py').read_bytes()).hexdigest():refuse('instrument identity')
    rows=receipt.get('cases')
    if not isinstance(rows,list) or len(rows)!=len(SPECS):refuse('case count')
    strong=[]
    for spec,row in zip(SPECS,rows):
        name,seed,width,count,off,endian,kind,valid=spec
        if row['case']!=name or row['expected_positive'] is not valid:refuse('case identity')
        original=expected_bytes(spec)
        if row['raw_sha256']!=hashlib.sha256(original).hexdigest() or row['raw_bytes']!=len(original):refuse('source SHA/size')
        if (row['detected'] is not None)!=valid:refuse('positive/admission')
        if not valid:continue
        if row['detected']!=[width,off,endian]:refuse('layout')
        independent_payload=bytearray()
        for k in range(count):
            b=original[k*width:(k+1)*width];part=b[:off]+b[off+4:]
            if b[off:off+4]!=binascii.crc32(part).to_bytes(4,'little' if endian==0 else 'big'):refuse('CRC mismatch')
            independent_payload.extend(part)
        folded=zstd(bytes(independent_payload))
        independent_artifact=struct.pack(HEADER,b'CFOLD001',width,off,endian,count,len(folded),hashlib.sha256(original).digest())+folded
        if row['artifact_sha256']!=hashlib.sha256(independent_artifact).hexdigest():refuse('artifact SHA')
        if row['fold_artifact_bytes']!=len(independent_artifact) or row['fold_header_bytes']!=HEADSZ or row['compressed_body_bytes']!=len(folded):refuse('charged artifact bytes')
        decoded=zstd(independent_artifact[HEADSZ:],True)
        if decoded!=bytes(independent_payload):refuse('independent compressed decode')
        rebuilt=bytearray()
        for k in range(count):
            body=decoded[k*(width-4):(k+1)*(width-4)]
            rebuilt.extend(body[:off]+binascii.crc32(body).to_bytes(4,'little' if endian==0 else 'big')+body[off:])
        if bytes(rebuilt)!=original or row['reconstructed_sha256']!=hashlib.sha256(rebuilt).hexdigest():refuse('exact reconstruction')
        direct=zstd(original); xz=lzma.compress(original,format=lzma.FORMAT_XZ,preset=9)
        transposed=bytes(original[k*width+j] for j in range(width) for k in range(count))
        t=zstd(transposed)
        sizes={'solid_zstd19':len(direct),'solid_xz9':len(xz),'transposed_zstd19_charged':len(t)+12}
        if row['solid_zstd19_bytes']!=sizes['solid_zstd19'] or row['solid_xz9_bytes']!=sizes['solid_xz9'] or row['transpose_zstd19_charged_bytes']!=sizes['transposed_zstd19_charged']:refuse('comparator bytes')
        if row['best_control_bytes']!=min(sizes.values()) or row['best_control']!=min(sizes,key=sizes.get):refuse('best comparator')
        diff=min(sizes.values())-len(independent_artifact)
        if row['fold_gain_bytes']!=diff or abs(row['fold_gain_percent']-round(diff/min(sizes.values())*100,6))>0.000001:refuse('win ratio')
        if not set(row['tamper_rejected'])=={'bad_magic','bad_offset','encoded_length_mismatch','digest_mismatch','truncate','altered_payload'}:refuse('tamper controls')
        if row['fold_gain_percent']>=5:strong.append((width,off))
    result='O0_STRUCTURAL_HEADROOM_ONLY' if len(set(strong))>=2 else 'O0_HYPOTHESIS_FALSIFIED'
    if receipt['decision']!=result:refuse('decision')
    return {'referee':'PASS','cases':len(SPECS),'positive_cases':4,'negative_controls':3,'strong_distinct_regimes':len(set(strong)),
            'decision':result,'independent_regeneration':True,'independent_roundtrip':True,'raw_measured_times_independently_verified':False}


def main():
    src=Path(sys.argv[1]);d=json.loads(src.read_text());out=audit(d)
    rejected=[]
    for label,patch in [
        ('source_sha',lambda x:x['cases'][0].__setitem__('raw_sha256','0'*64)),
        ('fold_size',lambda x:x['cases'][1].__setitem__('fold_artifact_bytes',x['cases'][1]['fold_artifact_bytes']-1)),
        ('chosen_comparator',lambda x:x['cases'][3].__setitem__('best_control','solid_zstd19')),
        ('decision',lambda x:x.__setitem__('decision','O0_HYPOTHESIS_FALSIFIED')),
        ('derived_bytes',lambda x:x['cases'][2].__setitem__('artifact_sha256','f'*64)),
        ('admission',lambda x:x['cases'][6].__setitem__('detected',[68,0,0]))]:
        v=copy.deepcopy(d);patch(v)
        try:audit(v)
        except (ValueError,AssertionError):rejected.append(label)
        else:raise AssertionError('receipt mutation accepted '+label)
    out['forged_receipts_rejected']=rejected
    if len(rejected)!=6:raise AssertionError('mutation coverage')
    target=Path(sys.argv[2]) if len(sys.argv)>2 else src.with_name('a14_independent_referee_receipt.json')
    target.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
