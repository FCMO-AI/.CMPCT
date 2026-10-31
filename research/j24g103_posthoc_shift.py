#!/usr/bin/env python3
"""J24G103 post-result structural shift sensitivity only; not a frozen gate."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from j24g102_cow_root_oracle import SOURCES,HEAD,makepair
from j24g103_cdc_shift import charge

def main():
 p=argparse.ArgumentParser()
 for host in SOURCES:p.add_argument('--'+host,type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args(); cases={}
 for host,expected in SOURCES.items():
  original=getattr(a,host).read_bytes()
  if hashlib.sha256(original).hexdigest()!=expected:raise AssertionError('provider ZIP mismatch')
  with zipfile.ZipFile(io.BytesIO(original)) as z:
   if z.read('checkout-head.txt').decode().strip()!=HEAD:raise AssertionError('source HEAD mismatch')
   for n in (4096,8192):
    old,new,_=makepair(z.read(f'{n}-A.cmpct'),z.read(f'{n}-B.cmpct'),n)
    offsets=sorted(set(x for x in (0,1,63,512,4095,4096,16383,16384,
      len(new)//3,len(new)//2,len(new)//2+1,len(new)*3//4,
      len(new)-16384,len(new)-4096,len(new)-2,len(new)-1) if 0<=x<len(new)))
    for target in (4096,16384):
     for op in ('insert','delete'):
      trials=[]
      for offset in offsets:
       variant=(new[:offset]+b'!'+new[offset:]) if op=='insert' else (new[:offset]+new[offset+1:])
       ratio=charge(old,variant,target,verify=False)['ratio_larger_image']
       trials.append({'offset':offset,'charged_ratio':ratio})
      name=f'{host}-{n}-{target}-{op}'
      cases[name]={'min':min(x['charged_ratio'] for x in trials),
       'max':max(x['charged_ratio'] for x in trials),
       'above_1p25':sum(x['charged_ratio']>1.25 for x in trials),
       'trials':trials}
 result={'schema':'J24G103-POSTRESULT-SENSITIVITY-NONFROZEN',
   'source_producer_sha':HEAD,'original_provider_SHA256':SOURCES,
   'evidence_tier':'EXPLORATORY_ONLY_NO_PRODUCT_OR_FROZEN_GATE_CREDIT',
   'cases':cases}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'case_groups':len(cases),'trials':sum(len(v['trials']) for v in cases.values()),
   'above_1p25':sum(v['above_1p25'] for v in cases.values()),
   'receipt_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest()},sort_keys=True))
if __name__=='__main__':main()
