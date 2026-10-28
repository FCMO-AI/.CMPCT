from __future__ import annotations

"""Fused/streaming observation repair for the Analytics R4 dual-owner build.

Mission lock / preregistration
------------------------------
The unchanged fresh-process RSS gate is <=324,435 KiB.  The prior early-lifetime
repair reached 324,900 KiB, only 465 KiB above that bar, while preserving the
owner grammar and exact tree.  This experiment changes *observation
materialization only*: CSV and JSONL are consumed one physical row at a time,
semantic equality is proven as rows arrive, and complete row groups are encoded
immediately.  It deliberately does not retain raw CSV/JSONL byte strings, a
second CSV row tree, or the complete JSON row tree.

Falsification: preserve the result as negative if reconstructed tree differs,
if the emitted TCOL owner differs byte-for-byte from the existing FAST owner on
the same admitted pair, if candidate stored bytes regress >4 KiB, if peak RSS
exceeds 324,435 KiB, or if CPU/wall materially regress.  No grammar, group size,
admission rule, codec, threshold or product format changes are allowed.
"""

import argparse
import csv
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import struct
import time
import zipfile

import zstandard as zstd

from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_dual_owner_early_release_repair as EARLY
from benchmarks import v030_r4_tabular_integrated_archive as I
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = 'cmpct-v030-r4-dual-owner-streaming-observation-repair-v1'
REFERENCE_PEAK_KIB = EARLY.REFERENCE_PEAK_KIB
TARGET_PEAK_KIB = EARLY.TARGET_PEAK_KIB
MAX_BYTE_REGRESSION = EARLY.MAX_BYTE_REGRESSION
CPU_REGRESSION_S = 0.50
WALL_REGRESSION_S = 1.00


def rss() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _csv_values(line: bytes) -> list[str]:
    text = line.decode('utf-8')
    rows = list(csv.reader(io.StringIO(text, newline='')))
    if len(rows) != 1:
        raise ValueError('streaming owner rejects multiline CSV rows')
    return list(rows[0])


def _expected_csv(fields: list[str], row: dict) -> list[str]:
    return [str(row[f]) if not isinstance(row[f], bool) else ('True' if row[f] else 'False') for f in fields]


def _stream_owner(csvp: Path, jsonp: Path, group_rows: int) -> tuple[bytes, dict]:
    """Emit the exact FAST binary owner without whole-file/whole-table materialization."""
    cctx = zstd.ZstdCompressor(level=FAST.B.LEVEL)
    payload = bytearray()
    groups: list[tuple[int, int, int, list[tuple[bytes, int]]]] = []
    row_count = 0

    with csvp.open('rb') as cf, jsonp.open('rb') as jf:
        header = cf.readline()
        if not header or not header.endswith(b'\n'):
            raise ValueError('streaming owner requires LF-terminated CSV header')
        fields = _csv_values(header)
        if not fields:
            raise ValueError('empty CSV header')

        while True:
            rows: list[dict] = []
            csv_len = len(header) if row_count == 0 else 0
            json_len = 0
            for _ in range(group_rows):
                cline = cf.readline()
                jline = jf.readline()
                if not cline and not jline:
                    break
                if not cline or not jline:
                    raise ValueError('CSV/JSONL row-count mismatch')
                if not cline.endswith(b'\n') or not jline.endswith(b'\n'):
                    raise ValueError('streaming owner requires one LF-terminated physical line per row')
                crow = _csv_values(cline)
                jrow = json.loads(jline.decode('utf-8'))
                if not isinstance(jrow, dict) or list(jrow.keys()) != fields:
                    raise ValueError('JSONL field order drift')
                if crow != _expected_csv(fields, jrow):
                    raise ValueError('streaming semantic pair mismatch')
                rows.append(jrow)
                csv_len += len(cline)
                json_len += len(jline)
            if not rows:
                if cf.read(1) or jf.read(1):
                    raise ValueError('unexpected trailing bytes')
                break

            cols: list[tuple[bytes, int]] = []
            for field in fields:
                raw = json.dumps([r[field] for r in rows], separators=(',', ':')).encode()
                comp = cctx.compress(raw)
                cols.append((comp, len(raw)))
                payload.extend(comp)
            groups.append((len(rows), csv_len, json_len, cols))
            row_count += len(rows)

    chunks = [struct.pack('<IIIH', row_count, group_rows, len(groups), len(fields))]
    for field in fields:
        b = field.encode()
        chunks.append(struct.pack('<H', len(b)) + b)
    for n, csv_len, json_len, cols in groups:
        chunks.append(struct.pack('<IQQ', n, csv_len, json_len))
        for comp, logical in cols:
            chunks.append(struct.pack('<II32s', len(comp), logical, hashlib.sha256(comp).digest()))
    manifest = b''.join(chunks)
    prefix = FAST.B.MAGIC + struct.pack('<I', len(manifest)) + hashlib.sha256(manifest).digest()
    owner = prefix + manifest + bytes(payload)
    return owner, {
        'row_count': row_count,
        'group_count': len(groups),
        'manifest_bytes': len(manifest),
        'payload_bytes': len(payload),
        'whole_csv_bytes_materialized': False,
        'whole_jsonl_bytes_materialized': False,
        'whole_csv_row_tree_materialized': False,
        'whole_json_row_tree_materialized': False,
    }


