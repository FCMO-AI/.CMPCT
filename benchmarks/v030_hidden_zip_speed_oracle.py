from __future__ import annotations
"""Gifted max-speed oracle for #205 rehabilitation; not a product policy or promotion evaluator.

Uses Builder's existing documented CMPCT_DEFLATE_REUSE_MIN=0 maximum-speed policy to estimate how much
hidden-ZIP extraction/create debt comes from dropping exact Deflate streams, and how many byte savings that
policy gives back. Same-tree A-B-B-A, fresh child processes, three fresh Office trees.
"""
import json,os,shutil,statistics,subprocess,sys
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from benchmarks import v030_hidden_zip_resource_gate as RESOURCE
REPS=3

def _run(script:Path,source:Path,arm:str,root:Path,tag:str,*,speed:bool=False)->dict:
    arc=root/f'{tag}.cmpct';out=root/f'{tag}-out';result=root/f'{tag}.json';env=dict(os.environ);env['PYTHONPATH']=os.getcwd()
    if speed:env['CMPCT_DEFLATE_REUSE_MIN']='0'
    subprocess.run([sys.executable,os.fspath(script),'--child','--source',os.fspath(source),'--arm',arm,'--arc',os.fspath(arc),'--extract',os.fspath(out),'--child-output',os.fspath(result)],check=True,env=env)
    return json.loads(result.read_text())

def _med(rows,key):return float(statistics.median(float(x[key]) for x in rows))
def run(root:Path)->dict:
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);child=Path(RESOURCE.__file__).resolve();reps=[]
    for rep in range(REPS):
        work=root/f'rep-{rep}';suite=work/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_hidden_speed_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_hidden_speed_r_{rep}');repair.install_generation_hooks(n);n.build(suite);repair.normalize_root(suite);source=suite/'02_office_workspace';want=PRODUCT.treehash(source);rr=work/'runs';rr.mkdir(parents=True)
        seq=[_run(child,source,'base',rr,'0-base'),_run(child,source,'candidate',rr,'1-speed',speed=True),_run(child,source,'candidate',rr,'2-speed',speed=True),_run(child,source,'base',rr,'3-base')]
        if any(x['tree_sha256']!=want for x in seq):raise RuntimeError('oracle tree identity drift')
        base=[seq[0],seq[3]];speed=[seq[1],seq[2]]
        reps.append({'rep':rep,'source_tree_sha256':want,'sequence':seq,'base_bytes':base[0]['archive_bytes'],'speed_bytes':speed[0]['archive_bytes'],'saving_bytes':base[0]['archive_bytes']-speed[0]['archive_bytes'],'base_create_wall_s':_med(base,'create_wall_s'),'speed_create_wall_s':_med(speed,'create_wall_s'),'base_extract_wall_s':_med(base,'extract_wall_s'),'speed_extract_wall_s':_med(speed,'extract_wall_s'),'base_peak_rss_kib':_med(base,'peak_rss_kib'),'speed_peak_rss_kib':_med(speed,'peak_rss_kib'),'base_selective_wall_s':statistics.median(x['selective_read']['wall_s'] for x in base),'speed_selective_wall_s':statistics.median(x['selective_read']['wall_s'] for x in speed)})
    def m(k):return statistics.median(r[k] for r in reps)
    summary={'saving_bytes_by_rep':[r['saving_bytes'] for r in reps],'saving_bytes_median':m('saving_bytes'),'create_wall_ratio':m('speed_create_wall_s')/m('base_create_wall_s'),'extract_wall_ratio':m('speed_extract_wall_s')/m('base_extract_wall_s'),'peak_rss_ratio':m('speed_peak_rss_kib')/m('base_peak_rss_kib'),'selective_wall_ratio':m('speed_selective_wall_s')/m('base_selective_wall_s')}
    return {'schema':'cmpct-v030-hidden-zip-max-speed-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'policy_under_test':{'CMPCT_DEFLATE_REUSE_MIN':0,'status':'gifted oracle only; no product credit'},'repetitions':REPS,'rows':reps,'summary':summary,'question':'Can existing exact-stream retention recover runtime/selective performance while preserving material hidden-ZIP byte gain?'}

def main():
    import argparse;p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-speed-oracle-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-speed-oracle.json'));a=p.parse_args();result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
