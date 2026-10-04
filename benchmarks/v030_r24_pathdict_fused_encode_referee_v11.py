from __future__ import annotations
import ctypes,time
from cmpct import codec as C
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v10 as V10
_u=C._z.ZSTD_compress_usingDict
_u.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];_u.restype=ctypes.c_size_t
class B(V10.StickyRawDictFusedBuilder):
 def _ensure(self,d):
  if self._ctx:return
  c=time.process_time();w=time.perf_counter();self._ctx=C._z.ZSTD_createCCtx();self._setup_cpu+=time.process_time()-c;self._setup_wall+=time.perf_counter()-w
  if not self._ctx:raise MemoryError
 def _zcd_sticky(self,data,d):
  if not data:return b''
  self._ensure(d);s=ctypes.create_string_buffer(data);db=ctypes.create_string_buffer(d);cap=int(C._z.ZSTD_compressBound(len(data)));o=ctypes.create_string_buffer(cap);c=time.process_time();w=time.perf_counter();n=C._zck(_u(self._ctx,o,cap,s,len(data),db,len(d),12));self._cpu+=time.process_time()-c;self._wall+=time.perf_counter()-w;self._calls+=1;out=o.raw[:n];ref=C.zcd(data,d,12);self._checks+=1
  if out!=ref:self._fails+=1
  return out
def _one(source,root):
 old=V10.StickyRawDictFusedBuilder;V10.StickyRawDictFusedBuilder=B
 try:return V10._one(source,root)
 finally:V10.StickyRawDictFusedBuilder=old
V1._one=_one
if __name__=='__main__':V1.main()
