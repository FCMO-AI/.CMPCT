from __future__ import annotations

"""Measure a lossless lazy-inflate boundary for the EG08 Office graph scan.

The historical EntropyGraph inspector eagerly inflates every DEFLATE/STORED member of every ZIP-like top-level
file so it can hash member plaintext and discover exact cross-representation reuse with loose top-level files.
An exact match necessarily has the same uncompressed byte length and CRC32, both already available without inflate:
ZIP carries file_size/CRC in its central directory and top-level bytes are already materialized by the graph engine.

This oracle compares the historical eager member-plaintext scan with a candidate that inflates only members whose
(size, CRC32) pair exists among top-level files, then performs the same SHA-256 equality test. The cheap pair is only
a prefilter; SHA-256 remains the admission proof. It records exact discovered-edge identity plus rotated wall time and
member inflate counts. No production behavior or release authority is changed here.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time
import zipfile
import zlib

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1

ROUNDS = 11
SUPPORTED = (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED)


def _materialize(stage: Path) -> tuple[list[Path], dict[Path, bytes], dict[bytes, list[Path]], set[tuple[int, int]]]:
    files = sorted(p for p in stage.rglob('*') if p.is_file())
    raws = {p: p.read_bytes() for p in files}
    top_by_hash: dict[bytes, list[Path]] = {}
    cheap = set()
    for p, raw in raws.items():
        top_by_hash.setdefault(hashlib.sha256(raw).digest(), []).append(p)
        cheap.add((len(raw), zlib.crc32(raw) & 0xFFFFFFFF))
    return files, raws, top_by_hash, cheap


def _scan(files: list[Path], raws: dict[Path, bytes], top_by_hash: dict[bytes, list[Path]], cheap: set[tuple[int, int]], lazy: bool) -> dict:
    edges = []
    zip_members = 0
    inflates = 0
    inflated_bytes = 0
    for p in files:
        raw = raws[p]
        if not raw.startswith(b'PK\x03\x04') or len(raw) < 4096:
            continue
        try:
            with zipfile.ZipFile(p) as ar:
                infos = sorted((i for i in ar.infolist() if not i.is_dir()), key=lambda x: x.header_offset)
                for zi in infos:
                    if zi.compress_type not in SUPPORTED:
                        continue
                    zip_members += 1
                    if lazy and (int(zi.file_size), int(zi.CRC) & 0xFFFFFFFF) not in cheap:
                        continue
                    plain = ar.read(zi)
                    inflates += 1
                    inflated_bytes += len(plain)
                    ph = hashlib.sha256(plain).digest()
                    for tp in top_by_hash.get(ph, ()):
                        if tp != p:
                            edges.append((p.relative_to(stage).as_posix(), int(zi.header_offset), tp.relative_to(stage).as_posix(), len(plain), ph.hex()))
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
            continue
    return {
        'edges': sorted(edges),
        'zip_members': zip_members,
        'inflates': inflates,
        'inflated_bytes': inflated_bytes,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root / 'frozen')
    stage = V1.EXT._normalized_stage(source, work_root / 'normalized')
    tree_sha = V1.EG07._treehash(stage)
    files, raws, top_by_hash, cheap = _materialize(stage)

    samples = []
    eager_ref = None
    lazy_ref = None
    for i in range(ROUNDS):
        order = (False, True) if i % 2 == 0 else (True, False)
        pair = {}
        for lazy in order:
            started = time.perf_counter()
            result = _scan(files, raws, top_by_hash, cheap, lazy)
            elapsed = time.perf_counter() - started
            label = 'lazy' if lazy else 'eager'
            pair[label] = {'wall_s': float(elapsed), **result}
        eager_ref = eager_ref or pair['eager']
        lazy_ref = lazy_ref or pair['lazy']
        if pair['eager']['edges'] != pair['lazy']['edges']:
            raise RuntimeError('cheap ZIP plaintext prefilter changed exact discovered edges')
        if pair['eager']['zip_members'] != pair['lazy']['zip_members']:
            raise RuntimeError('ZIP member census drifted')
        samples.append({
            'eager_s': pair['eager']['wall_s'],
            'lazy_s': pair['lazy']['wall_s'],
            'eager_inflates': pair['eager']['inflates'],
            'lazy_inflates': pair['lazy']['inflates'],
            'eager_inflated_bytes': pair['eager']['inflated_bytes'],
            'lazy_inflated_bytes': pair['lazy']['inflated_bytes'],
        })

    eager_median = statistics.median(x['eager_s'] for x in samples)
    lazy_median = statistics.median(x['lazy_s'] for x in samples)
    saving = eager_median - lazy_median
    fraction = saving / eager_median if eager_median else 0.0
    inflate_removed = int(eager_ref['inflates']) - int(lazy_ref['inflates'])
    byte_removed = int(eager_ref['inflated_bytes']) - int(lazy_ref['inflated_bytes'])
    return {
        'schema': 'cmpct-v030-eg08-zip-plain-lazy-prefilter-v1',
        'contract': {
            'release_credit': False,
            'production_change': False,
            'benchmark_identity_not_policy_input': True,
            'cheap_prefilter_inputs': ['zip_member_uncompressed_size', 'zip_member_crc32', 'top_level_size', 'top_level_crc32'],
            'exact_admission_proof': 'SHA-256 plaintext equality',
            'rounds': ROUNDS,
            'ties_fail': True,
        },
        'office': {
            'accepted_v029_bytes': int(accepted_v029),
            'normalized_tree_sha256': tree_sha,
            'top_level_files': len(files),
            'zip_supported_members': int(eager_ref['zip_members']),
            'exact_cross_representation_edges': len(eager_ref['edges']),
        },
        'work_removed': {
            'eager_member_inflates': int(eager_ref['inflates']),
            'lazy_member_inflates': int(lazy_ref['inflates']),
            'member_inflates_removed': inflate_removed,
            'member_inflate_fraction_removed': inflate_removed / max(1, int(eager_ref['inflates'])),
            'eager_plaintext_bytes_inflated': int(eager_ref['inflated_bytes']),
            'lazy_plaintext_bytes_inflated': int(lazy_ref['inflated_bytes']),
            'plaintext_bytes_inflate_removed': byte_removed,
        },
        'timing': {
            'samples': samples,
            'eager_median_s': float(eager_median),
            'lazy_median_s': float(lazy_median),
            'median_saving_s': float(saving),
            'relative_speedup': float(fraction),
        },
        'gate': {
            'exact_edge_identity': eager_ref['edges'] == lazy_ref['edges'],
            'member_census_identity': eager_ref['zip_members'] == lazy_ref['zip_members'],
            'removed_real_inflate_work': inflate_removed > 0 and byte_removed > 0,
            'experiment_valid': True,
            'promotion_signal': eager_ref['edges'] == lazy_ref['edges'] and inflate_removed > 0 and lazy_median < eager_median,
            'release_credit': False,
        },
        'claim_boundary': (
            'Research-only causal Office graph-scan evidence. Size+CRC32 is only a no-false-negative prefilter for '
            'possible exact top-level plaintext matches; SHA-256 remains mandatory before an edge is admitted. A '
            'positive result justifies changing eager member plaintext inflation to lazy exact-candidate inflation, '
            'but final C25EG08 byte identity, complete create timing, all-15, native/Android/recovery and strict release '
            'authority remain separate requirements.'
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-eg08-zip-plain-lazy-work'))
    p.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-eg08-zip-plain-lazy.json'))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'office': result['office'], 'work_removed': result['work_removed'], 'timing': result['timing'], 'gate': result['gate']}, indent=2), flush=True)
    if not result['gate']['experiment_valid']:
        raise SystemExit('EG08 lazy ZIP plaintext prefilter oracle invalid')


if __name__ == '__main__':
    main()
