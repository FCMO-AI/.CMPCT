from __future__ import annotations

"""Sparse-anchor localization oracle for Analytics Mode2.

A coarse page-dependency graph failed because charging an entire source page recursively turns one
irrelevant copy edge into hundreds of pages, even though the exact decoded-byte closure is ~1.01x.
This oracle preserves exact byte-level dependency sparsity while asking whether fixed 4 KiB token
anchors are sufficient to *locate* those ancestors economically.

For every 4 KiB-aligned request plus the exact final suffix, compute the exact transitive decoded-byte
closure. Then group only those actually-needed bytes by 4 KiB page. A conservative anchored scan charge
counts bytes from each page start through its furthest needed byte; this approximates token traversal
from a page anchor while allowing irrelevant copy payloads to be skipped by length and recursively
resolving only bytes that are actually needed.

Pre-registered disproof: reject `4KiB anchors + sparse copy resolution` if any request needs >8 unique
closure pages OR >32,768 anchored logical scan bytes. No page-size sweep. This remains a lower bound:
it gifts exact compressed bit anchors, dynamic-Huffman state, physical range I/O, authentication and
CPU cost of token parsing.
"""

import argparse
from array import array
import json
import os
from pathlib import Path
import shutil
import time
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_sparse_dependency_oracle as SPARSE

SCHEMA = 'cmpct-v030-r4-deflate-sparse-anchor-oracle-v1'
PAGE = 4096
LIMIT_PAGES = 8
LIMIT_SCAN_BYTES = 8 * PAGE
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
ANCHOR_BYTES = 16
BLOCK_STATE_BYTES = 64


def closure_nodes(parents: array, start: int, end: int) -> set[int]:
    seen: set[int] = set()
    stack = list(range(start, end))
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        parent = parents[node]
        if parent >= 0 and parent not in seen:
            stack.append(parent)
    return seen


def anchored_charge(nodes: set[int], request_start: int, request_end: int) -> dict:
    pages: dict[int, int] = {}
    for node in nodes:
        page = node // PAGE
        off = node - page * PAGE
        pages[page] = max(pages.get(page, -1), off)
    # Target request itself is charged exactly by its requested width. Ancestor pages are charged from
    # page anchor through the furthest actually-needed position. If an ancestor lies in target page,
    # it is already contained in the request charge for aligned requests.
    target_page = request_start // PAGE
    request_bytes = request_end - request_start
    scan = request_bytes
    for page, maxoff in pages.items():
        if page == target_page:
            continue
        scan += maxoff + 1
    return {
        'closure_pages': len(pages),
        'anchored_logical_scan_bytes': scan,
        'scan_amplification': scan / max(1, request_bytes),
        'dependency_pages': len(pages - {target_page}) if isinstance(pages, set) else len([p for p in pages if p != target_page]),
    }


