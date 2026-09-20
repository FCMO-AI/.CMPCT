from __future__ import annotations
"""Bounded-ownership oracle for the promoted G0-G4 overlay path.

Research-only. It preserves ordered canonical auditions and output bytes while
removing the full ``payloads -> outcomes -> records/transforms/auditions``
overlap from the parent. Promotion requires held-out and whole-product proof.
"""
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
import os
from pathlib import Path

from experiments import entropygraph_v030_release_product as RP


def bounded_parallel_deferred_overlay(graph_path: Path, overlay_path: Path) -> dict:
    shared = RP.C.SHARED
    source_format, _source_module, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))
    n = len(graph_records)
    records=[]; transforms=[]; auditions=[]

    if n and RP._g04_process_pool_eligible(graph_path, graph_records):
        workers=min(RP.G04_AUDITION_MAX_WORKERS,n,max(1,os.cpu_count() or 1)); window=max(workers,2*workers)
        ctx=mp.get_context('spawn')
        with ProcessPoolExecutor(max_workers=workers,mp_context=ctx) as pool:
            pending={}; next_submit=0
            while next_submit<min(n,window):
                rec=graph_records[next_submit]
                pending[next_submit]=pool.submit(RP._g04_audition_worker,(next_submit,rec,users[next_submit]))
                graph_records[next_submit]=None; next_submit+=1
            for idx in range(n):
                row=pending.pop(idx).result(); records.append(row[0]); transforms.append(row[1]); auditions.append(row[2])
                if next_submit<n:
                    rec=graph_records[next_submit]
                    pending[next_submit]=pool.submit(RP._g04_audition_worker,(next_submit,rec,users[next_submit]))
                    graph_records[next_submit]=None; next_submit+=1
        scheduler='bounded-window-ordered-spawn-process-pool-v1'
    elif n:
        workers=min(RP.G04_AUDITION_MAX_WORKERS,n); window=max(workers,2*workers)
        def audition(record_id,record): return shared.G._audition_record(record_id,record,users[record_id])
        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-v030-g04-bounded') as pool:
            pending={}; next_submit=0
            while next_submit<min(n,window):
                rec=graph_records[next_submit]; pending[next_submit]=pool.submit(audition,next_submit,rec)
                graph_records[next_submit]=None; next_submit+=1
            for idx in range(n):
                row=pending.pop(idx).result(); records.append(row[0]); transforms.append(row[1]); auditions.append(row[2])
                if next_submit<n:
                    rec=graph_records[next_submit]; pending[next_submit]=pool.submit(audition,next_submit,rec)
                    graph_records[next_submit]=None; next_submit+=1
        scheduler='bounded-window-ordered-thread-pool-v1'
    else:
        workers=0; window=0; scheduler='empty'

    graph_records.clear()
    annotated_meta=dict(graph_meta); annotated_meta['overlay_source_format']=source_format
    write_stats=shared.G._write_overlay(annotated_meta,records,transforms,overlay_path)
    return {'source_format':source_format,'records':records,'transforms':transforms,'auditions':auditions,
            'write_stats':write_stats,'verified':None,'verification_state':'deferred-until-byte-win',
            'audition_workers':workers,'audition_scheduler':scheduler,'audition_window':window,
            'audition_process_min_graph_bytes':RP.G04_PROCESS_MIN_GRAPH_BYTES,
            'audition_process_min_records':RP.G04_PROCESS_MIN_RECORDS,'delimiter_transpose':'bulk-rectangular-prefix-v1'}


def install() -> None:
    RP.C.SHARED._overlay_retained_graph=bounded_parallel_deferred_overlay
