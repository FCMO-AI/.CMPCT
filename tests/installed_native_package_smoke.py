from __future__ import annotations
import ctypes, ctypes.util, hashlib, importlib.util, json, tempfile
from pathlib import Path

spec=importlib.util.find_spec("cmpct"); assert spec and spec.submodule_search_locations
assert importlib.util.find_spec("zstandard") is None,"clean installed product still depends on Python zstandard"
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
compressed=encoded.raw[:encoded_len.value]; expected_sha="0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6"; assert len(compressed)==104 and hashlib.sha256(compressed).hexdigest()==expected_sha
out=ctypes.create_string_buffer(len(payload)); out_len=ctypes.c_size_t(); rc=lib.cmpct_codec_zstd_decompress_using_dict(compressed,len(compressed),dictionary,len(dictionary),out,len(payload),ctypes.byref(out_len)); assert rc==0 and out_len.value==len(payload) and out.raw==payload

real_find_library=ctypes.util.find_library
def guarded_find_library(name):
    if str(name).lower()=="zstd": raise AssertionError("shipping Python attempted ambient Zstd discovery")
    return real_find_library(name)
ctypes.util.find_library=guarded_find_library
archive_sha=None
try:
    from cmpct.codec import zc, zcd, zd
    from cmpct.native_codec import DictDecoder
    plain=zc(payload,9); assert zd(plain,len(payload))==payload
    via_shipping=zcd(payload,dictionary,9); assert via_shipping==compressed and hashlib.sha256(via_shipping).hexdigest()==expected_sha
    decoder=DictDecoder(dictionary)
    try: assert decoder.decompress(via_shipping,len(payload))==payload
    finally: decoder.close()

    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    with tempfile.TemporaryDirectory(prefix="cmpct-installed-smoke-") as td:
        root=Path(td); src=root/"src"; dst=root/"dst"; arc=root/"representative.cmpct"
        (src/"nested").mkdir(parents=True)
        expected={"readme.txt":b"portable exact archive\n"*4096,"nested/data.bin":bytes((i*73+19)&255 for i in range(128*1024))}
        for rel,data in expected.items(): p=src/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        Builder(src,workers=1,reproducible=True,reproducible_epoch_ns=0).build(arc)
        archive_sha=hashlib.sha256(arc.read_bytes()).hexdigest()
        with CMPCT(arc) as reader:
            assert reader.verify()==len(expected)
            for rel,data in expected.items(): assert reader.read(rel)==data
            reader.extractall(dst,metadata=False)
        for rel,data in expected.items():
            actual=(dst/rel).read_bytes()
            assert actual==data,{"member":rel,"expected_len":len(data),"actual_len":len(actual),"expected_sha":hashlib.sha256(data).hexdigest(),"actual_sha":hashlib.sha256(actual).hexdigest(),"first_mismatch":next((i for i,(a,b) in enumerate(zip(data,actual)) if a!=b),None)}
finally:
    ctypes.util.find_library=real_find_library

print(json.dumps({"schema":"cmpct-installed-native-package-smoke-v4","library":str(candidates[0]),"symbols":"ok","dict_vector_bytes":104,"dict_vector_sha256":expected_sha,"roundtrip":True,"representative_archive_create_read_extract":True,"representative_archive_sha256":archive_sha,"shipping_python_no_ambient_zstd":True,"python_zstandard_absent":True}))
