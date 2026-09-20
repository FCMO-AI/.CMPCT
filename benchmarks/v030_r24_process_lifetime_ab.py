from __future__ import annotations
"""Fresh-process r24 lifetime A/B. Research evidence only; no release credit."""
import argparse,hashlib,json,os,resource,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def r24_child(root,out):
 from experiments import entropygraph_v030_release_product as RP
 stats=RP.C._r24_build(root,out)
 print(json.dumps({'stats':stats,'ru_maxrss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)},separators=(',',':')))
def product_child(mode,root,out):
 from experiments import entropygraph_v030_release_product as RP
 child_receipts=[]
 if mode=='isolated':
  # Shipping normally starts an r24 prebuild from profile preparation. Disable only that scheduling hook in this
  # research arm so r24 is not accidentally built once in-parent and again in the child. Grammar/policy stay exact.
  RP.C._prepare_profile_tree=RP._BASE_IMPL._ORIGINAL_PREPARE_PROFILE_TREE
  def isolated_r24(src,dst):
   env={**os.environ,'PYTHONPATH':str(ROOT)}
   p=subprocess.run([sys.executable,__file__,'--r24-child','--source',str(src),'--archive',str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
   row=json.loads([x for x in p.stdout.splitlines() if x.strip()][-1]);child_receipts.append(row);return row['stats']
  RP.C._r24_build=isolated_r24
 t0=time.perf_counter();stats=RP.build(root,out);wall=time.perf_counter()-t0;verified=RP.C.strong_verify(out)
 print(json.dumps({'mode':mode,'wall_s':wall,'parent_peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),'archive_bytes':out.stat().st_size,'archive_sha256':sha(out),'selected':stats.get('selected'),'format_revision':stats.get('format_revision'),'tree_sha256':verified.get('tree_sha256'),'r24_child_receipts':child_receipts},separators=(',',':')))
def invoke(mode,source,out):
 env={**os.environ,'PYTHONPATH':str(ROOT)};p=subprocess.run([sys.executable,__file__,'--product-child',mode,'--source',str(source),'--archive',str(out)],cwd=ROOT,env=env,check=True,capture_output=True,text=True);return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--r24-child',action='store_true');ap.add_argument('--product-child',choices=('base','isolated'));ap.add_argument('--source',type=Path);ap.add_argument('--archive',type=Path);ap.add_argument('--work-root',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 if a.r24_child:r24_child(a.source,a.archive);return
 if a.product_child:product_child(a.product_child,a.source,a.archive);return
 from benchmarks import v030_release_performance as PERF
 shutil.rmtree(a.work_root,ignore_errors=True);a.work_root.mkdir(parents=True);source=PERF._build_corpora(a.work_root/'corpus')[("neutral_hostile_v1","09_ml_artifacts")]
 rows=[]
 for rep,order in enumerate((('base','isolated'),('isolated','base'))):
  pair={'rep':rep}
  for mode in order:pair[mode]=invoke(mode,source,a.work_root/f'ml-{rep}-{mode}.cmpct')
  pair['identity_equal']=all(pair['base'][k]==pair['isolated'][k] for k in ('archive_bytes','archive_sha256','selected','format_revision','tree_sha256'))
  pair['parent_rss_ratio']=pair['isolated']['parent_peak_rss_kib']/pair['base']['parent_peak_rss_kib'];pair['wall_ratio']=pair['isolated']['wall_s']/pair['base']['wall_s'];rows.append(pair)
 result={'schema':'cmpct-v030-r24-process-lifetime-ab-v1','release_credit':False,'rows':rows,'all_exact':all(r['identity_equal'] for r in rows),'claim_boundary':'Frozen ML whole promoted build; canonical r24 construction and its allocator lifetime move to a short-lived child; exact product identity and parent RSS/wall charged; child peak exposed separately.'}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['all_exact']:raise SystemExit('r24 process lifetime changed product identity')
if __name__=='__main__':main()
