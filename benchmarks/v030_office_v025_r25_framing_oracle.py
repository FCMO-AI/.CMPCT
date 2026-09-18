from __future__ import annotations

"""Research-only oracle: does the proven v0.25 Office ZIP-stream value survive r25 filesystem framing?

This is deliberately not a product candidate. It prices the current canonical r25 prepared-tree/control semantics
into the already-proven v0.25 representation family, then compares complete artifacts on the same accepted Office
source tree. The question is narrower than productization: whether filesystem framing itself destroys the large
ZIP-stream headroom before locality/admission/reader work is attempted.
"""

import hashlib
import json
from pathlib import Path
import tempfile

from benchmarks.neutral_hostile_determinism_repair_v6 import build_repair_v6_corpus
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_canonical_final_impl as FINAL


def _tree_sha(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        rel = p.relative_to(root).as_posix().encode()
        data = p.read_bytes()
        h.update(len(rel).to_bytes(4, 'little')); h.update(rel)
        h.update(len(data).to_bytes(8, 'little')); h.update(data)
    return h.hexdigest()


def _verify(archive: Path, expected_root: Path, out: Path) -> dict:
    V25.extract(archive, out)
    expected = {p.relative_to(expected_root).as_posix(): p.read_bytes() for p in expected_root.rglob('*') if p.is_file()}
    actual = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}
    if actual != expected:
        raise RuntimeError('v0.25 r25-framing oracle exact-tree verification failed')
    return {'ok': True, 'files': len(actual), 'tree_sha256': _tree_sha(out)}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix='cmpct-v030-office-v025-r25-framing-') as td:
        work = Path(td)
        corpus = build_repair_v6_corpus(work / 'corpus')
        office = corpus['Office']
        office_sha = _tree_sha(office)
        logical = sum(p.stat().st_size for p in office.rglob('*') if p.is_file())

        control_archive = work / 'control.cmpct'
        control_build = V25.pack(office, control_archive, level=9)
        control_verify = _verify(control_archive, office, work / 'control-out')

        staging = work / 'r25-staging'
        with FINAL._revision25_profile_context():
            prepared = FINAL._prepare_profile_tree(office, staging)
        framed_archive = work / 'r25-framed-v025.cmpct'
        framed_build = V25.pack(staging, framed_archive, level=9)
        framed_verify = _verify(framed_archive, staging, work / 'framed-out')

        selected_manifest = bytes(prepared['selected_manifest_raw'])
        source_manifest = bytes(prepared['source_manifest_raw'])
        framed_delta = framed_archive.stat().st_size - control_archive.stat().st_size
        payload = {
            'schema': 'cmpct-v030-office-v025-r25-framing-oracle-v1',
            'claim_boundary': 'research-only oracle; v0.25 representation on current canonical r25 prepared-tree semantics; no locality/product/release credit',
            'substrate': 'neutral-hostile-determinism-repair-v6',
            'office_tree_sha256': office_sha,
            'files': sum(1 for p in office.rglob('*') if p.is_file()),
            'logical_bytes': logical,
            'control_v025': {
                'archive_bytes': control_archive.stat().st_size,
                'build': control_build,
                'strong_verify': control_verify,
            },
            'r25_prepared_tree': {
                'entries': int(prepared['entries']),
                'selected_manifest_encoding': prepared['selected_manifest_encoding'],
                'filesystem_v1_manifest_bytes': len(source_manifest),
                'selected_manifest_bytes': len(selected_manifest),
                'manifest_control_saving_bytes': int(prepared['manifest_control_saving_bytes']),
                'staged_files': sum(1 for p in staging.rglob('*') if p.is_file()),
                'tree_sha256': _tree_sha(staging),
            },
            'v025_on_r25_prepared_tree': {
                'archive_bytes': framed_archive.stat().st_size,
                'build': framed_build,
                'strong_verify': framed_verify,
            },
            'r25_framing_minus_original_v025_bytes': framed_delta,
            'r25_framing_overhead_pct_of_original_v025': 100.0 * framed_delta / control_archive.stat().st_size,
            'decision': 'R25_FRAMING_PRESERVES_ZIPSTREAM_HEADROOM' if framed_delta < 1_000_000 else 'R25_FRAMING_COST_MATERIAL_REQUIRES_ATTRIBUTION',
            'release_credit': False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
