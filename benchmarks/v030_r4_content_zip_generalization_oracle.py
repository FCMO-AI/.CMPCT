from __future__ import annotations

"""15-workload generalization oracle for content-driven admission into existing S_VZIP.

This remains diagnostic: original logical names are preserved externally by building an equal-path-length mirror
whose *content-validated* hidden ZIP containers are renamed to an equal-length `.zip` spelling solely to exercise
the unchanged r24 Builder.  The detector never consults the original extension when deciding whether bytes are a
valid ZIP candidate.  Malformed PK-like inputs are rejected by the detector and remain opaque.  Every probe archive
is extracted, names restored, and compared with the original product tree identity.
"""

import argparse, json, os, shutil, time, zipfile
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP
from experiments import entropygraph_v030_release_product as PRODUCT

SUPPORTED={zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED}


def _valid_zip_by_content(path:Path)->bool:
    try:
        if path.stat().st_size<64:return False
        with path.open('rb') as f:
            if f.read(4)!=b'PK\x03\x04':return False
        with zipfile.ZipFile(path) as z:
            infos=[i for i in z.infolist() if not i.is_dir()]
            if not infos or any(i.compress_type not in SUPPORTED for i in infos):return False
            # Read a bounded first member as a structural/CRC check; Builder performs exact full recipe proof later.
            first=infos[0]
            with z.open(first) as r:r.read(min(first.file_size,4096))
        return True
    except Exception:return False


def _zip_spelling(path:Path)->Path|None:
    name=path.name
    if len(name)<4:return None
    stem_len=len(name)-4
    return path.with_name(name[:stem_len]+'.zip')


def _mirror(src:Path,dst:Path)->tuple[dict[str,str],dict]:
    shutil.rmtree(dst,ignore_errors=True);shutil.copytree(src,dst,symlinks=True)
    reverse={};observed=validated=renamed=0;bytes_sniffed=0;t0=time.process_time()
    for p in sorted(q for q in dst.rglob('*') if q.is_file() and not q.is_symlink()):
        observed+=1;bytes_sniffed+=min(4096,p.stat().st_size)
        if not _valid_zip_by_content(p):continue
        validated+=1
        if p.suffix.lower() in {'.zip','.whl'}:continue # baseline already reaches S_VZIP; do not perturb.
        q=_zip_spelling(p)
        if q is None or q==p or q.exists():continue
        old=p.relative_to(dst).as_posix();new=q.relative_to(dst).as_posix()
        if len(old.encode())!=len(new.encode()):raise RuntimeError('content-ZIP mirror path length drift')
        p.rename(q);reverse[new]=old;renamed+=1
    return reverse,{'files_observed':observed,'bytes_sniffed_upper_bound':bytes_sniffed,'valid_zip_by_content':validated,'hidden_zip_candidates_renamed':renamed,'discovery_cpu_s':time.process_time()-t0}


def _restore(root:Path,reverse:dict[str,str])->None:
    for new,old in sorted(reverse.items(),reverse=True):
        src=root.joinpath(*Path(new).parts);dst=root.joinpath(*Path(old).parts);dst.parent.mkdir(parents=True,exist_ok=True);src.rename(dst)


