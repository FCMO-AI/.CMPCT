from __future__ import annotations

"""Frozen R33 cProfile attribution of residual R32 create-time debt."""
import argparse,cProfile,hashlib,json,os,pstats,shutil,statistics,time
from pathlib import Path
from benchmarks import v030_r32_regenerable_deflate_output_dead_zstd_elision as R32
from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r33-regenerable-deflate-residual-phase-attribution-v1'
REPS=3
ARMS=('release-all-exact','no-ordinary-zstd')
EXPECTED={
 'full-backups':{
  'release-all-exact':(8088619,'dc789b874da673584046af26e7f21f593cfcc1fa8cd365bc6298942c2f752eb7'),
  'no-ordinary-zstd':(8056193,'d812ffa7a0002e4e137e578918010d5ce00dfb8055a4c9fb188ebbd9212c79e9')},
 'nested-only':{
  'release-all-exact':(2231160,'6d6973cb4931edcc2ed776b8fdb8500dc80da084f0b06681e87eff544646d6ef'),
  'no-ordinary-zstd':(2197414,'b2cb86d7c51eecec959989b3e592f344311c3da32af3d47ed1251284f2223bea')}}

def _sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def _interesting(fn):
 s=fn.replace('\\','/')
 return '/src/cmpct/' in s or s.endswith('v030_r32_regenerable_deflate_output_dead_zstd_elision.py') or 'entropygraph_v030_release_product' in s

def _one(arm,src,out):
 pr=cProfile.Profile();t=time.perf_counter();ret=pr.runcall(R32._build_arm,arm,src,out);wall=time.perf_counter()-t
 v=dict(PRODUCT.strong_verify(out))
 if not v.get('ok') or v.get('tree_sha256')!=PRODUCT.treehash(src):raise RuntimeError(f'{arm} verification/tree failure')
 st=pstats.Stats(pr);rows=[]
 for (fn,line,name),(cc,nc,tt,ct,_callers) in st.stats.items():
  if _interesting(fn):rows.append({'signature':f'{Path(fn).name}:{line}:{name}','calls':int(nc),'internal_s':float(tt),'cumulative_s':float(ct)})
 rows.sort(key=lambda x:(-x['cumulative_s'],x['signature']))
 return {'wall_s':wall,'archive_bytes':Path(out).stat().st_size,'archive_sha256':_sha(out),'strong_verify_ok':True,'profile':rows,'top40':rows[:40],'build_stats':ret[0]}

def _median(reps):
 sigs=sorted({x['signature'] for r in reps for x in r['profile']});out={}
 for sig in sigs:
  vals=[]
  for r in reps:
   vals.append(next((x for x in r['profile'] if x['signature']==sig),{'calls':0,'internal_s':0.0,'cumulative_s':0.0}))
  out[sig]={'calls':int(statistics.median(x['calls'] for x in vals)),'internal_s':float(statistics.median(x['internal_s'] for x in vals)),'cumulative_s':float(statistics.median(x['cumulative_s'] for x in vals))}
 return out

def _sources(root):
 full=None;expected=None;observed=None
 for suite,src,exp in A._build_corpora(root/'corpus'):
  if suite==R32.TARGET_SUITE and src.name==R32.TARGET_NAME:
   full=src;expected=str(exp['tree_sha256']);observed=A.RC.treehash(src);break
 if full is None or observed!=expected:raise RuntimeError('R33 frozen corpus identity failure')
 nf=full/R32.NESTED_MEMBER;nested=root/'nested-only';nested.mkdir(parents=True);shutil.copyfile(nf,nested/R32.NESTED_MEMBER)
 return {'full-backups':full,'nested-only':nested},{'tree_sha256':observed,'nested_sha256':_sha(nf)}

def run(root):
 shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True)
 sources,identity=_sources(root);res={'schema':SCHEMA,'status':'diagnostic-only-no-release-credit','evidence_head':os.environ.get('CMPCT_EVIDENCE_HEAD',''),'parent_r32_head':'0b1f3cd653f0e2489964b93cdd19fa8324adda2e','identity':identity,'repetitions':REPS,'targets':{}};ok=True
 for tn,src in sources.items():
  t={'arms':{}}
  for arm in ARMS:
   reps=[]
   for i in range(REPS):
    out=root/'archives'/tn/arm/f'{i}.cmpct';out.parent.mkdir(parents=True,exist_ok=True);r=_one(arm,src,out);eb,es=EXPECTED[tn][arm];r['identity_ok']=r['archive_bytes']==eb and r['archive_sha256']==es;ok=ok and r['identity_ok'];reps.append(r)
   t['arms'][arm]={'repetitions':reps,'median_wall_s':float(statistics.median(r['wall_s'] for r in reps)),'median_profile':_median(reps)}
  base=t['arms']['release-all-exact']['median_profile'];cand=t['arms']['no-ordinary-zstd']['median_profile'];d=[]
  for sig in sorted(set(base)|set(cand)):
   b=base.get(sig,{'cumulative_s':0.0,'internal_s':0.0,'calls':0});c=cand.get(sig,{'cumulative_s':0.0,'internal_s':0.0,'calls':0});delta=c['cumulative_s']-b['cumulative_s']
   if delta>0:d.append({'signature':sig,'cumulative_delta_s':delta,'internal_delta_s':c['internal_s']-b['internal_s'],'call_delta':c['calls']-b['calls']})
  d.sort(key=lambda x:(-x['cumulative_delta_s'],x['signature']));t['positive_cumulative_deltas']=d[:40];res['targets'][tn]=t
 if not ok:res['decision']='SUBSTRATE_OR_IDENTITY_FAILURE';return res
 f={x['signature']:x for x in res['targets']['full-backups']['positive_cumulative_deltas']};n={x['signature']:x for x in res['targets']['nested-only']['positive_cumulative_deltas']};owners=[]
 for sig,x in n.items():
  y=f.get(sig)
  if y and x['cumulative_delta_s']>=0.010 and y['cumulative_delta_s']>0:owners.append({'signature':sig,'nested_delta_s':x['cumulative_delta_s'],'full_delta_s':y['cumulative_delta_s']})
 owners.sort(key=lambda x:(-x['nested_delta_s'],x['signature']));res['localized_owners']=owners;res['decision']='PHASE_OWNER_LOCALIZED' if owners else 'RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR';return res

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':r['decision'],'output':str(a.output)}))
if __name__=='__main__':main()
