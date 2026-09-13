from __future__ import annotations

"""Attribute *why* locality-derived micro-packs reduce fresh creation cost.

This is a diagnostic mechanism referee, not a performance result.  It freezes the
same current-fingerprint workloads used by the fresh-process economics receipt and
observes Builder state immediately before and after only `_build_micro_packs()`.
The experiment asks whether the creation win has a concrete work-elimination path:
fewer independent candidates and/or removal of dictionary-training work that has
become redundant after small text members are fused into locality-bounded packs.

No archive is promoted from this file and no selector/threshold is changed.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_micropack_fresh_process_economics as FRESH
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE


def _dict_surface(builder) -> dict:
    samples = [
        c.raw for c in builder.cands.values()
        if len(c.raw) >= 64
        and '.cmpct-pack' not in c.hints
        and any(x in BASE.BUILDER.TEXT_EXT for x in c.hints)
    ]
    total = sum(map(len, samples))
    return {
        'sample_count': len(samples),
        'sample_bytes': total,
        'training_gate_open': len(samples) >= 16 and total >= 96 * 1024,
    }


def _snapshot(builder) -> dict:
    cands = list(builder.cands.values())
    return {
        'candidate_count': len(cands),
        'candidate_raw_bytes': sum(len(c.raw) for c in cands),
        'text_candidate_count': sum(any(x in BASE.BUILDER.TEXT_EXT for x in c.hints) for c in cands),
        'pack_candidate_count': sum('.cmpct-pack' in c.hints for c in cands),
        'dictionary_surface': _dict_surface(builder),
    }


def _one(source: Path) -> dict:
    b = BASE.LocalityDerivedBuilder(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    b.scan()
    before = _snapshot(b)
    b._build_micro_packs()
    after = _snapshot(b)
    groups = list(getattr(b, '_locality_derived_groups', []))
    return {
        'before': before,
        'after': after,
        'group_count': len(groups),
        'group_members': sum(int(g['members']) for g in groups),
        'candidate_count_delta': after['candidate_count'] - before['candidate_count'],
        'candidate_raw_bytes_delta': after['candidate_raw_bytes'] - before['candidate_raw_bytes'],
        'dictionary_sample_count_delta': after['dictionary_surface']['sample_count'] - before['dictionary_surface']['sample_count'],
        'dictionary_sample_bytes_delta': after['dictionary_surface']['sample_bytes'] - before['dictionary_surface']['sample_bytes'],
        'dictionary_gate_closed_by_micropack': (
            before['dictionary_surface']['training_gate_open']
            and not after['dictionary_surface']['training_gate_open']
        ),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    source_root = work_root / 'source'
    FRESH.ATTR._build_sources(source_root)
    rows = {}
    for ident in FRESH.TARGETS:
        rows[ident] = _one(source_root / ident.split('/', 1)[1])
    aggregate = {
        'groups': sum(r['group_count'] for r in rows.values()),
        'group_members': sum(r['group_members'] for r in rows.values()),
        'candidate_count_delta': sum(r['candidate_count_delta'] for r in rows.values()),
        'dictionary_sample_count_delta': sum(r['dictionary_sample_count_delta'] for r in rows.values()),
        'dictionary_sample_bytes_delta': sum(r['dictionary_sample_bytes_delta'] for r in rows.values()),
        'dictionary_gates_closed': sum(r['dictionary_gate_closed_by_micropack'] for r in rows.values()),
    }
    # The mechanism is explained only if the transformation removes independent
    # work on every workload where the fresh-process gate observed groups.
    unexplained = [
        name for name, r in rows.items()
        if r['group_count'] <= 0 or r['candidate_count_delta'] >= 0
    ]
    verdict = 'MICROPACK_HAS_CONCRETE_WORK_ELIMINATION_PATH' if not unexplained else 'MICROPACK_SPEED_CAUSE_STILL_UNEXPLAINED'
    return {
        'schema': 'cmpct-v030-r24-micropack-work-elimination-attribution-v1',
        'experiment_valid': True,
        'release_credit': False,
        'canonical_builder_changed': False,
        'performance_credit': False,
        'targets': rows,
        'aggregate': aggregate,
        'unexplained_targets': unexplained,
        'verdict': verdict,
        'interpretation_guard': 'Counts explain eliminated work but do not substitute for the fresh-process timing receipt.',
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-micropack-work-elimination-work'))
    ap.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-micropack-work-elimination.json'))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
