from __future__ import annotations
import argparse,json,shutil,traceback
from pathlib import Path
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks import v030_r24_pathdict_cdict_proxy_gate_v14 as V14

def run(root:Path)->dict:
 shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True,exist_ok=True);paths,ids=CUR._build(root/'corpus');fp=CUR._fingerprint(ids);rows={};errors={}
 for ident in ids:
  key=f"{ident['suite']}/{ident['name']}"
  try:rows[key]=V14._one(paths[key],root/'work'/ident['suite']/ident['name'])
  except Exception as e:errors[key]={'type':type(e).__name__,'message':str(e),'traceback':''.join(traceback.format_exception(type(e),e,e.__traceback__,limit=8))}
 bad=[k for k,r in rows.items() if not r['identity_pass']];proxy=sum(r['gate']['proxy_calls'] for r in rows.values());exact=sum(r['gate']['exact_calls'] for r in rows.values());pr=sum(r['gate']['proxy_rejects'] for r in rows.values());er=sum(r['gate']['exact_rejects_after_proxy_accept'] for r in rows.values());pc=sum(r['gate']['proxy_cpu_s'] for r in rows.values());ec=sum(r['gate']['exact_cpu_s'] for r in rows.values());ci=sum(r['clean']['independent']['cpu_s'] for r in rows.values());cw=sum(r['clean']['independent']['wall_s'] for r in rows.values());fc=sum(r['fused']['portfolio_cpu_s'] for r in rows.values());fw=sum(r['fused']['portfolio_wall_s'] for r in rows.values())
 verdict='CURRENT15_PROXY_EXECUTION_BLOCKED' if errors else ('RETIRE_CDICT_PROXY_GATE' if bad or er else 'CURRENT15_CDICT_PROXY_GATE_GENERALIZES')
 return {'schema':'cmpct-v030-r24-pathdict-cdict-proxy-current15-v1','release_credit':False,'canonical_builder_changed':False,'genesis_rescore':False,'corpus_fingerprint':fp,'identities':ids,'rows':rows,'execution_errors':errors,'identity_failures':bad,'aggregate':{'completed_workloads':len(rows),'proxy_calls':proxy,'exact_calls':exact,'proxy_rejects':pr,'exact_rejects_after_proxy_accept':er,'call_reduction':proxy-exact,'call_reduction_pct':((proxy-exact)/proxy*100 if proxy else 0),'proxy_cpu_s':pc,'exact_cpu_s':ec,'single_independent_cpu_s':ci,'single_independent_wall_s':cw,'fused_portfolio_cpu_s':fc,'fused_portfolio_wall_s':fw,'cpu_ratio_vs_single_independent':fc/ci if ci else None,'wall_ratio_vs_single_independent':fw/cw if cw else None},'verdict':verdict}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v15-work'));ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v15.json'));a=ap.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps({'verdict':d['verdict'],'fingerprint':d['corpus_fingerprint'],'identity_failures':d['identity_failures'],'execution_errors':d['execution_errors'],'aggregate':d['aggregate']},indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