def _reference_owner(csvp: Path, jsonp: Path) -> bytes:
    """Construct the old owner only as an equivalence control, then release it before NPZ work."""
    csv_source = csvp.read_bytes()
    json_source = jsonp.read_bytes()
    fields, csv_rows = OWNER._parse_csv(csv_source)
    jfields, json_rows = OWNER._parse_jsonl(json_source)
    if fields != jfields or not OWNER._semantic_equal(fields, csv_rows, json_rows):
        raise RuntimeError('reference semantic pair mismatch')
    csv_lengths = FAST._line_lengths(csv_source, len(json_rows), I.GROUP_ROWS, header=True)
    json_lengths = FAST._line_lengths(json_source, len(json_rows), I.GROUP_ROWS, header=False)
    owner, _ = FAST._encode(fields, json_rows, I.GROUP_ROWS, csv_lengths, json_lengths)
    return owner


def build_streaming(source: Path, out: Path, work: Path) -> dict:
    discovery = I._discover(source)
    if len(discovery['accepted']) != 1:
        raise RuntimeError('expected exactly one tabular relation')
    tab = discovery['accepted'][0]
    rel = DUAL._npz_relation(source)['accepted']
    csvp = source.joinpath(*Path(tab['csv_path']).parts)
    jsonp = source.joinpath(*Path(tab['jsonl_path']).parts)
    npyp = source.joinpath(*Path(rel['npy_path']).parts)
    npzp = source.joinpath(*Path(rel['npz_path']).parts)

    csv_meta = {'path': tab['csv_path'], **I._stat_record(csvp), 'sha256': _file_sha(csvp)}
    json_meta = {'path': tab['jsonl_path'], **I._stat_record(jsonp), 'sha256': _file_sha(jsonp)}
    npy_meta = {'path': rel['npy_path'], **I._stat_record(npyp)}
    npz_meta = {'path': rel['npz_path'], **I._stat_record(npzp)}

    tcol, tcol_stats = _stream_owner(csvp, jsonp, I.GROUP_ROWS)
    rss_after_stream_owner = rss()

    # Hostile control: the fused writer must emit *identical owner bytes* to the established FAST grammar.
    reference = _reference_owner(csvp, jsonp)
    owner_identical = reference == tcol
    del reference
    gc.collect()
    if not owner_identical:
        raise RuntimeError('streaming observation changed owner bytes')
    rss_after_equivalence = rss()

    npz_raw = npzp.read_bytes()
    with zipfile.ZipFile(npzp, 'r') as zf:
        npy_from_npz = zf.read(rel['member'])
    with npyp.open('rb') as f:
        npy_hash = hashlib.sha256(f.read()).hexdigest()
    if hashlib.sha256(npy_from_npz).hexdigest() != npy_hash:
        raise RuntimeError('NPZ relation mismatch')
    npy_meta['sha256'] = hashlib.sha256(npy_from_npz).hexdigest()
    npz_meta['sha256'] = hashlib.sha256(npz_raw).hexdigest()
    del npy_from_npz
    gc.collect()

    stripped = work / 'stripped'
    I._copy_without(source, stripped, {tab['csv_path'], tab['jsonl_path'], rel['npy_path'], rel['npz_path']})
    base = work / 'base.cmpct'
    base_stats = dict(PRODUCT.build(stripped, base))
    manifest = {
        'schema': 'cmpct-v030-r4-analytics-dual-owner-bundle-v1',
        'group_rows': I.GROUP_ROWS,
        'members': {'csv': csv_meta, 'jsonl': json_meta, 'npy': npy_meta, 'npz': npz_meta},
        'tabular_discovery': discovery,
        'npz_relation': {'accepted': rel},
    }
    bundle = DUAL._write_bundle(out, base, tcol, npz_raw, manifest)
    return {
        'stored_bytes': bundle['stored_bytes'],
        'bundle': bundle,
        'base_stats': base_stats,
        'tcol_stats': tcol_stats,
        'owner_identical_to_fast': owner_identical,
        'rss_after_stream_owner_kib': rss_after_stream_owner,
        'rss_after_equivalence_kib': rss_after_equivalence,
    }


