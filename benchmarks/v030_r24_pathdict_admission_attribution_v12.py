from __future__ import annotations
"""v12 referee: attribute which exact pathdict auditions actually pay.

No selector changes. Every historical raw-dictionary audition still executes through
exact ZSTD_compress_usingDict. We only record pre-audition observables and the exact
stored-byte margin versus the already-computed normal candidate. The purpose is to
decide whether cheap opportunity gating is scientifically justified before building
one. No threshold receives product credit from this run.
"""
import msgpack,time
from cmpct.codec import CODEC_RAW,CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks import v030_r24_pathdict_fused_encode_referee_v8 as V8
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder

class AttributionBuilder(V8.ReusedCCtxFusedPathBlindDictionaryBuilder):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self._econ=[]
 def _encode_candidate(self,h,c):
  if self.dict_hash is not None and h==self.dict_hash:return CODEC_RAW,c.raw,b''
  normal=self._fused_normal_encode_cache.get(h)
  if normal is None:
   self._fused_misses+=1;d=self.dictionary;self.dictionary=b''
   try:normal=super(V8.TimedFusedPathBlindDictionaryBuilder,self)._encode_candidate(h,c)
   finally:self.dictionary=d
  else:self._fused_hits+=1
  if h in self.secondary_stream_hashes or h in self.canonical_deflate:return normal
  codec,comp,meta=normal;d=self.dictionary
  if d and h in getattr(self,'_pathblind_dict_hashes',set()):
   dc=self._zcd_reused(c.raw,d,12);dm=msgpack.packb([12],use_bin_type=True);nb=len(comp)+len(meta);db=len(dc)+len(dm);raw=len(c.raw)
   self._econ.append({'raw':raw,'normal':nb,'dict':db,'margin':nb-db,'normal_ratio':nb/raw if raw else 0.0})
   if db<nb:return CODEC_ZSTDDICT,dc,dm
  return codec,comp,meta
 def economics(self):
  rows=self._econ;wins=[x for x in rows if x['margin']>0];loss=[x for x in rows if x['margin']<=0]
  def sb(x):
   n=x['raw']
   return '<1K' if n<1024 else ('1-4K' if n<4096 else ('4-16K' if n<16384 else ('16-64K' if n<65536 else '>=64K')))
  def rb(x):
   r=x['normal_ratio']
   return '<=.25' if r<=.25 else ('<=.50' if r<=.50 else ('<=.75' if r<=.75 else ('<=1.0' if r<=1.0 else '>1.0')))
  def bins(fn):
   out={}
   for x in rows:
    k=fn(x);z=out.setdefault(k,{'calls':0,'wins':0,'saving':0,'loss_if_forced':0});z['calls']+=1;z['wins']+=x['margin']>0;z['saving']+=max(0,x['margin']);z['loss_if_forced']+=max(0,-x['margin'])
   return out
  ms=sorted((x['margin'] for x in wins),reverse=True);tot=sum(ms)
  conc={str(k):sum(ms[:k]) for k in [1,5,10,25,50,100,250,500,1000] if k<=len(ms)}
  return {'calls':len(rows),'wins':len(wins),'nonwins':len(loss),'win_rate':len(wins)/len(rows) if rows else 0.0,'total_earned_saving':tot,'total_forced_loss_on_nonwins':sum(max(0,-x['margin']) for x in loss),'winner_saving_concentration':conc,'size_bins':bins(sb),'normal_ratio_bins':bins(rb),'top_winner_margins':ms[:20]}

def _one(source,root):
 root.mkdir(parents=True,exist_ok=True);ci=V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder,source),root/'clean-independent.cmpct');cd=V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder,source),root/'clean-dictionary.cmpct')
 seed=V1._new(V3.ScanSeedBuilder,source);c0=time.process_time();w0=time.perf_counter();seed.scan();sc=time.process_time()-c0;sw=time.perf_counter()-w0
 rec=V3._clone_seed(seed,CanonicalRecordingIndependentBuilder,source);ri=V1._build_obj(rec,root/'fused-independent.cmpct');f=V3._clone_seed(seed,AttributionBuilder,source);f._fused_normal_encode_cache=rec._normal_encode_cache
 try:fd=V1._build_obj(f,root/'fused-dictionary.cmpct')
 finally:f.close_reused_context()
 fc=sc+ri['cpu_s']+fd['cpu_s'];fw=sw+ri['wall_s']+fd['wall_s'];cc=ci['cpu_s']+cd['cpu_s'];cw=ci['wall_s']+cd['wall_s'];ident={'independent_exact':ci['sha256']==ri['sha256'] and ci['bytes']==ri['bytes'],'dictionary_exact':cd['sha256']==fd['sha256'] and cd['bytes']==fd['bytes'],'cache_miss_free':f._fused_misses==0}
 return {'clean':{'independent':ci,'dictionary':cd,'portfolio_cpu_s':cc,'portfolio_wall_s':cw},'fused':{'independent':ri,'dictionary':fd,'portfolio_cpu_s':fc,'portfolio_wall_s':fw,'dictionary_native_encode_cpu_s':f._dict_encode_cpu_s,'dictionary_native_encode_wall_s':f._dict_encode_wall_s,'calls':f._reuse_cctx_calls},'identity':ident,'identity_pass':all(ident.values()),'economics':f.economics()}
V1._one=_one
if __name__=='__main__':V1.main()
