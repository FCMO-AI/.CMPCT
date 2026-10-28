from __future__ import annotations

"""Adversarial/generalization campaign for r24 dictionary-training skip admission.

The frozen 15-workload admission search found generic pre-training envelopes where disabling dictionary
training preserves the complete canonical r24 archive byte-for-byte while saving material creation CPU.
This campaign challenges those envelopes with new deterministic, non-benchmark trees and then searches
for rules that survive *both* the frozen suite and the adversarial cases.

Production remains unchanged. A surviving rule is promotion evidence only; the ordinary all-15 external,
no-regression, runtime, integrity, native and Android authorities remain independently mandatory.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil

from benchmarks import v030_r24_dictionary_skip_admission_oracle as ADMIT
from benchmarks import v030_r24_dictionary_training_cost_oracle as COST

SEED = 0xC030D1C7


def _write_repeat(path: Path, *, size: int, token: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (token * ((size + len(token) - 1) // len(token)))[:size]
    path.write_bytes(data)


def _write_random(path: Path, *, size: int, rng: random.Random) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(rng.randbytes(size))


def _tree_provenance(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob('*') if x.is_file() and not x.is_symlink()):
        rel = p.relative_to(root).as_posix().encode()
        data = p.read_bytes()
        h.update(len(rel).to_bytes(4, 'little'))
        h.update(rel)
        h.update(len(data).to_bytes(8, 'little'))
        h.update(hashlib.sha256(data).digest())
    return h.hexdigest()


def _build_adversarial(root: Path) -> list[tuple[str, Path, str]]:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    rng = random.Random(SEED)
    cases: list[tuple[str, Path, str]] = []

    # High-entropy medium binary family: deliberately resembles the safe encrypted-like shape but is a new seed,
    # file count and size distribution. A useful skip rule should normally preserve bytes here.
    case = root / 'high_entropy_bins_40'
    for i in range(40):
        _write_random(case / f'chunk-{i:03d}.bin', size=192 * 1024 + (i % 5) * 4096, rng=rng)
    for i in range(96):
        _write_random(case / 'tiny' / f'item-{i:03d}.bin', size=160 + (i % 17), rng=rng)
    cases.append((case.name, case, _tree_provenance(case)))

    # Same broad shape but highly repetitive binary content. This is an adversarial counterexample candidate:
    # dictionary training may genuinely affect selected bytes even though file/sample counts look safe.
    case = root / 'compressible_bins_40'
    for i in range(40):
        token = (f'BIN-FAMILY-{i % 4:02d}-COMMON-PREFIX-').encode()
        _write_repeat(case / f'chunk-{i:03d}.bin', size=192 * 1024 + (i % 3) * 2048, token=token)
    cases.append((case.name, case, _tree_provenance(case)))

    # Text sidecars with strong cross-file redundancy. Any rule based only on counts/volume must prove it does not
    # suppress a dictionary that changes the winning r24 representation here.
    case = root / 'shared_text_64'
    common = b'{"tenant":"alpha","event":"telemetry","payload":"' + b'ABCD' * 128 + b'"}\n'
    for i in range(64):
        _write_repeat(case / f'event-{i:03d}.json', size=96 * 1024 + (i % 7) * 1024, token=common + str(i % 5).encode())
    cases.append((case.name, case, _tree_provenance(case)))

    # Shifted-version-like content, but generated independently from the frozen hostile corpus.
    case = root / 'shifted_text_36'
    base = bytearray((b'0123456789abcdef' * (128 * 1024 // 16)))
    for i in range(36):
        data = bytearray(base)
        shift = (i * 7919) % max(1, len(data) - 4096)
        marker = hashlib.sha256(f'variant-{i}'.encode()).digest() * 64
        data[shift : shift + len(marker)] = marker
        (case / f'version-{i:03d}.txt').parent.mkdir(parents=True, exist_ok=True)
        (case / f'version-{i:03d}.txt').write_bytes(bytes(data))
    cases.append((case.name, case, _tree_provenance(case)))

    # Threshold-neighbor cases make sure an apparently good rule is not merely memorizing one frozen sample count.
    for count in (31, 32, 33):
        case = root / f'borderline_bins_{count}'
        for i in range(count):
            _write_random(case / f'part-{i:03d}.bin', size=128 * 1024 + (i % 2) * 4096, rng=rng)
        cases.append((case.name, case, _tree_provenance(case)))

    return cases


def _measure_row(label: str, root: Path, provenance: str, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    features = ADMIT._pretraining_features(root)
    measurement = COST._measure(root, work, provenance)
    return {"label": label, "pretraining_features": features, "measurement": measurement}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    frozen_rows = []
    for label, root, accepted_source_tree in COST._sources(work_root / 'frozen-corpus'):
        frozen_rows.append(
            _measure_row(
                label,
                root,
                accepted_source_tree,
                work_root / 'frozen-rows' / label.replace('/', '__'),
            )
        )

    adversarial_rows = []
    for name, root, provenance in _build_adversarial(work_root / 'adversarial-corpus'):
        row = _measure_row(
            f'adversarial/{name}',
            root,
            provenance,
            work_root / 'adversarial-rows' / name,
        )
        adversarial_rows.append(row)
        print(
            json.dumps(
                {
                    'label': row['label'],
                    'features': row['pretraining_features'],
                    'exact': row['measurement']['exact_archive_bytes_and_sha'],
                    'saved_s': row['measurement']['saved_s'],
                }
            ),
            flush=True,
        )

    combined = frozen_rows + adversarial_rows
    solutions = ADMIT._search(combined)
    frozen_solutions = ADMIT._search(frozen_rows)

    # A surviving rule must admit at least one adversarial case; otherwise it has not generalized beyond the frozen
    # suite. It must also retain at least one material frozen opportunity so the rule remains useful.
    generalized = []
    by_label = {r['label']: r for r in combined}
    for solution in solutions:
        rules = [ADMIT.Rule(str(r['feature']), str(r['op']), float(r['threshold'])) for r in solution['rules']]
        admitted = [r for r in combined if all(rule.matches(r['pretraining_features']) for rule in rules)]
        adv = [r for r in admitted if r['label'].startswith('adversarial/')]
        frozen_material = [
            r for r in admitted
            if not r['label'].startswith('adversarial/') and r['measurement']['material_exact_opportunity']
        ]
        if adv and frozen_material:
            generalized.append(
                {
                    **solution,
                    'adversarial_admissions': [r['label'] for r in adv],
                    'frozen_material_admissions': [r['label'] for r in frozen_material],
                }
            )

    return {
        'schema': 'cmpct-v030-r24-dictionary-skip-adversarial-v1',
        'contract': {
            'production_change': False,
            'release_credit': False,
            'frozen_workloads': 15,
            'adversarial_cases': len(adversarial_rows),
            'policy_inputs': ADMIT.run.__globals__.get('POLICY_INPUTS', [
                'regular_files', 'logical_bytes', 'largest_file_bytes', 'dictionary_sample_count',
                'dictionary_sample_bytes', 'sample_mean_bytes', 'sample_bytes_per_regular',
                'sample_fraction_of_logical',
            ]),
            'forbidden_policy_inputs': ['workload_name', 'benchmark_name', 'path', 'filename', 'content_hash', 'archive_hash'],
            'exact_archive_identity_required_for_every_admission': True,
            'canonical_tree_equality_required_for_every_admission': True,
            'positive_saved_time_required_for_every_admission': True,
            'adversarial_admission_required_for_promotion_signal': True,
            'future_shipping_change_requires_separate_product_regression': True,
        },
        'frozen_rows': frozen_rows,
        'adversarial_rows': adversarial_rows,
        'frozen_solution_count': len(frozen_solutions),
        'combined_solution_count': len(solutions),
        'generalized_solutions': generalized,
        'summary': {
            'frozen_complete': len(frozen_rows) == 15,
            'adversarial_complete': len(adversarial_rows) == 7,
            'adversarial_counterexamples': [
                r['label'] for r in adversarial_rows
                if not r['measurement']['exact_archive_bytes_and_sha']
            ],
            'generalized_solution_count': len(generalized),
            'best_generalized_solution': generalized[0] if generalized else None,
            'promotion_signal': bool(generalized),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--work-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result['summary'], indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
