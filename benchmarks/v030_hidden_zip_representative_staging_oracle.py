from __future__ import annotations
"""Gifted research oracle for proof-known representative-only hidden-ZIP staging.

The oracle deliberately gifts admission and global logical identities. It asks one narrow question:
if proof already knew the 84 cohort-wide logical identities, what exact caller-visible cost remains to
validate/materialize/hash one deterministic representative per identity? No product credit.
"""
import argparse, ctypes, hashlib, io, json, os, shutil, statistics, time, zipfile
from pathlib import Path
from benchmarks import v030_hidden_zip_native_batch_oracle as B
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission

REPS=5
ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/'native/cmpct-hidden-zip-batch/target/release/libcmpct_hidden_zip_batch.so'

def _collect(paths):
    raws=[p.read_bytes() for p in paths]
    t0=time.perf_counter(); source=b''.join(raws); join_wall=time.perf_counter()-t0
    occurrences=[]; base=0; logical_total=0
    for raw in raws:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for ordinal,info in enumerate(z.infolist()):
                if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED: continue
                start,end=B._range(raw,info)
                logical=z.read(info)  # gifted identity establishment; intentionally untimed
                digest=hashlib.sha256(logical).digest()
                occurrences.append((digest,base+start,end-start,len(logical),int(info.CRC),ordinal,logical))
                logical_total += len(logical)
        base += len(raw)
    # Deterministic representative: first source/member occurrence in canonical admitted-path order.
    owners={}
    for occ in occurrences:
        owners.setdefault((occ[0],occ[3]),occ)
    selected=list(owners.values())
    jobs=[]; out_off=0; expected=[]
    for digest,start,nstream,nlogical,crc,ordinal,logical in selected:
        jobs.append(B.Job(start,nstream,out_off,nlogical,crc)); expected.append((out_off,logical,digest)); out_off+=nlogical
    return source,join_wall,jobs,expected,len(occurrences),logical_total,sum(o[2] for o in occurrences)

def _run_rep(lib,source,jobs,expected,join_wall):
    wall,bridge,material,digests=B._native_arm(lib,source,jobs,sum(j.output_len for j in jobs))
    for i,(off,logical,digest) in enumerate(expected):
        if material[off:off+len(logical)]!=logical: raise RuntimeError('representative material mismatch')
        if digests[i*32:(i+1)*32]!=digest: raise RuntimeError('representative identity mismatch')
    return wall,bridge,bridge+join_wall

def run(root):
    lib=ctypes.CDLL(str(LIB)); fn=lib.cmpct_hidden_zip_validate_deflate_batch
    fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(B.Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]; fn.restype=ctypes.c_int
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral'
        n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_repstage_n_{rep}')
        repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_repstage_r_{rep}'); repair.install_generation_hooks(n); n.corpus_office(suite); repair.normalize_root(suite)
        source_root=suite/'02_office_workspace'; before=PRODUCT.treehash(source_root)
        admitted=[a.rel for a in observe_hidden_zip_admission(source_root).admitted]; paths=[source_root/r for r in admitted]
        source,join_wall,jobs,expected,occurrences,logical_total,compressed_total=_collect(paths)
        wall,bridge,charged=_run_rep(lib,source,jobs,expected,join_wall)
        if PRODUCT.treehash(source_root)!=before: raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'winners':len(paths),'occurrences':occurrences,'representatives':len(jobs),'occurrence_logical_bytes':logical_total,'representative_logical_bytes':sum(j.output_len for j in jobs),'occurrence_compressed_bytes':compressed_total,'representative_compressed_bytes':sum(j.stream_len for j in jobs),'source_bytes':len(source),'source_join_wall_s':join_wall,'representative_kernel_wall_s':wall,'representative_bridge_wall_s':bridge,'representative_charged_bridge_wall_s':charged})
    med=lambda k:statistics.median(r[k] for r in rows)
    charged=med('representative_charged_bridge_wall_s')
    # Current decision debt is repository-preregistered from the exact product receipt; comparison is diagnostic only.
    debt_s=0.012484
    return {'schema':'cmpct-v030-hidden-zip-representative-staging-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'occurrences_median':med('occurrences'),'representatives_median':med('representatives'),'occurrence_logical_bytes_median':med('occurrence_logical_bytes'),'representative_logical_bytes_median':med('representative_logical_bytes'),'representative_kernel_wall_median_s':med('representative_kernel_wall_s'),'representative_bridge_wall_median_s':med('representative_bridge_wall_s'),'source_join_wall_median_s':med('source_join_wall_s'),'representative_charged_bridge_wall_median_s':charged,'preregistered_create_debt_s':debt_s,'charged_bridge_minus_create_debt_s':charged-debt_s},'contract':{'gifted_admission_untimed':True,'gifted_global_logical_identity_untimed':True,'deterministic_first_occurrence_representative':True,'representatives_receive_exact_consumption_length_crc_sha256_materialization':True,'caller_visible_bridge_charged':True,'source_join_charged':True,'zipfile_independent_crosscheck':True,'source_immutable':True,'reader_grammar_changed':False},'rows':rows}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/representative-staging-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/representative-staging.json')); a=p.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['summary'],indent=2))
if __name__=='__main__': main()
