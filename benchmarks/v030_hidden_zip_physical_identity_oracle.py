from __future__ import annotations
"""Research-only lower-rung oracle for #205's post-Python representation frame.

Measure a strong control for first-class exact ZIP payload identity: one charged
source read, one in-memory central-directory parse, direct local-header slicing,
and SHA-256 over every exact compressed payload, with no member inflation.
Admission is inherited only to gift the same bounded winners; its work is outside
the timed phase and earns no product credit. No format, selector or gate changes.
"""
import argparse, hashlib, io, json, os, shutil, statistics, struct, time, zipfile
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission

REPS=5; LOCAL_HEADER_BYTES=30; LOCAL_SIG=b'PK\x03\x04'


def _treehash(root: Path) -> str: return PRODUCT.treehash(root)


def _payload(raw: bytes, info: zipfile.ZipInfo) -> bytes:
    off=int(info.header_offset)
    if off<0 or off+LOCAL_HEADER_BYTES>len(raw) or raw[off:off+4]!=LOCAL_SIG: raise RuntimeError('local header bounds/signature')
    name_len,extra_len=struct.unpack_from('<HH',raw,off+26); start=off+LOCAL_HEADER_BYTES+name_len+extra_len; end=start+int(info.compress_size)
    if end>len(raw): raise RuntimeError('compressed payload bounds')
    return raw[start:end]


def _physical_identity(path: Path) -> dict:
    t0=time.perf_counter(); raw=path.read_bytes(); identities=[]; physical=logical=members=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            payload=_payload(raw,info)
            physical+=len(payload); logical+=int(info.file_size); members+=1
            identities.append((int(info.compress_type),len(payload),int(info.file_size),int(info.CRC),hashlib.sha256(payload).hexdigest()))
    return {'wall_s':time.perf_counter()-t0,'source_bytes_read':len(raw),'physical_payload_bytes':physical,'declared_logical_bytes':logical,'members':members,'identity_sha256':hashlib.sha256(json.dumps(identities,separators=(',',':')).encode()).hexdigest()}


def run(root: Path) -> dict:
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral'; n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_hidden_physical_id_n_{rep}'); repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_hidden_physical_id_r_{rep}'); repair.install_generation_hooks(n); n.build(suite); repair.normalize_root(suite)
        source=suite/'02_office_workspace'; before=_treehash(source); observation=observe_hidden_zip_admission(source); admitted=[a.rel for a in observation.admitted]
        t0=time.perf_counter(); parts=[{'rel':rel,**_physical_identity(source/rel)} for rel in admitted]; cohort_wall=time.perf_counter()-t0
        if _treehash(source)!=before: raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'source_tree_sha256':before,'admitted':admitted,'cohort_wall_s':cohort_wall,'source_bytes_read':sum(x['source_bytes_read'] for x in parts),'physical_payload_bytes':sum(x['physical_payload_bytes'] for x in parts),'declared_logical_bytes':sum(x['declared_logical_bytes'] for x in parts),'members':sum(x['members'] for x in parts),'parts':parts})
    walls=[r['cohort_wall_s'] for r in rows]; physical=statistics.median(r['physical_payload_bytes'] for r in rows); logical=statistics.median(r['declared_logical_bytes'] for r in rows)
    return {'schema':'cmpct-v030-hidden-zip-physical-identity-oracle-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'repetitions':REPS,'summary':{'cohort_wall_median_s':statistics.median(walls),'cohort_wall_min_s':min(walls),'cohort_wall_max_s':max(walls),'source_bytes_read_median':statistics.median(r['source_bytes_read'] for r in rows),'physical_payload_bytes_median':physical,'declared_logical_bytes_median':logical,'logical_to_physical_ratio':logical/physical if physical else None,'winner_count':statistics.median(len(r['admitted']) for r in rows)},'contract':{'admission_used_only_as_gifted_winner_selector':True,'timed_phase_source_read_charged':True,'timed_phase_inflates_members':False,'single_source_read_per_winner':True,'exact_compressed_payload_sha256':True,'all_payload_bytes_charged':True,'release_thresholds_unchanged':True},'rows':rows}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-physical-id-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-physical-id.json')); a=p.parse_args(); result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['summary'],indent=2))
if __name__=='__main__': main()
