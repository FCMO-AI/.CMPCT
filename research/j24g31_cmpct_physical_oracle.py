#!/usr/bin/env python3
"""Detached r24 primary/footer/physical-blob oracle, no CMPCT imports.

Scope: original seven single-member authentic r24 Builder products in J24G30
GitHub Actions artifact. Consult docs/FORMAT.md before extending grammar.
"""
from pathlib import Path
import hashlib,zipfile,struct,subprocess,binascii,json,zlib
import msgpack
HDR=struct.Struct('<8sHHQQQ32s')
BHDR=struct.Struct('<4sBBHQQII32s')
FTR=struct.Struct('<8sBBBBQQQ32s')
sha=lambda b:hashlib.sha256(b).digest()
checks=0

def okay(pred, label):
 global checks
 checks+=1
 if not pred:raise AssertionError(f'{checks}: {label}')

def decode_zstd(b):
 cp=subprocess.run(['zstd','-q','-d','-c'],input=b,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 return cp.stdout

def audit(name,b,expected):
 header=HDR.unpack_from(b)
 magic,ver,flags,cs,us,ds,ih=header
 okay(magic==b'CMPCT24\0' and ver==24 and flags==0,f'{name}: magic/revision/flags')
 okay(0<cs<len(b)-HDR.size and us<1024*1024,f'{name}: primary index declared bounds')
 primary=decode_zstd(b[HDR.size:HDR.size+cs]);okay(len(primary)==us and sha(primary)==ih,f'{name}: primary index length and digest')
 idx=msgpack.unpackb(primary,raw=False,strict_map_key=False)
 okay(set(('files','blobs','recipes')).issubset(idx),f'{name}: index key types')
 okay(len(idx['files'])==1 and len(idx['blobs'])>=1,f'{name}: one logical member and physical blob present')
 row=idx['files'][0]
 okay(row[3]==expected['mtime_ns'],f'{name}: signed metadata mtime equals producer manifest')
 okay(row[1]==0 and row[6][0]==0,f'{name}: file kind and physical blob storage')
 okay(isinstance(row[0],str) and len(row[0])>0,f'{name}: valid file name')
 blob=idx['blobs'][row[6][1]]
 off,blob_us,blob_cs,codec,ml=blob
 okay(codec in (0,1,4),f'{name}: supported small specimen codec')
 blob_start=HDR.size+cs+off
 okay(blob_start>=HDR.size+cs and blob_start+BHDR.size+ml+blob_cs<=len(b)-FTR.size,f'{name}: blob fully bounded')
 record=BHDR.unpack_from(b,blob_start)
 bm,c,flags,res,rus,rcs,rml,rcrc,rh=record
 okay(bm==b'CMA4' and c==codec and flags==0 and res==0,f'{name}: blob header identities')
 okay((rus,rcs,rml)==(blob_us,blob_cs,ml),f'{name}: index/record physical size parity')
 payload_start=blob_start+BHDR.size+rml
 compressed=b[payload_start:payload_start+blob_cs]
 if codec==0:payload=compressed
 elif codec==1:payload=decode_zstd(compressed)
 else:payload=zlib.decompress(compressed,-15)
 okay(len(payload)==blob_us and binascii.crc32(payload)&0xffffffff==rcrc,f'{name}: physical decompression and CRC')
 okay(sha(payload)==rh and sha(payload).hex()==expected['payload_sha256'],f'{name}: physical strong hash and manifest SHA')
 okay(row[4]==blob_us and row[5] in (None,rh),f'{name}: logical member size and optional SHA auth')
 footer_start=len(b)-FTR.size
 foot=FTR.unpack_from(b,footer_start)
 fm,kind,fc,ff,fr,fcs,fus,prev,fh=foot
 okay(fm==b'CMPTF24\0' and kind==0 and prev==0,f'{name}: full checkpoint commit tail identity')
 okay(fcs<len(b) and fc in (0,1),f'{name}: footer index codec / bounds')
 tail_p=footer_start-fcs
 okay(tail_p>=payload_start+blob_cs,f'{name}: physically disjoint tail index')
 tail=b[tail_p:footer_start]
 tail_raw=tail if fc==0 else decode_zstd(tail)
 okay(len(tail_raw)==fus and sha(tail_raw)==fh,f'{name}: footer strong identity')
 okay(tail_raw==primary,f'{name}: primary/tail independently materialized logical identity')
 return {'name':name,'size':len(b),'mtime_ns':row[3],'logical_name':row[0],'logical_bytes':len(payload),'physical_codec':codec,
         'physical_sha256':sha(b).hex(),'payload_sha256':sha(payload).hex(), 'raw_index_bytes':len(primary)}

def main(path):
 global checks
 checks=0
 okay(sha(path.read_bytes()).hex()==      '856777ebf5dcc1c2a7e85a4bb7b0fd5e7a15b3dbcbf6f94ab8eb4ddf68a7082a',
      'exact original GitHub Actions physical transport digest')
 with zipfile.ZipFile(path) as z:
  manifest=json.loads(z.read('manifest.json'))
  results={}
  for name,e in manifest['cases'].items():
   b=z.read(e['archive'])
   okay(len(b)==e['size'] and sha(b).hex()==e['sha256'],f'{name}: original archive source hash')
   results[name]=audit(name,b,e)
 return {'schema':'j24g31-independent-r24-physical-oracle-v1','checks':checks,'cases':results,
         'source':'GitHub Actions #40812726789 artifact #12871265991',
         'scope':'Independent r24 HEADER, Zstd primary/tail index, MessagePack, blob framing, Zstd payload, CRC/SHA, signed timestamp and footer. Not full arbitrary r24 grammar.'}

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--physical-artifact',type=Path,required=True);args=ap.parse_args()
 print(json.dumps(main(args.physical_artifact),indent=2))
