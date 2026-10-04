from __future__ import annotations

"""Precompiled-Zstd-dictionary Builder for exact pathdict auditions.

Mission lock
============
v7 attributed the exact fused portfolio's residual cost to dictionary candidate
encoding. v8 proved that reusing a ZSTD_CCtx is byte-exact but only modestly useful.
The remaining hot path still calls ``ZSTD_compress_usingDict`` thousands of times;
that API digests the raw dictionary for each compression. Zstd exposes CDict as the
compiled reusable form of a dictionary.

Falsifiable hypothesis
----------------------
Compile the unchanged 16 KiB dictionary once at level 12, reuse one CCtx, and execute
every existing dictionary audition through ``ZSTD_compress_usingCDict``. If the
compiled-dictionary setup is semantically equivalent for this product path, every
final archive must remain byte-identical to the clean path-blind dictionary control.
It earns mechanism credit only if candidate/portfolio CPU or wall falls materially.
Any SHA mismatch retires it regardless of speed.

Research-only: no dictionary bytes, samples, compression level, selector, threshold,
corpus, locality law, format, canonical Builder, comparator, Genesis score or release
state changes. No audition is skipped.
"""

import ctypes
import hashlib
import msgpack
import time

from cmpct import codec as C
from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import TimedFusedPathBlindDictionaryBuilder


_create_cdict = C._z.ZSTD_createCDict
_create_cdict.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
_create_cdict.restype = ctypes.c_void_p
_free_cdict = C._z.ZSTD_freeCDict
_free_cdict.argtypes = [ctypes.c_void_p]
_free_cdict.restype = ctypes.c_size_t
_compress_cdict = C._z.ZSTD_compress_usingCDict
_compress_cdict.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
_compress_cdict.restype = ctypes.c_size_t


class CompiledDictFusedBuilder(TimedFusedPathBlindDictionaryBuilder):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self._cctx=None; self._cdict=None; self._compiled_for=None
        self._cdict_calls=0; self._cdict_cpu_s=0.0; self._cdict_wall_s=0.0
        self._cdict_compile_cpu_s=0.0; self._cdict_compile_wall_s=0.0

    def _ensure_native_state(self, dictionary:bytes):
        key=(len(dictionary), hashlib.sha256(dictionary).digest())
        if self._compiled_for==key and self._cctx and self._cdict:
            return
        self.close_native_state()
        c0=time.process_time(); w0=time.perf_counter()
        db=ctypes.create_string_buffer(dictionary)
        self._cdict=_create_cdict(db,len(dictionary),12)
        self._cctx=C._z.ZSTD_createCCtx()
        self._cdict_compile_cpu_s += time.process_time()-c0
        self._cdict_compile_wall_s += time.perf_counter()-w0
        if not self._cdict or not self._cctx:
            self.close_native_state(); raise MemoryError('Zstd CDict/CCtx allocation failed')
        self._compiled_for=key

    def _zcd_compiled(self,data:bytes,dictionary:bytes)->bytes:
        if not data:return b''
        self._ensure_native_state(dictionary)
        src=ctypes.create_string_buffer(data); cap=int(C._z.ZSTD_compressBound(len(data))); dst=ctypes.create_string_buffer(cap)
        c0=time.process_time(); w0=time.perf_counter()
        n=C._zck(_compress_cdict(self._cctx,dst,cap,src,len(data),self._cdict))
        self._cdict_cpu_s += time.process_time()-c0; self._cdict_wall_s += time.perf_counter()-w0; self._cdict_calls += 1
        return dst.raw[:n]

    def _encode_candidate(self,h,c):
        if self.dict_hash is not None and h==self.dict_hash:return CODEC_RAW,c.raw,b''
        cached=self._fused_normal_encode_cache.get(h)
        if cached is None:
            self._fused_misses+=1; dictionary=self.dictionary; self.dictionary=b''
            try: cached=super(TimedFusedPathBlindDictionaryBuilder,self)._encode_candidate(h,c)
            finally:self.dictionary=dictionary
        else:self._fused_hits+=1
        if h in self.secondary_stream_hashes or h in self.canonical_deflate:return cached
        codec,comp,meta=cached; dictionary=self.dictionary
        if dictionary and h in getattr(self,'_pathblind_dict_hashes',set()):
            dc=self._zcd_compiled(c.raw,dictionary); dm=msgpack.packb([12],use_bin_type=True)
            if len(dc)+len(dm)<len(comp)+len(meta):return CODEC_ZSTDDICT,dc,dm
        return codec,comp,meta

    def close_native_state(self):
        if self._cctx:
            C._z.ZSTD_freeCCtx(self._cctx); self._cctx=None
        if self._cdict:
            _free_cdict(self._cdict); self._cdict=None
        self._compiled_for=None


