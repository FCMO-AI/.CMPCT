from __future__ import annotations
"""Research oracle for bounded hidden-ZIP native execution boundaries.

Admission gifts the existing hidden winners and is untimed. Baseline native/Python arms perform matched
exact-consumption, length, CRC, SHA-256 and materialization work. Identity-first arms validate/hash every
occurrence once but export one byte-exact representative per logical identity, including a cohort-wide arm.
Native receipts report kernel wall and caller-visible bridge wall; the cohort arm additionally charges the
source-buffer assembly its current FFI shape requires. Compact native output is copied directly from its pointer;
ctypes list materialization is intentionally excluded because a product wrapper would never require it. No product credit.
"""
import argparse, ctypes, hashlib, io, json, os, shutil, statistics, struct, time, zipfile, zlib
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission
REPS=5; LOCAL=30; SIG=b'PK\x03\x04'; ROOT=Path(__file__).resolve().parents[1]; LIB=ROOT/'native/cmpct-hidden-zip-batch/target/release/libcmpct_hidden_zip_batch.so'
class Job(ctypes.Structure): _fields_=[('stream_offset',ctypes.c_size_t),('stream_len',ctypes.c_size_t),('output_offset',ctypes.c_size_t),('output_len',ctypes.c_size_t),('crc32',ctypes.c_uint32)]
def _range(raw,info):
    off=int(info.header_offset)
    if off<0 or off+LOCAL>len(raw) or raw[off:off+4]!=SIG: raise RuntimeError('local header')
    n,e=struct.unpack_from('<HH',raw,off+26); start=off+LOCAL+n+e; end=start+int(info.compress_size)
    if end>len(raw): raise RuntimeError('payload bounds')
    return start,end
def _python_arm(raw,jobs):
    out=bytearray(sum(j.output_len for j in jobs)); hashes=[]; t0=time.perf_counter()
    for j in jobs:
        stream=raw[j.stream_offset:j.stream_offset+j.stream_len]; d=zlib.decompressobj(-15); logical=d.decompress(stream,j.output_len+1)+d.flush()
        if len(logical)!=j.output_len or not d.eof or d.unused_data or d.unconsumed_tail or (zlib.crc32(logical)&0xffffffff)!=j.crc32: raise RuntimeError('python control validation')
        out[j.output_offset:j.output_offset+j.output_len]=logical; hashes.append(hashlib.sha256(logical).digest())
    wall=time.perf_counter()-t0;return wall,bytes(out),b''.join(hashes)
def _native_arm(lib,raw,jobs,out_off):
    bt=time.perf_counter(); arr=(Job*len(jobs))(*jobs); src=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw); out=(ctypes.c_ubyte*out_off)(); hashes=(ctypes.c_ubyte*(32*len(jobs)))(); t0=time.perf_counter(); rc=lib.cmpct_hidden_zip_validate_deflate_batch(src,len(raw),arr,len(jobs),out,out_off,hashes,len(hashes)); wall=time.perf_counter()-t0
    if rc!=0: raise RuntimeError(f'native batch status {rc}')
    material=bytes(out); digest=bytes(hashes); bridge=time.perf_counter()-bt; return wall,bridge,material,digest
def _dedup_native_arm(lib,raw,jobs,out_off):
    bt=time.perf_counter(); arr=(Job*len(jobs))(*jobs); src=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw); out=(ctypes.c_ubyte*out_off)(); hashes=(ctypes.c_ubyte*(32*len(jobs)))(); offsets=(ctypes.c_size_t*len(jobs))(); used=ctypes.c_size_t(); t0=time.perf_counter(); rc=lib.cmpct_hidden_zip_validate_dedup_deflate_batch(src,len(raw),arr,len(jobs),out,out_off,hashes,len(hashes),offsets,len(offsets),ctypes.byref(used)); wall=time.perf_counter()-t0
    if rc!=0: raise RuntimeError(f'native dedup batch status {rc}')
    material=ctypes.string_at(out,used.value); digest=bytes(hashes); offs=tuple(int(x) for x in offsets); bridge=time.perf_counter()-bt; return wall,bridge,material,digest,offs,int(used.value)
