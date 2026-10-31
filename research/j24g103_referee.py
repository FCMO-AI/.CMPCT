#!/usr/bin/env python3
"""Detached byte oracle for J24G103. Neither CMPCT nor J24G102/J24G103 oracle imports."""
import argparse
import hashlib
import io
import json
import random
import struct
import zipfile
from pathlib import Path

D=lambda raw:hashlib.sha256(raw).hexdigest()
SHA=lambda raw:hashlib.sha256(raw).digest()
F=struct.Struct('<8sBBBBQQQ32s')
SOURCES={'ubuntu':'19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b',
         'windows':'c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab'}
PRODUCER='129edec976efe8bb604584517de39553487fec34'
TAB=[int.from_bytes(hashlib.sha256(b'J24G103-GEAR-v1'+bytes([i])).digest()[:8],'little') for i in range(256)]

# Re-derive the frozen mathematical boundary rule using absolute cut offsets,
# not the oracle's chunk generator or metadata objects.
def segment_offsets(blob, target):
    lo,hi=target//4,target*4
    value=0;begin=0;edges=[]
    for position in range(len(blob)):
        value=(2*value + TAB[blob[position]]) % (2**64)
        count=position+1-begin
        if count>=lo and (count>=hi or value % target==0):
            edges.append((begin,position+1))
            begin=position+1
            value=0
    if begin<len(blob):edges.append((begin,len(blob)))
    assert b''.join(blob[a:b] for a,b in edges)==blob
    assert all(0 < b-a <= hi for a,b in edges)
    return edges

def independent_charge(old,new,target):
    seen={};refs=[];chunk_counts=[]
    for data in (old,new):
        edges=segment_offsets(data,target)
        chunk_counts.append(len(edges))
        keys=[]
        for a,b in edges:
            raw=data[a:b];key=SHA(raw)
            assert key not in seen or seen[key]==raw
            seen[key]=raw
            keys.append(key)
        refs.append(keys)
    wire=sum(len(raw)+44 for raw in seen.values()) + 128 + 32*sum(chunk_counts)
    return {'charged_total_bytes':wire,'blocks_unique':len(seen),
            'blocks_old':chunk_counts[0], 'blocks_new':chunk_counts[1],
            'shared_sha_keys':len(set(refs[0]) & set(refs[1])),
            'ratio_larger_image':wire/max(len(old),len(new))}

def restore_physical(a,b):
    assert a[:8]==b'CMPCT24\0' and b.startswith(a)
    root=a.index(b'CMPTF24\0');last=len(b)-F.size
    tag,kind,codec,fl,res,length,plain,parent,ph=F.unpack_from(a,root)
    tag2,k2,c2,fl2,res2,length2,plain2,prev2,ph2=F.unpack_from(b,last)
    assert tag==tag2==b'CMPTF24\0' and kind==k2==0
    assert fl==res==parent==fl2==res2==0 and prev2==len(a)-F.size
    assert 0<length<root and 0<length2<last and codec in (0,1) and c2 in (0,1)
    old=a[:root+F.size]
    new=a[:root-length]+b[last-length2:last]+F.pack(tag2,0,c2,0,0,length2,plain2,0,ph2)
    return old,new

