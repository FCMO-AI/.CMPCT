from __future__ import annotations
"""Gifted native-simplification oracle for #205; never product credit.

Can hidden winners use only retained-secondary Deflate mode 1 (already native-supported) while preserving
a material byte win? Every exact hidden stream is fully charged as an ordinary opaque blob; canonical
mode 0 is disabled. Same-tree A-B-B-A, fresh processes, emitted recipe modes verified from the archive.
"""
import argparse,json,os,shutil,statistics,subprocess,sys
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from benchmarks import v030_hidden_zip_resource_gate as RESOURCE
REPS=3

def _mode1_child(source:Path,arc:Path,out:Path,result:Path):
    os.environ['CMPCT_DEFLATE_REUSE_MIN']=str(1<<60)
    from cmpct import builder_hidden_zip as BRIDGE
    from cmpct.codec import sha
    def retain_mode1(builder,cohort):
        for staged in cohort.staged.values():
            for _raw,_hint,stream,_ref in staged.candidates:
                if stream is None:continue
                stream_hash=sha(stream);got=builder.add_content(stream,'.opaque-deflate')
                if got!=stream_hash:raise RuntimeError('mode1 oracle lost exact stream identity')
                builder.secondary_stream_hashes.add(stream_hash)
    BRIDGE._retain_exact_streams_for_hidden_winners=retain_mode1
    RESOURCE._child(source,'candidate',arc,out,result)
    from cmpct.reader import CMPCT
    with CMPCT(arc) as reader:
        modes=[]
        for recipe in reader.index.get('recipes',[]):
            for payload in recipe[2]:
                if int(payload[1])==8:modes.append(int(payload[2]))
    if not modes or any(mode!=1 for mode in modes):raise RuntimeError(f'mode1 oracle emitted unexpected Deflate modes: {sorted(set(modes))}')
    row=json.loads(result.read_text());row['deflate_stream_modes']=modes;row['mode1_only_verified']=True;result.write_text(json.dumps(row,indent=2)+'\n')

def _run(script:Path,resource:Path,source:Path,arm:str,root:Path,tag:str):
    arc=root/f'{tag}.cmpct';out=root/f'{tag}-out';result=root/f'{tag}.json';env=dict(os.environ);env['PYTHONPATH']=os.getcwd()
    if arm=='base':cmd=[sys.executable,os.fspath(resource),'--child','--source',os.fspath(source),'--arm','base','--arc',os.fspath(arc),'--extract',os.fspath(out),'--child-output',os.fspath(result)]
    else:cmd=[sys.executable,os.fspath(script),'--child','--source',os.fspath(source),'--arc',os.fspath(arc),'--extract',os.fspath(out),'--child-output',os.fspath(result)]
    subprocess.run(cmd,check=True,env=env);return json.loads(result.read_text())

def _med(rows,key):return float(statistics.median(float(x[key]) for x in rows))
def run(root:Path):
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);script=Path(__file__).resolve();resource=Path(RESOURCE.__file__).resolve();reps=[]
    for rep in range(REPS):
        work=root/f'rep-{rep}';suite=work/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_hidden_mode1_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_hidden_mode1_r_{rep}');repair.install_generation_hooks(n);n.build(suite);repair.normalize_root(suite);source=suite/'02_office_workspace';want=PRODUCT.treehash(source);rr=work/'runs';rr.mkdir(parents=True)
        seq=[_run(script,resource,source,'base',rr,'0-base'),_run(script,resource,source,'mode1',rr,'1-mode1'),_run(script,resource,source,'mode1',rr,'2-mode1'),_run(script,resource,source,'base',rr,'3-base')]
        if any(x['tree_sha256']!=want for x in seq):raise RuntimeError('mode1 oracle tree identity drift')
        base=[seq[0],seq[3]];cand=[seq[1],seq[2]]
        if not all(x.get('mode1_only_verified') for x in cand):raise RuntimeError('mode1 oracle verification missing')
        reps.append({'rep':rep,'source_tree_sha256':want,'saving_bytes':base[0]['archive_bytes']-cand[0]['archive_bytes'],'base_bytes':base[0]['archive_bytes'],'mode1_bytes':cand[0]['archive_bytes'],'mode1_deflate_payloads':len(cand[0]['deflate_stream_modes']),'base_create_wall_s':_med(base,'create_wall_s'),'mode1_create_wall_s':_med(cand,'create_wall_s'),'base_extract_wall_s':_med(base,'extract_wall_s'),'mode1_extract_wall_s':_med(cand,'extract_wall_s'),'base_rss_kib':_med(base,'peak_rss_kib'),'mode1_rss_kib':_med(cand,'peak_rss_kib'),'base_selective_wall_s':statistics.median(x['selective_read']['wall_s'] for x in base),'mode1_selective_wall_s':statistics.median(x['selective_read']['wall_s'] for x in cand)})
    m=lambda k:statistics.median(r[k] for r in reps)
    summary={'saving_bytes_by_rep':[r['saving_bytes'] for r in reps],'saving_bytes_median':m('saving_bytes'),'mode1_deflate_payloads_median':m('mode1_deflate_payloads'),'create_wall_ratio':m('mode1_create_wall_s')/m('base_create_wall_s'),'extract_wall_ratio':m('mode1_extract_wall_s')/m('base_extract_wall_s'),'peak_rss_ratio':m('mode1_rss_kib')/m('base_rss_kib'),'selective_wall_ratio':m('mode1_selective_wall_s')/m('base_selective_wall_s')}
    return {'schema':'cmpct-v030-hidden-zip-mode1-only-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'status':'gifted charged oracle only; no product credit','representation':'hidden exact Deflate retained only as secondary mode 1; canonical mode 0 disabled; emitted recipe modes directly verified','rows':reps,'summary':summary,'decision':'prefer already-native-supported mode 1 if material gain survives full duplicate-stream charge; otherwise native mode-0 projection complexity remains justified debt'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-mode1-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-mode1-oracle.json'));p.add_argument('--child',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--arc',type=Path);p.add_argument('--extract',type=Path);p.add_argument('--child-output',type=Path);a=p.parse_args()
    if a.child:_mode1_child(a.source,a.arc,a.extract,a.child_output);return
    result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
