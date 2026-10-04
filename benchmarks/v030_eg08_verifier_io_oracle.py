from __future__ import annotations

"""Exact-semantics EG08 verifier expansion-I/O oracle.

C25EG08 verification currently reconstructs a complete EG07 physical archive in a
normal temporary directory and then asks the existing EG07 semantic owner to verify
that second archive.  Office now misses ZIP creation by a narrow enough margin that
this duplicate physical publication/read path is worth isolating before changing the
reader API.

This oracle changes *only* where that temporary compatibility archive lives: the
baseline uses shipping ``EG08.strong_verify``; the candidate uses the identical
``_expand_to_eg07 -> EG07.strong_verify`` sequence on Linux tmpfs.  It therefore
cannot earn production promotion itself.  A material result is evidence that the next
implementation should remove the compatibility-file publication entirely with an
in-memory/direct EG08 semantic-verification path.  A miss is valid negative evidence
that filesystem I/O is not a material part of the remaining office budget.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v5 as V5POL
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as DV4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

ROUNDS = 15
MIN_RELATIVE_IMPROVEMENT = 0.15
MIN_ABSOLUTE_SAVING_S = 0.005


def _tmpfs_verify(archive: Path, *, expected_tree: str) -> dict:
    shm = Path('/dev/shm')
    if not shm.is_dir():
        raise RuntimeError('EG08 verifier I/O oracle requires Linux /dev/shm')
    with tempfile.TemporaryDirectory(prefix='cmpct-eg08-verify-', dir=shm) as td:
        expanded = Path(td) / 'expanded.cmpct'
        parsed = EG08._expand_to_eg07(archive, expanded)
        result = dict(EG07.strong_verify(expanded, expected_tree=expected_tree))
    result.update({
        'profile': 'federated-eg08-compact-physical-framing',
        'compact_pack_count': len(parsed['packs']),
        'recovered_from_tail': parsed['primary_error'] is not None,
    })
    return result


def _identity(result: dict) -> tuple:
    return (
        bool(result.get('ok')),
        result.get('tree_sha256'),
        result.get('profile'),
        int(result.get('compact_pack_count', -1)),
        bool(result.get('recovered_from_tail')),
    )


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix='cmpct-eg08-verify-io-', dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / 'normalized')
        expected_tree = EG07._treehash(stage)
        raw_eg07, _ = DV5._tmpfs_capture_raw_final_eg07(stage, root / 'discovery')
        meta_comp, _meta_raw, _digest, raws = DV4._raw_eg07_parts(raw_eg07)
        features = V3._pack_features(raws)
        payload_table = V3._payload_table(raws)
        comparators = V1._comparators(stage, root / 'comparators')
        size_ceiling = min(
            int(accepted_v029),
            int(comparators['zip']['archive_bytes']),
            int(comparators['zstd19']['archive_bytes']),
        )
        rules, vector, projected_bytes, _search = V5POL._search_full_frontier(
            features, meta_comp, payload_table, size_ceiling
        )
        if rules is None or vector is None or projected_bytes is None:
            raise RuntimeError('office EG08 generic policy unexpectedly lost its size win')
        archive = root / 'office.c25eg08'
        emitted = V1._emit(raw_eg07, archive, V3._selection_dict(vector))
        if int(emitted['archive_bytes']) != int(projected_bytes):
            raise RuntimeError('EG08 verifier oracle archive disagrees with exact projected bytes')

        baseline_samples: list[float] = []
        tmpfs_samples: list[float] = []
        reference_identity = None
        for index in range(ROUNDS):
            if index % 2 == 0:
                started = time.perf_counter(); baseline = EG08.strong_verify(archive, expected_tree=expected_tree); baseline_s = time.perf_counter() - started
                started = time.perf_counter(); candidate = _tmpfs_verify(archive, expected_tree=expected_tree); candidate_s = time.perf_counter() - started
            else:
                started = time.perf_counter(); candidate = _tmpfs_verify(archive, expected_tree=expected_tree); candidate_s = time.perf_counter() - started
                started = time.perf_counter(); baseline = EG08.strong_verify(archive, expected_tree=expected_tree); baseline_s = time.perf_counter() - started
            if not baseline.get('ok') or not candidate.get('ok'):
                raise RuntimeError('EG08 verifier I/O oracle failed strong verification')
            if _identity(baseline) != _identity(candidate):
                raise RuntimeError('tmpfs EG08 verifier changed verification identity')
            if reference_identity is None:
                reference_identity = _identity(baseline)
            elif _identity(baseline) != reference_identity:
                raise RuntimeError('EG08 verification identity is nondeterministic')
            baseline_samples.append(float(baseline_s))
            tmpfs_samples.append(float(candidate_s))

        corrupt = root / 'corrupt.c25eg08'
        blob = bytearray(archive.read_bytes())
        parsed = EG08._parse(archive)
        first_payload = parsed['packs'][0][5]
        needle = bytes(first_payload)
        at = bytes(blob).find(needle)
        if at < 0 or not needle:
            raise RuntimeError('could not locate first EG08 payload for corruption proof')
        blob[at + len(needle) // 2] ^= 0x01
        corrupt.write_bytes(blob)
        rejected = []
        for verifier in (
            lambda: EG08.strong_verify(corrupt, expected_tree=expected_tree),
            lambda: _tmpfs_verify(corrupt, expected_tree=expected_tree),
        ):
            try:
                result = verifier()
                rejected.append(not bool(result.get('ok')))
            except Exception:
                rejected.append(True)
        if rejected != [True, True]:
            raise RuntimeError('EG08 verifier I/O candidate weakened corruption rejection')

    baseline_median = statistics.median(baseline_samples)
    tmpfs_median = statistics.median(tmpfs_samples)
    saving = baseline_median - tmpfs_median
    relative = saving / max(baseline_median, 1e-12)
    material = saving >= MIN_ABSOLUTE_SAVING_S and relative >= MIN_RELATIVE_IMPROVEMENT
    gate = {
        'exact_verification_identity': True,
        'physical_corruption_rejected_by_both': True,
        'experiment_valid': True,
        'material_speedup': bool(material),
        'promotion_signal': bool(material),
        'release_credit': False,
    }
    gate['passed'] = bool(gate['experiment_valid'])
    return {
        'schema': 'cmpct-v030-eg08-verifier-io-v2',
        'archive_bytes': int(projected_bytes),
        'rounds': ROUNDS,
        'baseline_verify_s': baseline_samples,
        'tmpfs_verify_s': tmpfs_samples,
        'median_baseline_verify_s': float(baseline_median),
        'median_tmpfs_verify_s': float(tmpfs_median),
        'absolute_saving_s': float(saving),
        'relative_improvement': float(relative),
        'minimum_material_relative_improvement': MIN_RELATIVE_IMPROVEMENT,
        'minimum_material_absolute_saving_s': MIN_ABSOLUTE_SAVING_S,
        'gate': gate,
        'claim_boundary': (
            'Research-only causal I/O isolation. Candidate performs the exact same EG08 expansion and EG07 strong '
            'verification on tmpfs. A material result authorizes only a follow-up direct/in-memory verifier experiment. '
            'A non-material result is durable negative evidence; neither outcome earns release credit or weakens strong '
            'verification, locality, recovery, native/Android, external or release authority.'
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-eg08-verifier-io-work'))
    parser.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-eg08-verifier-io.json'))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)
    if not result['gate']['experiment_valid']:
        raise SystemExit('EG08 verifier I/O experiment was invalid')


if __name__ == '__main__':
    main()
