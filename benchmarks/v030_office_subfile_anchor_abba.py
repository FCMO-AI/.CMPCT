from __future__ import annotations

"""Exact-position A/B for a generic sub-file-search futility accelerator.

The historical EntropyGraph splice search performs ``parent.find(child)`` for every remaining whole-object pair.
Exact Office profiling attributes ~30.8 ms to those searches, while an exact contribution receipt found 105 eligible
size-ordered pairs and zero selected splice edges. This oracle tests a content-derived accelerator rather than an
Office-specific disable: search a fixed prefix anchor first, and only compare the full child at anchor positions.

If the full child exists, its prefix necessarily exists at the same first full-match position. Iterating prefix hits
in ascending order and returning the first ``parent.startswith(child, pos)`` therefore reproduces ``bytes.find``'s
exact first-match index, including overlapping/repetitive data. The A/B additionally ratchets exact positions for all
eligible frozen Office pairs and adversarial synthetic cases.

Research only. A positive result authorizes integrating the exact helper behind a differential ratchet; it does not
permit workload/path/hash dispatch or disable splice discovery.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as OFFICE

ROUNDS = 41
ANCHOR_BYTES = 32
MIN_ABSOLUTE_SAVING_S = 0.003
MIN_RELATIVE_SAVING = 0.20


def anchored_find(parent: bytes, child: bytes, *, anchor_bytes: int = ANCHOR_BYTES) -> int:
    if not child:
        return 0
    if len(child) <= anchor_bytes:
        return parent.find(child)
    anchor = child[:anchor_bytes]
    pos = parent.find(anchor)
    while pos >= 0:
        if parent.startswith(child, pos):
            return pos
        pos = parent.find(anchor, pos + 1)
    return -1


def _eligible_pairs(stage: Path) -> list[tuple[bytes, bytes]]:
    raws = [p.read_bytes() for p in sorted(stage.rglob('*')) if p.is_file() and p.stat().st_size >= 32 * 1024]
    return [(parent, child) for parent in raws for child in raws if child is not parent and len(child) < len(parent)]


def _adversarial_identity() -> bool:
    cases = [
        (b'', b''),
        (b'a' * 100, b'a' * 40),
        (b'a' * 100 + b'b', b'a' * 40 + b'b'),
        ((b'prefix-' * 1000) + b'UNIQUE-END', (b'prefix-' * 20) + b'UNIQUE-END'),
        (b'x' * 31 + b'y' * 96, b'y' * 64),
        (b'0123456789' * 1000, b'3456789' * 20),
        (b'abc' * 1000 + b'xyz', b'abc' * 100 + b'xyz'),
    ]
    for parent, child in cases:
        if anchored_find(parent, child) != parent.find(child):
            return False
    return True


def _run_loop(pairs: list[tuple[bytes, bytes]], candidate: bool) -> tuple[float, tuple[int, ...]]:
    started = time.perf_counter_ns()
    if candidate:
        positions = tuple(anchored_find(parent, child) for parent, child in pairs)
    else:
        positions = tuple(parent.find(child) for parent, child in pairs)
    return (time.perf_counter_ns() - started) / 1e9, positions


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, _accepted_v029 = OFFICE._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-office-subfile-anchor-', dir=work_root) as td:
        stage = OFFICE.EXT._normalized_stage(source, Path(td) / 'normalized')
        pairs = _eligible_pairs(stage)
        baseline_positions = tuple(parent.find(child) for parent, child in pairs)
        candidate_positions = tuple(anchored_find(parent, child) for parent, child in pairs)
        exact_positions = baseline_positions == candidate_positions
        baseline_times: list[float] = []
        candidate_times: list[float] = []
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for candidate in order:
                elapsed, positions = _run_loop(pairs, candidate)
                if positions != baseline_positions:
                    raise RuntimeError('anchored sub-file search changed exact first-match positions')
                (candidate_times if candidate else baseline_times).append(elapsed)

    baseline_median = float(statistics.median(baseline_times))
    candidate_median = float(statistics.median(candidate_times))
    saving_s = baseline_median - candidate_median
    saving_ratio = saving_s / baseline_median if baseline_median else 0.0
    adversarial_identity = _adversarial_identity()
    experiment_valid = bool(
        pairs
        and exact_positions
        and adversarial_identity
        and len(baseline_times) == len(candidate_times) == ROUNDS
        and baseline_median > 0
        and candidate_median > 0
    )
    promotion_signal = bool(
        experiment_valid
        and saving_s >= MIN_ABSOLUTE_SAVING_S
        and saving_ratio >= MIN_RELATIVE_SAVING
    )
    return {
        'schema': 'cmpct-v030-office-subfile-anchor-abba-v1',
        'contract': {
            'rounds': ROUNDS,
            'anchor_bytes': ANCHOR_BYTES,
            'minimum_absolute_saving_s': MIN_ABSOLUTE_SAVING_S,
            'minimum_relative_saving': MIN_RELATIVE_SAVING,
            'exact_first_match_positions_required': True,
            'adversarial_identity_required': True,
            'workload_identity_used_by_candidate': False,
            'release_credit': False,
        },
        'eligible_pair_count': len(pairs),
        'matched_pair_count': sum(pos >= 0 for pos in baseline_positions),
        'identity': {
            'frozen_pair_positions_exact': exact_positions,
            'adversarial_positions_exact': adversarial_identity,
        },
        'medians_s': {'bytes_find': baseline_median, 'anchored_find': candidate_median},
        'delta': {'saving_s': saving_s, 'saving_ratio': saving_ratio},
        'samples_s': {'baseline': baseline_times, 'candidate': candidate_times},
        'experiment_valid': experiment_valid,
        'promotion_signal': promotion_signal,
        'release_credit': False,
        'claim_boundary': (
            'Exact first-position search micro-architecture only. A positive signal may justify integrating a generic '
            'helper plus full archive-byte/generalization A/B; it does not authorize disabling splice discovery.'
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-office-subfile-anchor-work'))
    parser.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-office-subfile-anchor.json'))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'eligible_pair_count': result['eligible_pair_count'],
        'matched_pair_count': result['matched_pair_count'],
        'identity': result['identity'],
        'medians_s': result['medians_s'],
        'delta': result['delta'],
        'promotion_signal': result['promotion_signal'],
    }, indent=2), flush=True)
    if not result['experiment_valid']:
        raise SystemExit('Office exact sub-file anchor A/B evidence invalid')


if __name__ == '__main__':
    main()