def _build(builder,out):
    try:return V1._build_obj(builder,out)
    finally:builder.close_native_state()


def _one(source,root):
    root.mkdir(parents=True,exist_ok=True)
    clean_i=V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct')
    clean_d=V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct')
    seed=V1._new(V3.ScanSeedBuilder,source);c0=time.process_time();w0=time.perf_counter();seed.scan();scan_cpu=time.process_time()-c0;scan_wall=time.perf_counter()-w0
    rec=V3._clone_seed(seed,CanonicalRecordingIndependentBuilder,source);rec_build=V1._build_obj(rec,root/'fused-independent.cmpct')
    fused=V3._clone_seed(seed,CompiledDictFusedBuilder,source);fused._fused_normal_encode_cache=rec._normal_encode_cache;fused_build=_build(fused,root/'fused-dictionary.cmpct')
    fused_cpu=scan_cpu+rec_build['cpu_s']+fused_build['cpu_s'];fused_wall=scan_wall+rec_build['wall_s']+fused_build['wall_s'];clean_cpu=clean_i['cpu_s']+clean_d['cpu_s'];clean_wall=clean_i['wall_s']+clean_d['wall_s']
    identity={'independent_exact':clean_i['sha256']==rec_build['sha256'] and clean_i['bytes']==rec_build['bytes'],'dictionary_exact':clean_d['sha256']==fused_build['sha256'] and clean_d['bytes']==fused_build['bytes'],'independent_train_once':rec._dict_train_calls==1,'dictionary_train_once':fused._dict_train_calls==1,'cache_miss_free':fused._fused_misses==0}
    return {'clean':{'independent':clean_i,'dictionary':clean_d,'portfolio_cpu_s':clean_cpu,'portfolio_wall_s':clean_wall},'fused':{'scan_cpu_s':scan_cpu,'scan_wall_s':scan_wall,'ind_train_cpu_s':rec._dict_train_cpu_s,'ind_train_wall_s':rec._dict_train_wall_s,'ind_train_calls':rec._dict_train_calls,'dict_train_cpu_s':fused._dict_train_cpu_s,'dict_train_wall_s':fused._dict_train_wall_s,'dict_train_calls':fused._dict_train_calls,'independent':rec_build,'dictionary':fused_build,'portfolio_cpu_s':fused_cpu,'portfolio_wall_s':fused_wall,'cache_hits':fused._fused_hits,'cache_misses':fused._fused_misses,'cache_entries':len(rec._normal_encode_cache),'cdict_calls':fused._cdict_calls,'cdict_encode_cpu_s':fused._cdict_cpu_s,'cdict_encode_wall_s':fused._cdict_wall_s,'cdict_compile_cpu_s':fused._cdict_compile_cpu_s,'cdict_compile_wall_s':fused._cdict_compile_wall_s},'identity':identity,'identity_pass':all(identity.values()),'cpu_ratio_vs_clean_portfolio':fused_cpu/clean_cpu if clean_cpu else None,'wall_ratio_vs_clean_portfolio':fused_wall/clean_wall if clean_wall else None,'cpu_ratio_vs_single_independent':fused_cpu/clean_i['cpu_s'] if clean_i['cpu_s'] else None,'wall_ratio_vs_single_independent':fused_wall/clean_i['wall_s'] if clean_i['wall_s'] else None,'remaining_cpu_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_cpu},{'median_read_wall_s':clean_i['cpu_s']}),'remaining_wall_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fused_wall},{'median_read_wall_s':clean_i['wall_s']})}

V1._one=_one

def main():V1.main()
if __name__=='__main__':main()