def _call(lib,path,native_first):
    raw=path.read_bytes(); jobs=[]; expected=[]; out_off=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED: continue
            start,end=_range(raw,info); logical=z.read(info); expected.append((out_off,logical,hashlib.sha256(logical).digest())); jobs.append(Job(start,end-start,out_off,len(logical),int(info.CRC))); out_off+=len(logical)
    if native_first:nw,nb,no,nh=_native_arm(lib,raw,jobs,out_off); pw,po,ph=_python_arm(raw,jobs)
    else:pw,po,ph=_python_arm(raw,jobs); nw,nb,no,nh=_native_arm(lib,raw,jobs,out_off)
    dw,db,do,dh,offsets,used=_dedup_native_arm(lib,raw,jobs,out_off)
    if no!=po or nh!=ph or dh!=ph: raise RuntimeError('matched arms disagree')
    owners={}
    for i,(off,logical,digest) in enumerate(expected):
        if no[off:off+len(logical)]!=logical or nh[i*32:(i+1)*32]!=digest: raise RuntimeError('independent ZipFile crosscheck failed')
        doff=offsets[i]
        if doff+len(logical)>len(do) or do[doff:doff+len(logical)]!=logical: raise RuntimeError('identity-first materialization mismatch')
        prior=owners.setdefault(digest,(doff,len(logical)))
        if prior!=(doff,len(logical)): raise RuntimeError('identity-first owner contradiction')
    identities=[(nh[i*32:(i+1)*32].hex(),int(j.output_len)) for i,j in enumerate(jobs)]
    return {'native_wall_s':nw,'native_bridge_wall_s':nb,'python_wall_s':pw,'dedup_native_wall_s':dw,'dedup_native_bridge_wall_s':db,'source_bytes':len(raw),'jobs':len(jobs),'compressed_bytes':sum(j.stream_len for j in jobs),'logical_bytes':out_off,'unique_logical_bytes':used,'unique_logical_objects':len(owners),'logical_identities':identities}
def _cohort_dedup(lib,paths):
    raws=[p.read_bytes() for p in paths]; join_t0=time.perf_counter(); source=b''.join(raws); join_wall=time.perf_counter()-join_t0; jobs=[]; expected=[]; out_off=0; base=0
    for raw in raws:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED:continue
                start,end=_range(raw,info); logical=z.read(info); expected.append((logical,hashlib.sha256(logical).digest())); jobs.append(Job(base+start,end-start,out_off,len(logical),int(info.CRC))); out_off+=len(logical)
        base+=len(raw)
    wall,bridge,material,hashes,offsets,used=_dedup_native_arm(lib,source,jobs,out_off); owners={}
    for i,(logical,digest) in enumerate(expected):
        if hashes[i*32:(i+1)*32]!=digest:raise RuntimeError('cohort identity hash mismatch')
        off=offsets[i]
        if off+len(logical)>len(material) or material[off:off+len(logical)]!=logical:raise RuntimeError('cohort identity material mismatch')
        prior=owners.setdefault(digest,(off,len(logical)))
        if prior!=(off,len(logical)):raise RuntimeError('cohort owner contradiction')
    return {'cohort_dedup_wall_s':wall,'cohort_dedup_bridge_wall_s':bridge,'cohort_source_join_wall_s':join_wall,'cohort_charged_bridge_wall_s':bridge+join_wall,'cohort_unique_logical_bytes':used,'cohort_unique_logical_objects':len(owners)}
