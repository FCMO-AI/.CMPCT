#!/usr/bin/env python3
"""Detached r24 physical auditor. Deliberately NEVER imports cmpct."""
import argparse, hashlib, json, random, struct, zlib
from pathlib import Path
import msgpack, zstandard
H=struct.Struct("<8sHHQQQ32s");B=struct.Struct("<4sBBHQQII32s");F=struct.Struct("<8sBBBBQQQ32s")
def sha(x):return hashlib.sha256(x).digest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--case-dir",type=Path,required=True);a=p.parse_args()
 manifest=json.loads((a.case_dir/"manifest.json").read_text())
 assert manifest["schema"]=="j24i37-direct-zstd-v1"
 tile=random.Random(manifest["seed"]).randbytes(manifest["tile_bytes"]);records={}
 for mib in (8,32,64):
  info=manifest["records"][str(mib)]
  rawfile=(a.case_dir/("direct-zstd-%dm.cmpct"%mib)).read_bytes()
  assert sha(rawfile).hex()==info["archive_sha256"]
  magic,rev,flags,cs,us,span,ih=H.unpack_from(rawfile)
  assert (magic,rev,flags)==(b"CMPCT24\0",24,0)
  ic=rawfile[H.size:H.size+cs]
  wire=zstandard.ZstdDecompressor().decompress(ic,max_output_size=us)
  assert len(wire)==us and sha(wire)==ih
  idx=msgpack.unpackb(wire,raw=False);assert len(idx["files"])==len(idx["blobs"])==1
  row=idx["files"][0];n=mib*1024*1024
  assert row[0]=="payload.bin" and row[1]==0 and row[4]==n and row[5] is None and row[6]==[0,0]
  assert idx["blobs"]==[[0,n,info["encoded_bytes"],1,0]]
  start=H.size+cs;magic_b,codec,flags_b,res,usz,csz,meta,crc,digest=B.unpack_from(rawfile,start)
  assert (magic_b,codec,flags_b,res,meta)==(b"CMA4",1,0,0,0)
  assert (usz,csz,span)==(n,info["encoded_bytes"],B.size+csz)
  physical=rawfile[start+B.size:start+span]
  decoded=zstandard.ZstdDecompressor().decompress(physical,max_output_size=n)
  assert decoded==tile*(n//len(tile))
  assert sha(decoded)==digest and digest.hex()==info["payload_sha256"]
  assert crc==(zlib.crc32(decoded)&0xffffffff)==info["crc32"]
  tail=start+span
  assert rawfile[tail:tail+cs]==ic and tail+cs+F.size==len(rawfile)
  assert F.unpack_from(rawfile,tail+cs)==(b"CMPTF24\0",0,1,0,0,cs,us,0,ih)
  records[str(mib)]={"archive_sha256":sha(rawfile).hex(),"logical_sha256":sha(decoded).hex(),
                     "physical_bytes":csz,"index_copies_equal":True,"physical_crc32":crc}
 report={"schema":"j24i37-independent-physical-audit-v1","result":"PASS","records":records}
 (a.case_dir/"detached-audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps(report,sort_keys=True))
if __name__=="__main__":main()
