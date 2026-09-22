from __future__ import annotations
"""Three-repetition full-matrix rung for information-yield + bounded-regret exact Deflate search."""
import argparse,hashlib,json,multiprocessing as mp,os,resource,statistics,shutil,zlib
from pathlib import Path
from benchmarks import v030_r4_content_zip_information_yield_gate as YIELD
from cmpct import codec
from cmpct.codec import S_PACK
from cmpct.reader import CMPCT
ORDER=(6,0,1,2,3,4,5,7,8,9);REPS=3

def _search(raw:bytes,target:bytes):
    for level in ORDER:
        co=zlib.compressobj(level,zlib.DEFLATED,-15)
        if co.compress(raw)+co.flush()==target:return level
    return None

def _pack_locality(work:Path):
    checks=[]
    for suite,root in (('neutral_hostile_v1',work/'neutral'),('resemblance_hostile_v1',work/'resemblance')):
        rows=work/'rows'/suite
        if not rows.exists():continue
        for wd in sorted(p for p in rows.iterdir() if p.is_dir()):
            arc=wd/'yield_gate.cmpct';source=root/wd.name
            if not arc.exists():continue
            with CMPCT(arc) as ar:
                for rec in ar.files:
                    if rec[1]!=0 or not rec[6] or rec[6][0]!=S_PACK:continue
                    name=rec[0];raw=(source/name).read_bytes();ln=min(4096,len(raw));starts=sorted({0,max(0,len(raw)//2-ln//2),max(0,len(raw)-ln)})
                    for start in starts:
                        got=ar.read_range(name,start,ln)
                        if got!=raw[start:start+ln]:raise RuntimeError(f'S_PACK range mismatch {suite}/{wd.name}/{name}')
                        checks.append([suite,wd.name,name,start,ln])
    return checks

def _child(i:int,root:str,conn):
    work=Path(root)/f'rep-{i}';old=codec.deflate_level_for;codec.deflate_level_for=_search
    try:d=YIELD.run(work);packs=_pack_locality(work)
    finally:codec.deflate_level_for=old
    try:conn.send({'rep':i,'result':d,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'pack_range_checks':packs})
    finally:conn.close()

def run(root:Path):
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);ctx=mp.get_context('spawn');reps=[]
    for i in range(REPS):
        # Do not join before draining the IPC payload. The full matrix result is larger than a
        # typical pipe buffer: Queue.put() + parent join() can deadlock after the child has finished
        # all scientific work but before it can flush the result. A one-way Pipe lets the parent
        # receive concurrently, while poll() still preserves fail-fast child-exit diagnostics.
        parent,child=ctx.Pipe(duplex=False);p=ctx.Process(target=_child,args=(i,str(root),child));p.start();child.close()
        while not parent.poll(1.0):
            if not p.is_alive():
                p.join();raise RuntimeError(f'rep {i} exited before evidence payload: {p.exitcode}')
        payload=parent.recv();parent.close();p.join()
        if p.exitcode!=0:raise RuntimeError(f'rep {i} failed: {p.exitcode}')
        reps.append(payload)
    keys=[(r['suite'],r['name']) for r in reps[0]['result']['rows']]
    if any([(r['suite'],r['name']) for r in x['result']['rows']]!=keys for x in reps):raise RuntimeError('row identity drift')
    rows=[];reg=[]
    for j,key in enumerate(keys):
        rr=[x['result']['rows'][j] for x in reps];sizes={r['yield_gate']['archive_bytes'] for r in rr};trees={r['yield_gate']['tree_sha256'] for r in rr};adm={r['yield_gate']['stats']['information_yield_gate']['admitted_hidden_zip_files'] for r in rr}
        if len(sizes)!=1 or len(trees)!=1 or len(adm)!=1:raise RuntimeError(f'nondeterministic {key}')
        base=rr[0]['baseline']['archive_bytes'];size=next(iter(sizes));delta=base-size
        if delta<0:reg.append('/'.join(key))
        rows.append({'suite':key[0],'name':key[1],'baseline_bytes':base,'fast_gate_bytes':size,'saving_bytes':delta,'admitted':next(iter(adm)),'cpu_median_s':statistics.median(r['yield_gate']['create_cpu_s'] for r in rr),'wall_median_s':statistics.median(r['yield_gate']['create_wall_s'] for r in rr)})
    totals={'baseline_bytes':sum(r['baseline_bytes'] for r in rows),'fast_gate_bytes':sum(r['fast_gate_bytes'] for r in rows),'saving_bytes':sum(r['saving_bytes'] for r in rows),'regressed_rows':reg,'fast_gate_cpu_median_sum_s':sum(r['cpu_median_s'] for r in rows),'fast_gate_wall_median_sum_s':sum(r['wall_median_s'] for r in rows),'peak_rss_median_kib':statistics.median(x['peak_rss_kib'] for x in reps),'pack_range_checks':sum(len(x['pack_range_checks']) for x in reps)}
    hostiles=[x['result']['hostiles'] for x in reps];supported=not reg and all(all(v['passes'] for v in h.values()) for h in hostiles)
    return {'schema':'cmpct-v030-content-zip-fast-search-generalization-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'level_order':list(ORDER),'rows':rows,'totals':totals,'hostiles_by_rep':hostiles,'hypothesis':{'zero_byte_regressions':not reg,'all_inherited_hostiles_pass':all(all(v['passes'] for v in h.values()) for h in hostiles),'supported_for_productization_design':supported},'contract':{'research_only':True,'shipping_changed':False,'format_changed':False,'three_fresh_process_repetitions':True,'exact_tree_and_vzip_ranges_inherited':True,'s_pack_ranges_charged':True},'next_if_supported':'design a small canonical implementation without scan fusion; compare strongest-current external matrix before promotion','next_if_falsified':'preserve failing row; do not retune order or admission post hoc'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/fast-search-generalization-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/fast-search-generalization.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d['totals'],indent=2));assert d['hypothesis']['supported_for_productization_design']
if __name__=='__main__':main()
