from __future__ import annotations

"""Real-Office economics gate for transient compact-LOC1 checkpoints.

Mission Lock / Referee
======================
The adjudicated v7 Office representation is rebuilt unchanged from the frozen source-sealed v0.29
control. This gate does not alter a single archive byte, group, locator byte, auth rule, locality charge,
or admission decision. It extracts the *actual* v7 LOC1 bytes and exact family keys, then compares two
fresh-process reader algorithms on those same bytes:

A) current v7 streaming validation + rescanning family view;
B) the frozen stride-256, five-u64 packed checkpoint candidate already surviving near-ceiling and hostile
   duplicate/variable-uvarint review.

Two operation shapes are frozen before execution: (1) open/build + one late-key lookup, representing a
cold selective-read metadata decision; (2) one open/build + all exact Office metadata-key lookups,
representing repeated reads after an archive is open. The candidate must never change lookup results.

Hypothesis
----------
Checkpointing is economically justified for the actual Office locator only if it is exact, its fresh-
process current-RSS delta over the v7 streaming reader is <=1024 KiB, cold open+late-query wall is no
worse than 1.10x current v7, and open+all-lookups wall improves by >=2x. These are integration materiality
bounds, not product codec thresholds; no stride or threshold sweep is allowed after observing the result.

Disproof
--------
Any exactness mismatch, >1 MiB RSS increase, >10% cold regression, or <2x repeated-read improvement means
keep v7's simpler streaming reader for Office and retain checkpoints only as a hostile-scale research tool.
PASS authorizes only the next product-reader integration/referee; it grants no density, locality, native,
platform or release credit.
"""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_office_compact_monotone_directory_v5 as V5
from benchmarks import v030_r4_office_compact_monotone_directory_v7 as V7
from benchmarks import v030_r4_office_serialized_group_directory_referee as SER
from benchmarks import v030_r4_compact_locator_parser_resource_v2 as FAST
from benchmarks import v030_r4_compact_locator_checkpoint_lookup as CP

SCHEMA = "cmpct-v030-r4-office-locator-checkpoint-economics-v1"
RSS_DELTA_LIMIT_KIB = 1024
COLD_RATIO_LIMIT = 1.10
WARM_SPEEDUP_MIN = 2.0


def _rss_kib() -> int:
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    except OSError:
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _load_queries(path: Path) -> list[tuple[int, str, int]]:
    return [(int(x[0]), str(x[1]), int(x[2])) for x in json.loads(path.read_text())]


def worker(mode: str, raw_path: Path, query_path: Path) -> dict:
    raw = raw_path.read_bytes()
    queries = _load_queries(query_path)
    if not queries:
        raise RuntimeError('empty Office query set')
    late = queries[-1]
    gc.collect()
    before = _rss_kib()
    cpu0=time.process_time(); wall0=time.perf_counter()
    original = V4._read_canonical_uvarint
    V4._read_canonical_uvarint = FAST._read_canonical_uvarint_fast
    try:
        if mode == 'streaming':
            reader = V4._parse_locator_streaming(raw)
            locate = lambda q: V1._locate(reader[(q[0],q[1])], q[2])
        elif mode == 'checkpoint':
            reader = CP.CheckpointLocator(raw)
            locate = lambda q: reader.locate((q[0],q[1]), q[2])
        else:
            raise ValueError(mode)
        build_cpu=time.process_time()-cpu0; build_wall=time.perf_counter()-wall0
        # Retained reader state is live at this RSS sample.
        gc.collect(); after_build=_rss_kib()
        qcpu0=time.process_time(); qwall0=time.perf_counter()
        late_value=locate(late)
        late_cpu=time.process_time()-qcpu0; late_wall=time.perf_counter()-qwall0
        acpu0=time.process_time(); awall0=time.perf_counter()
        values=[locate(q) for q in queries]
        all_cpu=time.process_time()-acpu0; all_wall=time.perf_counter()-awall0
        after_all=_rss_kib()
    finally:
        V4._read_canonical_uvarint=original
    return {
        'mode': mode,
        'raw_locator_bytes': len(raw),
        'queries': len(queries),
        'build_cpu_s': build_cpu,
        'build_wall_s': build_wall,
        'late_query_cpu_s': late_cpu,
        'late_query_wall_s': late_wall,
        'build_plus_late_wall_s': build_wall+late_wall,
        'all_queries_cpu_s': all_cpu,
        'all_queries_wall_s': all_wall,
        'build_plus_all_wall_s': build_wall+all_wall,
        'late_value': late_value,
        'values': values,
        'current_rss_before_kib': before,
        'current_rss_after_build_kib': after_build,
        'current_rss_after_all_kib': after_all,
        'current_rss_delta_kib': after_build-before,
        'checkpoint_bytes': getattr(reader, 'packed_checkpoint_bytes', 0),
        'record_count': int(reader.record_count),
    }


def _fresh(mode: str, raw_path: Path, query_path: Path) -> dict:
    cp=subprocess.run([sys.executable,__file__,'--worker-mode',mode,'--raw',str(raw_path),'--queries',str(query_path)],check=True,capture_output=True,text=True)
    return json.loads(cp.stdout.strip().splitlines()[-1])


