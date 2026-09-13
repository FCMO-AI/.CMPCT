from __future__ import annotations

"""Back-to-back determinism referee for the current 15-workload corpus surface.

Mission lock
============
Two exact-head v0.30 current-15 research runs that both call the shared corpus
builder emitted different portfolio fingerprints.  Comparisons inside each run
remain same-tree fair, but cross-run evidence must not be called same-input until
this is explained.

Hypothesis: the current corpus generators are byte-stable across immediate
regeneration on one runner.  Disproof: any workload differs in files, logical
bytes, or tree_sha256 between build A and build B.  This benchmark does not
modify or normalize the corpus; it only identifies the unstable producer.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_r24_micropack_current15_transfer as CUR


def _map(rows: list[dict]) -> dict[str, dict]:
    return {f"{r['suite']}/{r['name']}": r for r in rows}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    _p1, first = CUR._build(work_root / 'a')
    _p2, second = CUR._build(work_root / 'b')
    a = _map(first); b = _map(second)
    keys = sorted(set(a) | set(b))
    diffs = {}
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
    fp_a = CUR._fingerprint(first)
    fp_b = CUR._fingerprint(second)
    stable = not diffs and fp_a == fp_b
    return {
        'schema':'cmpct-v030-current15-fingerprint-stability-v1',
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
        'verdict':'CURRENT15_FINGERPRINT_STABLE' if stable else 'CURRENT15_FINGERPRINT_SUBSTRATE_UNSTABLE',
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-current15-stability-work')); ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-current15-stability.json')); args=ap.parse_args()
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
