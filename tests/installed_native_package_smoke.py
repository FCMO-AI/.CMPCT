from __future__ import annotations
import ctypes, importlib.util, json
from pathlib import Path

spec=importlib.util.find_spec("cmpct")
assert spec and spec.submodule_search_locations
pkg=Path(next(iter(spec.submodule_search_locations)))
candidates=[p for p in pkg.glob("cmpct_core*") if p.is_file() and p.suffix.lower() in {".so",".dylib",".dll",".pyd"}]
assert len(candidates)==1,(pkg,candidates)
lib=ctypes.CDLL(str(candidates[0]))
for symbol in ("cmpct_codec_zstd_compress_bound","cmpct_codec_zstd_compress","cmpct_codec_zstd_compress_using_dict","cmpct_codec_zstd_decompress","cmpct_codec_zstd_decompress_using_dict","cmpct_codec_zstd_dict_decoder_create","cmpct_codec_zstd_dict_decoder_decompress","cmpct_codec_zstd_dict_decoder_free"):
    assert getattr(lib,symbol)
print(json.dumps({"schema":"cmpct-installed-native-package-smoke-v1","library":str(candidates[0]),"symbols":"ok"}))