def worker(mode: str, source: Path, out: Path, work: Path, result: Path) -> None:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    shutil.rmtree(out, ignore_errors=True)
    c0 = time.process_time(); w0 = time.perf_counter()
    row = DUAL._build_candidate(source, out, work) if mode == 'baseline' else build_streaming(source, out, work)
    verify = work / 'verify'; shutil.rmtree(verify, ignore_errors=True)
    v = DUAL._extract_candidate(out, verify)
    row.update({
        'mode': mode,
        'peak_rss_kib': rss(),
        'cpu_s': time.process_time() - c0,
        'wall_s': time.perf_counter() - w0,
        'tree_sha256': v['tree_sha256'],
    })
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps(row, default=str) + '\n')
    print(json.dumps({k: row[k] for k in ('mode','stored_bytes','peak_rss_kib','cpu_s','wall_s','tree_sha256')}, sort_keys=True))


def aggregate(work: Path, tree: str) -> dict:
    b = json.loads((work/'workers'/'baseline.json').read_text())
    r = json.loads((work/'workers'/'repaired.json').read_text())
    delta = int(r['stored_bytes']) - int(b['stored_bytes'])
    tree_ok = b['tree_sha256'] == tree and r['tree_sha256'] == tree
    peak = int(r['peak_rss_kib'])
    cpu_delta = float(r['cpu_s']) - float(b['cpu_s'])
    wall_delta = float(r['wall_s']) - float(b['wall_s'])
    supported = (tree_ok and r.get('owner_identical_to_fast') is True and peak <= TARGET_PEAK_KIB
                 and delta <= MAX_BYTE_REGRESSION and cpu_delta <= CPU_REGRESSION_S
                 and wall_delta <= WALL_REGRESSION_S)
    return {
        'schema': SCHEMA,
        'source_commit': os.environ.get('EVIDENCE_HEAD'),
        'expected_tree_sha256': tree,
        'baseline': b,
        'repaired': r,
        'comparison': {
            'byte_delta': delta,
            'peak_rss_delta_kib': peak - int(b['peak_rss_kib']),
            'peak_reduction_fraction_vs_reference': 1 - peak / REFERENCE_PEAK_KIB,
            'cpu_delta_s': cpu_delta,
            'wall_delta_s': wall_delta,
        },
        'hypothesis': {
            'streaming_observation_supported': supported,
            'tree_exact': tree_ok,
            'owner_byte_identical_to_fast': r.get('owner_identical_to_fast') is True,
            'repaired_peak_at_or_below_unchanged_target': peak <= TARGET_PEAK_KIB,
            'byte_regression_within_4KiB': delta <= MAX_BYTE_REGRESSION,
            'cpu_regression_within_0_5s': cpu_delta <= CPU_REGRESSION_S,
            'wall_regression_within_1s': wall_delta <= WALL_REGRESSION_S,
        },
        'contract': {
            'diagnostic_only': True,
            'release_credit': False,
            'unchanged_peak_target_kib': TARGET_PEAK_KIB,
            'owner_grammar_changed': False,
            'group_size_changed': False,
            'admission_changed': False,
            'codec_changed': False,
            'product_format_changed': False,
            'no_threshold_sweep': True,
        },
        'next_if_supported': 'carry fused observation into integrated Analytics builder; then combine with token-anchor physical reader and remeasure composed size/CPU/RSS/locality/recovery',
        'next_if_falsified': 'preserve negative; profile per-column Python materialization and extraction peak separately; do not relax the 20% gate',
    }


def prepare(work: Path) -> dict:
    return EARLY.prepare(work)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-r4-stream-work'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-r4-stream.json'))
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--worker', choices=('baseline','repaired'))
    p.add_argument('--source', type=Path)
    p.add_argument('--archive', type=Path)
    p.add_argument('--worker-work', type=Path)
    p.add_argument('--worker-result', type=Path)
    p.add_argument('--aggregate', action='store_true')
    p.add_argument('--expected-tree')
    a = p.parse_args()
    if a.prepare_only:
        print(json.dumps(prepare(a.work_root), sort_keys=True)); return
    if a.worker:
        if not all((a.source,a.archive,a.worker_work,a.worker_result)): raise SystemExit('missing worker args')
        worker(a.worker,a.source,a.archive,a.worker_work,a.worker_result); return
    if a.aggregate:
        if not a.expected_tree: raise SystemExit('--expected-tree required')
        d = aggregate(a.work_root,a.expected_tree)
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,default=str)+'\n')
        print(json.dumps({'comparison':d['comparison'],'hypothesis':d['hypothesis']},indent=2)); return
    raise SystemExit('choose mode')


if __name__ == '__main__':
    main()
