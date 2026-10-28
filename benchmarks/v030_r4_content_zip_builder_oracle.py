from __future__ import annotations

"""Integrated-product falsifier for research-only content-driven ZIP discovery.

Unlike the mirror/rename oracle, this uses original logical paths and the research ContentZipBuilder directly.
The format/reader remains unchanged.  It verifies exact extraction, exact selective 4 KiB ranges of every newly
virtualized Office member, malformed-suffix opaque fallback, complete archive bytes and discovery/build CPU.
"""

import argparse, json, os, shutil, time
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments.v030_r4_content_zip_builder import ContentZipBuilder
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP

TARGET='02_office_workspace'
RANGE=4096


def _build(cls,root:Path,archive:Path)->tuple[dict,float]:
    t=time.process_time();stats=dict(cls(root).build(archive));return stats,time.process_time()-t


def _verify(archive:Path,source:Path,out:Path)->dict:
    expected=PRODUCT.treehash(source);shutil.rmtree(out,ignore_errors=True)
    with CMPCT(archive) as ar:
        virtual=[row[0] for row in ar.files if row[1]==0 and row[6] and row[6][0]==S_VZIP]
        range_checks=[]
        for name in virtual:
            raw=(source/name).read_bytes();ln=min(RANGE,len(raw))
            for start in sorted({0,max(0,len(raw)//2-ln//2),max(0,len(raw)-ln)}):
                t=time.process_time();got=ar.read_range(name,start,ln);cpu=time.process_time()-t
                if got!=raw[start:start+ln]:raise RuntimeError(f'exact VZIP range mismatch: {name} {start}+{ln}')
                range_checks.append({'name':name,'start':start,'length':ln,'cpu_s':cpu})
        t=time.process_time();ar.extractall(out,metadata=True);extract_cpu=time.process_time()-t
    got=PRODUCT.treehash(out)
    if got!=expected:raise RuntimeError(f'extracted tree mismatch {got} != {expected}')
    return {'tree_sha256':got,'vzip_files':virtual,'vzip_file_count':len(virtual),'range_checks':range_checks,'extract_cpu_s':extract_cpu}


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_content_zip_builder_neutral');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_content_zip_builder_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus);source=corpus/TARGET
    baseline_archive=work/'baseline.cmpct';candidate_archive=work/'candidate.cmpct'
    bstats,bcpu=_build(Builder,source,baseline_archive);cstats,ccpu=_build(ContentZipBuilder,source,candidate_archive)
    baseline_verify=_verify(baseline_archive,source,work/'baseline-out');candidate_verify=_verify(candidate_archive,source,work/'candidate-out')

    # Hardening control: suffix may be wrong; research builder must preserve bytes instead of aborting.
    fake_root=work/'fake-root';fake_root.mkdir();raw=b'PK\x03\x04'+b'not-a-valid-zip'*64;(fake_root/'broken.zip').write_bytes(raw);fake_archive=work/'fake.cmpct';fstats,fcpu=_build(ContentZipBuilder,fake_root,fake_archive)
    with CMPCT(fake_archive) as ar:
        fake_storage=ar.by['broken.zip'][6][0];got=ar.read('broken.zip')
    if got!=raw or fake_storage==S_VZIP:raise RuntimeError('malformed ZIP did not fall back exactly')

    saving=baseline_archive.stat().st_size-candidate_archive.stat().st_size
    return {'schema':'cmpct-v030-r4-content-zip-builder-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'workload':TARGET,'baseline':{'archive_bytes':baseline_archive.stat().st_size,'create_cpu_s':bcpu,'builder_stats':bstats,**baseline_verify},'candidate':{'archive_bytes':candidate_archive.stat().st_size,'create_cpu_s':ccpu,'builder_stats':cstats,**candidate_verify},'saving_bytes':saving,'create_cpu_delta_s':ccpu-bcpu,'malformed_suffix_control':{'archive_bytes':fake_archive.stat().st_size,'create_cpu_s':fcpu,'storage_kind':fake_storage,'exact_bytes':got==raw,'parse_fallbacks':fstats.get('content_zip_parse_fallbacks')},'hypothesis':{'original_paths_exact':candidate_verify['tree_sha256']==baseline_verify['tree_sha256'],'six_office_members_virtualized':candidate_verify['vzip_file_count']==6,'all_vzip_4k_ranges_exact':len(candidate_verify['range_checks'])==18,'saves_at_least_8mb':saving>=8*1024*1024,'malformed_suffix_clean_opaque_fallback':got==raw and fake_storage!=S_VZIP,'supported_for_full_matrix_research_candidate':candidate_verify['vzip_file_count']==6 and saving>=8*1024*1024 and got==raw and fake_storage!=S_VZIP},'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'format_changed':False,'reader_changed':False,'original_logical_paths_preserved':True,'content_driven_discovery':True,'malformed_suffix_fallback_required':True},'next_if_supported':'run ContentZipBuilder directly on all frozen workloads with actual original paths and compare bytes/create/selective/recovery/native behavior; then consider shipping Builder change only after matrix and hardening gates','next_if_falsified':'keep mirror oracle as representation headroom only; do not integrate content ZIP discovery'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-builder-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-builder.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'baseline_bytes':r['baseline']['archive_bytes'],'candidate_bytes':r['candidate']['archive_bytes'],'saving_bytes':r['saving_bytes'],'create_cpu_delta_s':r['create_cpu_delta_s'],'candidate_vzip_files':r['candidate']['vzip_files'],'malformed':r['malformed_suffix_control'],'hypothesis':r['hypothesis']},indent=2))

if __name__=='__main__':main()
