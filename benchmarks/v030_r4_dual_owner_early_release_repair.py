from __future__ import annotations

"""Second causal lifetime repair for Analytics R4 dual-owner build.

The first lifetime intervention recovered ~79.6 MiB of peak RSS but missed the preregistered 20% target
by 229 KiB (324,664 KiB observed vs <=324,435 KiB required). That remains a negative. Inspection showed
that it still retained parsed CSV/JSON rows while reading the ~3.56 MiB NPZ, materializing the ~3.84 MiB
NPY member, and copying the stripped tree. This v2 changes only object lifetime: after the tabular owner
and compact file metadata/hashes exist, all large tabular raw/parsed structures are released *before*
any NPZ work or tree copy.

The scientific gate is intentionally unchanged: exact reconstruction/treehash, <=4 KiB stored-byte
regression against same-run baseline, and repaired peak RSS <=324,435 KiB. No owner grammar, group size,
admission, codec, threshold, or product format change.
"""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import shutil
import time
import zipfile

from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r4-dual-owner-early-release-repair-v1'
REFERENCE_PEAK_KIB=405_544
TARGET_PEAK_KIB=324_435
MAX_BYTE_REGRESSION=4096


def rss()->int:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def prepare(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    from benchmarks import mosaic_v029_generalization_bench as V029
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_early_neutral')
    repair=V029._load(V029.REPAIR_PATH,'r4_early_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus)
    source=corpus/'04_analytics_and_database'
    return {'source':str(source),'tree_sha256':PRODUCT.treehash(source)}


def build_early(source:Path,out:Path,work:Path)->dict:
    discovery=I._discover(source)
    if len(discovery['accepted'])!=1:raise RuntimeError('expected exactly one tabular relation')
    tab=discovery['accepted'][0];rel=DUAL._npz_relation(source)['accepted']
    csvp=source.joinpath(*Path(tab['csv_path']).parts);jsonp=source.joinpath(*Path(tab['jsonl_path']).parts)
    npyp=source.joinpath(*Path(rel['npy_path']).parts);npzp=source.joinpath(*Path(rel['npz_path']).parts)
    csv_meta={'path':tab['csv_path'],**I._stat_record(csvp)};json_meta={'path':tab['jsonl_path'],**I._stat_record(jsonp)}
    npy_meta={'path':rel['npy_path'],**I._stat_record(npyp)};npz_meta={'path':rel['npz_path'],**I._stat_record(npzp)}

    csv_source=csvp.read_bytes();json_source=jsonp.read_bytes();cf,cr=OWNER._parse_csv(csv_source);jf,jr=OWNER._parse_jsonl(json_source)
    if cf!=jf or not OWNER._semantic_equal(cf,cr,jr):raise RuntimeError('semantic owner mismatch')
    csv_lengths=FAST._line_lengths(csv_source,len(jr),I.GROUP_ROWS,header=True);json_lengths=FAST._line_lengths(json_source,len(jr),I.GROUP_ROWS,header=False)
    tcol,tcol_stats=FAST._encode(cf,jr,I.GROUP_ROWS,csv_lengths,json_lengths)
    csv_raw,json_raw=I._owner_raw(tcol)
    if csv_raw!=csv_source or json_raw!=json_source:raise RuntimeError('tabular reconstruction mismatch')
    csv_meta['sha256']=DUAL._sha(csv_raw);json_meta['sha256']=DUAL._sha(json_raw)

    # Intervention: drop every large tabular intermediate before NPZ read/materialization/tree-copy.
    del csv_source,json_source,cf,cr,jf,jr,csv_lengths,json_lengths,csv_raw,json_raw
    gc.collect();rss_after_tabular_release=rss()

    npz_raw=npzp.read_bytes()
    with zipfile.ZipFile(npzp,'r') as zf:npy_from_npz=zf.read(rel['member'])
    npy_on_disk=npyp.read_bytes()
    if npy_from_npz!=npy_on_disk:raise RuntimeError('NPZ relation mismatch')
    npy_meta['sha256']=DUAL._sha(npy_from_npz);npz_meta['sha256']=DUAL._sha(npz_raw)
    del npy_from_npz,npy_on_disk
    gc.collect();rss_after_npz_proof=rss()

    stripped=work/'stripped';I._copy_without(source,stripped,{tab['csv_path'],tab['jsonl_path'],rel['npy_path'],rel['npz_path']})
    base=work/'base.cmpct';base_stats=dict(PRODUCT.build(stripped,base));rss_after_base=rss()
    manifest={'schema':'cmpct-v030-r4-analytics-dual-owner-bundle-v1','group_rows':I.GROUP_ROWS,'members':{'csv':csv_meta,'jsonl':json_meta,'npy':npy_meta,'npz':npz_meta},'tabular_discovery':discovery,'npz_relation':{'accepted':rel}}
    bundle=DUAL._write_bundle(out,base,tcol,npz_raw,manifest)
    return {'stored_bytes':bundle['stored_bytes'],'bundle':bundle,'base_stats':base_stats,'tcol_stats':tcol_stats,'rss_after_tabular_release_kib':rss_after_tabular_release,'rss_after_npz_proof_kib':rss_after_npz_proof,'rss_after_base_kib':rss_after_base}


def worker(mode:str,source:Path,out:Path,work:Path,result:Path)->None:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);shutil.rmtree(out,ignore_errors=True)
    c0=time.process_time();w0=time.perf_counter()
    row=DUAL._build_candidate(source,out,work) if mode=='baseline' else build_early(source,out,work)
    verify=work/'verify';shutil.rmtree(verify,ignore_errors=True);v=DUAL._extract_candidate(out,verify)
    row.update({'mode':mode,'peak_rss_kib':rss(),'cpu_s':time.process_time()-c0,'wall_s':time.perf_counter()-w0,'tree_sha256':v['tree_sha256']})
    result.parent.mkdir(parents=True,exist_ok=True);result.write_text(json.dumps(row,default=str)+'\n');print(json.dumps({'mode':mode,'stored_bytes':row['stored_bytes'],'peak_rss_kib':row['peak_rss_kib'],'cpu_s':row['cpu_s'],'wall_s':row['wall_s'],'tree_sha256':row['tree_sha256']},sort_keys=True))


def aggregate(work:Path,tree:str)->dict:
    b=json.loads((work/'workers'/'baseline.json').read_text());r=json.loads((work/'workers'/'repaired.json').read_text());delta=int(r['stored_bytes'])-int(b['stored_bytes']);tree_ok=b['tree_sha256']==tree and r['tree_sha256']==tree;peak=int(r['peak_rss_kib']);supported=tree_ok and peak<=TARGET_PEAK_KIB and delta<=MAX_BYTE_REGRESSION
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'expected_tree_sha256':tree,'baseline':b,'repaired':r,'comparison':{'byte_delta':delta,'peak_rss_delta_kib':peak-int(b['peak_rss_kib']),'peak_reduction_fraction_vs_reference':1-peak/REFERENCE_PEAK_KIB,'cpu_delta_s':r['cpu_s']-b['cpu_s'],'wall_delta_s':r['wall_s']-b['wall_s']},'hypothesis':{'early_release_supported':supported,'tree_exact':tree_ok,'repaired_peak_at_or_below_unchanged_target':peak<=TARGET_PEAK_KIB,'byte_regression_within_4KiB':delta<=MAX_BYTE_REGRESSION},'contract':{'diagnostic_only':True,'release_credit':False,'unchanged_peak_target_kib':TARGET_PEAK_KIB,'owner_grammar_changed':False,'group_size_changed':False,'admission_changed':False,'codec_changed':False,'product_format_changed':False,'no_threshold_sweep':True},'next_if_supported':'carry early release ordering into integrated builder and remeasure composed size/CPU/RSS; then profile parser materialization separately','next_if_falsified':'preserve negative; switch from Python row materialization to streaming/fused tabular observation rather than relaxing the 20% gate'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-early-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-early.json'));p.add_argument('--prepare-only',action='store_true');p.add_argument('--worker',choices=('baseline','repaired'));p.add_argument('--source',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--worker-work',type=Path);p.add_argument('--worker-result',type=Path);p.add_argument('--aggregate',action='store_true');p.add_argument('--expected-tree');a=p.parse_args()
    if a.prepare_only:print(json.dumps(prepare(a.work_root),sort_keys=True));return
    if a.worker:
        if not all((a.source,a.archive,a.worker_work,a.worker_result)):raise SystemExit('missing worker args')
        worker(a.worker,a.source,a.archive,a.worker_work,a.worker_result);return
    if a.aggregate:
        if not a.expected_tree:raise SystemExit('--expected-tree required')
        d=aggregate(a.work_root,a.expected_tree);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,default=str)+'\n');print(json.dumps({'comparison':d['comparison'],'hypothesis':d['hypothesis']},indent=2));return
    raise SystemExit('choose mode')

if __name__=='__main__':main()
