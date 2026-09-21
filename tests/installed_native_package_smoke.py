from __future__ import annotations
import ctypes, hashlib, importlib.util, json
from pathlib import Path

spec=importlib.util.find_spec("cmpct"); assert spec and spec.submodule_search_locations
pkg=Path(next(iter(spec.submodule_search_locations)))
candidates=[p for p in pkg.glob("cmpct_core*") if p.is_file() and p.suffix.lower() in {".so",".dylib",".dll",".pyd"}]
assert len(candidates)==1,(pkg,candidates); lib=ctypes.CDLL(str(candidates[0]))
for symbol in ("cmpct_codec_zstd_compress_bound","cmpct_codec_zstd_compress","cmpct_codec_zstd_compress_using_dict","cmpct_codec_zstd_decompress","cmpct_codec_zstd_decompress_using_dict","cmpct_codec_zstd_dict_decoder_create","cmpct_codec_zstd_dict_decoder_decompress","cmpct_codec_zstd_dict_decoder_free"): assert getattr(lib,symbol)

lib.cmpct_codec_zstd_compress_bound.argtypes=[ctypes.c_size_t]; lib.cmpct_codec_zstd_compress_bound.restype=ctypes.c_size_t
lib.cmpct_codec_zstd_compress_using_dict.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int32,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]; lib.cmpct_codec_zstd_compress_using_dict.restype=ctypes.c_int32
lib.cmpct_codec_zstd_decompress_using_dict.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]; lib.cmpct_codec_zstd_decompress_using_dict.restype=ctypes.c_int32
payload=b"structured-record\0"*8192+bytes(range(64))*128
seed=b"alpha beta gamma delta structured-record\0"; dictionary=(seed*((4096+len(seed)-1)//len(seed)))[:4096]
cap=lib.cmpct_codec_zstd_compress_bound(len(payload)); encoded=ctypes.create_string_buffer(cap); encoded_len=ctypes.c_size_t()
rc=lib.cmpct_codec_zstd_compress_using_dict(payload,len(payload),dictionary,len(dictionary),9,encoded,cap,ctypes.byref(encoded_len)); assert rc==0
compressed=encoded.raw[:encoded_len.value]; assert len(compressed)==104 and hashlib.sha256(compressed).hexdigest()=="0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6"
out=ctypes.create_string_buffer(len(payload)); out_len=ctypes.c_size_t(); rc=lib.cmpct_codec_zstd_decompress_using_dict(compressed,len(compressed),dictionary,len(dictionary),out,len(payload),ctypes.byref(out_len)); assert rc==0 and out_len.value==len(payload) and out.raw==payload
print(json.dumps({"schema":"cmpct-installed-native-package-smoke-v2","library":str(candidates[0]),"symbols":"ok","dict_vector_bytes":104,"dict_vector_sha256":hashlib.sha256(compressed).hexdigest(),"roundtrip":True}))
