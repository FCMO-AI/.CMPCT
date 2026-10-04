from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_ml_filehash_fold_oracle as BASE
from experiments import entropygraph_v030_release_product as PRODUCT
ROOT=Path(__file__).resolve().parents[1]
ORDER=(("control","fold"),("fold","control"))

def install_bounded_fold():
 BASE._install_fold("fold-semantic")
 from experiments import entropygraph_v030_verified_restore as VR
 R=VR.C.POLICY.R; Inner=R._G04Session
 class BoundedFoldSession(Inner):
  def record(self,rid):
   rid=R._int(rid,"record id",maximum=len(self.offsets)-1)
   if rid not in self.record_cache:
    pos=self.stream.tell()
    try:
     self.stream.seek(self.record_start+self.offsets[rid]); header=self.stream.read(R.PH.size)
     if len(header)!=R.PH.size: raise RuntimeError("short G0-G4 physical header")
     _codec,usize,csize,_crc,_sha=R.PH.unpack(header)
     if usize>R.G04.MAX_DECODE_UNIT or csize>R.G04.MAX_DECODE_UNIT+1024*1024: raise RuntimeError("G0-G4 physical resource bound")
    finally: self.stream.seek(pos)
   return super().record(rid)
 R._G04Session=BoundedFoldSession

def worker(arm,archive,dst):
 if arm=="fold": install_bounded_fold()
 t=time.perf_counter(); PRODUCT.extract(archive,dst); return {"arm":arm,"wall_s":time.perf_counter()-t,"tree_sha256":PRODUCT.treehash(dst)}
def fresh(arm,archive,dst):
 env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else ""); cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,"--archive",str(archive),"--dst",str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True); return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])
def run(root):
 shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); src=PERF._build_corpora(root/"corpora")[("neutral_hostile_v1","09_ml_artifacts")]; archive=root/"ml.cmpct"; PRODUCT.build(src,archive); expected=PRODUCT.treehash(src); pairs=[]
 for rep,order in enumerate(ORDER):
  rows={arm:fresh(arm,archive,root/f"r{rep}-{arm}") for arm in order}
  if any(x["tree_sha256"]!=expected for x in rows.values()): raise RuntimeError("semantic drift")
  c=rows["control"]["wall_s"]; f=rows["fold"]["wall_s"]; pairs.append({"rep":rep,"order":list(order),"rows":rows,"wall_improvement_pct":(c-f)/c*100})
 return {"schema":"cmpct-v030-ml-semantic-hash-fold-bounded-oracle-v1","release_credit":False,"pairs":pairs,"restored_check":"usize/csize physical resource bound before every uncached record decode","preserved":["payload SHA","record CRC","all original transform/node bounds","terminal authenticated streamed-tree SHA"],"claim_boundary":"valid-input headroom confirmation only; hostile matrix and selective/strong-verify product policy unpaid"}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--worker",choices=("control","fold")); ap.add_argument("--archive",type=Path); ap.add_argument("--dst",type=Path); ap.add_argument("--root",type=Path,default=Path("benchmark-artifacts/v030-ml-semantic-fold-bounded")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-ml-semantic-fold-bounded.json")); a=ap.parse_args()
 if a.worker: print(json.dumps(worker(a.worker,a.archive,a.dst),separators=(",",":"))); return
 d=run(a.root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n"); print(json.dumps(d,indent=2))
if __name__=="__main__": main()
