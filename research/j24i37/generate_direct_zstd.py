#!/usr/bin/env python3
"""Source-independent r24 direct-Zstd scaling generator; research only."""
import argparse, base64, hashlib, json, random, struct, zlib
from pathlib import Path
import msgpack, zstandard
H=struct.Struct("<8sHHQQQ32s"); B=struct.Struct("<4sBBHQQII32s"); F=struct.Struct("<8sBBBBQQQ32s")
def sha(x):return hashlib.sha256(x).digest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 fixture=json.loads(Path("tests/conformance/v24-direct-codecs.json").read_text())
 assert fixture["schema"]=="cmpct-v24-golden-direct-codecs-v1"
 vec=next(v for v in fixture["vectors"] if v["codec"]==1)
 original=base64.b64decode(vec["archive_base64"],validate=True)
 assert sha(original).hex()==vec["archive_sha256"]
 magic,rev,flags,cs,us,span,index_sha=H.unpack_from(original)
 assert (magic,rev,flags)==(b"CMPCT24\0",24,0)
 idxwire=zstandard.ZstdDecompressor().decompress(original[H.size:H.size+cs],max_output_size=us)
 assert sha(idxwire)==index_sha
 template=msgpack.unpackb(idxwire,raw=False)
 assert len(template["files"])==len(template["blobs"])==1
 assert template["files"][0][1]==0 and template["files"][0][6][0]==0
 tile=random.Random(0x24137).randbytes(256*1024)
 manifest={"schema":"j24i37-direct-zstd-v1","base_sha":"9ef1644d8c6129de4d7d8008bfdadad5fffcbe06",
           "source_golden":vec["archive_sha256"],"seed":0x24137,"tile_bytes":len(tile),"records":{}}
 for mib in (8,32,64):
  raw=tile*(mib*1024*1024//len(tile))
  comp=zstandard.ZstdCompressor(level=3).compress(raw)
  index=msgpack.unpackb(idxwire,raw=False)
  row=index["files"][0];row[0]="payload.bin";row[4]=len(raw);row[5]=None;row[6]=[0,0]
  index["blobs"]=[[0,len(raw),len(comp),1,0]]
  iw=msgpack.packb(index,use_bin_type=True);ic=zstandard.ZstdCompressor(level=3).compress(iw)
  rec=B.pack(b"CMA4",1,0,0,len(raw),len(comp),0,zlib.crc32(raw)&0xffffffff,sha(raw))+comp
  out=H.pack(b"CMPCT24\0",24,0,len(ic),len(iw),len(rec),sha(iw))+ic+rec+ic
  out+=F.pack(b"CMPTF24\0",0,1,0,0,len(ic),len(iw),0,sha(iw))
  path=a.output/("direct-zstd-%dm.cmpct"%mib);path.write_bytes(out)
  from cmpct.reader import CMPCT
  with CMPCT(path) as reader:
   assert reader.read_range("payload.bin",0,64)==raw[:64]
   assert reader.verify()==1
  manifest["records"][str(mib)]={"logical_bytes":len(raw),"encoded_bytes":len(comp),
      "archive_bytes":len(out),"archive_sha256":sha(out).hex(),
      "payload_sha256":sha(raw).hex(),"crc32":zlib.crc32(raw)&0xffffffff}
 (a.output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"schema":manifest["schema"],"records":manifest["records"]},sort_keys=True))
if __name__=="__main__":main()
