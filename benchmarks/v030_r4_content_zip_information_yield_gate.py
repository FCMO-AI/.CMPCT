from __future__ import annotations

"""Bounded information-yield gate for optional hidden-ZIP virtualization.

This is a research falsifier, not a shipping policy. It composes three independently observed facts:
1) hidden ZIPs can expose large existing-S_VZIP wins;
2) any-positive reuse is unsafe (1 shared byte increased archive size);
3) the two-container break-even ladder measured a stable 406..537 B representation/control tax.

Before this result-bearing run we round the worst observed tax up to 544 B (17 * 32-byte units) and require a 4x
safety/compute margin: at least 2176 B of central-directory-visible repeated compressed-stream mass owned by the
candidate itself.  This deliberately forfeits the marginal 1 KiB ladder win; it is a conservative research bound,
not a fitted density target.

The descriptor is (CRC32, logical size, compression method, compressed size).  It is only an opportunity hint.
Exact recipe construction/tree/range verification remain proof. Hidden candidates first pass the bounded EOCD
preflight; explicit .zip/.whl behavior remains unchanged.
"""

import argparse
from collections import defaultdict
import json, os, shutil, time, zipfile
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import v030_r4_content_zip_builder as CZ
from experiments.v030_r4_zip_preflight import hidden_zip_preflight
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT

EXPLICIT={'.zip','.whl'}
CONTROL_COST_BOUND=544
SAFETY_MULTIPLIER=4
MIN_EXPECTED_REUSE=CONTROL_COST_BOUND*SAFETY_MULTIPLIER
RANGE=4096


def _observe(root:Path):
    descriptors={}; valid={}; preflight_rejects=defaultdict(int); cpu0=time.process_time(); files=0
    for p in sorted(q for q in root.rglob('*') if q.is_file() and not q.is_symlink()):
        files+=1; rp=p.resolve(); explicit=p.suffix.lower() in EXPLICIT
        try:
            if not explicit:
                pf=hidden_zip_preflight(p)
                if not pf.eligible:
                    valid[rp]=False; preflight_rejects[pf.reason]+=1; continue
            with zipfile.ZipFile(p) as z:
                infos=[i for i in z.infolist() if not i.is_dir()]
                if not infos or any(i.compress_type not in CZ.SUPPORTED for i in infos): valid[rp]=False; continue
                descriptors[rp]={(int(i.CRC),int(i.file_size),int(i.compress_type),int(i.compress_size)) for i in infos if i.file_size>0}
                valid[rp]=True
        except Exception:
            valid[rp]=False
    owners=defaultdict(set)
    for p,ds in descriptors.items():
        for d in ds: owners[d].add(p)
    reuse={p:sum(d[3] for d in ds if len(owners[d])>=2) for p,ds in descriptors.items()}
    hidden={p for p,ok in valid.items() if ok and p.suffix.lower() not in EXPLICIT}
    admitted={p for p in hidden if reuse.get(p,0)>=MIN_EXPECTED_REUSE}
    return valid,admitted,{'files_observed':files,'hidden_valid_zip_files':len(hidden),'admitted_hidden_zip_files':len(admitted),
        'predicted_reusable_compressed_bytes_by_path':{str(p.relative_to(root.resolve())):v for p,v in reuse.items()},
        'control_cost_bound_bytes':CONTROL_COST_BOUND,'safety_multiplier':SAFETY_MULTIPLIER,'min_expected_reuse_bytes':MIN_EXPECTED_REUSE,
        'preflight_rejects':dict(preflight_rejects),'observation_cpu_s':time.process_time()-cpu0}


class InformationYieldBuilder(CZ.ContentZipBuilder):
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.information_yield_stats={}
    def scan(self):
        valid,admitted,stats=_observe(self.root); self.information_yield_stats=stats; original=CZ._valid_zip_content
        def gate(path:Path):
            rp=Path(path).resolve(); ok=bool(valid.get(rp,False))
            return ok and (rp.suffix.lower() in EXPLICIT or rp in admitted)
        CZ._valid_zip_content=gate
        try:return super().scan()
        finally:CZ._valid_zip_content=original
    def build(self,out:Path):
        s=dict(super().build(out));s['information_yield_gate']=dict(self.information_yield_stats);return s


def _build(cls,root,arc):
    c=time.process_time();w=time.perf_counter();s=dict(cls(root).build(arc));return s,time.process_time()-c,time.perf_counter()-w

