from __future__ import annotations
import cProfile, json, pstats, shutil, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
    src=PERF._build_corpora(root/'corpora')[("neutral_hostile_v1","09_ml_artifacts")]
    archive=root/'ml.cmpct'; dst=root/'extract'; build=PRODUCT.build(src,archive); expected=PRODUCT.treehash(src)
    profiler=cProfile.Profile(); started=time.perf_counter(); profiler.enable(); PRODUCT.extract(archive,dst); profiler.disable(); wall=time.perf_counter()-started
    if PRODUCT.treehash(dst)!=expected: raise RuntimeError('ML extraction semantic-tree drift')
    stats=pstats.Stats(profiler); rows=[]
    for (filename,lineno,function),(cc,nc,tt,ct,_callers) in stats.stats.items():
        rows.append({'file':filename,'line':lineno,'function':function,'primitive_calls':cc,'calls':nc,'self_s':tt,'cumulative_s':ct})
    rows.sort(key=lambda r:(r['cumulative_s'],r['self_s']),reverse=True)
    return {'schema':'cmpct-v030-ml-postfold-profile-v1','selected':build.get('selected'),'archive_bytes':archive.stat().st_size,'profiled_wall_s':wall,'total_profile_cpu_s':stats.total_tt,'top_by_cumulative':rows[:60],'claim_boundary':'post-#146 exact-head attribution only; profiler timing has no release credit'}

if __name__=='__main__':
    result=run(Path('benchmark-artifacts/v030-ml-postfold-profile-work')); out=Path('benchmark-artifacts/v030-ml-postfold-profile.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
