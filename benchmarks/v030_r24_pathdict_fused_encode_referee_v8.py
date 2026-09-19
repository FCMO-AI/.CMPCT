from __future__ import annotations

"""Reusable-Zstd-context Builder for the exact fused pathdict portfolio.

Mission lock
============
v6 restored exact portfolio identity and v7 attributed the residual second-branch
cost: across the five frozen first-gate workloads, dictionary candidate encoding
consumes ~6.53 s CPU versus ~0.45 s dictionary training and ~0.13 s residual work.
The mature ``zcd()`` helper creates and frees a ZSTD_CCtx for every dictionary
candidate. Tiny Files alone executes roughly five thousand dictionary-branch
candidate calls.

Falsifiable hypothesis
----------------------
Reusing one ZSTD_CCtx for the lifetime of the path-blind dictionary branch, while
continuing to call the same ``ZSTD_compress_usingDict`` function with the same raw
bytes, dictionary bytes and level, will materially reduce dictionary-encode CPU/wall
without changing any compressed payload or final archive byte.  Disproof is any
artifact SHA mismatch, cache miss, correctness change, or no meaningful encode-time
reduction.

This is research-only and changes no format, selector, dictionary, training sample,
compression level, locality rule, comparator, corpus, canonical Builder, Genesis
score, or release state.  It deliberately does *not* skip auditions.
"""

import ctypes
import msgpack
import time

from cmpct import codec as C
from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import TimedFusedPathBlindDictionaryBuilder


class ReusedCCtxFusedPathBlindDictionaryBuilder(TimedFusedPathBlindDictionaryBuilder):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._reuse_cctx = None
        self._reuse_cctx_calls = 0
        self._dict_encode_cpu_s = 0.0
        self._dict_encode_wall_s = 0.0

    def _zcd_reused(self, data: bytes, dictionary: bytes, level: int) -> bytes:
        if not data:
            return b''
        if self._reuse_cctx is None:
            self._reuse_cctx = C._z.ZSTD_createCCtx()
            if not self._reuse_cctx:
                raise MemoryError('ZSTD_createCCtx failed')
        src = ctypes.create_string_buffer(data)
        db = ctypes.create_string_buffer(dictionary)
        cap = int(C._z.ZSTD_compressBound(len(data)))
        dst = ctypes.create_string_buffer(cap)
        c0 = time.process_time(); w0 = time.perf_counter()
        n = C._zck(C._z.ZSTD_compress_usingDict(
            self._reuse_cctx, dst, cap, src, len(data), db, len(dictionary), level
        ))
        self._dict_encode_cpu_s += time.process_time() - c0
        self._dict_encode_wall_s += time.perf_counter() - w0
        self._reuse_cctx_calls += 1
        return dst.raw[:n]

    def _encode_candidate(self, h, c):
        # Preserve the inherited dictionary-blob fast path before consulting the
        # independent cache: the path-blind dictionary blob does not exist there.
        if self.dict_hash is not None and h == self.dict_hash:
            return CODEC_RAW, c.raw, b''
        cached = self._fused_normal_encode_cache.get(h)
        if cached is None:
            self._fused_misses += 1
            dictionary = self.dictionary
            self.dictionary = b''
            try:
                cached = super(TimedFusedPathBlindDictionaryBuilder, self)._encode_candidate(h, c)
            finally:
                self.dictionary = dictionary
        else:
            self._fused_hits += 1
        if h in self.secondary_stream_hashes or h in self.canonical_deflate:
            return cached
        codec, comp, meta = cached
        dictionary = self.dictionary
        if dictionary and h in getattr(self, '_pathblind_dict_hashes', set()):
            dc = self._zcd_reused(c.raw, dictionary, 12)
            dm = msgpack.packb([12], use_bin_type=True)
            if len(dc) + len(dm) < len(comp) + len(meta):
                return CODEC_ZSTDDICT, dc, dm
        return codec, comp, meta

    def close_reused_context(self):
        if self._reuse_cctx is not None:
            C._z.ZSTD_freeCCtx(self._reuse_cctx)
            self._reuse_cctx = None


