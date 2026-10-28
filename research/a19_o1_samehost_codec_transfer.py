#!/usr/bin/env python3
"""A19-O1 same-host exact-source Zstd library-version control (post O0)."""
from __future__ import annotations
import hashlib
import json
import statistics
import sys
import ctypes
import ctypes.util
import pathlib
import msgpack
import zstandard

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from a19_o0_program_composition import fixture, candidates, transform, inverse

NATIVE = ctypes.CDLL(ctypes.util.find_library("zstd"))
NATIVE.ZSTD_versionString.restype=ctypes.c_char_p
NATIVE.ZSTD_compressBound.argtypes=[ctypes.c_size_t]
NATIVE.ZSTD_compressBound.restype=ctypes.c_size_t
NATIVE.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int]
NATIVE.ZSTD_compress.restype=ctypes.c_size_t
NATIVE.ZSTD_isError.argtypes=[ctypes.c_size_t]
NATIVE.ZSTD_isError.restype=ctypes.c_uint
NATIVE.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
NATIVE.ZSTD_decompress.restype=ctypes.c_size_t

def native_compress(raw):
    bound=NATIVE.ZSTD_compressBound(len(raw))
    src=ctypes.create_string_buffer(raw)
    dst=ctypes.create_string_buffer(bound)
    n=NATIVE.ZSTD_compress(dst,bound,src,len(raw),19)
    if NATIVE.ZSTD_isError(n):raise RuntimeError("native Zstd compression error")
    return dst.raw[:n]

def native_decompress(comp,n):
    src=ctypes.create_string_buffer(comp)
    dst=ctypes.create_string_buffer(n)
    result=NATIVE.ZSTD_decompress(dst,n,src,len(comp))
    if NATIVE.ZSTD_isError(result) or result!=n:raise RuntimeError("native Zstd decode failed")
    return dst.raw[:result]

def winner(arms,typ):
    return min((a for a in arms if a["type"]==typ),key=lambda x:(x["size"],str(x["steps"])))

def run():
    version_native=NATIVE.ZSTD_versionString().decode()
    version_wheel=".".join(map(str,zstandard.ZSTD_VERSION))
    output={"schema":"cmpct-a19-o1-codec-transfer-v1",
            "prereg_first_commit":"7f19a1b88c5894cd805e88025b495dc655cdd666",
            "o0_result_head":"0d153b0a8ffe183e1346fe03b16a3ad285dd8a2a",
            "versions":{"system_zstd":version_native,"wheel_zstd":version_wheel,
                        "zstandard_py":zstandard.__version__},
            "status":"PENDING","cases":[]}
    frame_dir=pathlib.Path("receipts/o1-frames")
    frame_dir.mkdir(parents=True,exist_ok=True)
    comp=zstandard.ZstdCompressor(level=19)
    decomp=zstandard.ZstdDecompressor()
    for fam in ("progression","quantized","heldout","random","periodic"):
        for seed in (0,1):
            logical=fixture(fam,seed)
            entries={"system":[],"wheel":[]}
            for program in candidates():
                transformed=transform(logical,program)
                hdr=msgpack.packb({
                    "v":1,"len":len(logical),"sha256":hashlib.sha256(logical).digest(),
                    "codec":"zstd19","program":program
                },use_bin_type=True)
                comp_native=native_compress(transformed)
                comp_wheel=comp.compress(transformed)
                if native_decompress(comp_native,len(logical))!=transformed:
                    raise AssertionError("native corrupt compressed transform")
                if decomp.decompress(comp_wheel,max_output_size=len(logical))!=transformed:
                    raise AssertionError("wheel corrupt compressed transform")
                if inverse(transformed,program)!=logical:raise AssertionError("invalid inverse")
                for name,frame in (("system",comp_native),("wheel",comp_wheel)):
                    frame_rel=f"{fam}-{seed}-{len(entries[name]):02d}-{name}.a19"
                    full=b"A19O"+len(hdr).to_bytes(4,"big")+hdr+frame
                    (frame_dir/frame_rel).write_bytes(full)
                    typ=("direct" if not program else "unary" if len(program)==1 else "composed")
                    entries[name].append({
                        "type":typ,"steps":program,"size":8+len(hdr)+len(frame),
                        "frame_rel":frame_rel,"complete_frame_sha256":hashlib.sha256(full).hexdigest(),
                        "compressed_sha256":hashlib.sha256(frame).hexdigest(),
                        "meta_sha256":hashlib.sha256(hdr).hexdigest(),
                        "transformed_sha256":hashlib.sha256(transformed).hexdigest(),
                    })
            outcomes={}
            for name,arms in entries.items():
                direct=winner(arms,"direct")
                unary=winner(arms,"unary")
                composed=winner(arms,"composed")
                diff=unary["size"]-composed["size"]
                outcomes[name]={
                    "direct_bytes":direct["size"],"best_unary_bytes":unary["size"],
                    "best_composed_bytes":composed["size"],
                    "best_unary_steps":unary["steps"],"best_composed_steps":composed["steps"],
                    "delta_bytes":diff,"delta_pct":100*diff/unary["size"],
                    "meets_original_o0_single_case_gate":
                    (diff>=128 and diff/unary["size"]>=.01 and composed["size"]<direct["size"])
                }
            output["cases"].append({
                "family":fam,"seed":seed,"source_sha256":hashlib.sha256(logical).hexdigest(),
                "frame_count":len(entries["system"]),
                "compressed_byte_exact_matches":sum(a["compressed_sha256"]==b["compressed_sha256"] for a,b in zip(entries["system"],entries["wheel"])),
                "physical_program_headers_match":all(a["meta_sha256"]==b["meta_sha256"] for a,b in zip(entries["system"],entries["wheel"])),
                "same_transformed_bytes":all(a["transformed_sha256"]==b["transformed_sha256"] for a,b in zip(entries["system"],entries["wheel"])),
                "results":outcomes
            })
    if version_native!="1.5.5" or version_wheel!="1.5.7":
        output["status"]="VERSION_COMPARISON_UNCERTAIN"
    else:
        family="progression"
        got={}
        for codec in ("system","wheel"):
            both=[c for c in output["cases"] if c["family"]==family]
            got[codec]=all(c["results"][codec]["meets_original_o0_single_case_gate"] for c in both)
        output["status"]="VERSION_SENSITIVITY_SUPPORTED" if got["system"] and not got["wheel"] else "VERSION_HYPOTHESIS_NOT_CONFIRMED"
    assert len(output["cases"])==10 and all(c["frame_count"]==20 and c["same_transformed_bytes"] and c["physical_program_headers_match"] for c in output["cases"])
    return output

if __name__=="__main__":
    output=run()
    pathlib.Path("receipts").mkdir(exist_ok=True)
    pathlib.Path("receipts/a19_o1_version_transfer.json").write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    for c in output["cases"]:
        n,w=c["results"]["system"],c["results"]["wheel"]
        print(c["family"],c["seed"],"lib",n["best_unary_bytes"],n["best_composed_bytes"],
              "wheel",w["best_unary_bytes"],w["best_composed_bytes"],
              "matches",c["compressed_byte_exact_matches"])
    print("DECISION",output["status"],output["versions"])
