#!/usr/bin/env python3
"""J24G102b source-exact installed public CMPCT Reader checkpoint-repack court.

Prospectively posted on PR #879 before implementation. Product source unmodified.
All evidence derives from four SHA-pinned original Builder/Writer physical A/B cases.
"""
import argparse,hashlib,io,json,os,sys,tempfile,zipfile
from pathlib import Path
import msgpack
from cmpct.reader import CMPCT
from j24g102_cow_root_oracle import SOURCES,HEAD,makepair
H=lambda x:hashlib.sha256(x).hexdigest()
def run_one(a,b,n,host):
 old,new,meta=makepair(a,b,n)
 originals={'old':old,'A':a,'B':b,'new':new}
 expected={'old':n,'A':n-63,'B':n-63,'new':n-63}
 depth={'old':0,'A':63,'B':0,'new':0}
 with tempfile.TemporaryDirectory(prefix='j24g102b-') as td:
  observations={}
  for label,raw in originals.items():
   path=Path(td)/(label+'.cmpct');path.write_bytes(raw)
   with CMPCT(path) as reader:
    names=list(reader.by)
    if len(names)!=expected[label]:raise AssertionError(f'{host}/{n}/{label}: member count {len(names)}')
    if reader.delta_depth!=depth[label]:raise AssertionError(f'{host}/{n}/{label}: delta depth {reader.delta_depth}')
    verified=reader.verify()
    if verified!=expected[label]:raise AssertionError(f'{host}/{n}/{label}: verify {verified}')
    # Calculate full logical byte identity from Reader, not from file path guesses.
    logical=hashlib.sha256()
    for name in sorted(names):
     payload=reader.read(name)
     logical.update(len(name.encode()).to_bytes(4,'little'))
     logical.update(name.encode())
     logical.update(len(payload).to_bytes(8,'little'))
     logical.update(hashlib.sha256(payload).digest())
    obs={'file_sha256':H(raw),'file_bytes':len(raw),'member_count':len(names),
         'delta_depth':reader.delta_depth,'verified':verified,
         'index_sha256':H(msgpack.packb(reader.index,use_bin_type=True)),
         'logical_member_sha256':logical.hexdigest()}
    observations[label]=obs
  for label in ('B','new'):
   if observations[label]['logical_member_sha256']!=observations['A']['logical_member_sha256']:
    raise AssertionError(f'{host}/{n}/{label}: original A logical byte mismatch')
   if observations[label]['index_sha256']!=observations['A']['index_sha256']:
    raise AssertionError(f'{host}/{n}/{label}: original A complete index mismatch')
  if observations['new']['index_sha256']!=meta['final_index_SHA256']:
   raise AssertionError(f'{host}/{n}: physical final footer SHA/index packing mismatch')
  return {'source':host,'n':n,'observations':observations,'exact_public_reader_parity':True}
def main():
 p=argparse.ArgumentParser()
 for host in SOURCES:p.add_argument('--'+host,type=Path,required=True)
 p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 cases={}
 for host,digest in SOURCES.items():
  data=getattr(a,host).read_bytes()
  if H(data)!=digest:raise AssertionError('original provider checksum mismatch')
  with zipfile.ZipFile(io.BytesIO(data)) as source:
   if source.read('checkout-head.txt').decode().strip()!=HEAD:raise AssertionError('source commit mismatch')
   for n in (4096,8192):
    cases[f'{host}-{n}']=run_one(source.read(f'{n}-A.cmpct'),source.read(f'{n}-B.cmpct'),n,host)
 out={'schema':'CMPCT-J24G102b-INSTALLED-READER-REPACK-COURT','product_code_changed':False,
      'python':sys.version,'source_head':HEAD,'cases':cases,'status':'INSTALLED_PUBLIC_READER_EXACT_PARITY_NOT_RELEASE'}
 a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'physical_cases':len(cases),'sha256':H(a.out.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
