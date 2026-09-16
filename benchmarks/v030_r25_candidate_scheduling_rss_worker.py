from __future__ import annotations

"""Fresh-process A/B worker for exact r25 candidate scheduling RSS.

Diagnostic only.  ``serialized`` replaces only the private canonical release-candidate module's
ThreadPoolExecutor with an inline submit/result executor.  Candidate builders, admission, selection,
verification and product framing remain untouched.
"""

import argparse, hashlib, json, resource, time
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

class _ImmediateFuture:
    def __init__(self, fn, args, kwargs):
        self._value = fn(*args, **kwargs)
    def result(self): return self._value

class _InlineExecutor:
    submissions = 0
    def __init__(self, *args, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def submit(self, fn, *args, **kwargs):
        type(self).submissions += 1
        return _ImmediateFuture(fn, args, kwargs)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=('concurrent','serialized'), required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    a = p.parse_args()

    from experiments import entropygraph_v030_canonical_final as canonical
    from experiments import entropygraph_v030_release_product as product
    iso = canonical.PROFILE_ISOLATION
    if canonical.RC.PG is not iso.PG or canonical.RC.G04 is not iso.SHARED or canonical.RC.READER is not iso.POLICY:
        raise RuntimeError('canonical semantic-owner identity mismatch')
    eligible, reason = canonical.RC._prefixgraph_eligibility(a.source, canonical.RC.treehash(a.source))
    if not eligible:
        raise RuntimeError(f'preregistered shifted workload unexpectedly PrefixGraph-ineligible: {reason}')

    original_executor = canonical.RC.ThreadPoolExecutor
    if a.mode == 'serialized': canonical.RC.ThreadPoolExecutor = _InlineExecutor
    try:
        baseline = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        t0 = time.perf_counter()
        stats = dict(product.build(a.source, a.archive))
        wall = time.perf_counter() - t0
        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    finally:
        canonical.RC.ThreadPoolExecutor = original_executor

    verify = dict(product.strong_verify(a.archive))
    if not verify.get('ok'):
        raise RuntimeError(f'strong verification failed: {verify!r}')
    print(json.dumps({
        'mode': a.mode, 'archive_bytes': a.archive.stat().st_size, 'archive_sha256': _sha(a.archive),
        'tree_sha256': verify['tree_sha256'], 'selected': stats.get('selected'), 'wall_s': wall,
        'baseline_rss_kib': baseline, 'peak_rss_kib': peak,
        'incremental_peak_rss_kib': max(0, peak-baseline),
        'inline_executor_submissions': _InlineExecutor.submissions if a.mode == 'serialized' else 0,
        'semantic_owners': {'pg': canonical.RC.PG.__name__, 'g04': canonical.RC.G04.__name__, 'reader': canonical.RC.READER.__name__, 'identity_exact': True},
        'build_stats': stats,
    }, separators=(',',':'), default=str))

if __name__ == '__main__': main()