def _build_reused(builder, out):
    try:
        return V1._build_obj(builder, out)
    finally:
        builder.close_reused_context()


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)
    clean_i = V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder, source), root/'clean-independent.cmpct')
    clean_d = V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder, source), root/'clean-dictionary.cmpct')

    seed = V1._new(V3.ScanSeedBuilder, source)
    c0=time.process_time(); w0=time.perf_counter(); seed.scan()
    scan_cpu=time.process_time()-c0; scan_wall=time.perf_counter()-w0

    rec = V3._clone_seed(seed, CanonicalRecordingIndependentBuilder, source)
    rec_build = V1._build_obj(rec, root/'fused-independent.cmpct')

    fused = V3._clone_seed(seed, ReusedCCtxFusedPathBlindDictionaryBuilder, source)
    fused._fused_normal_encode_cache = rec._normal_encode_cache
    fused_build = _build_reused(fused, root/'fused-dictionary.cmpct')

    fused_cpu=scan_cpu+rec_build['cpu_s']+fused_build['cpu_s']
    fused_wall=scan_wall+rec_build['wall_s']+fused_build['wall_s']
    clean_port_cpu=clean_i['cpu_s']+clean_d['cpu_s']; clean_port_wall=clean_i['wall_s']+clean_d['wall_s']
    identity={
        'independent_exact': clean_i['sha256']==rec_build['sha256'] and clean_i['bytes']==rec_build['bytes'],
        'dictionary_exact': clean_d['sha256']==fused_build['sha256'] and clean_d['bytes']==fused_build['bytes'],
        'independent_train_once': rec._dict_train_calls==1,
        'dictionary_train_once': fused._dict_train_calls==1,
        'cache_miss_free': fused._fused_misses==0,
    }
    return {
        'clean':{'independent':clean_i,'dictionary':clean_d,'portfolio_cpu_s':clean_port_cpu,'portfolio_wall_s':clean_port_wall},
        'fused':{
            'scan_cpu_s':scan_cpu,'scan_wall_s':scan_wall,
            'ind_train_cpu_s':rec._dict_train_cpu_s,'ind_train_wall_s':rec._dict_train_wall_s,'ind_train_calls':rec._dict_train_calls,
            'dict_train_cpu_s':fused._dict_train_cpu_s,'dict_train_wall_s':fused._dict_train_wall_s,'dict_train_calls':fused._dict_train_calls,
            'independent':rec_build,'dictionary':fused_build,'portfolio_cpu_s':fused_cpu,'portfolio_wall_s':fused_wall,
            'cache_hits':fused._fused_hits,'cache_misses':fused._fused_misses,'cache_entries':len(rec._normal_encode_cache),
            'reused_cctx_calls':fused._reuse_cctx_calls,
            'dictionary_native_encode_cpu_s':fused._dict_encode_cpu_s,
            'dictionary_native_encode_wall_s':fused._dict_encode_wall_s,
        },
        'identity':identity,'identity_pass':all(identity.values()),
        'cpu_ratio_vs_clean_portfolio':fused_cpu/clean_port_cpu if clean_port_cpu else None,
        'wall_ratio_vs_clean_portfolio':fused_wall/clean_port_wall if clean_port_wall else None,
        'cpu_ratio_vs_single_independent':fused_cpu/clean_i['cpu_s'] if clean_i['cpu_s'] else None,
        'wall_ratio_vs_single_independent':fused_wall/clean_i['wall_s'] if clean_i['wall_s'] else None,
        'remaining_cpu_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_cpu},{'median_read_wall_s':clean_i['cpu_s']}),
        'remaining_wall_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_wall},{'median_read_wall_s':clean_i['wall_s']}),
    }


V1._one=_one


def main():
    V1.main()


if __name__=='__main__':
    main()
