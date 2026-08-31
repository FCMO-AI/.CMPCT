from __future__ import annotations

"""Exact fresh-process PrefixGraph direct-floor vs full-builder RSS ownership oracle."""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_candidate as CAND

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / 'benchmarks' / 'v030_prefixgraph_direct_floor_rss_worker.py'
TARGET = ('resemblance_hostile_v1', '01_shifted_versions')
ORDERS = (('direct-floor', 'full'), ('full', 'direct-floor'))


def source_commit() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    cp = subprocess.run(
        [sys.executable, str(WORKER), '--mode', mode, '--source', str(source), '--archive', str(archive)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    if cp.returncode != 0:
        return {'mode': mode, 'worker_failed': True, 'returncode': cp.returncode, 'stdout': cp.stdout, 'stderr': cp.stderr}
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    if not lines:
        return {'mode': mode, 'worker_failed': True, 'returncode': 0, 'stdout': cp.stdout, 'stderr': cp.stderr, 'failure': 'missing receipt'}
    try:
        receipt = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {'mode': mode, 'worker_failed': True, 'returncode': 0, 'stdout': cp.stdout, 'stderr': cp.stderr, 'failure': repr(exc)}
    receipt['worker_failed'] = False
    return receipt


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / 'corpora')
    source = roots[TARGET]
    expected_tree = CAND.treehash(source)
    reps = []
    valid = True
    for round_index, order in enumerate(ORDERS):
        row = {'round': round_index, 'execution_order': list(order)}
        for mode in order:
            archive = work_root / 'archives' / f'r{round_index}-{mode}.cmpct'
            receipt = run_worker(mode, source, archive)
            row[mode] = receipt
            if (
                receipt.get('worker_failed')
                or receipt.get('tree_sha256') != expected_tree
                or receipt.get('strong_verify_ok') is not True
                or receipt.get('rss_measurement_boundary') != 'build-before-strong-verify-v2'
            ):
                valid = False
        reps.append(row)

    floor_rss = statistics.median(float(r['direct-floor']['incremental_build_peak_rss_kib']) for r in reps if not r['direct-floor'].get('worker_failed')) if valid else None
    full_rss = statistics.median(float(r['full']['incremental_build_peak_rss_kib']) for r in reps if not r['full'].get('worker_failed')) if valid else None
    floor_wall = statistics.median(float(r['direct-floor']['build_wall_s']) for r in reps if not r['direct-floor'].get('worker_failed')) if valid else None
    full_wall = statistics.median(float(r['full']['build_wall_s']) for r in reps if not r['full'].get('worker_failed')) if valid else None
    ratio = None if not full_rss else floor_rss / full_rss
    return {
        'schema': 'cmpct-v030-prefixgraph-direct-floor-rss-v2',
        'source_commit': source_commit(),
        'target': '/'.join(TARGET),
        'tree_sha256': expected_tree,
        'rounds': len(ORDERS),
        'repetitions': reps,
        'direct_floor_median_incremental_build_peak_rss_kib': floor_rss,
        'full_median_incremental_build_peak_rss_kib': full_rss,
        'direct_floor_to_full_build_rss_ratio': ratio,
        'direct_floor_median_build_wall_s': floor_wall,
        'full_median_build_wall_s': full_wall,
        'anchor_audition_owned_rss_signal': bool(valid and ratio is not None and ratio <= 0.65),
        'experiment_valid': valid,
        'selector_change': False,
        'release_credit': False,
        'contract': {
            'fresh_process_per_measurement': True,
            'same_source_tree': True,
            'rss_sample_captured_before_strong_verify': True,
            'strong_verify_after_measurement_is_mandatory': True,
            'verification_rss_excluded_from_build_peak': True,
            'direct_floor_uses_shipping_raws_and_direct_payload_floor': True,
            'direct_floor_uses_historical_all_direct_serializer': True,
            'full_uses_shipping_prefixgraph_builder': True,
            'archive_bytes_changed_in_product': False,
            'candidate_set_changed_in_product': False,
            'selector_changed': False,
            'grammar_changed': False,
            'integrity_changed': False,
            'locality_limit_changed': False,
            'decode_unit_limit_changed': False,
            'recovery_changed': False,
        },
        'claim_boundary': 'Diagnostic ownership only; no cancellation, selector, byte, policy or release credit follows from this result.',
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-prefixgraph-direct-floor-rss-work'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-prefixgraph-direct-floor-rss.json'))
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'target': result['target'],
        'floor_build_rss_kib': result['direct_floor_median_incremental_build_peak_rss_kib'],
        'full_build_rss_kib': result['full_median_incremental_build_peak_rss_kib'],
        'floor_to_full_build_rss_ratio': result['direct_floor_to_full_build_rss_ratio'],
        'anchor_audition_owned_rss_signal': result['anchor_audition_owned_rss_signal'],
        'experiment_valid': result['experiment_valid'],
    }, indent=2), flush=True)
    if not result['experiment_valid']:
        raise SystemExit('PrefixGraph direct-floor RSS ownership evidence invalid')


if __name__ == '__main__':
    main()
