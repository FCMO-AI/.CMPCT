from __future__ import annotations

"""Rotated A/B for eliminating duplicate semantic/disk identity work from promoted Logs extraction."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_logs_terminal_admission_oracle as TERMINAL
from experiments import entropygraph_v030_logs_fused_extract as FUSED
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 11
MIN_RELATIVE_SPEEDUP = 0.10


def _tree(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix().encode()
        if p.is_file() and not p.is_symlink():
            raw=p.read_bytes(); h.update(b"f\0"+rel+b"\0"+hashlib.sha256(raw).digest())
        elif p.is_symlink():
            h.update(b"l\0"+rel+b"\0"+p.readlink().as_posix().encode())
        elif p.is_dir():
            h.update(b"d\0"+rel)
    return h.hexdigest()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    neutral=TERMINAL.GENERAL.V029._load(TERMINAL.GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_logs_fused_extract_neutral')
    repair=TERMINAL.GENERAL.V029._load(TERMINAL.GENERAL.V029.REPAIR_PATH,'cmpct_v030_logs_fused_extract_repair')
    repair.install_generation_hooks(neutral)
    corpus=work_root/'neutral'; neutral.build(corpus); repair.normalize_root(corpus)
    source=corpus/'05_logs_and_telemetry'
    stage=TERMINAL.EXT._normalized_stage(source, work_root/'stage-root')
    archive=work_root/'logs.cmpct'; LOGS.build(stage, archive)
    verified=PRODUCT.strong_verify(archive)
    if not verified.get('ok'): raise RuntimeError('logs candidate failed strong verification')
    expected_tree=verified['tree_sha256']

    samples={'current':[],'fused':[]}; digests={'current':[],'fused':[]}
    for i in range(ROUNDS):
        for name in (('current','fused') if i%2==0 else ('fused','current')):
            dst=work_root/f'{name}-{i}'; shutil.rmtree(dst, ignore_errors=True)
            t=time.perf_counter()
            (PRODUCT.extract if name=='current' else FUSED.extract)(archive,dst)
            samples[name].append(time.perf_counter()-t)
            digests[name].append(_tree(dst))
    cm=statistics.median(samples['current']); fm=statistics.median(samples['fused'])
    exact=len(set(digests['current']+digests['fused']))==1
    saving=cm-fm; relative=saving/cm if cm else 0.0
    return {
      'schema':'cmpct-v030-logs-fused-extract-oracle-v1',
      'contract':{
        'rounds':ROUNDS,'minimum_relative_speedup':MIN_RELATIVE_SPEEDUP,
        'same_archive_bytes':True,'same_archive_semantic_owner':True,
        'same_filesystem_manifest':True,'one_authenticated_archive_session':True,
        'second_on_disk_sha_pass':False,'archive_bytes_changed':False,'selector_change':False,'release_credit':False,
      },
      'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'tree_sha256':expected_tree,'samples_s':samples,'median_s':{'current':cm,'fused':fm},
      'absolute_saving_s':saving,'relative_speedup':relative,'all_outputs_exact':exact,
      'promotion_signal':bool(exact and relative>=MIN_RELATIVE_SPEEDUP),'release_credit':False,
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps(r))
    if not r['all_outputs_exact']: raise SystemExit('fused logs extraction changed output')
if __name__=='__main__': main()
