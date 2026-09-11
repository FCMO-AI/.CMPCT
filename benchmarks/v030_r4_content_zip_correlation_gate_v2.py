from __future__ import annotations

"""Second content-ZIP admission falsifier.

V1 was falsified by two hostile controls: (CRC=0,size=0) could manufacture a signal and a real correlated pair
admitted unrelated passengers because admission was cohort-wide.

V2 predictor, fixed before result-bearing execution:
- observe supported ZIP central-directory member signatures after the 4-byte PK gate;
- ignore zero-length signatures;
- for each valid container, sum unique positive member sizes whose (CRC32,size) signature occurs in at least one
  *other* valid container;
- admit a hidden container iff its own shared_positive_bytes > 0;
- explicit .zip/.whl paths retain the existing behavior.

The signal is only an opportunity gate. Exact VZIP recipe construction, extraction and sampled range checks remain the
proof. This V2 deliberately has no tuned byte threshold: the experiment asks whether removing the two causal V1 flaws
is already sufficient. A later tiny-shared-byte hostile control may prove that an economic lower bound is needed.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import v030_r4_content_zip_builder as CZ
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT

RANGE=4096
EXPLICIT={'.zip','.whl'}
MAX_OBSERVED_ENTRIES=8192


def _observe(root: Path):
    valid={}; sigs_by_path={}; observed=plausible=cap_reject=sniffed=0
    cpu0=time.process_time()
    for p in sorted(q for q in root.rglob('*') if q.is_file() and not q.is_symlink()):
        rp=p.resolve(); observed+=1
        try:
            size=p.stat().st_size; sniffed+=min(4,size)
            if size<64: valid[rp]=False; continue
            with p.open('rb') as fh: magic=fh.read(4)
            if magic!=b'PK\x03\x04': valid[rp]=False; continue
            plausible+=1
            with zipfile.ZipFile(p) as z:
                infos=[i for i in z.infolist() if not i.is_dir()]
                if not infos or len(infos)>MAX_OBSERVED_ENTRIES:
                    if len(infos)>MAX_OBSERVED_ENTRIES: cap_reject+=1
                    valid[rp]=False; continue
                if any(i.compress_type not in CZ.SUPPORTED for i in infos): valid[rp]=False; continue
                first=infos[0]
                with z.open(first) as r: r.read(min(first.file_size,4096))
                sigs_by_path[rp]={(int(i.CRC),int(i.file_size)) for i in infos}
                valid[rp]=True
        except Exception:
            valid[rp]=False
    owners=defaultdict(set)
    for p,sigs in sigs_by_path.items():
        for sig in sigs:
            if sig[1]>0: owners[sig].add(p)
    shared_positive={}
    for p,sigs in sigs_by_path.items():
        shared_positive[p]=sum(size for crc,size in sigs if size>0 and len(owners[(crc,size)])>=2)
    hidden={p for p,ok in valid.items() if ok and p.suffix.lower() not in EXPLICIT}
    admitted={p for p in hidden if shared_positive.get(p,0)>0}
    return valid,admitted,{
        'files_observed':observed,'plausible_pk_files':plausible,'valid_zip_files':sum(valid.values()),
        'hidden_valid_zip_files':len(hidden),'admitted_hidden_zip_files':len(admitted),
        'entry_cap_rejections':cap_reject,'sniffed_magic_bytes':sniffed,'observation_cpu_s':time.process_time()-cpu0,
        'containers_with_positive_shared_bytes':sum(v>0 for v in shared_positive.values()),
        'shared_positive_bytes_by_path':{str(p.relative_to(root.resolve())):v for p,v in shared_positive.items()},
    }


class PositiveByteGateBuilder(CZ.ContentZipBuilder):
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.positive_gate_stats={}
    def scan(self):
        valid,admitted,stats=_observe(self.root); self.positive_gate_stats=stats; original=CZ._valid_zip_content
        def gate(path:Path):
            rp=Path(path).resolve(); ok=bool(valid.get(rp,False))
            if not ok:return False
            return rp.suffix.lower() in EXPLICIT or rp in admitted
        CZ._valid_zip_content=gate
        try:return super().scan()
        finally:CZ._valid_zip_content=original
    def build(self,out:Path):
        s=dict(super().build(out)); s['positive_byte_gate']=dict(self.positive_gate_stats); return s


def _build(cls,root,archive):
    c0=time.process_time(); w0=time.perf_counter(); s=dict(cls(root).build(archive)); return s,time.process_time()-c0,time.perf_counter()-w0


def _verify(archive:Path,source:Path,out:Path):
    want=PRODUCT.treehash(source); shutil.rmtree(out,ignore_errors=True); checks=[]
    with CMPCT(archive) as ar:
        virtual=[r[0] for r in ar.files if r[1]==0 and r[6] and r[6][0]==S_VZIP]
        for name in virtual:
            raw=(source/name).read_bytes(); ln=min(RANGE,len(raw)); starts=sorted({0,max(0,len(raw)//2-ln//2),max(0,len(raw)-ln)})
            for start in starts:
                if ar.read_range(name,start,ln)!=raw[start:start+ln]: raise RuntimeError(f'range mismatch {name}')
                checks.append([name,start,ln])
        ar.extractall(out,metadata=True)
    got=PRODUCT.treehash(out)
    if got!=want: raise RuntimeError(f'tree mismatch {got} != {want}')
    return {'tree_sha256':got,'vzip_files':virtual,'vzip_file_count':len(virtual),'range_checks':checks}


def _measure(suite,source,wd,accepted):
    wd.mkdir(parents=True,exist_ok=True); variants={}
    for label,cls in (('baseline',Builder),('all_valid',CZ.ContentZipBuilder),('positive_gate',PositiveByteGateBuilder)):
        arc=wd/f'{label}.cmpct'; s,c,w=_build(cls,source,arc); v=_verify(arc,source,wd/f'{label}-out')
        variants[label]={'archive_bytes':arc.stat().st_size,'create_cpu_s':c,'create_wall_s':w,'builder_stats':s,**v}
    b=variants['baseline']; a=variants['all_valid']; g=variants['positive_gate']
    return {'suite':suite,'name':source.name,'accepted_v029_bytes':int(accepted[(suite,source.name)]['accepted_v029_bytes']),**variants,
            'all_valid_saving':b['archive_bytes']-a['archive_bytes'],'gated_saving':b['archive_bytes']-g['archive_bytes']}


def _write_zip(path,members):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n,r in members:z.writestr(n,r)


def _hostiles(work:Path):
    out={}
    root=work/'h-empty'; root.mkdir(parents=True)
    _write_zip(root/'left.bin',[('empty',b''),('left',bytes(range(256))*256)])
    _write_zip(root/'right.bin',[('empty',b''),('right',bytes(reversed(range(256)))*256)])
    arc=work/'h-empty.cmpct'; s,_,_=_build(PositiveByteGateBuilder,root,arc); st=s['positive_byte_gate']
    out['empty_only']={'stats':st,'archive_bytes':arc.stat().st_size,'passes':st['admitted_hidden_zip_files']==0}
    root2=work/'h-passenger'; root2.mkdir(parents=True); shared=b'shared\n'*8192
    _write_zip(root2/'a.bin',[('shared',shared),('a',b'A'*4096)]); _write_zip(root2/'b.bin',[('shared',shared),('b',b'B'*4096)]); _write_zip(root2/'passenger.bin',[('p',bytes((i*131+17)&255 for i in range(512*1024)))])
    arc2=work/'h-passenger.cmpct'; s2,_,_=_build(PositiveByteGateBuilder,root2,arc2); st2=s2['positive_byte_gate']
    with CMPCT(arc2) as ar:vzip={r[0] for r in ar.files if r[1]==0 and r[6] and r[6][0]==S_VZIP}
    out['passenger']={'stats':st2,'vzip_files':sorted(vzip),'passes':vzip=={'a.bin','b.bin'}}
    return out


def run(work:Path):
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True); accepted=GENERAL._accepted_v029_rows()
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_zipcorr2_n')
    hostile=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_zipcorr2_h')
    repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_zipcorr2_r'); repair.install_generation_hooks(neutral)
    rows=[]
    for suite,generator,root in (('neutral_hostile_v1',neutral,work/'neutral'),('resemblance_hostile_v1',hostile,work/'resemblance')):
        generator.build(root)
        if suite=='neutral_hostile_v1':repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            row=_measure(suite,source,work/'rows'/suite/source.name,accepted);rows.append(row)
            gs=row['positive_gate']['builder_stats'].get('positive_byte_gate',{})
            print(json.dumps({'suite':suite,'name':source.name,'base':row['baseline']['archive_bytes'],'all':row['all_valid']['archive_bytes'],'gate':row['positive_gate']['archive_bytes'],'admitted':gs.get('admitted_hidden_zip_files'),'shared':gs.get('shared_positive_bytes_by_path')}),flush=True)
    h=_hostiles(work/'hostiles')
    base=sum(r['baseline']['archive_bytes'] for r in rows); allb=sum(r['all_valid']['archive_bytes'] for r in rows); gate=sum(r['positive_gate']['archive_bytes'] for r in rows)
    saving_all=base-allb; saving_gate=base-gate; reg=[f"{r['suite']}/{r['name']}" for r in rows if r['positive_gate']['archive_bytes']>r['baseline']['archive_bytes']]
    office=next(r for r in rows if r['name']=='02_office_workspace'); analytics=next(r for r in rows if r['name']=='04_analytics_and_database')
    exact=all(r['positive_gate']['tree_sha256']==r['baseline']['tree_sha256'] for r in rows)
    retain=saving_gate/max(1,saving_all)
    return {'schema':'cmpct-v030-r4-content-zip-positive-byte-gate-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'rows':rows,'hostiles':h,
            'totals':{'workloads':len(rows),'baseline_bytes':base,'all_valid_bytes':allb,'positive_gate_bytes':gate,'all_valid_saving':saving_all,'positive_gate_saving':saving_gate,'retention_fraction':retain,
                      'baseline_cpu_s':sum(r['baseline']['create_cpu_s'] for r in rows),'all_valid_cpu_s':sum(r['all_valid']['create_cpu_s'] for r in rows),'positive_gate_cpu_s':sum(r['positive_gate']['create_cpu_s'] for r in rows),'regressed_rows':reg},
            'hypothesis':{'all_trees_exact':exact,'zero_byte_regressions':not reg,'office_retains_all_valid_bytes':office['positive_gate']['archive_bytes']==office['all_valid']['archive_bytes'],
                          'analytics_returns_to_baseline':analytics['positive_gate']['archive_bytes']==analytics['baseline']['archive_bytes'],'retains_at_least_99_9pct_saving':retain>=.999,
                          'empty_signature_hostile_passes':h['empty_only']['passes'],'unrelated_passenger_hostile_passes':h['passenger']['passes'],
                          'supported_for_next_hardening':exact and not reg and office['positive_gate']['archive_bytes']==office['all_valid']['archive_bytes'] and analytics['positive_gate']['archive_bytes']==analytics['baseline']['archive_bytes'] and retain>=.999 and h['empty_only']['passes'] and h['passenger']['passes']},
            'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'format_changed':False,'reader_changed':False,'positive_shared_bytes_is_hint_not_proof':True},
            'next_if_supported':'attack tiny-positive-sharing economics and ZIP parser resource bounds; fuse observation into canonical scan before repeated CPU/RSS/locality receipts',
            'next_if_falsified':'preserve negative; do not tune by workload; inspect exact failing row/control and derive next causal predicate'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-positive-gate-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-positive-gate.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'totals':r['totals'],'hypothesis':r['hypothesis']},indent=2))
if __name__=='__main__':main()
