from __future__ import annotations
"""Fresh-process r24-only vs r25-only RSS discriminator. Diagnostic only."""
import argparse,json,os,resource,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def child(mode:str,source:Path,out:Path):
    from experiments import entropygraph_v030_release_product_base as RP
    prebuild_peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    started=time.perf_counter()
    if mode=='r24': stats=RP._locality_bounded_r24_build(source,out)
    elif mode=='r25':
        with tempfile.TemporaryDirectory(prefix='cmpct-r25-only-',dir=out.parent) as td:
            staged=Path(td)/'profile-tree'; RP._ORIGINAL_PREPARE_PROFILE_TREE(source,staged); stats=RP.C._r25_build(staged,out)
    else: raise ValueError(mode)
    pack_wall=time.perf_counter()-started
    pack_peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    verified=RP.strong_verify(out)
    post_verify_peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print(json.dumps({'mode':mode,'prebuild_peak_rss_kib':prebuild_peak,'pack_wall_s':pack_wall,'pack_peak_rss_kib':pack_peak,
                      'pack_incremental_peak_kib':max(0,pack_peak-prebuild_peak),'post_verify_peak_rss_kib':post_verify_peak,
                      'archive_bytes':out.stat().st_size,'selected':stats.get('selected'),'verify_ok':bool(verified.get('ok'))},separators=(',',':')))

def invoke(mode,source,out):
    env={**os.environ,'PYTHONPATH':str(ROOT)}
    p=subprocess.run([sys.executable,__file__,'--child',mode,'--source',str(source),'--archive',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--child',choices=('r24','r25')); p.add_argument('--source',type=Path); p.add_argument('--archive',type=Path); p.add_argument('--work-root',type=Path); p.add_argument('--output',type=Path); a=p.parse_args()
    if a.child: child(a.child,a.source,a.archive); return
    # Keep the heavy frozen-corpus builder out of child imports: otherwise its benchmark modules establish a ~120 MiB
    # high-water before product construction and mask the very component increment this diagnostic is meant to isolate.
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True)
    corp=PERF._build_corpora(a.work_root/'corpus'); rows={}
    targets=(('resemblance_hostile_v1','01_shifted_versions'),('neutral_hostile_v1','09_ml_artifacts'))
    for suite,name in targets:
        source=corp[(suite,name)]; rows[name]={}
        for mode in ('r24','r25'): rows[name][mode]=invoke(mode,source,a.work_root/f'{name}-{mode}.cmpct')
    d={'schema':'cmpct-v030-rss-component-owner-v1','release_credit':False,'rows':rows,
       'claim_boundary':'Fresh-process component pack high-water attribution with product-only child import baselines; verification is reported separately; overlap/live aggregate and full product gates remain separate.'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
