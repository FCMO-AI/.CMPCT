from __future__ import annotations

"""Fresh-process stage attribution for the Analytics R4 dual-owner build RSS debt.

The repaired operation-level receipt measured 405,544 KiB peak RSS for dual_build versus 173,948 KiB
for ordinary v0.30 build. This diagnostic isolates the major causal stages in independent processes,
using a preparation phase only to freeze exact relation paths. It intentionally does not subtract RSS
peaks as exact ownership.

Pre-registered interpretation:
- 405,544 KiB is the observed full dual-build reference peak.
- A stage is a primary owner if its isolated peak is >=300 MiB AND >=75% of the dual-build peak.
- If no isolated stage qualifies, classify the debt as coexistence/lifetime interaction and prioritize
  fused/streaming execution or earlier release of intermediates rather than tuning an arbitrary stage.
No product/format/selector change and no memory-threshold sweep.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import time

SCHEMA = "cmpct-v030-r4-dual-build-rss-stage-attribution-v1"
DUAL_BUILD_REFERENCE_KIB = 405_544
PRIMARY_ABS_KIB = 300 * 1024
PRIMARY_RATIO = 0.75
MODES = (
    "runtime",
    "tabular_read",
    "tabular_parse",
    "tabular_encode",
    "npz_read",
    "stripped_base_build",
)


def _rss() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _current() -> int | None:
    try:
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    except OSError:
        return None
    return None


def prepare(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    from benchmarks import mosaic_v029_generalization_bench as V029
    from benchmarks import v030_r4_tabular_integrated_archive as I
    from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
    neutral = V029._load(V029.ROOT / 'benchmarks' / 'neutral_hostile_corpus_v1.py', 'r4_rss_stage_neutral')
    repair = V029._load(V029.REPAIR_PATH, 'r4_rss_stage_repair')
    repair.install_generation_hooks(neutral)
    corpus = work / 'neutral'
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / '04_analytics_and_database'
    tab = I._discover(source)
    if len(tab['accepted']) != 1:
        raise RuntimeError('expected exactly one tabular relation')
    npz = DUAL._npz_relation(source)['accepted']
    meta = {
        'source': str(source),
        'csv_path': tab['accepted'][0]['csv_path'],
        'jsonl_path': tab['accepted'][0]['jsonl_path'],
        'npy_path': npz['npy_path'],
        'npz_path': npz['npz_path'],
        'npz_member': npz['member'],
    }
    (work / 'stage-meta.json').write_text(json.dumps(meta, indent=2) + '\n')
    return meta


def _paths(work: Path) -> tuple[Path, dict]:
    meta = json.loads((work / 'stage-meta.json').read_text())
    return Path(meta['source']), meta


def worker(mode: str, work: Path, worker_out: Path) -> dict:
    source, meta = _paths(work)
    start_current = _current(); start_peak = _rss(); c0 = time.process_time(); w0 = time.perf_counter()
    details = {}
    if mode == 'runtime':
        pass
    elif mode in ('tabular_read', 'tabular_parse', 'tabular_encode'):
        from benchmarks import v030_r4_tabular_owner_oracle as OWNER
        csvp = source.joinpath(*Path(meta['csv_path']).parts)
        jsonp = source.joinpath(*Path(meta['jsonl_path']).parts)
        csv_raw = csvp.read_bytes(); json_raw = jsonp.read_bytes()
        details['csv_bytes'] = len(csv_raw); details['jsonl_bytes'] = len(json_raw)
        if mode != 'tabular_read':
            cf, cr = OWNER._parse_csv(csv_raw); jf, jr = OWNER._parse_jsonl(json_raw)
            if cf != jf or not OWNER._semantic_equal(cf, cr, jr):
                raise RuntimeError('semantic relation mismatch')
            details['rows'] = len(jr); details['fields'] = len(cf)
            if mode == 'tabular_encode':
                from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
                from benchmarks import v030_r4_tabular_integrated_archive as I
                csv_lengths = FAST._line_lengths(csv_raw, len(jr), I.GROUP_ROWS, header=True)
                json_lengths = FAST._line_lengths(json_raw, len(jr), I.GROUP_ROWS, header=False)
                owner, stats = FAST._encode(cf, jr, I.GROUP_ROWS, csv_lengths, json_lengths)
                details.update({'owner_bytes': len(owner), **stats})
    elif mode == 'npz_read':
        npyp = source.joinpath(*Path(meta['npy_path']).parts)
        npzp = source.joinpath(*Path(meta['npz_path']).parts)
        a = npyp.read_bytes(); b = npzp.read_bytes()
        details.update({'npy_bytes': len(a), 'npz_bytes': len(b)})
    elif mode == 'stripped_base_build':
        from benchmarks import v030_r4_tabular_integrated_archive as I
        from experiments import entropygraph_v030_release_product as PRODUCT
        stripped = worker_out / 'stripped'; archive = worker_out / 'base.cmpct'
        remove = {meta['csv_path'], meta['jsonl_path'], meta['npy_path'], meta['npz_path']}
        I._copy_without(source, stripped, remove)
        stats = dict(PRODUCT.build(stripped, archive))
        details.update({'archive_bytes': archive.stat().st_size, 'product_stats': stats})
    else:
        raise ValueError(mode)
    return {
        'mode': mode,
        'start_current_rss_kib': start_current,
        'start_peak_rss_kib': start_peak,
        'end_current_rss_kib': _current(),
        'peak_rss_kib': _rss(),
        'cpu_s': time.process_time() - c0,
        'wall_s': time.perf_counter() - w0,
        'details': details,
    }


def aggregate(work: Path) -> dict:
    rows = {}
    for mode in MODES:
        p = work / 'stage-workers' / f'{mode}.json'
        if not p.exists(): raise RuntimeError(f'missing {p}')
        rows[mode] = json.loads(p.read_text())
    qualifying = []
    for mode, row in rows.items():
        if mode == 'runtime': continue
        peak = int(row['peak_rss_kib'])
        if peak >= PRIMARY_ABS_KIB and peak >= PRIMARY_RATIO * DUAL_BUILD_REFERENCE_KIB:
            qualifying.append(mode)
    classification = 'isolated-primary-owner' if qualifying else 'coexistence-or-lifetime-interaction'
    return {
        'schema': SCHEMA,
        'source_commit': os.environ.get('EVIDENCE_HEAD'),
        'dual_build_reference_peak_rss_kib': DUAL_BUILD_REFERENCE_KIB,
        'primary_owner_thresholds': {'absolute_kib': PRIMARY_ABS_KIB, 'ratio_of_dual_build': PRIMARY_RATIO},
        'fresh_process_stages': rows,
        'qualifying_primary_owner_stages': qualifying,
        'classification': classification,
        'contract': {
            'diagnostic_only': True,
            'release_credit': False,
            'fresh_shell_process_per_stage': True,
            'preparation_unmeasured': True,
            'no_peak_subtraction_as_exact_ownership': True,
            'no_memory_threshold_sweep': True,
            'product_format_changed': False,
            'selector_changed': False,
        },
        'next_if_isolated_owner': 'replace materialization in the qualifying stage with streaming/fused state, then remeasure exact build bytes/CPU/RSS',
        'next_if_coexistence': 'instrument object lifetimes and restructure dual build so large stage intermediates do not coexist; then remeasure fresh-process peak',
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-r4-rss-stage-work'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-r4-rss-stage.json'))
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--worker', choices=MODES)
    p.add_argument('--worker-out', type=Path)
    p.add_argument('--worker-json', type=Path)
    p.add_argument('--aggregate', action='store_true')
    a = p.parse_args()
    if a.prepare_only:
        print(json.dumps(prepare(a.work_root), sort_keys=True)); return
    if a.worker:
        if not a.worker_out or not a.worker_json: raise SystemExit('--worker requires --worker-out and --worker-json')
        shutil.rmtree(a.worker_out, ignore_errors=True); a.worker_out.mkdir(parents=True)
        d = worker(a.worker, a.work_root, a.worker_out)
        a.worker_json.parent.mkdir(parents=True, exist_ok=True); a.worker_json.write_text(json.dumps(d, indent=2) + '\n')
        print(json.dumps(d, sort_keys=True)); return
    if a.aggregate:
        d = aggregate(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(d, indent=2) + '\n')
        print(json.dumps({'fresh_process_stages': d['fresh_process_stages'], 'qualifying_primary_owner_stages': d['qualifying_primary_owner_stages'], 'classification': d['classification']}, indent=2)); return
    raise SystemExit('choose --prepare-only, --worker MODE, or --aggregate')


if __name__ == '__main__': main()
