from __future__ import annotations
import argparse, binascii, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
ROOT=Path(__file__).resolve().parents[1]
ORDER=(("control","fold-file"),("fold-file","control"),("control","fold-semantic"),("fold-semantic","control"))

def _install_fold(mode:str):
 from experiments import entropygraph_v030_verified_restore as VR
 R=VR.C.POLICY.R; G=R.G04; A5=R.A5; P=R.P
 def folded_file(session,rel,desc,tree,target_root,*,verify_file_sha=True):
  # This is a historical research oracle whose purpose is to remove the file-SHA pass. Accept the production
  # reader's newer scoped keyword so the oracle remains executable, but deliberately ignore it here rather than
  # silently changing the experiment that produced the preserved headroom evidence.
  _=verify_file_sha
  safe=R._safe_relpath(rel); expected_size=int(desc[2]); rb=rel.encode(); tree.update(len(rb).to_bytes(4,"little")); tree.update(rb); tree.update(expected_size.to_bytes(8,"little")); written=0; output=None
  try:
   if target_root is not None: target=target_root.joinpath(*safe.parts); target.parent.mkdir(parents=True,exist_ok=True); output=target.open("wb")
   chunks=[session.record(int(desc[1]))] if desc[0]=="preflate" else (session.node(int(n)) for n in desc[1])
   for raw in chunks:
    written+=len(raw)
    if written>expected_size: raise RuntimeError("streamed file exceeds size")
    tree.update(raw)
    if output is not None: output.write(raw)
  finally:
   if output is not None: output.close()
  if written!=expected_size: raise RuntimeError("streamed file size mismatch")
  return written
 R._consume_g04_file=folded_file
 if mode!="fold-semantic": return
 class FoldSession(R._G04Session):
  def record(self,rid):
   rid=R._int(rid,"record id",maximum=len(self.offsets)-1); cached=self.record_cache.pop(rid,None)
   if cached is not None: self.record_cache[rid]=cached; return cached
   self.stream.seek(self.record_start+self.offsets[rid]); h=self.stream.read(R.PH.size)
   if len(h)!=R.PH.size: raise RuntimeError("short header")
   codec,usize,csize,crc,_=R.PH.unpack(h); payload=self.stream.read(csize)
   if len(payload)!=csize or R.H(payload)!=self.leaves[rid]: raise RuntimeError("payload auth")
   if codec==G.O.CODEC_RAW: physical=payload
   elif codec==G.O.CODEC_ZSTD: physical=G.O.zd(payload,usize)
   elif codec==G.O.CODEC_PREFLATE: physical=A5.V028._preflate_unpack(payload,usize)
   else: raise RuntimeError("codec")
   if len(physical)!=usize: raise RuntimeError("physical size")
   t=self.transforms[rid]
   if t is None: original=physical
   elif t[0]=="lane": original=G.O.lane_inverse(physical,int(t[1]),int(t[2]))
   elif t[0]=="delimiter": original=G.O.delimiter_inverse(physical,int(t[2]))
   elif t[0]=="hierarchical":
    p,s=int(t[1]),int(t[2]); pref=bool(int(t[3])); logical=int(t[4]); magic=G.HG.MAGIC_PREFIX if pref else G.HG.MAGIC_PLAIN
    if len(physical)<6 or physical[:4]!=magic or physical[4:6]!=bytes((p,s)): raise RuntimeError("hierarchy identity")
    original=G.HG.hierarchy_inverse(physical,logical)
   else: raise RuntimeError("transform")
   if (binascii.crc32(original)&0xffffffff)!=crc: raise RuntimeError("record CRC")
   self.physical_record_reads+=1; self.max_physical_record_bytes=max(self.max_physical_record_bytes,len(original)); R._cache_put(self.record_cache,self.record_cache_bytes,rid,original,R.MAX_RECORD_CACHE_BYTES); return original
  def node(self,nid):
   nid=R._int(nid,"node id",maximum=len(self.nodes)-1); cached=self.node_cache.pop(nid,None)
   if cached is not None: self.node_cache[nid]=cached; return cached
   d=self.nodes[nid]; k=d[0]
   if k=="direct":
    _,rid,off,length,_=d; pack=self.record(rid)
    if off>len(pack) or length>len(pack)-off: raise RuntimeError("direct bounds")
    raw=pack[off:off+length]
   elif k=="delta": _,base,rid,length,_=d; raw=P.delta_decode(self.node(base),self.record(rid),expected_size=length,max_output=A5.MAX_CHUNK)
   elif k=="delta_pack":
    _,base,rid,off,rlen,length,_=d; pack=self.record(rid)
    if len(pack)>A5.MAX_RESIDUAL_PACK or off>len(pack) or rlen>len(pack)-off or len(pack)/max(1,int(length))>A5.MAX_ADDITIONAL_RECIPE_AMP: raise RuntimeError("delta pack bounds")
    raw=P.delta_decode(self.node(base),pack[off:off+rlen],expected_size=length,max_output=A5.MAX_CHUNK)
   elif k=="mosaic": _,bases,rid,length,_=d; raw=P.mosaic_delta_decode([self.node(b) for b in bases],self.record(rid),expected_size=length,max_bases=A5.MAX_MOSAIC_BASES,max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,max_output=A5.MAX_CHUNK)
   elif k=="pack_mosaic":
    _,rid,off,rlen,bases,length,_=d; pack=self.record(rid)
    if off>len(pack) or rlen>len(pack)-off: raise RuntimeError("mosaic bounds")
    raw=P.mosaic_delta_decode([self.node(b) for b in bases],pack[off:off+rlen],expected_size=length,max_bases=A5.MAX_MOSAIC_BASES,max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,max_output=A5.MAX_CHUNK)
   else: raise RuntimeError("node kind")
   if len(raw)>A5.MAX_CHUNK: raise RuntimeError("node size")
   self.max_logical_node_bytes=max(self.max_logical_node_bytes,len(raw)); R._cache_put(self.node_cache,self.node_cache_bytes,nid,raw,R.MAX_NODE_CACHE_BYTES); return raw
 R._G04Session=FoldSession

