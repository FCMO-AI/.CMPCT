from __future__ import annotations

"""Hosted-ready v2 of fused Analytics observation with RSS-clean equivalence control.

Supersedes the unrun v1 benchmark only as measurement methodology: v1 correctly
specified the streaming writer but built the legacy FAST owner in the repaired
process as an equivalence control, which contaminates process-lifetime ru_maxrss.
Here the legacy owner is built in a third fresh process. Scientific thresholds
and the candidate mechanism are unchanged.
"""

import argparse, gc, hashlib, json, os, resource, shutil, time, zipfile
from pathlib import Path

from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_dual_owner_early_release_repair as EARLY
from benchmarks import v030_r4_dual_owner_streaming_observation_repair as V1
from benchmarks import v030_r4_tabular_integrated_archive as I
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r4-dual-owner-streaming-observation-repair-v2'
TARGET_PEAK_KIB=EARLY.TARGET_PEAK_KIB
REFERENCE_PEAK_KIB=EARLY.REFERENCE_PEAK_KIB
MAX_BYTE_REGRESSION=EARLY.MAX_BYTE_REGRESSION
CPU_REGRESSION_S=V1.CPU_REGRESSION_S
WALL_REGRESSION_S=V1.WALL_REGRESSION_S


def rss()->int:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def build_streaming(source:Path,out:Path,work:Path)->dict:
    discovery=I._discover(source)
    if len(discovery['accepted'])!=1:raise RuntimeError('expected exactly one tabular relation')
    tab=discovery['accepted'][0];rel=DUAL._npz_relation(source)['accepted']
    csvp=source.joinpath(*Path(tab['csv_path']).parts);jsonp=source.joinpath(*Path(tab['jsonl_path']).parts)
    npyp=source.joinpath(*Path(rel['npy_path']).parts);npzp=source.joinpath(*Path(rel['npz_path']).parts)
    csv_meta={'path':tab['csv_path'],**I._stat_record(csvp),'sha256':V1._file_sha(csvp)}
    json_meta={'path':tab['jsonl_path'],**I._stat_record(jsonp),'sha256':V1._file_sha(jsonp)}
    npy_meta={'path':rel['npy_path'],**I._stat_record(npyp)};npz_meta={'path':rel['npz_path'],**I._stat_record(npzp)}

    tcol,tcol_stats=V1._stream_owner(csvp,jsonp,I.GROUP_ROWS)
    owner_sha=hashlib.sha256(tcol).hexdigest();rss_after_stream_owner=rss()

    npz_raw=npzp.read_bytes()
    with zipfile.ZipFile(npzp,'r') as zf:npy_from_npz=zf.read(rel['member'])
    npy_hash=V1._file_sha(npyp)
    if hashlib.sha256(npy_from_npz).hexdigest()!=npy_hash:raise RuntimeError('NPZ relation mismatch')
    npy_meta['sha256']=npy_hash;npz_meta['sha256']=hashlib.sha256(npz_raw).hexdigest()
    del npy_from_npz;gc.collect();rss_after_npz_proof=rss()

    stripped=work/'stripped';I._copy_without(source,stripped,{tab['csv_path'],tab['jsonl_path'],rel['npy_path'],rel['npz_path']})
    base=work/'base.cmpct';base_stats=dict(PRODUCT.build(stripped,base));rss_after_base=rss()
    manifest={'schema':'cmpct-v030-r4-analytics-dual-owner-bundle-v1','group_rows':I.GROUP_ROWS,'members':{'csv':csv_meta,'jsonl':json_meta,'npy':npy_meta,'npz':npz_meta},'tabular_discovery':discovery,'npz_relation':{'accepted':rel}}
    bundle=DUAL._write_bundle(out,base,tcol,npz_raw,manifest)
    return {'stored_bytes':bundle['stored_bytes'],'bundle':bundle,'base_stats':base_stats,'tcol_stats':tcol_stats,'owner_sha256':owner_sha,'rss_after_stream_owner_kib':rss_after_stream_owner,'rss_after_npz_proof_kib':rss_after_npz_proof,'rss_after_base_kib':rss_after_base}


def reference_owner(source:Path,result:Path)->None:
    discovery=I._discover(source)
    if len(discovery['accepted'])!=1:raise RuntimeError('expected exactly one tabular relation')
    tab=discovery['accepted'][0]
    csvp=source.joinpath(*Path(tab['csv_path']).parts);jsonp=source.joinpath(*Path(tab['jsonl_path']).parts)
    owner=V1._reference_owner(csvp,jsonp)
    row={'owner_sha256':hashlib.sha256(owner).hexdigest(),'owner_bytes':len(owner)}
    result.parent.mkdir(parents=True,exist_ok=True);result.write_text(json.dumps(row)+'\n');print(json.dumps(row,sort_keys=True))


