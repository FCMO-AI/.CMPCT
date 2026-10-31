#!/usr/bin/env python3
"""Independently rederive J24G102 physical byte economics. Never imports court or CMPCT."""
import argparse,hashlib,io,json,struct,zipfile
from pathlib import Path
D=lambda x:hashlib.sha256(x).hexdigest()
F=struct.Struct('<8sBBBBQQQ32s')
PROVIDERS={'ubuntu':'19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b',
'windows':'c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab'}
def audit_case(report,a,b):
 assert b[:len(a)]==a
 # This parser obtains the initial commit through scanning and never follows the ancestry
 # pointer traversal used by the experiment. All proposed bytes checked independently.
 first=a.index(b'CMPTF24\0')
 m,k,c,fl,res,n,ul,prev,h=F.unpack_from(a,first)
 assert k==0 and prev==0 and fl==res==0 and n>0
 last=len(b)-F.size
 mf,kf,cf,ff,rf,nf,uf,prevf,hf=F.unpack_from(b,last)
 assert mf==m and kf==0 and ff==rf==0 and prevf==len(a)-F.size
 old=a[:first+F.size]
 new=a[:first-n]+b[last-nf:last]+F.pack(m,0,cf,0,0,nf,uf,0,hf)
 assert D(old)==report['old_sha256'] and D(new)==report['new_sha256']
 assert len(old)==report['old_bytes'] and len(new)==report['new_bytes']
 for blocksize,metrics in report['COW_costs'].items():
  bs=int(blocksize)
  arms=[[x[i:i+bs] for i in range(0,len(x),bs)] for x in (old,new)]
  unique={hashlib.sha256(piece).digest():piece for seq in arms for piece in seq}
  stored=sum(len(v)+44 for v in unique.values())
  manifests=128+32*sum(map(len,arms))
  charged=stored+manifests
  assert charged==metrics['charged_total_bytes'] and stored==metrics['charged_blocks_bytes']
  assert manifests==metrics['charged_two_manifests_bytes']
  assert len(unique)==metrics['blocks_unique']
  assert abs(charged/max(len(old),len(new))-metrics['ratio_larger_image'])<1e-12
  assert abs(charged/(len(old)+len(new))-metrics['ratio_two_copies'])<1e-12
  assert metrics['ratio_larger_image']<1.20
  # Independent hostile shifted/unrelated controls; only the sharing limit matters.
  shifted=new[:512]+b'!'+new[512:]
  shiftedblocks={hashlib.sha256(piece).digest():piece for x in (old,shifted) for i in range(0,len(x),bs) for piece in (x[i:i+bs],)}
  ratio=(sum(len(v)+44 for v in shiftedblocks.values())+128+32*((len(old)+bs-1)//bs+(len(shifted)+bs-1)//bs))/max(len(old),len(shifted))
  assert abs(ratio-report['non_cmpct_geometric_perturbations'][blocksize]['one_byte_early_insertion'])<1e-6
  assert ratio>1.99,'hostile one-byte misalignment should destroy generic sharing'
 return True

def audit(data,src):
 assert set(data['cases'])=={'ubuntu-4096','ubuntu-8192','windows-4096','windows-8192'}
 for osname,expected_sha in PROVIDERS.items():
  b=Path(src[osname]).read_bytes();assert D(b)==expected_sha
  with zipfile.ZipFile(io.BytesIO(b)) as zip:
   assert zip.read('checkout-head.txt').decode().strip()==data['head']
   for n in (4096,8192):
    c=data['cases'][f'{osname}-{n}']
    a=zip.read(f'{n}-A.cmpct');barchive=zip.read(f'{n}-B.cmpct')
    assert D(a)==c['A_SHA256'] and D(barchive)==c['B_SHA256']
    assert audit_case(c,a,barchive)
 return True

def main():
 p=argparse.ArgumentParser()
 for key in PROVIDERS:p.add_argument('--'+key,required=True,type=Path)
 p.add_argument('--receipt',required=True,type=Path)
 a=p.parse_args();src={k:getattr(a,k) for k in PROVIDERS}
 data=json.loads(a.receipt.read_text());assert audit(data,src)
 # Falsify independently modified numeric and SHA claims.
 bad=json.loads(json.dumps(data));bad['cases']['ubuntu-4096']['COW_costs']['4096']['charged_total_bytes']+=1
 try:audit(bad,src)
 except AssertionError:pass
 else:raise AssertionError('forged charge accepted')
 bad=json.loads(json.dumps(data));bad['cases']['windows-8192']['new_sha256']='0'*64
 try:audit(bad,src)
 except AssertionError:pass
 else:raise AssertionError('forged SHA accepted')
 print(json.dumps({'verdict':'INDEPENDENT_PHYSICAL_BYTE_AND_CHARGE_PASS','cases':4,'blocksize_models':8,
                   'hostile_shifts':8,'forged_receipts_rejected':2,'receipt_sha256':D(a.receipt.read_bytes())},sort_keys=True))
if __name__=='__main__':main()
