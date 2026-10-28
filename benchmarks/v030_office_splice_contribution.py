from __future__ import annotations

"""Exact-byte contribution oracle for the historical Office sub-file splice search.

The exact Office graph profile attributes ~30 ms of self time to 45 ``bytes.find`` calls in EntropyGraph's generic
whole-object sub-file search. Before designing a faster matcher, establish whether that work contributes any actual
Office graph edge at all. This oracle runs the normal RAM-backed raw-final EG07 builder and a second semantically
identical capture that retains ``entropygraph_v025.build()``'s own returned statistics. The two finalized EG07 blobs
must be byte-identical.

Diagnostic only. A zero-splice result proves this exact Office execution spent the search cost without selecting an
edge; it does not by itself authorize workload-specific disabling. Any terminal/preflight must remain content-derived
and prove its own exact-byte/generalization boundary before product promotion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DIRECT
from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as EG07_EFFORT
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from benchmarks import v030_federated_compact_framing_v8_policy_distill as OFFICE
from experiments import entropygraph_v025 as V25


def _capture_with_stats(stage: Path, root: Path) -> tuple[bytes, float, dict]:
    root.mkdir(parents=True, exist_ok=True)
    shm = Path('/dev/shm')
    if not shm.is_dir():
        raise RuntimeError('Office splice evidence requires Linux /dev/shm')
    profile, _ = EG07_EFFORT._prepare(stage, root / 'profile-stage')
    original_zc = V25.zc

    def raw_final(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            return original_zc(raw, min(requested, 1))
        return raw

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='cmpct-eg08-splice-', dir=shm) as td:
        archive = Path(td) / 'semantic-stage.c25eg07'
        with V4.BASE._eg07_effort_bindings():
            with EFFORT._engine(archive, profile, raw_final):
                stats = dict(V25.build())
        if not archive.is_file():
            raise RuntimeError('Office splice diagnostic captured no EG07 archive')
        blob = archive.read_bytes()
    return blob, time.perf_counter() - started, stats


def _eligible_pair_count(stage: Path) -> int:
    files = [p for p in stage.rglob('*') if p.is_file() and p.stat().st_size >= 32 * 1024]
    sizes = [p.stat().st_size for p in files]
    return sum(1 for i, parent in enumerate(sizes) for j, child in enumerate(sizes) if i != j and child < parent)


def run(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    source, _accepted_v029 = OFFICE._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-office-splice-', dir=work_root) as td:
        root = Path(td)
        stage = OFFICE.EXT._normalized_stage(source, root / 'normalized')
        baseline, baseline_s = DIRECT._tmpfs_capture_raw_final_eg07(stage, root / 'baseline')
        observed, observed_s, stats = _capture_with_stats(stage, root / 'observed')
        pair_count = _eligible_pair_count(stage)

    if baseline != observed:
        raise RuntimeError('capturing historical build statistics changed raw-final EG07 bytes')
    return {
        'schema': 'cmpct-v030-office-splice-contribution-v1',
        'archive_bytes': len(baseline),
        'archive_sha256': hashlib.sha256(baseline).hexdigest(),
        'exact_raw_final_identity': True,
        'baseline_wall_s': baseline_s,
        'observed_wall_s': observed_s,
        'eligible_subfile_pair_count': pair_count,
        'historical_build_stats': stats,
        'selected_splice_edges': int(stats.get('splices', -1)),
        'contract': {
            'frozen_office_source': True,
            'raw_final_eg07_byte_identity_required': True,
            'historical_engine_changed': False,
            'release_credit': False,
        },
        'release_credit': False,
        'claim_boundary': (
            'Diagnostic-only contribution evidence. Zero selected splice edges can justify researching a generic '
            'content-derived impossibility/preflight rule, but cannot justify Office-specific or path/hash dispatch.'
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-office-splice-work'))
    parser.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-office-splice.json'))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + '\n', encoding='utf-8')
    print(json.dumps({
        'archive_bytes': result['archive_bytes'],
        'eligible_subfile_pair_count': result['eligible_subfile_pair_count'],
        'selected_splice_edges': result['selected_splice_edges'],
        'historical_build_stats': result['historical_build_stats'],
    }, indent=2, default=str), flush=True)
    if not result['exact_raw_final_identity']:
        raise SystemExit('Office splice contribution evidence lost raw-final identity')


if __name__ == '__main__':
    main()
