from __future__ import annotations

import base64, ctypes, hashlib, json, resource, shutil, statistics, subprocess, sys, tempfile, time, types
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests/conformance/v24-zstd-dictionary.json"
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
REPEATS = 120
EXTRACT_REPEATS = 15
ROUNDS = 5


def _lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_codec_zstd_dict_decoder_create.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)]; lib.cmpct_codec_zstd_dict_decoder_create.restype=ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_decompress.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]; lib.cmpct_codec_zstd_dict_decoder_decompress.restype=ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_free.argtypes=[ctypes.c_void_p]; lib.cmpct_codec_zstd_dict_decoder_free.restype=ctypes.c_int32
    return lib


def _install_native_decode(lib, archive: CMPCT):
    state={"handle":None}
    def decode(self,comp:bytes,usize:int)->bytes:
        with self._zdict_lock:
            if state["handle"] is None:
                dictionary=self._blob(self.dict_idx); handle=ctypes.c_void_p(); rc=lib.cmpct_codec_zstd_dict_decoder_create(dictionary,len(dictionary),ctypes.byref(handle))
                if rc!=0 or not handle.value: raise IOError(f"native dictionary decoder init failed: {rc}")
                state["handle"]=handle
            out=ctypes.create_string_buffer(usize); out_len=ctypes.c_size_t(); rc=lib.cmpct_codec_zstd_dict_decoder_decompress(state["handle"],comp,len(comp),out,usize,ctypes.byref(out_len))
            if rc!=0 or out_len.value!=usize: raise IOError(f"native dictionary decode failed: {rc} {out_len.value}/{usize}")
            return out.raw[:out_len.value]
    archive._zdict_decode=types.MethodType(decode,archive); return state


def _identity(got:bytes,vector:dict):
    assert len(got)==vector["logical_size"] and hashlib.sha256(got).hexdigest()==vector["logical_sha256"]


def _child(mode:str,path:Path,name:str,vector:dict):
    lib=_lib(); walls=[]; cpus=[]; extract_walls=[]; extract_cpus=[]
    with CMPCT(path) as ar:
        state=_install_native_decode(lib,ar) if mode=="native" else None
        try:
            _identity(ar.read(name),vector)
            for _ in range(REPEATS):
                ar.cache.clear(); t0=time.perf_counter_ns(); c0=time.process_time_ns(); got=ar.read(name); c1=time.process_time_ns(); t1=time.perf_counter_ns(); _identity(got,vector); walls.append(t1-t0); cpus.append(c1-c0)
            with tempfile.TemporaryDirectory(prefix=f"cmpct-extract-{mode}-") as td:
                root=Path(td)
                for i in range(EXTRACT_REPEATS):
                    dest=root/str(i); ar.cache.clear(); t0=time.perf_counter_ns(); c0=time.process_time_ns(); ar.extractall(dest,metadata=False); c1=time.process_time_ns(); t1=time.perf_counter_ns(); _identity((dest/name).read_bytes(),vector); extract_walls.append(t1-t0); extract_cpus.append(c1-c0); shutil.rmtree(dest)
        finally:
            if state and state["handle"] is not None: assert lib.cmpct_codec_zstd_dict_decoder_free(state["handle"])==0
    print(json.dumps({"mode":mode,"read_wall_ns_median":int(statistics.median(walls)),"read_cpu_ns_median":int(statistics.median(cpus)),"extract_wall_ns_median":int(statistics.median(extract_walls)),"extract_cpu_ns_median":int(statistics.median(extract_cpus)),"maxrss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}))


def main():
    vector=json.loads(VECTOR.read_text())["vector"]; archive_bytes=base64.b64decode(vector["archive_base64"])
    with tempfile.TemporaryDirectory(prefix="cmpct-zstd-reader-ab-") as td:
        path=Path(td)/"dictionary.cmpct"; path.write_bytes(archive_bytes); samples={"ambient":[],"native":[]}
        for _ in range(ROUNDS):
            for mode in ("ambient","native"):
                cp=subprocess.run([sys.executable,__file__,"--child",mode,str(path),vector["name"]],check=True,capture_output=True,text=True); samples[mode].append(json.loads(cp.stdout))
        keys=("read_wall_ns_median","read_cpu_ns_median","extract_wall_ns_median","extract_cpu_ns_median","maxrss_kib")
        summary={mode:{k:int(statistics.median(r[k] for r in rows)) for k in keys} for mode,rows in samples.items()}
        summary["ratios"]={k:summary["native"][k]/summary["ambient"][k] for k in keys}
        print(json.dumps({"schema":"cmpct-zstd-reader-owner-ab-v3","scope":"frozen real codec-3 archive; decoded cache evicted; dictionary state load-once; isolated subprocess arms","read_repeats":REPEATS,"extract_repeats":EXTRACT_REPEATS,"rounds":ROUNDS,"summary":summary,"raw":samples},sort_keys=True))


if __name__=="__main__":
    vector=json.loads(VECTOR.read_text())["vector"]
    if len(sys.argv)>1 and sys.argv[1]=="--child": _child(sys.argv[2],Path(sys.argv[3]),sys.argv[4],vector)
    else: main()
