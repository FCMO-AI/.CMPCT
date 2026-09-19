from __future__ import annotations

"""Direct exact-parent canonical v0.30 ML-create A/B for bounded pack-plan reuse."""
import argparse, hashlib, json, os, shutil, statistics, subprocess, sys
from pathlib import Path
from benchmarks import v030_release_performance as PERF

ROOT=Path(__file__).resolve().parents[1]

def _git_sha(root: Path) -> str:
    return subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()

def _run(root: Path, source: Path, archive: Path) -> dict:
    env={**os.environ,'PYTHONPATH':str(root)}
    p=subprocess.run([sys.executable,str(root/'benchmarks/v030_perf_worker.py'),'--engine','v030','--op','pack',
                      '--source',str(source),'--archive',str(archive)],cwd=root,env=env,check=True,
                     capture_output=True,text=True)
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def main():
    p=argparse.ArgumentParser(); p.add_argument('--control-root',type=Path,required=True); p.add_argument('--work-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--pairs',type=int,default=3); a=p.parse_args()
    shutil.rmtree(a.work_root,ignore_errors=True); a.work_root.mkdir(parents=True)
    source=PERF._build_corpora(a.work_root/'corpus')[('neutral_hostile_v1','09_ml_artifacts')]
    rows=[]
    for i in range(a.pairs):
        order=('control','candidate') if i%2==0 else ('candidate','control'); got={}
        for arm in order:
            root=a.control_root if arm=='control' else ROOT
            got[arm]=_run(root,source,a.work_root/f'{i}-{arm}.cmpct')
        c,n=got['control'],got['candidate']
        if c['archive_bytes']!=n['archive_bytes'] or c['tree_sha256']!=n['tree_sha256']:
            raise RuntimeError('canonical pack cache changed archive size or user-tree identity')
        rows.append({'order':order,'control':c,'candidate':n,
                     'wall_improvement_pct':(c['wall_s']-n['wall_s'])/c['wall_s']*100,
                     'rss_change_pct':(n['peak_rss_kib']-c['peak_rss_kib'])/max(1,c['peak_rss_kib'])*100})
    walls=[r['wall_improvement_pct'] for r in rows]; rss=[r['rss_change_pct'] for r in rows]
    d={'schema':'cmpct-v030-pack-cache-canonical-ml-ab-v1','release_credit':False,
       'candidate_sha':_git_sha(ROOT),'control_sha':_git_sha(a.control_root),'pairs':a.pairs,'rows':rows,
       'median_wall_improvement_pct':statistics.median(walls),'median_rss_change_pct':statistics.median(rss),
       'required_wall_improvement_pct_from_authority_1_42957_to_1_25':(1-1.25/1.429574301832984)*100,
       'claim_boundary':'Direct exact-parent canonical v0.30 ML pack A/B; unchanged full runtime gate still owns release credit.'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
