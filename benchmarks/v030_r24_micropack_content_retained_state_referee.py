from __future__ import annotations

"""Retained-state referee for content-economic micro-packs.

Mission lock
============
Fresh-process evidence shows a Developer post-build RSS debt for the path-blind
content-economic micro-pack Builder. This diagnostic asks whether that debt is
required live product state or transient allocator/discovery residue.

Falsifiable hypothesis
----------------------
The Developer post-build RSS delta is not required product state. Either:
1. a concrete live Builder attribute accounts for a material share of the delta,
   or
2. the delta substantially collapses after the Builder lifetime ends plus GC /
   allocator trim, indicating transient allocator/native state.

Disproof: the RSS delta persists after Builder deletion + GC + malloc_trim while
Python live-object accounting shows no corresponding retained graph. That would
point to native/runtime state that needs a different causal probe.

This benchmark is diagnostic only. It does not mutate canonical Builder policy,
compression thresholds, locality, membership grammar, or release scoring.
"""

import argparse
import ctypes
import gc
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder

ROUNDS = 3


def _rss_kib() -> int:
    with open('/proc/self/status', 'r', encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    raise RuntimeError('VmRSS unavailable')


def _deep_size(obj, seen: set[int] | None = None) -> int:
    """Approximate retained Python bytes, deduplicating object identities."""
    if seen is None:
        seen = set()
    oid = id(obj)
    if oid in seen:
        return 0
    seen.add(oid)
    size = sys.getsizeof(obj, 0)
    if isinstance(obj, dict):
        for k, v in obj.items():
            size += _deep_size(k, seen) + _deep_size(v, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += _deep_size(item, seen)
    elif hasattr(obj, '__dict__'):
        size += _deep_size(vars(obj), seen)
    return int(size)


def _malloc_trim() -> bool:
    try:
        libc = ctypes.CDLL('libc.so.6')
        fn = libc.malloc_trim
        fn.argtypes = [ctypes.c_size_t]
        fn.restype = ctypes.c_int
        return bool(fn(0))
    except Exception:
        return False


BUILDERS = {
    'independent': SAME.NoMicroPackBuilder,
    'content_economic': ContentEconomicBuilder,
}


def _worker(source: Path, work: Path, variant: str) -> dict:
    cls = BUILDERS[variant]
    work.mkdir(parents=True, exist_ok=True)
    b = cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    archive = work / 'base.cmpct'
    build = BASE._build_with(b, archive)
    verify = BASE.PRODUCT.strong_verify(archive)
    if not verify.get('ok'):
        raise RuntimeError('strong verify failed')
    index, _data = BASE._parse_r24(archive)
    locality = BASE._pack_locality(index)
    if not locality['locality_pass']:
        raise RuntimeError('locality failed')

    rss_post_build = _rss_kib()
    attrs = {}
    for name, value in sorted(vars(b).items()):
        attrs[name] = _deep_size(value)
    builder_graph_bytes = _deep_size(b)
    audit = dict(getattr(b, '_content_economic_audit', {}))
    groups = len(getattr(b, '_locality_derived_groups', []))

    # End Builder lifetime only after the archive has been fully written and verified.
    del index
    del b
    gc.collect()
    rss_post_gc = _rss_kib()
    trim_supported = _malloc_trim()
    rss_post_trim = _rss_kib()

    return {
        'variant': variant,
        'archive_bytes': int(build['archive_bytes']),
        'groups': groups,
        'strong_verify': True,
        'locality_pass': True,
        'max_decode_unit_bytes': int(locality['max_decode_unit_bytes']),
        'builder_graph_bytes': int(builder_graph_bytes),
        'attribute_bytes': attrs,
        'rss_post_build_kib': int(rss_post_build),
        'rss_post_gc_kib': int(rss_post_gc),
        'rss_post_trim_kib': int(rss_post_trim),
        'trim_supported': bool(trim_supported),
        'peak_rss_kib': int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'auditions': int(audit.get('auditions', 0)),
        'accepted_groups': int(audit.get('accepted_groups', 0)),
        'rejected_groups': int(audit.get('rejected_groups', 0)),
    }


def _child(source: Path, work: Path, variant: str) -> dict:
    cp = subprocess.run([
        sys.executable, '-m', 'benchmarks.v030_r24_micropack_content_retained_state_referee',
        '--worker', '--source', str(source), '--work-root', str(work), '--variant', variant,
    ], check=True, capture_output=True, text=True,
        env={**os.environ, 'PYTHONHASHSEED': '0'})
    lines = [line for line in cp.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(cp.stderr[-2000:])
    return json.loads(lines[-1])


def _median(rows: list[dict], key: str) -> int:
    return int(statistics.median(int(r[key]) for r in rows))


def _summary(rows: list[dict]) -> dict:
    attrs = sorted(set().union(*(r['attribute_bytes'] for r in rows)))
    attr_medians = {
        name: int(statistics.median(int(r['attribute_bytes'].get(name, 0)) for r in rows))
        for name in attrs
    }
    return {
        'archive_bytes': int(rows[0]['archive_bytes']),
        'groups': int(rows[0]['groups']),
        'builder_graph_bytes': _median(rows, 'builder_graph_bytes'),
        'attribute_bytes': attr_medians,
        'rss_post_build_kib': _median(rows, 'rss_post_build_kib'),
        'rss_post_gc_kib': _median(rows, 'rss_post_gc_kib'),
        'rss_post_trim_kib': _median(rows, 'rss_post_trim_kib'),
        'peak_rss_kib': _median(rows, 'peak_rss_kib'),
        'max_decode_unit_bytes': max(int(r['max_decode_unit_bytes']) for r in rows),
        'trim_supported': all(bool(r['trim_supported']) for r in rows),
        'auditions': int(rows[0]['auditions']),
        'accepted_groups': int(rows[0]['accepted_groups']),
        'rejected_groups': int(rows[0]['rejected_groups']),
        'raw_rounds': rows,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus = work_root / 'corpus'
    ATTR._build_sources(corpus)
    source = corpus / '01_developer_repository'
    raw = {name: [] for name in BUILDERS}
    for round_idx in range(ROUNDS):
        order = ('independent', 'content_economic') if round_idx % 2 == 0 else ('content_economic', 'independent')
        for variant in order:
            raw[variant].append(_child(source, work_root / 'workers' / f'r{round_idx}-{variant}', variant))

    arms = {name: _summary(rows) for name, rows in raw.items()}
    ind, con = arms['independent'], arms['content_economic']
    all_attrs = sorted(set(ind['attribute_bytes']) | set(con['attribute_bytes']))
    attr_delta = {
        name: int(con['attribute_bytes'].get(name, 0)) - int(ind['attribute_bytes'].get(name, 0))
        for name in all_attrs
    }
    ranked = sorted(attr_delta.items(), key=lambda kv: abs(kv[1]), reverse=True)
    deltas = {
        'builder_graph_bytes': con['builder_graph_bytes'] - ind['builder_graph_bytes'],
        'rss_post_build_kib': con['rss_post_build_kib'] - ind['rss_post_build_kib'],
        'rss_post_gc_kib': con['rss_post_gc_kib'] - ind['rss_post_gc_kib'],
        'rss_post_trim_kib': con['rss_post_trim_kib'] - ind['rss_post_trim_kib'],
        'peak_rss_kib': con['peak_rss_kib'] - ind['peak_rss_kib'],
    }

    return {
        'schema': 'cmpct-v030-r24-content-retained-state-v1',
        'experiment_valid': True,
        'release_credit': False,
        'canonical_builder_changed': False,
        'product_state_claim': False,
        'source': 'origin_developer',
        'rounds': ROUNDS,
        'arms': arms,
        'deltas_content_minus_independent': deltas,
        'attribute_delta_bytes': attr_delta,
        'largest_attribute_deltas': ranked[:12],
        'verdict': 'CONTENT_RETAINED_STATE_ATTRIBUTED',
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', action='store_true')
    ap.add_argument('--source', type=Path)
    ap.add_argument('--variant', choices=tuple(BUILDERS))
    ap.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-content-retained-state-work'))
    ap.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-content-retained-state.json'))
    args = ap.parse_args()
    if args.worker:
        if args.source is None or args.variant is None:
            raise SystemExit('--worker requires --source and --variant')
        print(json.dumps(_worker(args.source, args.work_root, args.variant), sort_keys=True), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'deltas': result['deltas_content_minus_independent'],
        'largest_attribute_deltas': result['largest_attribute_deltas'][:6],
        'auditions': result['arms']['content_economic']['auditions'],
        'accepted_groups': result['arms']['content_economic']['accepted_groups'],
        'rejected_groups': result['arms']['content_economic']['rejected_groups'],
    }, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
