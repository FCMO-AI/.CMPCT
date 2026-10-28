from __future__ import annotations
"""v14 Builder: CDict is a cheap admission gate; only exact zcd bytes are emitted.

Frozen rule from v13: compute the CDict candidate for every eligible pathdict member.
Only when CDict_total < normal_total do we pay for the historical exact zcd audition.
The exact candidate must still strictly beat normal before CODEC_ZSTDDICT is emitted.
CDict bytes are never stored. Final archive identity with clean pathdict is mandatory.
"""
import msgpack,time
from cmpct import codec as C
from cmpct.codec import CODEC_RAW,CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks import v030_r24_pathdict_fused_encode_referee_v9 as V9
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder
class ProxyGateBuilder(V9.CompiledDictFusedBuilder):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self._exact_calls=0;self._exact_cpu=0.;self._exact_wall=0.;self._proxy_rejects=0;self._exact_rejects=0
 def _encode_candidate(self,h,c):
  if self.dict_hash is not None and h==self.dict_hash:return CODEC_RAW,c.raw,b''
  normal=self._fused_normal_encode_cache.get(h)
  if normal is None:
   self._fused_misses+=1;d=self.dictionary;self.dictionary=b''
   try:normal=super(V9.TimedFusedPathBlindDictionaryBuilder,self)._encode_candidate(h,c)
   finally:self.dictionary=d
  else:self._fused_hits+=1
  if h in self.secondary_stream_hashes or h in self.canonical_deflate:return normal
  codec,comp,meta=normal;d=self.dictionary
  if d and h in getattr(self,'_pathblind_dict_hashes',set()):
   proxy=self._zcd_compiled(c.raw,d);dm=msgpack.packb([12],use_bin_type=True);normal_n=len(comp)+len(meta)
   if len(proxy)+len(dm)>=normal_n:self._proxy_rejects+=1;return normal
   c0=time.process_time();w0=time.perf_counter();exact=C.zcd(c.raw,d,12);self._exact_cpu+=time.process_time()-c0;self._exact_wall+=time.perf_counter()-w0;self._exact_calls+=1
   if len(exact)+len(dm)<normal_n:return CODEC_ZSTDDICT,exact,dm
   self._exact_rejects+=1
  return normal
 def gate_stats(self):return {'proxy_calls':self._cdict_calls,'proxy_cpu_s':self._cdict_cpu_s,'proxy_wall_s':self._cdict_wall_s,'proxy_compile_cpu_s':self._cdict_compile_cpu_s,'proxy_rejects':self._proxy_rejects,'exact_calls':self._exact_calls,'exact_cpu_s':self._exact_cpu,'exact_wall_s':self._exact_wall,'exact_rejects_after_proxy_accept':self._exact_rejects}
def _one(source,root):
 root.mkdir(parents=True,exist_ok=True);ci=V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct');cd=V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct');seed=V1._new(V3.ScanSeedBuilder,source);c0=time.process_time();w0=time.perf_counter();seed.scan();sc=time.process_time()-c0;sw=time.perf_counter()-w0;rec=V3._clone_seed(seed,CanonicalRecordingIndependentBuilder,source);ri=V1._build_obj(rec,root/'fused-independent.cmpct');f=V3._clone_seed(seed,ProxyGateBuilder,source);f._fused_normal_encode_cache=rec._normal_encode_cache
 try:fd=V1._build_obj(f,root/'fused-dictionary.cmpct')
 finally:f.close_native_state()
 fc=sc+ri['cpu_s']+fd['cpu_s'];fw=sw+ri['wall_s']+fd['wall_s'];cc=ci['cpu_s']+cd['cpu_s'];cw=ci['wall_s']+cd['wall_s'];ident={'independent_exact':ci['sha256']==ri['sha256'] and ci['bytes']==ri['bytes'],'dictionary_exact':cd['sha256']==fd['sha256'] and cd['bytes']==fd['bytes'],'cache_miss_free':f._fused_misses==0}
 return {'clean':{'independent':ci,'dictionary':cd,'portfolio_cpu_s':cc,'portfolio_wall_s':cw},'fused':{'scan_cpu_s':sc,'scan_wall_s':sw,'clone_cpu_s':0.,'clone_wall_s':0.,'cache_hits':f._fused_hits,'cache_misses':f._fused_misses,'independent':ri,'dictionary':fd,'portfolio_cpu_s':fc,'portfolio_wall_s':fw},'identity':ident,'identity_pass':all(ident.values()),'gate':f.gate_stats(),'cpu_ratio_vs_clean_portfolio':fc/cc,'wall_ratio_vs_clean_portfolio':fw/cw,'cpu_ratio_vs_single_independent':fc/ci['cpu_s'],'wall_ratio_vs_single_independent':fw/ci['wall_s'],'remaining_cpu_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fc},{'median_read_wall_s':ci['cpu_s']}),'remaining_wall_debt':V1.SEL._confirmed_regression({'median_read_wall_s':fw},{'median_read_wall_s':ci['wall_s']})}
V1._one=_one
if __name__=='__main__':V1.main()
