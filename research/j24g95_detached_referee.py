#!/usr/bin/env python3
"""Detached standard-library-only referee for J24G95; no CMPCT imports."""
from __future__ import annotations
import hashlib, json, statistics, struct, sys
from pathlib import Path
F = struct.Struct('<8sBBBBQQQ32s')
P = struct.calcsize('<8sBBBBQQ')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def check(root):
    data=json.loads((root/'receipt.json').read_text())
    assert data['status']=='PASS' and data['product_credit']==0
    summary={}
    for sn,case in data['cases'].items():
        n=int(sn)
        raw={label:(root/f'{n}-{label}.cmpct').read_bytes() for label in case['records']}
        original=raw['normal'];a=F.unpack_from(original,len(original)-F.size)
        assert a[0]==b'CMPTF24\0' and a[1]==1
        final_pos=len(original)-F.size
        parent_pos=a[7]
        assert 0<parent_pos<final_pos
        parent=F.unpack_from(original,parent_pos)
        assert parent[0]==b'CMPTF24\0' and parent[1]==1
        for name,blob in raw.items():
            item=case['records'][name]
            assert digest(blob)==item['sha256']
            assert len(blob)==item['bytes']
            assert item['pinned_sha_accept']==(name=='normal')
        assert digest(original)==case['trusted_snapshot_anchor_sha256']
        assert case['physical_snapshot_source_sha256']==digest(original)
        assert len(original)==len(raw['rewired'])==len(raw['double'])
        one=[i for i,(x,y) in enumerate(zip(original,raw['rewired'])) if x!=y]
        double=[i for i,(x,y) in enumerate(zip(original,raw['double'])) if x!=y]
        assert one and all(final_pos+P<=i<final_pos+P+8 for i in one)
        assert set(one).issubset(double) and all(
            (final_pos+P<=i<final_pos+P+8) or (parent_pos+P<=i<parent_pos+P+8)
            for i in double)
        assert all(F.unpack_from(raw[k],final_pos)[-1]==a[-1]
                   for k in ('normal','rewired','double'))
        assert raw['authorized_append'].startswith(original)
        assert len(raw['authorized_append'])>len(original)
        timing=case['same_input_open_economics']
        samples=timing['raw'];assert len(samples)==70
        for m in ('wall_ns','cpu_ns'):
            for op in ('hash','reader'):
                med=statistics.median(s[m] for s in samples if s['operation']==op)
                assert med==timing['medians'][m][op]
        summary[sn]={'original_bytes':len(original),'rewire_bytes_changed':len(one),
                     'double_bytes_changed':len(double),
                     'wall_ns_hash':timing['medians']['wall_ns']['hash'],
                     'wall_ns_reader':timing['medians']['wall_ns']['reader']}
    result={'status':'PASS','cases':summary,'source_head':data['source']['head']}
    (root/'detached-audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('DETACHED',json.dumps(result,sort_keys=True))
if __name__=='__main__':check(Path(sys.argv[1]))