def request_starts(n: int) -> list[int]:
    if n <= PAGE: return [0]
    starts = list(range(0, n - PAGE + 1, PAGE))
    tail = n - PAGE
    if starts[-1] != tail: starts.append(tail)
    return starts


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / 'benchmarks' / 'neutral_hostile_corpus_v1.py', 'r4_sparse_anchor_neutral')
    repair = V029._load(V029.REPAIR_PATH, 'r4_sparse_anchor_repair'); repair.install_generation_hooks(neutral)
    corpus = work / 'neutral'; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / '04_analytics_and_database'
    relation = DUAL._npz_relation(source)['accepted']
    npz = source.joinpath(*Path(relation['npz_path']).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, relation['member'])
    if method != zipfile.ZIP_DEFLATED: raise RuntimeError(f'expected DEFLATE, got {method}')
    t0 = time.perf_counter(); parsed = SPARSE.parse_parents(comp); parse_wall = time.perf_counter() - t0
    actual = zlib.decompress(comp, -15)
    if actual != expected or len(parsed['parents']) != len(actual): raise RuntimeError('parser mismatch')

    worst_pages = None; worst_scan = None; total_pages = total_scan = 0
    t0 = time.perf_counter()
    for start in request_starts(len(actual)):
        end = min(start + PAGE, len(actual)); nodes = closure_nodes(parsed['parents'], start, end)
        charge = anchored_charge(nodes, start, end)
        row = {
            'start': start, 'end': end, 'request_bytes': end-start,
            'unique_decoded_closure_bytes': len(nodes), **charge,
        }
        total_pages += row['closure_pages']; total_scan += row['anchored_logical_scan_bytes']
        if worst_pages is None or row['closure_pages'] > worst_pages['closure_pages']: worst_pages = row
        if worst_scan is None or row['anchored_logical_scan_bytes'] > worst_scan['anchored_logical_scan_bytes']: worst_scan = row
    probe_wall = time.perf_counter() - t0
    assert worst_pages and worst_scan
    passes = worst_pages['closure_pages'] <= LIMIT_PAGES and worst_scan['anchored_logical_scan_bytes'] <= LIMIT_SCAN_BYTES
    pages_total = (len(actual) + PAGE - 1) // PAGE
    index_envelope = pages_total * ANCHOR_BYTES + parsed['blocks'] * BLOCK_STATE_BYTES
    aux_budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    return {
        'schema': SCHEMA,
        'source_commit': os.environ.get('EVIDENCE_HEAD'),
        'workload': '04_analytics_and_database',
        'member': {'compressed_bytes':len(comp),'raw_bytes':len(actual),'crc32':info.CRC,'compress_type':info.compress_type},
        'parser': {'blocks':parsed['blocks'],'tokens':parsed['tokens'],'literal_tokens':parsed['literal_tokens'],'copy_tokens':parsed['copy_tokens'],'exact_raw_match':True,'parse_wall_s':parse_wall},
        'sparse_anchor': {
            'anchor_page_bytes': PAGE,
            'requests': len(request_starts(len(actual))),
            'limit_pages': LIMIT_PAGES,
            'limit_scan_bytes': LIMIT_SCAN_BYTES,
            'mean_closure_pages': total_pages / len(request_starts(len(actual))),
            'mean_anchored_scan_bytes': total_scan / len(request_starts(len(actual))),
            'worst_closure_pages': worst_pages,
            'worst_anchored_scan': worst_scan,
            'passes_lower_bound': passes,
            'probe_wall_s': probe_wall,
        },
        'economics': {
            'dual_owner_bytes':DUAL_OWNER_BYTES,'accepted_v029_bytes':ACCEPTED_V029_ANALYTICS,
            'max_auxiliary_bytes_to_beat_v029':aux_budget,
            'illustrative_page_anchor_plus_block_state_bytes':index_envelope,
            'illustrative_index_within_budget':index_envelope <= aux_budget,
        },
        'hypothesis': {'4KiB_anchors_plus_sparse_resolution_can_meet_8x_lower_bound':passes},
        'contract': {
            'diagnostic_only':True,'release_credit':False,'lower_bound_only':True,'no_page_size_sweep':True,
            'no_product_format_change':True,
            'important_limitation':'gifts exact compressed-bit anchors, dynamic-Huffman state, physical pread bytes, authentication, range fragmentation and token parsing CPU; pass only authorizes a physical prototype',
        },
        'next_if_supported':'build and charge a physical bit-anchor/sparse-copy reader with arbitrary-offset 4KiB requests, authenticated compressed ranges, exact reconstruction and metadata under the 1.682 MB budget',
        'next_if_falsified':'preserve negative and change owner boundary; do not sweep page size against Analytics',
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-sparse-anchor-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-sparse-anchor.json')); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'member':d['member'],'parser':d['parser'],'sparse_anchor':d['sparse_anchor'],'economics':d['economics'],'hypothesis':d['hypothesis']},indent=2))

if __name__=='__main__': main()