def run(root):
    lib=ctypes.CDLL(str(LIB)); full=lib.cmpct_hidden_zip_validate_deflate_batch;full.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];full.restype=ctypes.c_int
    dedup=lib.cmpct_hidden_zip_validate_dedup_deflate_batch;dedup.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t),ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];dedup.restype=ctypes.c_int
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral'; n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_native_batch_n_{rep}'); repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_native_batch_r_{rep}'); repair.install_generation_hooks(n); n.corpus_office(suite); repair.normalize_root(suite)
        source=suite/'02_office_workspace'; before=PRODUCT.treehash(source); admitted=[a.rel for a in observe_hidden_zip_admission(source).admitted]; paths=[source/rel for rel in admitted]; parts=[{'rel':rel,**_call(lib,source/rel,(rep%2)==0)} for rel in admitted]; cohort=_cohort_dedup(lib,paths)
        if PRODUCT.treehash(source)!=before: raise RuntimeError('oracle mutated source')
        ids={}
        for p in parts:
            for digest,nbytes in p['logical_identities']:
                prior=ids.setdefault(digest,nbytes)
                if prior!=nbytes: raise RuntimeError('SHA-256 identity length contradiction')
        logical=sum(p['logical_bytes'] for p in parts); unique=sum(ids.values())
        if cohort['cohort_unique_logical_bytes']!=unique or cohort['cohort_unique_logical_objects']!=len(ids):raise RuntimeError('cohort/global uniqueness disagreement')
        rows.append({'rep':rep,'native_wall_s':sum(p['native_wall_s'] for p in parts),'native_bridge_wall_s':sum(p['native_bridge_wall_s'] for p in parts),'python_wall_s':sum(p['python_wall_s'] for p in parts),'dedup_native_wall_s':sum(p['dedup_native_wall_s'] for p in parts),'dedup_native_bridge_wall_s':sum(p['dedup_native_bridge_wall_s'] for p in parts),**cohort,'winners':len(parts),'jobs':sum(p['jobs'] for p in parts),'compressed_bytes':sum(p['compressed_bytes'] for p in parts),'logical_bytes':logical,'unique_logical_bytes':unique,'duplicate_logical_bytes':logical-unique,'unique_logical_objects':len(ids),'per_container_unique_logical_bytes':sum(p['unique_logical_bytes'] for p in parts)})
    med=lambda k:statistics.median(r[k] for r in rows); nm=med('native_wall_s'); nb=med('native_bridge_wall_s'); pm=med('python_wall_s'); dm=med('dedup_native_wall_s'); db=med('dedup_native_bridge_wall_s'); cm=med('cohort_dedup_wall_s'); cb=med('cohort_dedup_bridge_wall_s'); cc=med('cohort_charged_bridge_wall_s'); lm=med('logical_bytes'); um=med('unique_logical_bytes')
    return {'schema':'cmpct-v030-hidden-zip-native-batch-oracle-v8','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'native_kernel_wall_median_s':nm,'native_bridge_wall_median_s':nb,'python_wall_median_s':pm,'native_kernel_vs_python_ratio':nm/pm,'per_container_dedup_kernel_wall_median_s':dm,'per_container_dedup_bridge_wall_median_s':db,'cohort_dedup_kernel_wall_median_s':cm,'cohort_dedup_bridge_wall_median_s':cb,'cohort_source_join_wall_median_s':med('cohort_source_join_wall_s'),'cohort_charged_bridge_wall_median_s':cc,'cohort_charged_bridge_vs_full_native_bridge_ratio':cc/nb,'jobs_median':med('jobs'),'compressed_bytes_median':med('compressed_bytes'),'logical_bytes_median':lm,'unique_logical_bytes_median':um,'duplicate_logical_bytes_median':lm-um,'unique_logical_fraction':um/lm if lm else 1.0,'unique_logical_objects_median':med('unique_logical_objects'),'per_container_unique_logical_bytes_median':med('per_container_unique_logical_bytes')},'contract':{'gifted_admission_untimed':True,'matched_exact_consumption_length_crc_sha256_materialization':True,'native_bridge_charges_ctypes_input_output_and_direct_pointer_return_copy':True,'cohort_charged_bridge_adds_current_source_join':True,'identity_first_validates_every_occurrence_once':True,'cohort_identity_first_exports_one_exact_representative_globally':True,'identity_first_sha_collision_byte_check':True,'arm_order_alternates':True,'zipfile_independent_crosscheck':True,'logical_uniqueness_accounting_untimed':True,'office_only_generator_equivalent_by_independent_reseed':True,'reader_grammar_changed':False},'rows':rows}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/native-batch-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/native-batch.json')); a=p.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['summary'],indent=2))
if __name__=='__main__': main()
