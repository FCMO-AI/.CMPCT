from __future__ import annotations

"""Phase attribution after exact fused pathdict rehabilitation.

Mission lock
============
v6 restored exact product semantics: both portfolio artifacts are byte-identical to
clean controls on all five first-gate workloads, with 8,402 normal-encode cache hits
and zero misses.  Yet the exact fused portfolio still costs ~2.2x one independent
build.  Before changing any mechanism, measure where the residual time lives.

Falsifiable hypothesis
----------------------
The residual debt is expected to be concentrated in the second branch's candidate
encode loop (now primarily dictionary auditions) and/or duplicate publication, not
filesystem scan.  Instrument candidate-encode and dictionary-training CPU/wall time
without changing execution order or decisions.  Residual build time is derived as
branch build minus training minus candidate encoding.  If encode is not dominant,
future work must target the measured residual instead of adding more encode caches.

Instrumentation only.  No codec, selector, threshold, corpus, locality, format,
canonical Builder, comparator, Genesis score, or release state changes.  Exact v6
artifact identity remains a hard validity gate.
"""

import time

from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import (
    TimedFusedPathBlindDictionaryBuilder,
)
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import (
    CanonicalRecordingIndependentBuilder,
)


class PhaseRecordingIndependentBuilder(CanonicalRecordingIndependentBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._encode_cpu_s = 0.0
        self._encode_wall_s = 0.0
        self._encode_calls = 0

    def _encode_candidate(self, h, c):
        c0 = time.process_time(); w0 = time.perf_counter()
        try:
            return super()._encode_candidate(h, c)
        finally:
            self._encode_cpu_s += time.process_time() - c0
            self._encode_wall_s += time.perf_counter() - w0
            self._encode_calls += 1


class PhaseFusedPathBlindDictionaryBuilder(TimedFusedPathBlindDictionaryBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._encode_cpu_s = 0.0
        self._encode_wall_s = 0.0
        self._encode_calls = 0

    def _encode_candidate(self, h, c):
        c0 = time.process_time(); w0 = time.perf_counter()
        try:
            return super()._encode_candidate(h, c)
        finally:
            self._encode_cpu_s += time.process_time() - c0
            self._encode_wall_s += time.perf_counter() - w0
            self._encode_calls += 1


def _branch_phase(build, b, prefix):
    train_cpu = float(getattr(b, '_dict_train_cpu_s', 0.0))
    train_wall = float(getattr(b, '_dict_train_wall_s', 0.0))
    enc_cpu = float(getattr(b, '_encode_cpu_s', 0.0))
    enc_wall = float(getattr(b, '_encode_wall_s', 0.0))
    # Training is invoked outside _encode_candidate, so these are disjoint timers.
    residual_cpu = max(0.0, build['cpu_s'] - train_cpu - enc_cpu)
    residual_wall = max(0.0, build['wall_s'] - train_wall - enc_wall)
    return {
        f'{prefix}_build_cpu_s': build['cpu_s'],
        f'{prefix}_build_wall_s': build['wall_s'],
        f'{prefix}_train_cpu_s': train_cpu,
        f'{prefix}_train_wall_s': train_wall,
        f'{prefix}_encode_cpu_s': enc_cpu,
        f'{prefix}_encode_wall_s': enc_wall,
        f'{prefix}_encode_calls': int(getattr(b, '_encode_calls', 0)),
        f'{prefix}_residual_cpu_s': residual_cpu,
        f'{prefix}_residual_wall_s': residual_wall,
    }


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)

    clean_i = V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder, source), root / 'clean-independent.cmpct')
    clean_d = V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder, source), root / 'clean-dictionary.cmpct')

    seed = V1._new(V3.ScanSeedBuilder, source)
    c0 = time.process_time(); w0 = time.perf_counter()
    seed.scan()
    scan_cpu = time.process_time() - c0
    scan_wall = time.perf_counter() - w0

    rec = V3._clone_seed(seed, PhaseRecordingIndependentBuilder, source)
    rec_build = V1._build_obj(rec, root / 'fused-independent.cmpct')

    fused = V3._clone_seed(seed, PhaseFusedPathBlindDictionaryBuilder, source)
    fused._fused_normal_encode_cache = rec._normal_encode_cache
    fused_build = V1._build_obj(fused, root / 'fused-dictionary.cmpct')

    fused_cpu = scan_cpu + rec_build['cpu_s'] + fused_build['cpu_s']
    fused_wall = scan_wall + rec_build['wall_s'] + fused_build['wall_s']
    clean_port_cpu = clean_i['cpu_s'] + clean_d['cpu_s']
    clean_port_wall = clean_i['wall_s'] + clean_d['wall_s']

    identity = {
        'independent_exact': clean_i['sha256'] == rec_build['sha256'] and clean_i['bytes'] == rec_build['bytes'],
        'dictionary_exact': clean_d['sha256'] == fused_build['sha256'] and clean_d['bytes'] == fused_build['bytes'],
        'independent_train_once': rec._dict_train_calls == 1,
        'dictionary_train_once': fused._dict_train_calls == 1,
        'cache_miss_free': fused._fused_misses == 0,
    }
    phases = {
        'scan_cpu_s': scan_cpu,
        'scan_wall_s': scan_wall,
        **_branch_phase(rec_build, rec, 'independent'),
        **_branch_phase(fused_build, fused, 'dictionary'),
    }

    return {
        'clean': {'independent': clean_i, 'dictionary': clean_d, 'portfolio_cpu_s': clean_port_cpu, 'portfolio_wall_s': clean_port_wall},
        'fused': {
            'scan_cpu_s': scan_cpu, 'scan_wall_s': scan_wall,
            'ind_train_cpu_s': rec._dict_train_cpu_s, 'ind_train_wall_s': rec._dict_train_wall_s,
            'ind_train_calls': rec._dict_train_calls,
            'dict_train_cpu_s': fused._dict_train_cpu_s, 'dict_train_wall_s': fused._dict_train_wall_s,
            'dict_train_calls': fused._dict_train_calls,
            'independent': rec_build, 'dictionary': fused_build,
            'portfolio_cpu_s': fused_cpu, 'portfolio_wall_s': fused_wall,
            'cache_hits': fused._fused_hits, 'cache_misses': fused._fused_misses,
            'cache_entries': len(rec._normal_encode_cache),
        },
        'phase_attribution': phases,
        'identity': identity,
        'identity_pass': all(identity.values()),
        'cpu_ratio_vs_clean_portfolio': fused_cpu / clean_port_cpu if clean_port_cpu else None,
        'wall_ratio_vs_clean_portfolio': fused_wall / clean_port_wall if clean_port_wall else None,
        'cpu_ratio_vs_single_independent': fused_cpu / clean_i['cpu_s'] if clean_i['cpu_s'] else None,
        'wall_ratio_vs_single_independent': fused_wall / clean_i['wall_s'] if clean_i['wall_s'] else None,
        'remaining_cpu_debt': V1.SEL._confirmed_regression({'median_read_wall_s': fused_cpu}, {'median_read_wall_s': clean_i['cpu_s']}),
        'remaining_wall_debt': V1.SEL._confirmed_regression({'median_read_wall_s': fused_wall}, {'median_read_wall_s': clean_i['wall_s']}),
    }


V1._one = _one


def main():
    V1.main()


if __name__ == '__main__':
    main()
