from __future__ import annotations
"""Gifted oracle for proof-known representative-only hidden-ZIP staging.

Admission/global identity are gifted. The measured fork is stricter: all-occurrence vs representative-only
native staging under the same caller boundary, plus the marginal cost of adding logical SHA-256 to the
already-required chunked proof inflate+CRC pass. No product credit.
"""
import argparse, binascii, ctypes, hashlib, io, json, os, shutil, statistics, time, zipfile, zlib
from pathlib import Path
from benchmarks import v030_hidden_zip_native_batch_oracle as B
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission
REPS=5; CHUNK=1024*1024; ROOT=Path(__file__).resolve().parents[1]; LIB=ROOT/'native/cmpct-hidden-zip-batch/target/release/libcmpct_hidden_zip_batch.so'

def _collect(paths):
    raws=[p.read_bytes() for p in paths]; t0=time.perf_counter(); source=b''.join(raws); join_wall=time.perf_counter()-t0
    occ=[]; base=0; logical_total=0
    for raw in raws:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for ordinal,info in enumerate(z.infolist()):
                if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED:continue
                start,end=B._range(raw,info); logical=z.read(info); digest=hashlib.sha256(logical).digest()
                occ.append((digest,base+start,end-start,len(logical),int(info.CRC),ordinal,logical));logical_total+=len(logical)
        base+=len(raw)
    owners={}
    for o in occ:owners.setdefault((o[0],o[3]),o)
    def jobs_for(rows):
        jobs=[];expected=[];out=0
        for digest,start,nstream,nlogical,crc,ordinal,logical in rows:
            jobs.append(B.Job(start,nstream,out,nlogical,crc));expected.append((out,logical,digest));out+=nlogical
        return jobs,expected,out
    all_jobs,all_expected,all_out=jobs_for(occ);rep_jobs,rep_expected,rep_out=jobs_for(list(owners.values()))
    return source,join_wall,occ,all_jobs,all_expected,all_out,rep_jobs,rep_expected,rep_out,logical_total,sum(o[2] for o in occ)

def _native_checked(lib,source,jobs,expected,out_size,join_wall):
    wall,bridge,material,digests=B._native_arm(lib,source,jobs,out_size)
    for i,(off,logical,digest) in enumerate(expected):
        if material[off:off+len(logical)]!=logical or digests[i*32:(i+1)*32]!=digest:raise RuntimeError('native material/identity mismatch')
    return wall,bridge,bridge+join_wall

def _proof_pass(source,occ,with_sha):
    t0=time.perf_counter(); identities=[]
    for expected,start,nstream,nlogical,crc,_ordinal,_logical in occ:
        d=zlib.decompressobj(-15); pending=source[start:start+nstream]; actual=0; got_crc=0; h=hashlib.sha256() if with_sha else None
        while True:
            out=d.decompress(pending,min(CHUNK,nlogical-actual+1));actual+=len(out);got_crc=binascii.crc32(out,got_crc)
            if h is not None:h.update(out)
            pending=d.unconsumed_tail
            if pending:continue
            if not d.eof:raise RuntimeError('proof truncated stream')
            break
        if actual!=nlogical or d.unused_data or (got_crc&0xffffffff)!=crc:raise RuntimeError('proof validation mismatch')
        if h is not None:
            got=h.digest();identities.append(got)
            if got!=expected:raise RuntimeError('proof SHA mismatch')
    return time.perf_counter()-t0,identities

def run(root):
    lib=ctypes.CDLL(str(LIB));fn=lib.cmpct_hidden_zip_validate_deflate_batch;fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(B.Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];fn.restype=ctypes.c_int
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_repstage_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_repstage_r_{rep}');repair.install_generation_hooks(n);n.corpus_office(suite);repair.normalize_root(suite)
        source_root=suite/'02_office_workspace';before=PRODUCT.treehash(source_root);admitted=[a.rel for a in observe_hidden_zip_admission(source_root).admitted];paths=[source_root/r for r in admitted]
        source,join_wall,occ,all_jobs,all_expected,all_out,rep_jobs,rep_expected,rep_out,logical_total,compressed_total=_collect(paths)
        if rep%2==0:
            aw,ab,ac=_native_checked(lib,source,all_jobs,all_expected,all_out,join_wall);rw,rb,rc=_native_checked(lib,source,rep_jobs,rep_expected,rep_out,join_wall);crc_wall,_=_proof_pass(source,occ,False);sha_wall,_=_proof_pass(source,occ,True)
        else:
            sha_wall,_=_proof_pass(source,occ,True);crc_wall,_=_proof_pass(source,occ,False);rw,rb,rc=_native_checked(lib,source,rep_jobs,rep_expected,rep_out,join_wall);aw,ab,ac=_native_checked(lib,source,all_jobs,all_expected,all_out,join_wall)
        if PRODUCT.treehash(source_root)!=before:raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'winners':len(paths),'occurrences':len(occ),'representatives':len(rep_jobs),'occurrence_logical_bytes':logical_total,'representative_logical_bytes':rep_out,'occurrence_compressed_bytes':compressed_total,'representative_compressed_bytes':sum(j.stream_len for j in rep_jobs),'source_bytes':len(source),'source_join_wall_s':join_wall,'all_kernel_wall_s':aw,'all_bridge_wall_s':ab,'all_charged_bridge_wall_s':ac,'representative_kernel_wall_s':rw,'representative_bridge_wall_s':rb,'representative_charged_bridge_wall_s':rc,'proof_crc_wall_s':crc_wall,'proof_crc_sha_wall_s':sha_wall,'proof_sha_marginal_s':sha_wall-crc_wall})
    med=lambda k:statistics.median(r[k] for r in rows); debt=0.012484; saved=med('all_charged_bridge_wall_s')-med('representative_charged_bridge_wall_s');sha_delta=med('proof_sha_marginal_s');net=saved-sha_delta
    return {'schema':'cmpct-v030-hidden-zip-representative-staging-oracle-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'occurrences_median':med('occurrences'),'representatives_median':med('representatives'),'occurrence_logical_bytes_median':med('occurrence_logical_bytes'),'representative_logical_bytes_median':med('representative_logical_bytes'),'all_charged_bridge_wall_median_s':med('all_charged_bridge_wall_s'),'representative_charged_bridge_wall_median_s':med('representative_charged_bridge_wall_s'),'representative_stage_saved_wall_s':saved,'proof_crc_wall_median_s':med('proof_crc_wall_s'),'proof_crc_sha_wall_median_s':med('proof_crc_sha_wall_s'),'proof_sha_marginal_median_s':sha_delta,'net_saved_after_proof_sha_s':net,'preregistered_create_debt_s':debt,'net_margin_vs_create_debt_s':net-debt},'contract':{'gifted_admission_untimed':True,'gifted_global_logical_identity_untimed':True,'deterministic_first_occurrence_representative':True,'matched_all_vs_representative_boundary':True,'representatives_receive_exact_consumption_length_crc_sha256_materialization':True,'proof_sha_marginal_measured_against_same_chunked_inflate_crc_control':True,'caller_visible_bridge_charged':True,'source_join_charged_both_arms':True,'arm_order_alternates':True,'zipfile_independent_crosscheck':True,'source_immutable':True,'reader_grammar_changed':False},'rows':rows}
def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/representative-staging-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/representative-staging.json'));a=p.parse_args();result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
