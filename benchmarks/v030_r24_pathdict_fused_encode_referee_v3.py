from __future__ import annotations

"""Harness-only v3 correction for fused pathdict encode attribution.

v2 proved the encode cache is exercised (8,404 hits, zero misses) and materially
reduced the two-build cost, but failed byte identity on two artifacts.  Root cause:
the shared snapshot was taken after the independent branch's scan had already run
its dictionary trainer and inserted that branch's dictionary candidate into cands.
The pathdict clone therefore inherited branch-specific state that a clean pathdict
build never sees.

v3 freezes the shared graph immediately after filesystem discovery but *before any
dictionary training*.  Each cloned branch then runs its own unchanged trainer once,
followed by the same build path.  No research policy, codec, threshold, corpus,
locality law, hypothesis or output schema changes.
"""

import copy
import time
import types

from cmpct.builder import Candidate
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks.v030_r24_pathdict_fused_encode_referee_v2 import RecordingIndependentBuilder


class ScanSeedBuilder(V1.SAME.NoMicroPackBuilder):
    def _train_dictionary(self):
        # Freeze candidate/filesystem discovery before branch-specific dictionary state.
        return None


def _seed_state(seed):
    return {
        'cands': {h: Candidate(c.raw, set(c.hints), {sh:[slot[0],slot[1]] for sh,slot in c.deflates.items()}) for h,c in seed.cands.items()},
        'files': copy.deepcopy(seed.files),
        'recipes': copy.deepcopy(seed.recipes),
        'dictionary': b'', 'dict_hash': None,
        'canonical_deflate': dict(seed.canonical_deflate),
        'secondary_stream_hashes': set(seed.secondary_stream_hashes),
        'inode_first': dict(seed.inode_first), 'meta_by_rel': copy.deepcopy(seed.meta_by_rel),
    }


def _clone_seed(seed, cls, source):
    b = V1._new(cls, source)
    for k,v in _seed_state(seed).items():
        setattr(b,k,v)
    b.scan = types.MethodType(lambda self: None, b)
    return b


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)
    clean_i = V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder, source), root/'clean-independent.cmpct')
    clean_d = V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder, source), root/'clean-dictionary.cmpct')

    seed = V1._new(ScanSeedBuilder, source)
    c0=time.process_time(); w0=time.perf_counter(); seed.scan(); scan_cpu=time.process_time()-c0; scan_wall=time.perf_counter()-w0

    rec = _clone_seed(seed, RecordingIndependentBuilder, source)
    c0=time.process_time(); w0=time.perf_counter(); rec._train_dictionary(); ind_train_cpu=time.process_time()-c0; ind_train_wall=time.perf_counter()-w0
    rec_build = V1._build_obj(rec, root/'fused-independent.cmpct')

    fused = _clone_seed(seed, V1.FusedPathBlindDictionaryBuilder, source)
    c0=time.process_time(); w0=time.perf_counter(); fused._train_dictionary(); dict_train_cpu=time.process_time()-c0; dict_train_wall=time.perf_counter()-w0
    fused._fused_normal_encode_cache = rec._normal_encode_cache
    fused_build = V1._build_obj(fused, root/'fused-dictionary.cmpct')

    fused_cpu = scan_cpu+ind_train_cpu+rec_build['cpu_s']+dict_train_cpu+fused_build['cpu_s']
    fused_wall = scan_wall+ind_train_wall+rec_build['wall_s']+dict_train_wall+fused_build['wall_s']
    clean_port_cpu=clean_i['cpu_s']+clean_d['cpu_s']; clean_port_wall=clean_i['wall_s']+clean_d['wall_s']
    identity={
        'independent_exact': clean_i['sha256']==rec_build['sha256'] and clean_i['bytes']==rec_build['bytes'],
        'dictionary_exact': clean_d['sha256']==fused_build['sha256'] and clean_d['bytes']==fused_build['bytes'],
    }
    return {
        'clean':{'independent':clean_i,'dictionary':clean_d,'portfolio_cpu_s':clean_port_cpu,'portfolio_wall_s':clean_port_wall},
        'fused':{'scan_cpu_s':scan_cpu,'scan_wall_s':scan_wall,'ind_train_cpu_s':ind_train_cpu,'ind_train_wall_s':ind_train_wall,'dict_train_cpu_s':dict_train_cpu,'dict_train_wall_s':dict_train_wall,'independent':rec_build,'dictionary':fused_build,'portfolio_cpu_s':fused_cpu,'portfolio_wall_s':fused_wall,'cache_hits':fused._fused_hits,'cache_misses':fused._fused_misses,'cache_entries':len(rec._normal_encode_cache)},
        'identity':identity,'identity_pass':all(identity.values()),
        'cpu_ratio_vs_clean_portfolio':fused_cpu/clean_port_cpu if clean_port_cpu else None,
        'wall_ratio_vs_clean_portfolio':fused_wall/clean_port_wall if clean_port_wall else None,
        'cpu_ratio_vs_single_independent':fused_cpu/clean_i['cpu_s'] if clean_i['cpu_s'] else None,
        'wall_ratio_vs_single_independent':fused_wall/clean_i['wall_s'] if clean_i['wall_s'] else None,
        'remaining_cpu_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_cpu},{'median_read_wall_s':clean_i['cpu_s']}),
        'remaining_wall_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_wall},{'median_read_wall_s':clean_i['wall_s']}),
    }


V1.RecordingIndependentBuilder = RecordingIndependentBuilder
V1._one = _one


def main():
    V1.main()


if __name__ == '__main__':
    main()
