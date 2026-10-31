#!/usr/bin/env python3
"""J24G98 detached referee: no CMPCT imports and no producer parser import."""
import argparse,hashlib,io,json,pathlib,statistics,struct,zipfile
F=struct.Struct("<8sBBBBQQQ32s")
INPUTS={
 "small-ubuntu":("d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d","f29561c5e2d36a8f47aa35f61191911c0611be6b",("16-normal.cmpct","128-normal.cmpct")),
 "small-windows":("f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e","f29561c5e2d36a8f47aa35f61191911c0611be6b",("16-normal.cmpct","128-normal.cmpct")),
 "deep-ubuntu":("19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b","129edec976efe8bb604584517de39553487fec34",("4096-A.cmpct","8192-A.cmpct")),
 "deep-windows":("c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab","129edec976efe8bb604584517de39553487fec34",("4096-A.cmpct","8192-A.cmpct"))}
def sha(b):return hashlib.sha256(b).hexdigest()
def yes(c,m):
 if not c:raise AssertionError(m)
def boundaries(raw):
 seen=set();pos=len(raw)-F.size; ends=[]
 while pos:
  yes(0<pos<len(raw) and pos not in seen and len(seen)<128,"footer loop")
  seen.add(pos)
  magic,kind,codec,flags,unused,clen,ulen,prev,payload=F.unpack_from(raw,pos)
  yes(magic==b"CMPTF24\0" and kind in (0,1) and flags==unused==0,"footer format")
  yes(0<clen<=pos and 0<ulen<=32*1024*1024 and 0<=prev<pos,"bounds")
  yes(kind==(0 if prev==0 else 1),"root/delta")
  ends.append(pos+F.size);pos=prev
 ends.reverse()
 yes(len(ends) in (4,64) and ends[-1]==len(raw),"tail/depth")
 return ends
def judge(sources,result):
 yes(result["schema"]=="j24g98-immutable-segment-science-v1","result schema")
 yes(len(result["cases"])==8,"case cardinality")
 for k,(expected,head,filenames) in INPUTS.items():
  zdata=sources[k].read_bytes();yes(sha(zdata)==expected,"original ZIP SHA")
  with zipfile.ZipFile(io.BytesIO(zdata)) as z:
   yes(z.read("checkout-head.txt").decode().strip()==head,"original source HEAD")
   for name in filenames:
    raw=z.read(name);v=result["cases"][k+"/"+name]
    ends=boundaries(raw);starts=[0]+ends[:-1]
    spans=[raw[a:b] for a,b in zip(starts,ends)]
    yes(v["sha256"]==sha(raw) and v["bytes"]==len(raw),"archive SHA/bytes")
    yes(v["footer_count"]==len(ends) and v["ends"]==ends,"footer geometry")
    yes(len(v["segments"])==len(spans),"segment count")
    for i,(part,e) in enumerate(zip(spans,v["segments"])):
     yes(e=={"name":f"seg-{i:03d}.bin","size":len(part),"sha256":sha(part)},"segment identity")
    yes(v["full_copy_retained_generation_bytes"]==sum(ends),"copy cost")
    yes(v["last_append_bytes"]==len(spans[-1]),"last append bytes")
    alloc=(v["allocated_segments"]+v["allocated_manifest"])/v["allocated_contiguous"]
    yes(abs(v["allocated_ratio"]-alloc)<1e-8,"allocated ratio")
    yes(v["corrupt_segment_hash_rejected_on_reverify"],"corruption control")
    p=v["read"];t=p["raw_ms_per_read"]
    yes(all(len(t[x])==15 for x in ("one","seg")),"sample size")
    yes(all(abs(statistics.median(t[x])-p["medians_ms_per_read"][x])<1e-9 for x in ("one","seg")),"median")
    ratio=p["medians_ms_per_read"]["seg"]/p["medians_ms_per_read"]["one"]
    yes(abs(ratio-p["ratio"])<1e-8,"read ratio")
    yes(v["passes_local_o1_filter"]==(alloc<=1.05 and ratio<=2.0),"frozen filter")
 deep=[v for v in result["cases"].values() if v["footer_count"]==64]
 want=("SEGMENT_PER_FOOTER_O1_ADMISSION_FAIL" if any(not v["passes_local_o1_filter"] for v in deep)
       else "O0_LOCAL_FILTER_SURVIVES")
 yes(result["decision"]==want,"verdict")
 return want
def main():
 ap=argparse.ArgumentParser()
 for key in INPUTS:ap.add_argument("--"+key,required=True,type=pathlib.Path)
 ap.add_argument("--result",required=True,type=pathlib.Path)
 args=ap.parse_args()
 sources={key:getattr(args,key.replace("-","_")) for key in INPUTS}
 received=json.loads(args.result.read_text());decision=judge(sources,received)
 import copy
 negative=0
 for typ in ("sha","length","segment","ratio","median","decision"):
  r=copy.deepcopy(received);v=next(iter(r["cases"].values()))
  if typ=="sha":v["sha256"]="0"*64
  if typ=="length":v["bytes"]+=1
  if typ=="segment":v["segments"][0]["sha256"]="0"*64
  if typ=="ratio":v["allocated_ratio"]=0.5
  if typ=="median":v["read"]["ratio"]=0.5
  if typ=="decision":r["decision"]="O0_LOCAL_FILTER_SURVIVES"
  try:judge(sources,r)
  except AssertionError:negative+=1
 yes(negative==6,"forged receipts not rejected")
 print(json.dumps({"cases":len(received["cases"]),"forgeries_rejected":negative,"decision":decision},sort_keys=True))
if __name__=="__main__":main()
