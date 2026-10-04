from __future__ import annotations

"""Dictionary-determinism attribution for the fused pathdict portfolio.

Mission lock
============
v4 restored canonical build order and trained each branch exactly once, yet Tiny
Files retained one 123-byte mismatch in the independent artifact while the path-blind
dictionary artifact remained exact.  Cache misses are zero.  The remaining plausible
causes are now narrow: either the mature extension-hinted Zstd trainer emits different
dictionaries across otherwise equivalent builds, or the shared post-scan graph still
carries semantically relevant state not captured by the clone.

Falsifiable hypothesis
----------------------
If the mature trainer is the source of the mismatch, the clean-independent and
shared-scan-independent Tiny builds will report different dictionary SHA-256 values
(or different trainer sample manifests).  If both dictionary bytes and ordered sample
manifests are identical while the archive still differs, trainer nondeterminism is
falsified and clone/publication state remains the target.

Instrumentation only: no codec, training command, sample policy, threshold, build
order, corpus, locality law, comparator, format, canonical Builder or Genesis score
changes.  The inherited v4 artifact identity gates remain authoritative.
"""

import hashlib
import time

from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import (
    TimedFusedPathBlindDictionaryBuilder,
    TimedRecordingIndependentBuilder,
)


class DictionaryAuditMixin:
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._trainer_sample_manifest_before = None
        self._trainer_dictionary_sha256 = None
        self._trainer_dictionary_bytes = 0

    def _sample_manifest(self):
        # Mirror the mature trainer's sample predicate and preserve cands insertion
        # order.  This is observation only; the inherited trainer still receives the
        # original state and performs the actual training.
        rows = []
        for h, c in self.cands.items():
            if len(c.raw) >= 64 and '.cmpct-pack' not in c.hints and any(
                x in V1.BASE.BUILDER.TEXT_EXT for x in c.hints
            ):
                rows.append((h.hex(), len(c.raw), hashlib.sha256(c.raw).hexdigest()))
        return rows

    def _train_dictionary(self):
        self._trainer_sample_manifest_before = self._sample_manifest()
        out = super()._train_dictionary()
        self._trainer_dictionary_bytes = len(self.dictionary)
        self._trainer_dictionary_sha256 = (
            hashlib.sha256(self.dictionary).hexdigest() if self.dictionary else None
        )
        return out


class AuditedCleanIndependentBuilder(DictionaryAuditMixin, V1.SAME.NoMicroPackBuilder):
    pass


class AuditedRecordingIndependentBuilder(DictionaryAuditMixin, TimedRecordingIndependentBuilder):
    pass


class AuditedFusedPathBlindDictionaryBuilder(DictionaryAuditMixin, TimedFusedPathBlindDictionaryBuilder):
    pass


def _audit(b):
    m = b._trainer_sample_manifest_before or []
    manifest_sha = hashlib.sha256(
        repr(m).encode('utf-8')
    ).hexdigest()
    return {
        'sample_count': len(m),
        'sample_bytes': sum(row[1] for row in m),
        'sample_manifest_sha256': manifest_sha,
        'dictionary_bytes': int(b._trainer_dictionary_bytes),
        'dictionary_sha256': b._trainer_dictionary_sha256,
    }


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)

    clean_ib = V1._new(AuditedCleanIndependentBuilder, source)
    clean_i = V1._build_obj(clean_ib, root / 'clean-independent.cmpct')
    clean_db = V1._new(V1.PathBlindDictionaryBuilder, source)
    clean_d = V1._build_obj(clean_db, root / 'clean-dictionary.cmpct')

    seed = V1._new(V3.ScanSeedBuilder, source)
    c0 = time.process_time(); w0 = time.perf_counter()
    seed.scan()
    scan_cpu = time.process_time() - c0
    scan_wall = time.perf_counter() - w0

    rec = V3._clone_seed(seed, AuditedRecordingIndependentBuilder, source)
    rec_build = V1._build_obj(rec, root / 'fused-independent.cmpct')

    fused = V3._clone_seed(seed, AuditedFusedPathBlindDictionaryBuilder, source)
    fused._fused_normal_encode_cache = rec._normal_encode_cache
    fused_build = V1._build_obj(fused, root / 'fused-dictionary.cmpct')

    fused_cpu = scan_cpu + rec_build['cpu_s'] + fused_build['cpu_s']
    fused_wall = scan_wall + rec_build['wall_s'] + fused_build['wall_s']
    clean_port_cpu = clean_i['cpu_s'] + clean_d['cpu_s']
    clean_port_wall = clean_i['wall_s'] + clean_d['wall_s']

    clean_a = _audit(clean_ib)
    fused_a = _audit(rec)
    identity = {
        'independent_exact': clean_i['sha256'] == rec_build['sha256'] and clean_i['bytes'] == rec_build['bytes'],
        'dictionary_exact': clean_d['sha256'] == fused_build['sha256'] and clean_d['bytes'] == fused_build['bytes'],
        'independent_train_once': rec._dict_train_calls == 1,
        'dictionary_train_once': fused._dict_train_calls == 1,
        'cache_miss_free': fused._fused_misses == 0,
    }
    trainer = {
        'clean_independent': clean_a,
        'shared_independent': fused_a,
        'sample_manifest_exact': clean_a['sample_manifest_sha256'] == fused_a['sample_manifest_sha256'],
        'dictionary_exact': clean_a['dictionary_sha256'] == fused_a['dictionary_sha256'],
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
        'trainer_attribution': trainer,
        'identity': identity, 'identity_pass': all(identity.values()),
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
