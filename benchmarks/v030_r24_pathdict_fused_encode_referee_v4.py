from __future__ import annotations

"""Build-order-preserving v4 correction for fused pathdict encode attribution.

Mission lock
============
v3 removed cross-branch dictionary contamination and recovered exact dictionary
artifacts on all five first-gate workloads, but Tiny Files still produced an
independent artifact 123 bytes smaller than its clean control.  Inspection of the
canonical Builder shows the harness itself inverted the product build order:
v3 explicitly called ``_train_dictionary()`` before ``build()``, while canonical
``build()`` performs micro-pack preparation and Deflate preparation first and then
trains exactly once.  The premature trainer inserted a stale dictionary Candidate
into Tiny Files before the branch's normal build path ran.

Falsifiable hypothesis
----------------------
If the remaining identity failure is solely harness-order contamination, cloning the
post-scan graph and letting each branch execute its unchanged ``build()`` pipeline
exactly once must make both independent and path-blind dictionary artifacts
byte-identical to their clean controls on all five first-gate workloads.  The
existing normal-encode cache must still record hits with zero misses.  Disproof is
any SHA/byte mismatch, cache miss, or changed contender semantics.

This correction changes no codec, threshold, candidate policy, locality law,
comparator, corpus, format, canonical Builder, Genesis score, or release status.
Dictionary-training timers are observational only and are charged inside each
branch's normal build time rather than added a second time.
"""

import time

from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v2 import RecordingIndependentBuilder


class TimedRecordingIndependentBuilder(RecordingIndependentBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._dict_train_cpu_s = 0.0
        self._dict_train_wall_s = 0.0
        self._dict_train_calls = 0

    def _train_dictionary(self):
        c0 = time.process_time(); w0 = time.perf_counter()
        try:
            return super()._train_dictionary()
        finally:
            self._dict_train_cpu_s += time.process_time() - c0
            self._dict_train_wall_s += time.perf_counter() - w0
            self._dict_train_calls += 1


class TimedFusedPathBlindDictionaryBuilder(V1.FusedPathBlindDictionaryBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._dict_train_cpu_s = 0.0
        self._dict_train_wall_s = 0.0
        self._dict_train_calls = 0

    def _train_dictionary(self):
        c0 = time.process_time(); w0 = time.perf_counter()
        try:
            return super()._train_dictionary()
        finally:
            self._dict_train_cpu_s += time.process_time() - c0
            self._dict_train_wall_s += time.perf_counter() - w0
            self._dict_train_calls += 1


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)

    # Clean, independently scanned controls remain the byte authorities.
    clean_i = V1._build_obj(
        V1._new(V1.SAME.NoMicroPackBuilder, source),
        root / 'clean-independent.cmpct',
    )
    clean_d = V1._build_obj(
        V1._new(V1.PathBlindDictionaryBuilder, source),
        root / 'clean-dictionary.cmpct',
    )

    # Share only filesystem/candidate discovery.  No dictionary state or physical
    # preparation is allowed to cross the branch boundary.
    seed = V1._new(V3.ScanSeedBuilder, source)
    c0 = time.process_time(); w0 = time.perf_counter()
    seed.scan()
    scan_cpu = time.process_time() - c0
    scan_wall = time.perf_counter() - w0

    # Each branch now executes canonical build order exactly once.  build() sees a
    # no-op scan, then performs micro-pack/Deflate preparation, dictionary training,
    # candidate encoding and publication in the inherited order.
    rec = V3._clone_seed(seed, TimedRecordingIndependentBuilder, source)
    rec_build = V1._build_obj(rec, root / 'fused-independent.cmpct')

    fused = V3._clone_seed(seed, TimedFusedPathBlindDictionaryBuilder, source)
    fused._fused_normal_encode_cache = rec._normal_encode_cache
    fused_build = V1._build_obj(fused, root / 'fused-dictionary.cmpct')

    fused_cpu = scan_cpu + rec_build['cpu_s'] + fused_build['cpu_s']
    fused_wall = scan_wall + rec_build['wall_s'] + fused_build['wall_s']
    clean_port_cpu = clean_i['cpu_s'] + clean_d['cpu_s']
    clean_port_wall = clean_i['wall_s'] + clean_d['wall_s']

    identity = {
        'independent_exact': (
            clean_i['sha256'] == rec_build['sha256']
            and clean_i['bytes'] == rec_build['bytes']
        ),
        'dictionary_exact': (
            clean_d['sha256'] == fused_build['sha256']
            and clean_d['bytes'] == fused_build['bytes']
        ),
        'independent_train_once': rec._dict_train_calls == 1,
        'dictionary_train_once': fused._dict_train_calls == 1,
        'cache_miss_free': fused._fused_misses == 0,
    }

    return {
        'clean': {
            'independent': clean_i,
            'dictionary': clean_d,
            'portfolio_cpu_s': clean_port_cpu,
            'portfolio_wall_s': clean_port_wall,
        },
        'fused': {
            'scan_cpu_s': scan_cpu,
            'scan_wall_s': scan_wall,
            'ind_train_cpu_s': rec._dict_train_cpu_s,
            'ind_train_wall_s': rec._dict_train_wall_s,
            'ind_train_calls': rec._dict_train_calls,
            'dict_train_cpu_s': fused._dict_train_cpu_s,
            'dict_train_wall_s': fused._dict_train_wall_s,
            'dict_train_calls': fused._dict_train_calls,
            'independent': rec_build,
            'dictionary': fused_build,
            'portfolio_cpu_s': fused_cpu,
            'portfolio_wall_s': fused_wall,
            'cache_hits': fused._fused_hits,
            'cache_misses': fused._fused_misses,
            'cache_entries': len(rec._normal_encode_cache),
        },
        'identity': identity,
        'identity_pass': all(identity.values()),
        'cpu_ratio_vs_clean_portfolio': (
            fused_cpu / clean_port_cpu if clean_port_cpu else None
        ),
        'wall_ratio_vs_clean_portfolio': (
            fused_wall / clean_port_wall if clean_port_wall else None
        ),
        'cpu_ratio_vs_single_independent': (
            fused_cpu / clean_i['cpu_s'] if clean_i['cpu_s'] else None
        ),
        'wall_ratio_vs_single_independent': (
            fused_wall / clean_i['wall_s'] if clean_i['wall_s'] else None
        ),
        'remaining_cpu_debt': V1.SEL._confirmed_regression(
            {'median_read_wall_s': fused_cpu},
            {'median_read_wall_s': clean_i['cpu_s']},
        ),
        'remaining_wall_debt': V1.SEL._confirmed_regression(
            {'median_read_wall_s': fused_wall},
            {'median_read_wall_s': clean_i['wall_s']},
        ),
    }


# Reuse the frozen v1 aggregation/verdict schema so only the harness-order bug moves.
V1._one = _one


def main():
    V1.main()


if __name__ == '__main__':
    main()