def _build(root:Path,work:Path,name:str,reverse:dict[str,str],want_tree:str)->dict:
    archive=work/f'{name}.cmpct';t0=time.process_time();w0=time.perf_counter();stats=dict(Builder(root).build(archive));cpu=time.process_time()-t0;wall=time.perf_counter()-w0
    with CMPCT(archive) as ar:
        vzip=sum(1 for row in ar.files if row[1]==0 and row[6] and row[6][0]==S_VZIP)
        out=work/f'{name}-out';shutil.rmtree(out,ignore_errors=True);t=time.process_time();ar.extractall(out,metadata=True);extract_cpu=time.process_time()-t
    _restore(out,reverse)
    got=PRODUCT.treehash(out)
    if got!=want_tree:raise RuntimeError(f'{name} product tree mismatch {got} != {want_tree}')
    return {'archive_bytes':archive.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'extract_cpu_s':extract_cpu,'vzip_file_count':vzip,'builder_stats':stats,'tree_sha256':got}


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_zipgen_neutral');hostile=V029._load(V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_zipgen_hostile');repair=V029._load(V029.REPAIR_PATH,'cmpct_v030_zipgen_repair');repair.install_generation_hooks(neutral)
    rows=[]
    for suite,builder,root in (('neutral_hostile_v1',neutral,work/'neutral'),('resemblance_hostile_v1',hostile,work/'resemblance')):
        builder.build(root)
        if suite=='neutral_hostile_v1':repair.normalize_root(root)
        for src in sorted(p for p in root.iterdir() if p.is_dir()):
            want=PRODUCT.treehash(src);wd=work/'rows'/suite/src.name;wd.mkdir(parents=True)
            baseline_root=wd/'baseline-root';shutil.copytree(src,baseline_root,symlinks=True);baseline=_build(baseline_root,wd,'baseline',{},want)
            probe_root=wd/'probe-root';reverse,disc=_mirror(src,probe_root);probe=_build(probe_root,wd,'probe',reverse,want)
            rows.append({'suite':suite,'name':src.name,'tree_sha256':want,'discovery':disc,'baseline':baseline,'probe':probe,'saving_bytes':baseline['archive_bytes']-probe['archive_bytes'],'create_cpu_delta_s':probe['create_cpu_s']+disc['discovery_cpu_s']-baseline['create_cpu_s'],'vzip_delta':probe['vzip_file_count']-baseline['vzip_file_count']})
    regress=[r for r in rows if r['saving_bytes']<0];changed=[r for r in rows if r['vzip_delta'] or r['saving_bytes']]
    office=next(r for r in rows if r['suite']=='neutral_hostile_v1' and r['name']=='02_office_workspace')
    return {'schema':'cmpct-v030-r4-content-zip-generalization-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'rows':rows,'summary':{'workloads':len(rows),'changed_workloads':len(changed),'byte_regressions':len(regress),'aggregate_saving_bytes':sum(r['saving_bytes'] for r in rows),'aggregate_discovery_cpu_s':sum(r['discovery']['discovery_cpu_s'] for r in rows),'aggregate_create_cpu_delta_s':sum(r['create_cpu_delta_s'] for r in rows),'hidden_zip_candidates_renamed':sum(r['discovery']['hidden_zip_candidates_renamed'] for r in rows)},'hypothesis':{'office_content_zip_discovery_saves_at_least_8mb':office['saving_bytes']>=8*1024*1024,'zero_byte_regressions_across_15':not regress,'all_15_exact_product_tree':len(rows)==15,'supported_for_research_builder_admission':office['saving_bytes']>=8*1024*1024 and not regress and len(rows)==15},'contract':{'diagnostic_only':True,'release_credit':False,'production_builder_changed':False,'original_extension_used_for_candidate_validation':False,'path_lengths_preserved_in_probe':True,'malformed_content_candidates_fail_closed_to_opaque_mirror':True,'exact_product_tree_required':True},'next_if_supported':'implement a research Builder content-signature gate with clean BadZipFile fallback, preserve original paths natively, and rerun complete r24 create/member-range/recovery/native plus selector economics','next_if_falsified':'keep OOXML result scoped; do not broaden S_VZIP discovery globally'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-generalization-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-generalization.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'summary':r['summary'],'changed':[{'suite':x['suite'],'name':x['name'],'saving_bytes':x['saving_bytes'],'create_cpu_delta_s':x['create_cpu_delta_s'],'vzip_delta':x['vzip_delta'],'hidden':x['discovery']['hidden_zip_candidates_renamed']} for x in r['rows'] if x['saving_bytes'] or x['vzip_delta']],'hypothesis':r['hypothesis']},indent=2))

if __name__=='__main__':main()
