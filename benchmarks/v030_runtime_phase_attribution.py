from __future__ import annotations

"""Research-only phase attribution for the exact-head v0.30 runtime blockers."""
import argparse, contextlib, functools, json, shutil, statistics, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS_PRODUCT
from experiments import entropygraph_v030_logs_fused_extract as LOGS_FUSED

TARGETS=(("resemblance_hostile_v1","01_shifted_versions"),("neutral_hostile_v1","05_logs_and_telemetry"),("neutral_hostile_v1","09_ml_artifacts")); ROUNDS=3
G04_ECON_KEYS=("selected","archive_bytes","v029_bytes","v029_floor_selected","v028_bytes","pre_overlay_graph_bytes","overlay_bytes","saving_vs_v029_bytes","raw_overlay_delta_vs_v029_bytes","overlay_improvement_vs_prefallback_graph_bytes","transformed_records","lane_records","delimiter_records","hierarchical_records","prefix_plane_records","hierarchical_total_records","transform_payload_saving_bytes","hierarchical_incremental_saving_bytes","overlay_max_member_read_amplification","overlay_locality_passed","overlay_selection_reject_reason","shared_candidate_build_s","v028_child_s","attempt5_child_s","attempt5_graph_build_count")

class PhaseRecorder:
    def __init__(self): self.samples={}
    def wrap(self,owner,name,label):
        original=getattr(owner,name)
        @functools.wraps(original)
        def timed(*args,**kwargs):
            started=time.perf_counter()
            try: return original(*args,**kwargs)
            finally: self.samples.setdefault(label,[]).append(time.perf_counter()-started)
        setattr(owner,name,timed); return original
    def summary(self):
        return {k:{"calls":len(v),"total_s":float(sum(v)),"median_call_s":float(statistics.median(v)),"max_call_s":float(max(v))} for k,v in sorted(self.samples.items()) if v}

@contextlib.contextmanager
def instrumented_phases(recorder):
    patches=[]; G04=BASE.C.RC.G04
    specs=[(PRODUCT,"_shared_frontdoor_preflight","build.frontdoor_preflight"),(LOGS_PRODUCT,"_parallel_candidates","build.logs_parallel_candidates"),(BASE.C,"build","build.canonical_final"),(BASE.C,"_prepare_profile_tree","build.canonical.prepare_profile_tree"),(BASE.C,"_r24_build","build.canonical.r24_floor"),(BASE.C,"_r25_build","build.canonical.r25_tournament"),(BASE.C.RC,"build","build.canonical.r25.release_candidate"),(G04,"build","build.canonical.r25.g04"),(BASE.C.RC.PG,"build","build.canonical.r25.prefixgraph"),(BASE,"_locality_bounded_r24_build","build.r24_candidate"),(BASE.POLICY,"extract_verified_into_staging","extract.r25_verified_stream"),(BASE.VERIFIED_RESTORE,"restore_verified_manifest_tree","extract.r25_fs_restore"),(LOGS_FUSED,"_restore_filesystem_metadata","extract.logs_fs_restore")]
    optional=[(G04,"_build_shared_candidates","build.canonical.r25.g04.shared_candidates"),(G04,"_overlay_retained_graph","build.canonical.r25.g04.overlay_pipeline"),(getattr(G04,"G",None),"_audition_record","build.canonical.r25.g04.record_audition"),(getattr(G04,"G",None),"_write_overlay","build.canonical.r25.g04.overlay_write"),(G04,"strong_verify","build.canonical.r25.g04.overlay_verify")]
    specs.extend((o,n,l) for o,n,l in optional if o is not None and hasattr(o,n))
    for o,n,l in specs: patches.append((o,n,recorder.wrap(o,n,l)))
    patches.append((LOGS_FUSED.LOGS.Archive,"_restore_session",recorder.wrap(LOGS_FUSED.LOGS.Archive,"_restore_session","extract.logs_restore_session")))
    try: yield
    finally:
        for o,n,original in reversed(patches): setattr(o,n,original)

def _g04_economics(build_stats):
    if not isinstance(build_stats,dict): return None
    r25=build_stats.get("r25")
    if not isinstance(r25,dict): return None
    g04=r25.get("g04")
    if not isinstance(g04,dict): return None
    # Release-candidate accounting nests the owning shared-portfolio receipt under r25.g04 even when PrefixGraph
    # wins the r25 tournament. Preserve only bounded scalar evidence; never copy the per-record audition corpus.
    return {k:g04[k] for k in G04_ECON_KEYS if k in g04 and isinstance(g04[k],(str,int,float,bool,type(None)))}

def _run_target(source,work):
    source_tree=PRODUCT.treehash(source); archive=work/"archive.cmpct"; build_rounds=[]; extract_rounds=[]; build_stats=None
    for index in range(ROUNDS):
        archive.unlink(missing_ok=True); recorder=PhaseRecorder()
        with instrumented_phases(recorder): started=time.perf_counter(); build_stats=PRODUCT.build(source,archive); wall=time.perf_counter()-started
        verified=PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256")!=source_tree: raise RuntimeError("instrumented build failed exact strong verification")
        build_rounds.append({"round":index,"wall_s":wall,"phases":recorder.summary(),"g04_economics":_g04_economics(build_stats)})
    for index in range(ROUNDS):
        dst=work/f"extract-{index}"; shutil.rmtree(dst,ignore_errors=True); recorder=PhaseRecorder()
        with instrumented_phases(recorder): started=time.perf_counter(); PRODUCT.extract(archive,dst); wall=time.perf_counter()-started
        if PRODUCT.treehash(dst)!=source_tree: raise RuntimeError("instrumented extraction failed exact tree identity")
        extract_rounds.append({"round":index,"wall_s":wall,"phases":recorder.summary()})
    return {"source_tree_sha256":source_tree,"archive_bytes":archive.stat().st_size,"selected":build_stats.get("selected") if isinstance(build_stats,dict) else None,"format_profile":build_stats.get("format_profile") if isinstance(build_stats,dict) else None,"build_rounds":build_rounds,"extract_rounds":extract_rounds,"build_wall_median_s":float(statistics.median(r["wall_s"] for r in build_rounds)),"extract_wall_median_s":float(statistics.median(r["wall_s"] for r in extract_rounds))}

def run(work_root):
    shutil.rmtree(work_root,ignore_errors=True); work_root.mkdir(parents=True); corpora=PERF._build_corpora(work_root/"corpus"); rows=[]
    for suite,name in TARGETS:
        w=work_root/f"{suite}-{name}"; w.mkdir(parents=True); rows.append({"suite":suite,"name":name,**_run_target(corpora[(suite,name)],w)})
    return {"schema":"cmpct-v030-runtime-phase-attribution-v3","release_credit":False,"rounds":ROUNDS,"targets":rows,"claim_boundary":"Research-only in-process semantic-phase ownership and bounded shipping G04 byte/child-cost economics. Nested times overlap and are not additive. Exact archive/tree semantics are verified; this is not fresh-process release timing and cannot unlock v0.30."}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
