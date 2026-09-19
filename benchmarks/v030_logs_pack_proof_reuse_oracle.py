from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
ROOT=Path(__file__).resolve().parents[1]
ORDER=(("control","reuse"),("reuse","control"))

def install_reuse():
 from experiments import entropygraph_v030_logs_fused_extract as F
 BASE=F.LOGS.Archive; skips=[0]
 class ProofArchive(BASE):
  def _restore_session(self,item,*,member_cache,pack_cache,active):
   if item in member_cache: return member_cache[item]
   if item in active or item<0 or item>=len(self.files): raise RuntimeError("logs profile dependency error")
   active.add(item)
   try:
    _prefix,_suffix,size,expected_sha,storage,_rel=self.files[item]; size=int(size); kind=storage[0]; proven=False
    if kind in ("pack","raw"):
     pack_index,offset,length=map(int,storage[1:]); pack=pack_cache.get(pack_index)
     if pack is None: pack=self._read_pack(pack_index); pack_cache[pack_index]=pack
     if offset<0 or length!=size or offset+length>len(pack): raise RuntimeError("logs profile slice bounds")
     value=pack[offset:offset+length]; decoded_context=len(pack) if kind=="pack" else length
     # _read_pack already computed H(pack) and compared it to this physical header digest. If this member owns
     # the entire pack and the header digest equals authenticated metadata expected_sha, the logical hash is proven.
     pack_sha=bytes(self.pack_offsets[pack_index][5]); proven=(offset==0 and length==len(pack) and pack_sha==bytes(expected_sha))
    elif kind=="derive":
     source_index=int(storage[1]);
     if source_index==item: raise RuntimeError("logs profile self dependency")
     source,source_context=self._restore_session(source_index,member_cache=member_cache,pack_cache=pack_cache,active=active); value=F.LOGS.V2.BASE._decode(storage[2],source); decoded_context=source_context+len(value)
    else: raise RuntimeError("unknown logs profile storage")
    if len(value)!=size or (not proven and hashlib.sha256(value).digest()!=expected_sha): raise RuntimeError("logs profile logical identity")
    if proven: skips[0]+=1
    member_cache[item]=(value,decoded_context); return member_cache[item]
   finally: active.discard(item)
 F.LOGS.Archive=ProofArchive
 return skips

def worker(arm,archive,dst):
 skips=[0]
 if arm=="reuse": skips=install_reuse()
 started=time.perf_counter(); PRODUCT.extract(archive,dst); wall=time.perf_counter()-started
 return {"arm":arm,"wall_s":wall,"tree_sha256":PRODUCT.treehash(dst),"logical_sha_reused":skips[0]}
def fresh(arm,archive,dst):
 env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else ""); cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,"--archive",str(archive),"--dst",str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True); return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])
def run(root):
 shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); src=PERF._build_corpora(root/"corpora")[("neutral_hostile_v1","05_logs_and_telemetry")]; archive=root/"logs.cmpct"; stats=PRODUCT.build(src,archive)
 if not stats.get("logs_terminal"): raise RuntimeError("frozen Logs workload did not select logs terminal")
 expected=PRODUCT.treehash(src); pairs=[]
 for rep,order in enumerate(ORDER):
  rows={arm:fresh(arm,archive,root/f"r{rep}-{arm}") for arm in order}
  if any(x["tree_sha256"]!=expected for x in rows.values()): raise RuntimeError("semantic drift")
  c=rows["control"]["wall_s"]; r=rows["reuse"]["wall_s"]; pairs.append({"rep":rep,"order":list(order),"rows":rows,"wall_improvement_pct":(c-r)/c*100})
 return {"schema":"cmpct-v030-logs-pack-proof-reuse-oracle-v1","release_credit":False,"pairs":pairs,"proof":"reuse only when full-pack member and pack-header SHA equals authenticated logical-member SHA; _read_pack already verifies H(decoded_pack)==pack-header SHA","claim_boundary":"fresh-process research oracle; product/hostile evidence unpaid"}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--worker",choices=("control","reuse")); ap.add_argument("--archive",type=Path); ap.add_argument("--dst",type=Path); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-logs-pack-proof")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-logs-pack-proof.json")); a=ap.parse_args()
 if a.worker: print(json.dumps(worker(a.worker,a.archive,a.dst),separators=(",",":"))); return
 d=run(a.root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
