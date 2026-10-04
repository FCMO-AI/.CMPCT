from __future__ import annotations

"""Shared-scan attribution for the exact path-blind dictionary portfolio.

Mission lock
============
The exact independent-vs-pathblind-dictionary portfolio is size/read safe on its
first five hard targets and retains two strict byte wins, but two complete builds
regress creation CPU and wall on all five.  Before refactoring encoding, isolate how
much of that debt is merely repeated filesystem scan/candidate discovery.

Falsifiable hypothesis
----------------------
One scan/candidate graph can feed both exact contenders without changing either
archive byte.  If sharing the scan materially reduces combined creation work, retain
it as the first rehabilitation layer.  If the creation debt remains confirmed, the
remaining duplicated ordinary encode/proof traffic becomes the next target.

No path signal, threshold, codec setting, locality law, comparator, format grammar,
Genesis score, or canonical Builder behavior changes.
"""

import argparse
import copy
import json
from pathlib import Path
import shutil
import time
import types

from cmpct.builder import Candidate
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks.v030_r24_pathblind_dictionary_referee import PathBlindDictionaryBuilder
from benchmarks.v030_r24_micropack_content_selective_read_referee import ABSOLUTE_REGRESSION_S, RELATIVE_REGRESSION


def _confirmed(candidate_s: float, base_s: float) -> dict:
    delta=float(candidate_s)-float(base_s)
    rel=(float(candidate_s)/float(base_s)-1.0) if float(base_s)>0 else 0.0
    return {'candidate_s':float(candidate_s),'base_s':float(base_s),'delta_s':delta,'relative':rel,
            'confirmed_regression':bool(delta>ABSOLUTE_REGRESSION_S and rel>RELATIVE_REGRESSION)}


def _snapshot(seed) -> dict:
    # Duplicate mutable graph structure while sharing immutable payload bytes.  The
    # clone cost is explicitly timed and charged to the shared-scan portfolio.
    return {
        'cands': {h: Candidate(c.raw, set(c.hints), {sh:[slot[0],slot[1]] for sh,slot in c.deflates.items()}) for h,c in seed.cands.items()},
        'files': copy.deepcopy(seed.files),
        'recipes': copy.deepcopy(seed.recipes),
        'dictionary': bytes(seed.dictionary), 'dict_hash': seed.dict_hash,
        'canonical_deflate': dict(seed.canonical_deflate), 'secondary_stream_hashes': set(seed.secondary_stream_hashes),
        'inode_first': dict(seed.inode_first), 'meta_by_rel': copy.deepcopy(seed.meta_by_rel),
    }


def _clone_from(seed, cls):
    b=cls(seed.root,deflate_reuse_min=seed.deflate_reuse_min,workers=1,reproducible=seed.reproducible,reproducible_epoch_ns=seed.reproducible_epoch_ns)
    b.micro_pack_target=seed.micro_pack_target;b.micro_pack_max_file=seed.micro_pack_max_file;b.encode_workers=seed.encode_workers
    state=_snapshot(seed)
    for k,v in state.items():setattr(b,k,v)
    b.scan=types.MethodType(lambda self: None,b)
    return b


def _build(builder,out:Path) -> dict:
    out.parent.mkdir(parents=True,exist_ok=True)
    c0=time.process_time();w0=time.perf_counter();stats=dict(builder.build(out));cpu=time.process_time()-c0;wall=time.perf_counter()-w0
    verify=BASE.PRODUCT.strong_verify(out)
    if not verify.get('ok'):raise RuntimeError('strong verify failed')
    return {'bytes':out.stat().st_size,'sha256':__import__('hashlib').sha256(out.read_bytes()).hexdigest(),'cpu_s':cpu,'wall_s':wall,'verify':True}


def _full(cls,source:Path,out:Path):
    b=cls(source,deflate_reuse_min=0,workers=1);b.micro_pack_max_file=int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    return _build(b,out)


def _one(source:Path,root:Path) -> dict:
    root.mkdir(parents=True,exist_ok=True)
    seq_i=_full(SAME.NoMicroPackBuilder,source,root/'seq-independent.cmpct')
    seq_d=_full(PathBlindDictionaryBuilder,source,root/'seq-dictionary.cmpct')
    seq_cpu=seq_i['cpu_s']+seq_d['cpu_s'];seq_wall=seq_i['wall_s']+seq_d['wall_s']

    seed=PathBlindDictionaryBuilder(source,deflate_reuse_min=0,workers=1);seed.micro_pack_max_file=int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    c0=time.process_time();w0=time.perf_counter();seed.scan();scan_cpu=time.process_time()-c0;scan_wall=time.perf_counter()-w0
    c0=time.process_time();w0=time.perf_counter();ib=_clone_from(seed,SAME.NoMicroPackBuilder);db=_clone_from(seed,PathBlindDictionaryBuilder);clone_cpu=time.process_time()-c0;clone_wall=time.perf_counter()-w0
    shared_i=_build(ib,root/'shared-independent.cmpct');shared_d=_build(db,root/'shared-dictionary.cmpct')
    shared_cpu=scan_cpu+clone_cpu+shared_i['cpu_s']+shared_d['cpu_s']
    shared_wall=scan_wall+clone_wall+shared_i['wall_s']+shared_d['wall_s']

    identity={
        'independent_bytes_exact':seq_i['sha256']==shared_i['sha256'] and seq_i['bytes']==shared_i['bytes'],
        'dictionary_bytes_exact':seq_d['sha256']==shared_d['sha256'] and seq_d['bytes']==shared_d['bytes'],
    }
    return {
        'sequential':{'independent':seq_i,'dictionary':seq_d,'combined_cpu_s':seq_cpu,'combined_wall_s':seq_wall},
        'shared_scan':{'scan_cpu_s':scan_cpu,'scan_wall_s':scan_wall,'clone_cpu_s':clone_cpu,'clone_wall_s':clone_wall,'independent':shared_i,'dictionary':shared_d,'combined_cpu_s':shared_cpu,'combined_wall_s':shared_wall},
        'identity':identity,'identity_pass':all(identity.values()),
        'cpu_delta_s':shared_cpu-seq_cpu,'wall_delta_s':shared_wall-seq_wall,
        'cpu_ratio':shared_cpu/seq_cpu if seq_cpu else None,'wall_ratio':shared_wall/seq_wall if seq_wall else None,
        'remaining_cpu_debt_vs_single_independent':_confirmed(shared_cpu,seq_i['cpu_s']),
        'remaining_wall_debt_vs_single_independent':_confirmed(shared_wall,seq_i['wall_s']),
    }


