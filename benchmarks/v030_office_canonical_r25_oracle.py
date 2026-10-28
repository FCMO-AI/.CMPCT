from __future__ import annotations

"""Office-only oracle for legal canonical-r25 contenders versus inherited/product/world floors."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_canonical_manifest_candidate as CAND
from experiments import entropygraph_v030_release_candidate as RC
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_TREE="aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"; EXPECTED_FILES=20; EXPECTED_LOGICAL_BYTES=16_063_798
SHIPPING_R24_BYTES=15_445_236; ZSTD19_BYTES=8_312_879; SEVENZIP_BYTES=7_455_748

def _source_commit(): return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def _build_office(w:Path):
 REPAIR.install_generation_hooks(CORPUS); CORPUS.corpus_office(w); s=w/"02_office_workspace"; REPAIR.normalize_workload(s)
 fs=sorted(p for p in s.rglob("*") if p.is_file()); logical=sum(p.stat().st_size for p in fs); tree=CORPUS.tree_hash(s)
 if tree!=EXPECTED_TREE or len(fs)!=EXPECTED_FILES or logical!=EXPECTED_LOGICAL_BYTES: raise RuntimeError(f"Office substrate drift: tree={tree} files={len(fs)} logical={logical}")
 return s,{"tree_sha256":tree,"files":len(fs),"logical_bytes":logical}
def _current_v029_floor(s:Path,w:Path):
 staged=w/"current-floor-stage"; CANON._prepare_profile_tree(s,staged); a=w/"current-inner-tournament.cmpct"
 with CANON._revision25_profile_context(): st=dict(RC.build(staged,a,post_publish_verify=False,defer_preselection_verify=True))
 floor=int(st["v029_bytes"])
 if floor<=0: raise RuntimeError("current v0.29 floor was not materialized")
 return floor,st
def run(w:Path):
 shutil.rmtree(w,ignore_errors=True); w.mkdir(parents=True); s,substrate=_build_office(w); floor,floor_stats=_current_v029_floor(s,w)
 a=w/"office-canonical-r25-only.cmpct"; t=time.perf_counter(); stats=CAND.build_ablation(s,a,"combined"); create_s=time.perf_counter()-t
 revision,profile=CANON._profile_for_archive(a)
 if revision!=CANON.REVISION: raise RuntimeError(f"non-r25 profile: {revision!r}/{profile!r}")
 verified=CAND.strong_verify(a); semantic=CAND.treehash(s)
 if not verified.get("ok") or verified.get("tree_sha256")!=semantic: raise RuntimeError(f"verification failed: {verified!r}")
 amp=0.0
 for row in CAND.list_members(a):
  if row.get("kind")=="file":
   _raw,rs=CAND.read_member_with_stats(a,row["path"]); amp=max(amp,float(rs["decoded_context_amplification"]))
 if amp>8.0: raise RuntimeError(f"locality exceeded: {amp:.6f}x")
 b=a.stat().st_size; br=b<SHIPPING_R24_BYTES; bv=b<=floor; bz=b<ZSTD19_BYTES
 decision="CANONICAL_R25_ZERO_REGRESSION_ESCAPE_PROVEN" if br and bv and bz else ("CANONICAL_R25_BEATS_WORLD_CONTROLS_BUT_REGRESSES_V029" if br and bz and not bv else "CANONICAL_R25_ESCAPE_INSUFFICIENT")
 diag={k:stats.get(k) for k in ("g04_bytes","prefixgraph_bytes","prefixgraph_eligible","prefixgraph_locality","prefixgraph_error","selected","selected_bytes") if k in stats}
 return {"schema":"cmpct-v030-office-canonical-r25-oracle-v3","source_commit":_source_commit(),"substrate":"neutral-hostile-determinism-repair-v6","substrate_evidence":substrate,"format_revision":revision,"format_profile":profile,"selected":stats.get("selected"),"candidate_set":stats.get("candidate_set"),"candidate_diagnostics":diag,"archive_bytes":b,"create_s":create_s,"max_member_read_amplification":amp,"within_locality_8x":True,"strong_verify_ok":True,"strong_verify_tree_exact":True,"shipping_r24_control_bytes":SHIPPING_R24_BYTES,"current_v029_floor_bytes":floor,"current_v029_floor_selected":floor_stats.get("g04_selected"),"zstd19_control_bytes":ZSTD19_BYTES,"sevenzip_control_bytes":SEVENZIP_BYTES,"saving_vs_shipping_r24_bytes":SHIPPING_R24_BYTES-b,"saving_vs_current_v029_bytes":floor-b,"saving_vs_zstd19_bytes":ZSTD19_BYTES-b,"saving_vs_7z_bytes":SEVENZIP_BYTES-b,"beats_shipping_r24":br,"preserves_v029_zero_regression":bv,"beats_zstd19":bz,"beats_7z":b<SEVENZIP_BYTES,"decision":decision,"release_credit":False,"claim_boundary":"Office-only canonical-r25 materialization oracle; all-15/recovery/native/platform authority remains separate."}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); x=p.parse_args(); r=run(x.work_root); x.output.parent.mkdir(parents=True,exist_ok=True); x.output.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8"); print(json.dumps(r,indent=2),flush=True)
if __name__=="__main__": main()
