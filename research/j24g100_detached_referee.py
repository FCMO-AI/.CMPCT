#!/usr/bin/env python3
"""Independent J24G100 physical-source and receipt referee; no experiment/CMPCT import."""
from __future__ import annotations
import argparse,copy,hashlib,io,json,math,zipfile
from pathlib import Path
from j24g96_trusted_head_oracle import ZIP_CASES,parse_chain,require

def sha(b):return hashlib.sha256(b).hexdigest()

def check(results,originals):
    require(results['schema']=='J24G100-POSIX-READER-EPOCH-O0-v1','schema')
    require(results['host']=='Linux','host')
    require(results['verdict']=='POSIX_COOPERATIVE_READER_EPOCH_H1_H2_PASS_NO_GATE_RACE_CONFIRMED','verdict')
    require(set(results['cases'])==set(originals),'original case identities')
    for key,raw in originals.items():
        row=results['cases'][key];nodes=parse_chain(raw)
        require(len(nodes)==64 and row['footer_count']==64,'physical footer count')
        require(row['source_sha256']==sha(raw) and row['source_bytes']==len(raw),'source identity')
        require(set(row['cases'])=={'held_reader_gc','delayed_manifest_open','no_gate_negative','abnormal_exit'},'scenario identity')
        c=row['cases']
        for r in c.values():require(r['pass'] is True,'scenario result')
        for name in ['held_reader_gc','delayed_manifest_open','abnormal_exit']:
            r=c[name]
            require(r['first']['held']==['tail-062.bin'] and r['first']['removed']==[],'held tail deletion')
            require(r['second']['removed']==['tail-062.bin'] and r['second']['held']==[],'deferred GC missing')
            require(r['active']['tail_count']==1 and r['active']['generation']==63,'live tail identity')
            require(len(raw)<=r['active']['allocated_bytes']<=math.ceil(len(raw)/4096)*4096+8192,'allocation')
            for x in ['first','second']:require(0<=r[x]['wall_ms']<60000,'GC time')
        require(c['delayed_manifest_open']['gate_exclusion'] is True,'gate race')
        require(c['no_gate_negative']['confirmed_ENOENT'] is True,'unsafe negative missing')
        require(c['no_gate_negative']['removed']==['tail-062.bin'],'unsafe deletion missing')
    return True

def main():
    ap=argparse.ArgumentParser()
    for k in ('deep-ubuntu','deep-windows'):ap.add_argument('--'+k,required=True,type=Path)
    ap.add_argument('--result',required=True,type=Path)
    a=ap.parse_args();originals={}
    for key in ('deep-ubuntu','deep-windows'):
        data=getattr(a,key.replace('-','_')).read_bytes()
        expected,head,names=ZIP_CASES[key]
        require(sha(data)==expected,'provider SHA')
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(z.read('checkout-head.txt').decode().strip()==head,'source commit')
            for n in names:originals[key+'/'+n]=z.read(n)
    receipt=json.loads(a.result.read_text());check(receipt,originals)
    forgeries=[]
    for label,mutation in [
      ('source_sha',lambda r:r['cases']['deep-ubuntu/4096-A.cmpct'].__setitem__('source_sha256','0'*64)),
      ('lost_case',lambda r:r['cases'].pop('deep-windows/8192-A.cmpct')),
      ('bogus_epoch',lambda r:r['cases']['deep-ubuntu/8192-A.cmpct']['cases']['held_reader_gc']['active'].__setitem__('generation',62)),
      ('fake_gate',lambda r:r['cases']['deep-windows/4096-A.cmpct']['cases']['delayed_manifest_open'].__setitem__('gate_exclusion',False)),
      ('fake_negative',lambda r:r['cases']['deep-ubuntu/4096-A.cmpct']['cases']['no_gate_negative'].__setitem__('confirmed_ENOENT',False))
    ]:
        x=copy.deepcopy(receipt);mutation(x);rejected=False
        try:check(x,originals)
        except (ValueError,AssertionError,KeyError,TypeError):rejected=True
        require(rejected,'accepted forged receipt '+label);forgeries.append(label)
    print(json.dumps({'verdict':'DETACHED_RECEIPT_PASS','physical_cases':len(originals),
      'scenarios':sum(len(x['cases']) for x in receipt['cases'].values()),
      'forgeries_rejected':forgeries,'source_sha256':{k:sha(v) for k,v in originals.items()}},sort_keys=True))
if __name__=='__main__':main()