def run(work_root:Path) -> dict:
    shutil.rmtree(work_root,ignore_errors=True)
    paths,identities=CUR._build(work_root/'corpus');fp=CUR._fingerprint(identities)
    targets={
        'neutral_hostile_v1/01_developer_repository','neutral_hostile_v1/08_many_tiny_files',
        'neutral_hostile_v1/07_incompressible_and_encrypted_like','resemblance_hostile_v1/02_false_neighbors','resemblance_hostile_v1/05_incompressible',
    }
    rows={k:_one(paths[k],work_root/'work'/k.replace('/','__')) for k in sorted(targets)}
    identity_failures=[k for k,r in rows.items() if not r['identity_pass']]
    cpu_improved=[k for k,r in rows.items() if r['cpu_delta_s']<0]
    wall_improved=[k for k,r in rows.items() if r['wall_delta_s']<0]
    remaining_cpu=[k for k,r in rows.items() if r['remaining_cpu_debt_vs_single_independent']['confirmed_regression']]
    remaining_wall=[k for k,r in rows.items() if r['remaining_wall_debt_vs_single_independent']['confirmed_regression']]
    agg={
        'sequential_cpu_s':sum(r['sequential']['combined_cpu_s'] for r in rows.values()),
        'shared_cpu_s':sum(r['shared_scan']['combined_cpu_s'] for r in rows.values()),
        'sequential_wall_s':sum(r['sequential']['combined_wall_s'] for r in rows.values()),
        'shared_wall_s':sum(r['shared_scan']['combined_wall_s'] for r in rows.values()),
        'scan_cpu_s':sum(r['shared_scan']['scan_cpu_s'] for r in rows.values()),
        'scan_wall_s':sum(r['shared_scan']['scan_wall_s'] for r in rows.values()),
        'clone_cpu_s':sum(r['shared_scan']['clone_cpu_s'] for r in rows.values()),
        'clone_wall_s':sum(r['shared_scan']['clone_wall_s'] for r in rows.values()),
    }
    agg['cpu_delta_s']=agg['shared_cpu_s']-agg['sequential_cpu_s'];agg['wall_delta_s']=agg['shared_wall_s']-agg['sequential_wall_s']
    agg['cpu_ratio']=agg['shared_cpu_s']/agg['sequential_cpu_s'] if agg['sequential_cpu_s'] else None
    agg['wall_ratio']=agg['shared_wall_s']/agg['sequential_wall_s'] if agg['sequential_wall_s'] else None
    if identity_failures:verdict='SHARED_SCAN_INVALID'
    elif agg['cpu_delta_s']<0 or agg['wall_delta_s']<0:
        verdict='SHARED_SCAN_HELPS_BUT_FUSED_ENCODE_STILL_REQUIRED' if (remaining_cpu or remaining_wall) else 'SHARED_SCAN_CLOSES_CREATION_DEBT'
    else:verdict='SCAN_NOT_DOMINANT_FUSE_ENCODING'
    return {'schema':'cmpct-v030-r24-pathdict-shared-scan-v1','experiment_valid':not identity_failures,'release_credit':False,'canonical_builder_changed':False,'genesis_rescore':False,'corpus_fingerprint':fp,'targets':sorted(targets),'rows':rows,'identity_failures':identity_failures,'cpu_improved_workloads':cpu_improved,'wall_improved_workloads':wall_improved,'remaining_cpu_debts':remaining_cpu,'remaining_wall_debts':remaining_wall,'aggregate':agg,'verdict':verdict}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-pathdict-shared-scan-work'));ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-pathdict-shared-scan.json'));a=ap.parse_args()
    d=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':d['verdict'],'fingerprint':d['corpus_fingerprint'],'identity_failures':d['identity_failures'],'cpu_improved':d['cpu_improved_workloads'],'wall_improved':d['wall_improved_workloads'],'remaining_cpu':d['remaining_cpu_debts'],'remaining_wall':d['remaining_wall_debts'],'aggregate':d['aggregate']},indent=2,sort_keys=True),flush=True)

if __name__=='__main__':main()
