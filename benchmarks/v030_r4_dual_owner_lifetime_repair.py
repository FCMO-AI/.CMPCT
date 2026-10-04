from __future__ import annotations

"""Causal lifetime repair for the Analytics R4 dual-owner builder.

Fresh-process attribution found the full dual build at 405,544 KiB peak RSS while isolated tabular
parse/encode peaked near 243 MiB and stripped base build near 165 MiB. No isolated stage crossed the
pre-registered primary-owner threshold, so the leading hypothesis is coexistence of large Python row
objects with the subsequent v0.30 base build.

This oracle keeps admission, owner grammar, group size, codecs and authenticated bundle semantics
unchanged. It captures the small manifest records needed later, then explicitly releases raw CSV/JSONL,
parsed row structures and lexical indexes before PRODUCT.build. The baseline and repaired builders run
in independent shell-launched processes on the exact same prepared source.

Pre-registered support: repaired peak RSS <= 324,435 KiB (>=20% below the observed 405,544 KiB full
build), reconstructed treehash identical, and authenticated stored bytes no more than 4 KiB above the
same-run baseline. No threshold sweep.
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

SCHEMA='cmpct-v030-r4-dual-owner-lifetime-repair-v1'
REFERENCE_PEAK_KIB=405_544
TARGET_PEAK_KIB=324_435
MAX_BYTE_REGRESSION=4096


def _rss_kib()->int:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def prepare(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    from benchmarks import mosaic_v029_generalization_bench as V029
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','r4_lifetime_neutral')
    repair=V029._load(V029.REPAIR_PATH,'r4_lifetime_repair');repair.install_generation_hooks(neutral)
    corpus=work/'neutral';neutral.build(corpus);repair.normalize_root(corpus)
    source=corpus/'04_analytics_and_database'
    return {'source':str(source),'tree_sha256':PRODUCT.treehash(source)}


def _optimized_build(source:Path,out:Path,work:Path)->dict:
    discovery=I._discover(source)
    if len(discovery['accepted'])!=1:raise RuntimeError('tabular admission did not yield exactly one relation')
    tab=discovery['accepted'][0];npz_rel=DUAL._npz_relation(source);rel=npz_rel['accepted']
    csvp=source.joinpath(*Path(tab['csv_path']).parts);jsonp=source.joinpath(*Path(tab['jsonl_path']).parts)
    npyp=source.joinpath(*Path(rel['npy_path']).parts);npzp=source.joinpath(*Path(rel['npz_path']).parts)
    # Capture durable filesystem records before dropping large lexical/semantic objects.
    csv_meta={'path':tab['csv_path'],**I._stat_record(csvp)};json_meta={'path':tab['jsonl_path'],**I._stat_record(jsonp)}
    npy_meta={'path':rel['npy_path'],**I._stat_record(npyp)};npz_meta={'path':rel['npz_path'],**I._stat_record(npzp)}
    csv_source=csvp.read_bytes();json_source=jsonp.read_bytes()
    cf,cr=OWNER._parse_csv(csv_source);jf,jr=OWNER._parse_jsonl(json_source)
    if cf!=jf or not OWNER._semantic_equal(cf,cr,jr):raise RuntimeError('semantic owner gate failed')
    csv_lengths=FAST._line_lengths(csv_source,len(jr),I.GROUP_ROWS,header=True);json_lengths=FAST._line_lengths(json_source,len(jr),I.GROUP_ROWS,header=False)
    tcol,tcol_stats=FAST._encode(cf,jr,I.GROUP_ROWS,csv_lengths,json_lengths)
    csv_raw,json_raw=I._owner_raw(tcol)
    if csv_raw!=csv_source or json_raw!=json_source:raise RuntimeError('tabular reconstruction mismatch')
    csv_meta['sha256']=DUAL._sha(csv_raw);json_meta['sha256']=DUAL._sha(json_raw)

    npz_raw=npzp.read_bytes()
    with zipfile.ZipFile(npzp,'r') as zf:npy_from_npz=zf.read(rel['member'])
    if npy_from_npz!=npyp.read_bytes():raise RuntimeError('NPZ relation mismatch')
    npy_meta['sha256']=DUAL._sha(npy_from_npz);npz_meta['sha256']=DUAL._sha(npz_raw)

    stripped=work/'stripped';I._copy_without(source,stripped,{tab['csv_path'],tab['jsonl_path'],rel['npy_path'],rel['npz_path']})
    # Causal intervention: after owner bytes + compact metadata exist, the huge raw/parsed structures
    # are dead. Release them before the product base build instead of letting Python locals retain them.
    del csv_source,json_source,cf,cr,jf,jr,csv_lengths,json_lengths,csv_raw,json_raw,npy_from_npz
    gc.collect()
    rss_before_base=_rss_kib()
    base=work/'base.cmpct';base_stats=dict(PRODUCT.build(stripped,base));rss_after_base=_rss_kib()
    manifest={'schema':'cmpct-v030-r4-analytics-dual-owner-bundle-v1','group_rows':I.GROUP_ROWS,'members':{'csv':csv_meta,'jsonl':json_meta,'npy':npy_meta,'npz':npz_meta},'tabular_discovery':discovery,'npz_relation':npz_rel}
    bundle=DUAL._write_bundle(out,base,tcol,npz_raw,manifest)
    return {'stored_bytes':bundle['stored_bytes'],'bundle':bundle,'base_stats':base_stats,'tcol_stats':tcol_stats,'rss_before_base_kib':rss_before_base,'rss_after_base_kib':rss_after_base}


def worker(mode:str,source:Path,out:Path,work:Path,result:Path)->None:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);shutil.rmtree(out,ignore_errors=True)
    c0=time.process_time();w0=time.perf_counter()
    if mode=='baseline':row=DUAL._build_candidate(source,out,work)
    elif mode=='repaired':row=_optimized_build(source,out,work)
    else:raise ValueError(mode)
    verify_out=work/'verify';shutil.rmtree(verify_out,ignore_errors=True);v=DUAL._extract_candidate(out,verify_out)
    row.update({'mode':mode,'peak_rss_kib':_rss_kib(),'cpu_s':time.process_time()-c0,'wall_s':time.perf_counter()-w0,'tree_sha256':v['tree_sha256']})
    result.parent.mkdir(parents=True,exist_ok=True);result.write_text(json.dumps(row,default=str)+'\n');print(json.dumps({'mode':mode,'stored_bytes':row['stored_bytes'],'peak_rss_kib':row['peak_rss_kib'],'cpu_s':row['cpu_s'],'wall_s':row['wall_s'],'tree_sha256':row['tree_sha256']},sort_keys=True))


def aggregate(work:Path,expected_tree:str)->dict:
    b=json.loads((work/'workers'/'baseline.json').read_text());r=json.loads((work/'workers'/'repaired.json').read_text())
    tree_ok=b['tree_sha256']==expected_tree and r['tree_sha256']==expected_tree
    byte_delta=int(r['stored_bytes'])-int(b['stored_bytes']);peak=int(r['peak_rss_kib'])
    supported=tree_ok and peak<=TARGET_PEAK_KIB and byte_delta<=MAX_BYTE_REGRESSION
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'expected_tree_sha256':expected_tree,'baseline':b,'repaired':r,'comparison':{'byte_delta':byte_delta,'peak_rss_delta_kib':peak-int(b['peak_rss_kib']),'peak_reduction_fraction_vs_observed_reference':1-peak/REFERENCE_PEAK_KIB,'cpu_delta_s':r['cpu_s']-b['cpu_s'],'wall_delta_s':r['wall_s']-b['wall_s']},'hypothesis':{'lifetime_repair_supported':supported,'tree_exact':tree_ok,'repaired_peak_at_or_below_target':peak<=TARGET_PEAK_KIB,'byte_regression_within_4KiB':byte_delta<=MAX_BYTE_REGRESSION},'contract':{'diagnostic_only':True,'release_credit':False,'owner_grammar_changed':False,'group_size_changed':False,'admission_changed':False,'codec_changed':False,'no_threshold_sweep':True},'next_if_supported':'apply the lifetime release/fusion discipline to the integrated R4 builder and re-run the composed size/speed/RSS gate','next_if_falsified':'preserve negative; profile coexistence inside PRODUCT.build and bundle assembly instead of tuning compression'}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-lifetime-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-lifetime.json'));p.add_argument('--prepare-only',action='store_true');p.add_argument('--worker',choices=('baseline','repaired'));p.add_argument('--source',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--worker-work',type=Path);p.add_argument('--worker-result',type=Path);p.add_argument('--aggregate',action='store_true');p.add_argument('--expected-tree');a=p.parse_args()
    if a.prepare_only:print(json.dumps(prepare(a.work_root),sort_keys=True));return
    if a.worker:
        if not all((a.source,a.archive,a.worker_work,a.worker_result)):raise SystemExit('worker args missing')
        worker(a.worker,a.source,a.archive,a.worker_work,a.worker_result);return
    if a.aggregate:
        if not a.expected_tree:raise SystemExit('--expected-tree required')
        d=aggregate(a.work_root,a.expected_tree);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,default=str)+'\n');print(json.dumps({'comparison':d['comparison'],'hypothesis':d['hypothesis']},indent=2));return
    raise SystemExit('choose mode')

if __name__=='__main__':main()
