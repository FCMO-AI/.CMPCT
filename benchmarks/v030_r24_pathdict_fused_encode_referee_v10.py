from __future__ import annotations
"""v10: sticky raw-dictionary Zstd referee.

Hypothesis: one CCtx with level 12 + the unchanged raw dictionary, reused between
frames with session-only reset, can reproduce cmpct.codec.zcd byte-for-byte while
removing repeated dictionary setup. One frame or final-archive mismatch falsifies the
route regardless of speed. Research-only: no selector/format/corpus/Genesis change.
"""
import ctypes, hashlib, msgpack, time
from cmpct import codec as C
from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder
from benchmarks.v030_r24_pathdict_fused_encode_referee_v4 import TimedFusedPathBlindDictionaryBuilder

_set=C._z.ZSTD_CCtx_setParameter; _set.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int]; _set.restype=ctypes.c_size_t
_load=C._z.ZSTD_CCtx_loadDictionary; _load.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t]; _load.restype=ctypes.c_size_t
_reset=C._z.ZSTD_CCtx_reset; _reset.argtypes=[ctypes.c_void_p,ctypes.c_int]; _reset.restype=ctypes.c_size_t
_comp=C._z.ZSTD_compress2; _comp.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]; _comp.restype=ctypes.c_size_t

class StickyRawDictFusedBuilder(TimedFusedPathBlindDictionaryBuilder):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self._ctx=None; self._key=None; self._calls=0; self._cpu=0.; self._wall=0.; self._setup_cpu=0.; self._setup_wall=0.; self._checks=0; self._fails=0; self._first=None
    def _ensure(self,d):
        key=(len(d),hashlib.sha256(d).digest())
        if self._ctx and self._key==key:return
        self.close_native_state(); c0=time.process_time(); w0=time.perf_counter(); ctx=C._z.ZSTD_createCCtx()
        if not ctx:raise MemoryError('Zstd CCtx allocation failed')
        try:
            C._zck(_set(ctx,100,12)); db=ctypes.create_string_buffer(d); C._zck(_load(ctx,db,len(d)))
        except Exception:
            C._z.ZSTD_freeCCtx(ctx); raise
        self._ctx=ctx; self._key=key; self._setup_cpu+=time.process_time()-c0; self._setup_wall+=time.perf_counter()-w0
    def _zcd_sticky(self,data,d):
        if not data:return b''
        self._ensure(d); C._zck(_reset(self._ctx,1)); src=ctypes.create_string_buffer(data); cap=int(C._z.ZSTD_compressBound(len(data))); dst=ctypes.create_string_buffer(cap)
        c0=time.process_time(); w0=time.perf_counter(); n=C._zck(_comp(self._ctx,dst,cap,src,len(data))); self._cpu+=time.process_time()-c0; self._wall+=time.perf_counter()-w0; self._calls+=1; out=dst.raw[:n]
        ref=C.zcd(data,d,12); self._checks+=1
        if out!=ref:
            self._fails+=1
            if self._first is None:self._first={'usize':len(data),'sticky_bytes':len(out),'reference_bytes':len(ref),'sticky_sha256':hashlib.sha256(out).hexdigest(),'reference_sha256':hashlib.sha256(ref).hexdigest()}
        return out
    def _encode_candidate(self,h,c):
        if self.dict_hash is not None and h==self.dict_hash:return CODEC_RAW,c.raw,b''
        cached=self._fused_normal_encode_cache.get(h)
        if cached is None:
            self._fused_misses+=1; d=self.dictionary; self.dictionary=b''
            try:cached=super(TimedFusedPathBlindDictionaryBuilder,self)._encode_candidate(h,c)
            finally:self.dictionary=d
        else:self._fused_hits+=1
        if h in self.secondary_stream_hashes or h in self.canonical_deflate:return cached
        codec,comp,meta=cached; d=self.dictionary
        if d and h in getattr(self,'_pathblind_dict_hashes',set()):
            dc=self._zcd_sticky(c.raw,d); dm=msgpack.packb([12],use_bin_type=True)
            if len(dc)+len(dm)<len(comp)+len(meta):return CODEC_ZSTDDICT,dc,dm
        return codec,comp,meta
    def close_native_state(self):
        if self._ctx:C._z.ZSTD_freeCCtx(self._ctx); self._ctx=None
        self._key=None

def _build(b,out):
    try:return V1._build_obj(b,out)
    finally:b.close_native_state()

def _one(source,root):
    root.mkdir(parents=True,exist_ok=True); ci=V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct'); cd=V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct')
    seed=V1._new(V3.ScanSeedBuilder,source); c0=time.process_time(); w0=time.perf_counter(); seed.scan(); sc=time.process_time()-c0; sw=time.perf_counter()-w0
    rec=V3._clone_seed(seed,CanonicalRecordingIndependentBuilder,source); ri=V1._build_obj(rec,root/'fused-independent.cmpct'); f=V3._clone_seed(seed,StickyRawDictFusedBuilder,source); f._fused_normal_encode_cache=rec._normal_encode_cache; fd=_build(f,root/'fused-dictionary.cmpct')
    fc=sc+ri['cpu_s']+fd['cpu_s']; fw=sw+ri['wall_s']+fd['wall_s']; cc=ci['cpu_s']+cd['cpu_s']; cw=ci['wall_s']+cd['wall_s']
    ident={'independent_exact':ci['sha256']==ri['sha256'] and ci['bytes']==ri['bytes'],'dictionary_exact':cd['sha256']==fd['sha256'] and cd['bytes']==fd['bytes'],'independent_train_once':rec._dict_train_calls==1,'dictionary_train_once':f._dict_train_calls==1,'cache_miss_free':f._fused_misses==0,'all_dictionary_frames_exact':f._fails==0 and f._checks==f._calls}
    return {'clean':{'independent':ci,'dictionary':cd,'portfolio_cpu_s':cc,'portfolio_wall_s':cw},'fused':{'scan_cpu_s':sc,'scan_wall_s':sw,'ind_train_cpu_s':rec._dict_train_cpu_s,'ind_train_wall_s':rec._dict_train_wall_s,'ind_train_calls':rec._dict_train_calls,'dict_train_cpu_s':f._dict_train_cpu_s,'dict_train_wall_s':f._dict_train_wall_s,'dict_train_calls':f._dict_train_calls,'independent':ri,'dictionary':fd,'portfolio_cpu_s':fc,'portfolio_wall_s':fw,'cache_hits':f._fused_hits,'cache_misses':f._fused_misses,'cache_entries':len(rec._normal_encode_cache),'sticky_calls':f._calls,'sticky_encode_cpu_s':f._cpu,'sticky_encode_wall_s':f._wall,'sticky_setup_cpu_s':f._setup_cpu,'sticky_setup_wall_s':f._setup_wall,'frame_identity_checks':f._checks,'frame_identity_failures':f._fails,'first_frame_mismatch':f._first},'identity':ident,'identity_pass':all(ident.values()),'cpu_ratio_vs_clean_portfolio':fc/cc,'wall_ratio_vs_clean_portfolio':fw/cw,'cpu_ratio_vs_single_independent':fc/ci['cpu_s'],'wall_ratio_vs_single_independent':fw/ci['wall_s'],'remaining_cpu_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fc},{'median_read_wall_s':ci['cpu_s']}),'remaining_wall_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fw},{'median_read_wall_s':ci['wall_s']})}

V1._one=_one
if __name__=='__main__':V1.main()