def worker(arm,archive,dst):
 if arm!="control": _install_fold(arm)
 started=time.perf_counter(); PRODUCT.extract(archive,dst); return {"arm":arm,"wall_s":time.perf_counter()-started,"tree_sha256":PRODUCT.treehash(dst)}
def fresh(arm,archive,dst):
 env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else ""); cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,"--archive",str(archive),"--dst",str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True); return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])
def run(root):
 shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); src=PERF._build_corpora(root/"corpora")[("neutral_hostile_v1","09_ml_artifacts")]; archive=root/"ml.cmpct"; PRODUCT.build(src,archive); expected=PRODUCT.treehash(src); pairs=[]
 for rep,order in enumerate(ORDER):
  rows={arm:fresh(arm,archive,root/f"r{rep}-{arm}") for arm in order}
  if any(x["tree_sha256"]!=expected for x in rows.values()): raise RuntimeError("semantic drift")
  c=rows["control"]["wall_s"]; other=next(x for k,x in rows.items() if k!="control"); pairs.append({"rep":rep,"order":list(order),"rows":rows,"wall_improvement_pct":(c-other["wall_s"])/c*100})
 return {"schema":"cmpct-v030-ml-semantic-hash-fold-oracle-v2","release_credit":False,"pairs":pairs,"fold_file_preserves":["payload SHA","record CRC+SHA","node SHA","final authenticated tree SHA"],"fold_semantic_preserves":["payload SHA","record CRC","structural/resource checks","final authenticated tree SHA"],"claim_boundary":"research headroom only; hostile equivalence/selective semantics unpaid"}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--worker",choices=("control","fold-file","fold-semantic")); ap.add_argument("--archive",type=Path); ap.add_argument("--dst",type=Path); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-ml-filehash-fold")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-ml-filehash-fold.json")); a=ap.parse_args()
 if a.worker: print(json.dumps(worker(a.worker,a.archive,a.dst),separators=(",",":"))); return
 d=run(a.root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