def audit(receipt,sources,focus=None):
    assert receipt['schema']=='J24G103-CONTENT-DEFINED-ROOT-O0'
    assert receipt['source_producer_sha']==PRODUCER
    assert receipt['prereg_commit']=='7a0ecce92cae0b65080f092eda3a2e21b93aa396'
    assert receipt['originals']==SOURCES
    assert set(receipt['cases'])=={f'{host}-{n}' for host in SOURCES for n in (4096,8192)}
    overall=True
    for host,expected in SOURCES.items():
        if focus and not focus.startswith(host+'-'):continue
        raw=sources[host].read_bytes();assert D(raw)==expected
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.read('checkout-head.txt').decode().strip()==PRODUCER
            for n in (4096,8192):
                key=f'{host}-{n}'
                if focus and key!=focus:continue
                item=receipt['cases'][key]
                a=z.read(f'{n}-A.cmpct');b=z.read(f'{n}-B.cmpct')
                old,new=restore_physical(a,b)
                source=item['source']
                for label,data in [('A_SHA256',a),('B_SHA256',b),('old_sha256',old),('new_sha256',new)]:
                    assert D(data)==source[label],(key,label)
                assert source['old_bytes']==len(old) and source['new_bytes']==len(new)
                for target in (4096,16384):
                    q=item['targets'][str(target)]
                    variations={
                      'early_insert':new[:512]+b'!'+new[512:],
                      'mid_insert':new[:len(new)//2]+b'!'+new[len(new)//2:],
                      'early_delete':new[:512]+new[513:],
                      'independent_random':random.Random(240103+target+len(new)).randbytes(len(new)),
                      'aligned_move_4096':new[4096:]+new[:4096]}
                    derived=independent_charge(old,new,target)
                    for field,observed in derived.items():
                        assert abs(observed-q['cdc'][field])<1e-10,(key,target,field)
                    for label,blob in variations.items():
                        check=independent_charge(old,blob,target)
                        for field,observed in check.items():
                            assert abs(observed-q['variants'][label][field])<1e-10,(key,target,label,field)
                    fixed_parts=[[raw[i:i+target] for i in range(0,len(raw),target)] for raw in (old,new)]
                    unique={SHA(part):part for parts in fixed_parts for part in parts}
                    fixed_cost=sum(len(v)+44 for v in unique.values())+128+32*sum(map(len,fixed_parts))
                    assert fixed_cost==q['fixed']['charged_total_bytes'],(key,target,'fixed-cost')
                    expected_pass=(derived['ratio_larger_image']<=1.25
                       and q['variants']['early_insert']['ratio_larger_image']<=1.25
                       and q['variants']['mid_insert']['ratio_larger_image']<=1.30
                       and q['variants']['early_delete']['ratio_larger_image']<=1.30
                       and derived['charged_total_bytes']<=1.15*fixed_cost)
                    assert q['frozen_byte_gate_pass']==expected_pass
                    overall &= expected_pass
                    for arm in ('raw_time_fixed','raw_time_cdc'):
                        assert len(q[arm])==3 and all(v['wall_ns']>0 and v['cpu_ns']>0 for v in q[arm])
    if focus is None:
        assert receipt['gate']==('O0_BYTE_GATE_PASS_NO_PRODUCT_CREDIT' if overall else 'O0_BYTE_GATE_FAIL_RETIRE_CDC_ROOT_SHARING')
    return overall

def main():
    p=argparse.ArgumentParser()
    for host in SOURCES:p.add_argument('--'+host,type=Path,required=True)
    p.add_argument('--receipt',required=True,type=Path)
    a=p.parse_args();sources={k:getattr(a,k) for k in SOURCES}
    original=json.loads(a.receipt.read_text());verdict=audit(original,sources)
    modifications=[]
    for kind in ('charged','source','shift','gate'):
        counterfeit=json.loads(json.dumps(original))
        if kind=='charged':counterfeit['cases']['ubuntu-4096']['targets']['4096']['cdc']['charged_total_bytes']+=1
        if kind=='source':counterfeit['cases']['windows-8192']['source']['old_sha256']='0'*64
        if kind=='shift':counterfeit['cases']['ubuntu-8192']['targets']['16384']['variants']['early_insert']['ratio_larger_image']+=0.01
        if kind=='gate':counterfeit['cases']['windows-4096']['targets']['4096']['frozen_byte_gate_pass']=not counterfeit['cases']['windows-4096']['targets']['4096']['frozen_byte_gate_pass']
        focus={'charged':'ubuntu-4096','source':'windows-8192','shift':'ubuntu-8192','gate':'windows-4096'}[kind]
        try:audit(counterfeit,sources,focus=focus)
        except AssertionError:modifications.append(kind)
        else:raise AssertionError('falsification escaped:'+kind)
    print(json.dumps({'verdict':'DETACHED_CHARGES_AND_FROZEN_GATE_VERIFIED','byte_gate_survived':verdict,
      'physical_pairs':4,'distinct_chunk_models':8,'geometric_perturbations':40,
      'falsifications_rejected':modifications,'receipt_sha256':D(a.receipt.read_bytes())},sort_keys=True))

if __name__=='__main__':main()
