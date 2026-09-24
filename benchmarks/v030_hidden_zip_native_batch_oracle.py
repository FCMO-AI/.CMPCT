from __future__ import annotations
"""Research oracle for one bounded native validation/hash/materialization boundary.

Admission gifts the existing hidden winners and is untimed. Native and Python arms receive the same
immutable RFC-1951 slices and perform the same exact-consumption, length, CRC, SHA-256 and materialization
work. Arm order alternates by repetition. ZipFile independently checks outputs. No product/release credit.
"""
import argparse, ctypes, hashlib, io, json, os, shutil, statistics, struct, time, zipfile, zlib
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission

REPS=5; LOCAL=30; SIG=b'PK\x03\x04'
ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/'native/cmpct-hidden-zip-batch/target/release/libcmpct_hidden_zip_batch.so'
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
    return time.perf_counter()-t0,bytes(out),b''.join(hashes)

def _native_arm(lib,raw,jobs,out_off):
    arr=(Job*len(jobs))(*jobs); src=(ctypes.c_ubyte*len(raw)).from_buffer_copy(raw); out=(ctypes.c_ubyte*out_off)(); hashes=(ctypes.c_ubyte*(32*len(jobs)))()
    t0=time.perf_counter(); rc=lib.cmpct_hidden_zip_validate_deflate_batch(src,len(raw),arr,len(jobs),out,out_off,hashes,len(hashes)); wall=time.perf_counter()-t0
    if rc!=0: raise RuntimeError(f'native batch status {rc}')
    return wall,bytes(out),bytes(hashes)

def _call(lib,path,native_first):
    raw=path.read_bytes(); jobs=[]; expected=[]; out_off=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED: continue
            start,end=_range(raw,info); logical=z.read(info); expected.append((out_off,logical,hashlib.sha256(logical).digest())); jobs.append(Job(start,end-start,out_off,len(logical),int(info.CRC))); out_off+=len(logical)
    if native_first:
        nw,no,nh=_native_arm(lib,raw,jobs,out_off); pw,po,ph=_python_arm(raw,jobs)
    else:
        pw,po,ph=_python_arm(raw,jobs); nw,no,nh=_native_arm(lib,raw,jobs,out_off)
    if no!=po or nh!=ph: raise RuntimeError('matched arms disagree')
    for i,(off,logical,digest) in enumerate(expected):
        if no[off:off+len(logical)]!=logical or nh[i*32:(i+1)*32]!=digest: raise RuntimeError('independent ZipFile crosscheck failed')
    return {'native_wall_s':nw,'python_wall_s':pw,'source_bytes':len(raw),'jobs':len(jobs),'compressed_bytes':sum(j.stream_len for j in jobs),'logical_bytes':out_off}

def run(root):
    lib=ctypes.CDLL(str(LIB)); fn=lib.cmpct_hidden_zip_validate_deflate_batch; fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(Job),ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]; fn.restype=ctypes.c_int
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral'; n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_native_batch_n_{rep}'); repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_native_batch_r_{rep}'); repair.install_generation_hooks(n); n.build(suite); repair.normalize_root(suite)
        source=suite/'02_office_workspace'; before=PRODUCT.treehash(source); admitted=[a.rel for a in observe_hidden_zip_admission(source).admitted]; parts=[{'rel':rel,**_call(lib,source/rel,(rep%2)==0)} for rel in admitted]
        if PRODUCT.treehash(source)!=before: raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'native_wall_s':sum(p['native_wall_s'] for p in parts),'python_wall_s':sum(p['python_wall_s'] for p in parts),'winners':len(parts),'jobs':sum(p['jobs'] for p in parts),'compressed_bytes':sum(p['compressed_bytes'] for p in parts),'logical_bytes':sum(p['logical_bytes'] for p in parts)})
    nm=statistics.median(r['native_wall_s'] for r in rows); pm=statistics.median(r['python_wall_s'] for r in rows)
    return {'schema':'cmpct-v030-hidden-zip-native-batch-oracle-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'native_wall_median_s':nm,'python_wall_median_s':pm,'native_vs_python_ratio':nm/pm,'jobs_median':statistics.median(r['jobs'] for r in rows),'compressed_bytes_median':statistics.median(r['compressed_bytes'] for r in rows),'logical_bytes_median':statistics.median(r['logical_bytes'] for r in rows)},'contract':{'gifted_admission_untimed':True,'matched_exact_consumption_length_crc_sha256_materialization':True,'arm_order_alternates':True,'zipfile_independent_crosscheck':True,'reader_grammar_changed':False},'rows':rows}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/native-batch-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/native-batch.json')); a=p.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['summary'],indent=2))
if __name__=='__main__': main()