def worker(mode:str,source:Path,out:Path,work:Path,result:Path)->None:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);shutil.rmtree(out,ignore_errors=True)
    c0=time.process_time();w0=time.perf_counter()
    row=DUAL._build_candidate(source,out,work) if mode=='baseline' else build_streaming(source,out,work)
    verify=work/'verify';shutil.rmtree(verify,ignore_errors=True);v=DUAL._extract_candidate(out,verify)
    row.update({'mode':mode,'peak_rss_kib':rss(),'cpu_s':time.process_time()-c0,'wall_s':time.perf_counter()-w0,'tree_sha256':v['tree_sha256']})
    result.parent.mkdir(parents=True,exist_ok=True);result.write_text(json.dumps(row,default=str)+'\n');print(json.dumps({k:row[k] for k in ('mode','stored_bytes','peak_rss_kib','cpu_s','wall_s','tree_sha256')},sort_keys=True))


def aggregate(work:Path,tree:str)->dict:
    b=json.loads((work/'workers'/'baseline.json').read_text());r=json.loads((work/'workers'/'repaired.json').read_text());ref=json.loads((work/'workers'/'reference.json').read_text())
    delta=int(r['stored_bytes'])-int(b['stored_bytes']);tree_ok=b['tree_sha256']==tree and r['tree_sha256']==tree;owner_ok=r['owner_sha256']==ref['owner_sha256'];peak=int(r['peak_rss_kib']);cpu_delta=float(r['cpu_s'])-float(b['cpu_s']);wall_delta=float(r['wall_s'])-float(b['wall_s'])
    supported=tree_ok and owner_ok and peak<=TARGET_PEAK_KIB and delta<=MAX_BYTE_REGRESSION and cpu_delta<=CPU_REGRESSION_S and wall_delta<=WALL_REGRESSION_S
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'expected_tree_sha256':tree,'baseline':b,'repaired':r,'reference_owner':ref,'comparison':{'byte_delta':delta,'peak_rss_delta_kib':peak-int(b['peak_rss_kib']),'peak_reduction_fraction_vs_reference':1-peak/REFERENCE_PEAK_KIB,'cpu_delta_s':cpu_delta,'wall_delta_s':wall_delta},'hypothesis':{'streaming_observation_supported':supported,'tree_exact':tree_ok,'owner_byte_identical_to_fast':owner_ok,'repaired_peak_at_or_below_unchanged_target':peak<=TARGET_PEAK_KIB,'byte_regression_within_4KiB':delta<=MAX_BYTE_REGRESSION,'cpu_regression_within_0_5s':cpu_delta<=CPU_REGRESSION_S,'wall_regression_within_1s':wall_delta<=WALL_REGRESSION_S},'contract':{'diagnostic_only':True,'release_credit':False,'unchanged_peak_target_kib':TARGET_PEAK_KIB,'owner_grammar_changed':False,'group_size_changed':False,'admission_changed':False,'codec_changed':False,'product_format_changed':False,'no_threshold_sweep':True,'reference_owner_isolated_from_measured_candidate_process':True},'next_if_supported':'carry fused observation into integrated Analytics builder, combine with token-anchor physical reader, then remeasure composed bytes/CPU/RSS/locality/recovery','next_if_falsified':'preserve negative; profile per-column Python materialization and extraction peak separately; do not relax the 20% gate'}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-stream-v2-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-stream-v2.json'));p.add_argument('--prepare-only',action='store_true');p.add_argument('--worker',choices=('baseline','repaired'));p.add_argument('--reference-owner',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--worker-work',type=Path);p.add_argument('--worker-result',type=Path);p.add_argument('--aggregate',action='store_true');p.add_argument('--expected-tree');a=p.parse_args()
    if a.prepare_only:print(json.dumps(EARLY.prepare(a.work_root),sort_keys=True));return
    if a.reference_owner:
        if not a.source or not a.worker_result:raise SystemExit('missing reference args')
        reference_owner(a.source,a.worker_result);return
    if a.worker:
        if not all((a.source,a.archive,a.worker_work,a.worker_result)):raise SystemExit('missing worker args')
        worker(a.worker,a.source,a.archive,a.worker_work,a.worker_result);return
    if a.aggregate:
        if not a.expected_tree:raise SystemExit('--expected-tree required')
        d=aggregate(a.work_root,a.expected_tree);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,default=str)+'\n');print(json.dumps({'comparison':d['comparison'],'hypothesis':d['hypothesis']},indent=2));return
    raise SystemExit('choose mode')

if __name__=='__main__':main()
