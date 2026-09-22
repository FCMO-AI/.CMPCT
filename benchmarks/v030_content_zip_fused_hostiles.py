from __future__ import annotations
import argparse,json,os,shutil,zipfile,zlib
from pathlib import Path
from benchmarks import v030_content_zip_fused_plan_cache as FUSED
from benchmarks import v030_r4_content_zip_information_yield_gate as YIELD
from cmpct import codec

def _zip(path:Path,raw:bytes):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('shared',raw)

def run(work:Path):
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    old_cls=YIELD.InformationYieldBuilder;old_search=codec.deflate_level_for
    codec.deflate_level_for=FUSED._search
    try:
        YIELD.InformationYieldBuilder=FUSED.FusedInformationYieldBuilder
        inherited=YIELD._hostiles(work/'inherited-fused')
        # Deliberate discriminator: legacy observation counts hardlink paths as independent byte owners,
        # while fused physical planning sees the second inode reference before ownership observation.
        h=work/'hardlink-owner';h.mkdir();raw=(b'hardlink-owner-proof-'*16384)+os.urandom(1024)
        a=h/'a.bin';b=h/'b.bin';_zip(a,raw);os.link(a,b)
        base_arc=work/'hardlink-legacy.cmpct';fused_arc=work/'hardlink-fused.cmpct'
        YIELD.InformationYieldBuilder=old_cls
        legacy,_,_=YIELD._build(old_cls,h,base_arc)
        fused,_,_=YIELD._build(FUSED.FusedInformationYieldBuilder,h,fused_arc)
        hardlink={'legacy_admitted':legacy['information_yield_gate']['admitted_hidden_zip_files'],'fused_admitted':fused['information_yield_gate']['admitted_hidden_zip_files'],'legacy_bytes':base_arc.stat().st_size,'fused_bytes':fused_arc.stat().st_size,'physical_owner_correction_observed':legacy['information_yield_gate']['admitted_hidden_zip_files']>fused['information_yield_gate']['admitted_hidden_zip_files']}
    finally:
        YIELD.InformationYieldBuilder=old_cls;codec.deflate_level_for=old_search
    return {'schema':'cmpct-v030-content-zip-fused-hostiles-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'inherited_hostiles':inherited,'hardlink_owner_discriminator':hardlink,'inherited_hostiles_pass':all(v['passes'] for v in inherited.values()),'contract':{'hardlink_is_diagnostic_not_promotion_credit':True,'generic_admission_equivalence_not_claimed':True}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/fused-hostiles-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/fused-hostiles.json'));a=p.parse_args();d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2));assert d['inherited_hostiles_pass']
if __name__=='__main__':main()
