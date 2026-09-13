from __future__ import annotations

"""Back-to-back determinism referee for the current 15-workload corpus surface.

Mission lock
============
Two exact-head v0.30 current-15 research runs that both call the shared corpus
builder emitted different portfolio fingerprints. Comparisons inside each run
remain same-tree fair, but cross-run evidence must not be called same-input until
this is explained.

Hypothesis: the current corpus generators are byte-stable across immediate
regeneration on one runner. Disproof: any workload differs in files, logical
bytes, or tree_sha256 between build A and build B.

When a workload differs, the referee additionally attributes the drift to exact
relative file paths and records size/hash/first-differing-byte evidence. That
attribution is observational only: this benchmark does not modify or normalize
the generated corpus.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_micropack_current15_transfer as CUR


def _map(rows: list[dict]) -> dict[str, dict]:
    return {f"{r['suite']}/{r['name']}": r for r in rows}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _first_difference(a: Path, b: Path) -> int | None:
    """Return the first byte offset that differs, or None for identical bytes."""
    offset = 0
    with a.open('rb') as fa, b.open('rb') as fb:
        while True:
            ba = fa.read(64 * 1024)
            bb = fb.read(64 * 1024)
            if ba == bb:
                if not ba:
                    return None
                offset += len(ba)
                continue
            common = min(len(ba), len(bb))
            for i in range(common):
                if ba[i] != bb[i]:
                    return offset + i
            return offset + common


def _file_differences(a_root: Path, b_root: Path) -> dict[str, dict]:
    a_files = {p.relative_to(a_root).as_posix(): p for p in a_root.rglob('*') if p.is_file()}
    b_files = {p.relative_to(b_root).as_posix(): p for p in b_root.rglob('*') if p.is_file()}
    out: dict[str, dict] = {}
    for rel in sorted(set(a_files) | set(b_files)):
        if rel not in a_files or rel not in b_files:
            out[rel] = {'missing_a': rel not in a_files, 'missing_b': rel not in b_files}
            continue
        pa, pb = a_files[rel], b_files[rel]
        size_a, size_b = pa.stat().st_size, pb.stat().st_size
        sha_a, sha_b = _sha256(pa), _sha256(pb)
        if size_a == size_b and sha_a == sha_b:
            continue
        out[rel] = {
            'size_a': size_a,
            'size_b': size_b,
            'sha256_a': sha_a,
            'sha256_b': sha_b,
            'first_differing_byte': _first_difference(pa, pb),
        }
    return out


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    p1, first = CUR._build(work_root / 'a')
    p2, second = CUR._build(work_root / 'b')
    a = _map(first); b = _map(second)
    keys = sorted(set(a) | set(b))
    diffs = {}
    file_diffs: dict[str, dict] = {}
    for key in keys:
        if key not in a or key not in b:
            diffs[key] = {'missing_a': key not in a, 'missing_b': key not in b}
            continue
        delta = {}
        for field in ('files','logical_bytes','tree_sha256'):
            if a[key][field] != b[key][field]:
                delta[field] = {'a': a[key][field], 'b': b[key][field]}
        if delta:
            diffs[key] = delta
            if key in p1 and key in p2:
                file_diffs[key] = _file_differences(p1[key], p2[key])
    fp_a = CUR._fingerprint(first)
    fp_b = CUR._fingerprint(second)
    stable = not diffs and fp_a == fp_b
    return {
        'schema':'cmpct-v030-current15-fingerprint-stability-v2',
        'experiment_valid':True,
        'release_credit':False,
        'corpus_mutated':False,
        'workloads_a':len(first),
        'workloads_b':len(second),
        'fingerprint_a':fp_a,
        'fingerprint_b':fp_b,
        'fingerprint_equal':fp_a == fp_b,
        'unstable_workloads':sorted(diffs),
        'differences':diffs,
        'file_differences':file_diffs,
        'verdict':'CURRENT15_FINGERPRINT_STABLE' if stable else 'CURRENT15_FINGERPRINT_SUBSTRATE_UNSTABLE',
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-current15-stability-work')); ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-current15-stability.json')); args=ap.parse_args()
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