def _verify(arc,source,out):
    want=PRODUCT.treehash(source);shutil.rmtree(out,ignore_errors=True);checks=[]
    with CMPCT(arc) as ar:
        virtual=[r[0] for r in ar.files if r[1]==0 and r[6] and r[6][0]==S_VZIP]
        for name in virtual:
            raw=(source/name).read_bytes();ln=min(RANGE,len(raw))
            for start in sorted({0,max(0,len(raw)//2-ln//2),max(0,len(raw)-ln)}):
                if ar.read_range(name,start,ln)!=raw[start:start+ln]:raise RuntimeError(f'range mismatch {name}')
                checks.append([name,start,ln])
        ar.extractall(out,metadata=True)
    got=PRODUCT.treehash(out)
    if got!=want:raise RuntimeError(f'tree mismatch {got} != {want}')
    return {'tree_sha256':got,'vzip_files':virtual,'vzip_file_count':len(virtual),'range_checks':checks}

def _measure(suite,source,wd,accepted):
    wd.mkdir(parents=True,exist_ok=True);vs={}
    for label,cls in (('baseline',Builder),('yield_gate',InformationYieldBuilder)):
        arc=wd/f'{label}.cmpct';s,c,w=_build(cls,source,arc);v=_verify(arc,source,wd/f'{label}-out');vs[label]={'archive_bytes':arc.stat().st_size,'create_cpu_s':c,'create_wall_s':w,'stats':s,**v}
    return {'suite':suite,'name':source.name,'accepted_v029_bytes':int(accepted[(suite,source.name)]['accepted_v029_bytes']),**vs,
            'saving_bytes':vs['baseline']['archive_bytes']-vs['yield_gate']['archive_bytes']}

def _zip(path,members,level=6):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=level) as z:
        for n,b in members:z.writestr(n,b)

def _hostiles(work:Path):
    work.mkdir(parents=True,exist_ok=True);out={}
    # Tiny-positive signal must be rejected by the information-yield budget.
    r=work/'tiny';r.mkdir();shared=b'X';_zip(r/'a.bin',[('shared',shared),('a',os.urandom(256*1024))]);_zip(r/'b.bin',[('shared',shared),('b',os.urandom(256*1024))]);arc=work/'tiny.cmpct';s,_,_=_build(InformationYieldBuilder,r,arc);st=s['information_yield_gate'];out['tiny_positive']={'admitted':st['admitted_hidden_zip_files'],'passes':st['admitted_hidden_zip_files']==0}
    # Same logical member at different deflate levels should not count unless the observable stream descriptor also matches.
    r2=work/'different-level';r2.mkdir();raw=(b'abcdef0123456789'*16384)+(b'Z'*4096);_zip(r2/'l1.bin',[('shared',raw)],level=1);_zip(r2/'l9.bin',[('shared',raw)],level=9);arc2=work/'different-level.cmpct';s2,_,_=_build(InformationYieldBuilder,r2,arc2);st2=s2['information_yield_gate'];out['different_deflate_level']={'predicted':st2['predicted_reusable_compressed_bytes_by_path'],'admitted':st2['admitted_hidden_zip_files'],'passes':st2['admitted_hidden_zip_files']==0}
    return out

def run(work:Path):
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);accepted=GENERAL._accepted_v029_rows()
    n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_yield_n');h=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_yield_h');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_yield_r');repair.install_generation_hooks(n)
    rows=[]
    for suite,generator,root in (('neutral_hostile_v1',n,work/'neutral'),('resemblance_hostile_v1',h,work/'resemblance')):
        generator.build(root)
        if suite=='neutral_hostile_v1':repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            row=_measure(suite,source,work/'rows'/suite/source.name,accepted);rows.append(row);st=row['yield_gate']['stats']['information_yield_gate'];print(json.dumps({'suite':suite,'name':source.name,'base':row['baseline']['archive_bytes'],'gate':row['yield_gate']['archive_bytes'],'saving':row['saving_bytes'],'admitted':st['admitted_hidden_zip_files']}),flush=True)
    hostiles=_hostiles(work/'hostiles');base=sum(r['baseline']['archive_bytes'] for r in rows);gate=sum(r['yield_gate']['archive_bytes'] for r in rows);reg=[f"{r['suite']}/{r['name']}" for r in rows if r['saving_bytes']<0];office=next(r for r in rows if r['name']=='02_office_workspace');analytics=next(r for r in rows if r['name']=='04_analytics_and_database');exact=all(r['baseline']['tree_sha256']==r['yield_gate']['tree_sha256'] for r in rows)
    return {'schema':'cmpct-v030-r4-content-zip-information-yield-gate-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'rows':rows,'hostiles':hostiles,
        'totals':{'baseline_bytes':base,'yield_gate_bytes':gate,'saving_bytes':base-gate,'regressed_rows':reg,'baseline_cpu_s':sum(r['baseline']['create_cpu_s'] for r in rows),'yield_gate_cpu_s':sum(r['yield_gate']['create_cpu_s'] for r in rows)},
        'hypothesis':{'all_trees_exact':exact,'zero_byte_regressions':not reg,'office_saves_at_least_9MB':office['saving_bytes']>=9_000_000,'analytics_returns_to_baseline':analytics['saving_bytes']==0,'tiny_positive_rejected':hostiles['tiny_positive']['passes'],'different_deflate_level_not_overclaimed':hostiles['different_deflate_level']['passes'],
            'supported_for_fused_research_integration':exact and not reg and office['saving_bytes']>=9_000_000 and analytics['saving_bytes']==0 and all(v['passes'] for v in hostiles.values())},
        'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'format_changed':False,'reader_changed':False,'preflight_composed':True,'threshold_preregistered_from_control_cost_envelope':True,'workload_identity_used':False},
        'next_if_supported':'factor preflight+descriptor observation into one canonical research scan cache, remove the second traversal, then measure repeated fresh-process CPU/RSS/S_PACK locality before any shipping patch',
        'next_if_falsified':'preserve the exact failing row/control; do not retune the multiplier post hoc; derive a better cost model from the failed mechanism'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-yield-gate-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-yield-gate.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'totals':r['totals'],'hypothesis':r['hypothesis'],'hostiles':r['hostiles']},indent=2))
if __name__=='__main__':main()