def run(work: Path, v029_checkout: Path, frozen_worker: Path) -> dict:
    d=V7.run(work,v029_checkout,frozen_worker)
    if not d['hypothesis']['direct_uvarint_proof_preserves_full_office_locator_contract']:
        raise RuntimeError('v7 prerequisite no longer passes')
    store=work/'compact-monotone-meta.bin'
    if not store.is_file():
        raise RuntimeError('v7 physical metadata store missing')
    fd=os.open(store,os.O_RDONLY)
    try:
        raw,_group_base,_frame=V5._read_frame_dual_bound(fd,0)
    finally:
        os.close(fd)
    _groups,_expected,family_keys=SER._build_groups(work)
    queries=[]
    for sf in sorted(family_keys):
        for key in family_keys[sf]:
            queries.append((int(sf[0]),str(sf[1]),int(key)))
    # Put a true late lookup last: last key of the lexicographically last non-empty family.
    if not queries:
        raise RuntimeError('no Office locator queries')
    queries.sort(key=lambda q:(q[0],V1.FAM_ID[q[1]],q[2]))
    raw_path=work/'office-v7-locator.raw'
    query_path=work/'office-v7-locator-queries.json'
    raw_path.write_bytes(raw); query_path.write_text(json.dumps(queries))
    baseline=_fresh('streaming',raw_path,query_path)
    candidate=_fresh('checkpoint',raw_path,query_path)
    exact=(baseline['values']==candidate['values'] and baseline['late_value']==candidate['late_value'] and baseline['record_count']==candidate['record_count'])
    rss_delta=candidate['current_rss_after_build_kib']-baseline['current_rss_after_build_kib']
    cold_ratio=candidate['build_plus_late_wall_s']/max(baseline['build_plus_late_wall_s'],1e-12)
    warm_speedup=baseline['build_plus_all_wall_s']/max(candidate['build_plus_all_wall_s'],1e-12)
    supported=exact and rss_delta<=RSS_DELTA_LIMIT_KIB and cold_ratio<=COLD_RATIO_LIMIT and warm_speedup>=WARM_SPEEDUP_MIN
    return {
        'schema':SCHEMA,
        'source_commit':os.environ.get('EVIDENCE_HEAD'),
        'v7_receipt':{
            'candidate_bytes_with_locator':d['compact_locator']['candidate_bytes_with_locator'],
            'same_input_v029_bytes':d['compact_locator']['same_input_v029_bytes'],
            'density_margin_bytes':d['compact_locator']['density_margin_bytes'],
            'charged_worst_read_bytes':d['selective_read']['charged_worst_read_bytes'],
            'locality_margin_bytes':d['selective_read']['locality_margin_bytes'],
        },
        'actual_office_locator':{
            'raw_locator_bytes':len(raw),
            'record_count':baseline['record_count'],
            'exact_queries':len(queries),
            'checkpoint_bytes':candidate['checkpoint_bytes'],
        },
        'streaming_v7':baseline,
        'checkpoint_candidate':candidate,
        'economics':{
            'exact_lookup_parity':exact,
            'checkpoint_rss_delta_vs_streaming_kib':rss_delta,
            'cold_build_plus_late_ratio':cold_ratio,
            'warm_build_plus_all_speedup_x':warm_speedup,
            'limits':{
                'rss_delta_kib':RSS_DELTA_LIMIT_KIB,
                'cold_ratio':COLD_RATIO_LIMIT,
                'warm_speedup_x':WARM_SPEEDUP_MIN,
            },
        },
        'hypothesis':{'checkpoints_are_worth_integrating_for_actual_office_locator':supported},
        'contract':{
            'v7_representation_unchanged':True,
            'same_actual_locator_bytes_and_queries':True,
            'checkpoint_stride_records':CP.STRIDE,
            'fixed_8x_and_auth_unchanged':True,
            'fresh_process_per_reader':True,
            'no_stride_or_threshold_sweep':True,
            'diagnostic_only':True,
            'release_credit':False,
        },
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument('--worker-mode',choices=['streaming','checkpoint'])
    p.add_argument('--raw',type=Path)
    p.add_argument('--queries',type=Path)
    p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-locator-checkpoint-economics-work'))
    p.add_argument('--v029-checkout',type=Path)
    p.add_argument('--frozen-worker',type=Path,default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py'))
    p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-locator-checkpoint-economics.json'))
    a=p.parse_args()
    if a.worker_mode:
        if a.raw is None or a.queries is None: raise SystemExit('worker needs --raw/--queries')
        print(json.dumps(worker(a.worker_mode,a.raw,a.queries),sort_keys=True)); return
    if a.v029_checkout is None: raise SystemExit('--v029-checkout required')
    d=run(a.work_root,a.v029_checkout,a.frozen_worker)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'v7_receipt':d['v7_receipt'],'actual_office_locator':d['actual_office_locator'],'economics':d['economics'],'hypothesis':d['hypothesis']},sort_keys=True))


if __name__=='__main__': main()
