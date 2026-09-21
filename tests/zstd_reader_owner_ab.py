from __future__ import annotations

import base64, ctypes, json, os, resource, statistics, subprocess, sys, tempfile, time, types
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests/conformance/v24-zstd-dictionary.json"
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
REPEATS = 120
ROUNDS = 5


def _lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_codec_zstd_dict_decoder_create.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_codec_zstd_dict_decoder_create.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_decompress.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_codec_zstd_dict_decoder_decompress.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_free.argtypes = [ctypes.c_void_p]
    lib.cmpct_codec_zstd_dict_decoder_free.restype = ctypes.c_int32
    return lib


def _install_native_decode(lib, archive: CMPCT):
    state = {"handle": None}
    def decode(self, comp: bytes, usize: int) -> bytes:
        with self._zdict_lock:
            if state["handle"] is None:
                dictionary = self._blob(self.dict_idx)
                handle = ctypes.c_void_p()
                rc = lib.cmpct_codec_zstd_dict_decoder_create(dictionary, len(dictionary), ctypes.byref(handle))
                if rc != 0 or not handle.value: raise IOError(f"native dictionary decoder init failed: {rc}")
                state["handle"] = handle
            out = ctypes.create_string_buffer(usize); out_len = ctypes.c_size_t()
            rc = lib.cmpct_codec_zstd_dict_decoder_decompress(state["handle"], comp, len(comp), out, usize, ctypes.byref(out_len))
            if rc != 0 or out_len.value != usize: raise IOError(f"native dictionary decode failed: {rc} {out_len.value}/{usize}")
            return out.raw[:out_len.value]
    archive._zdict_decode = types.MethodType(decode, archive)
    return state


def _child(mode: str, path: Path, name: str, want: bytes):
    lib = _lib(); walls=[]; cpus=[]
    with CMPCT(path) as ar:
        state = _install_native_decode(lib, ar) if mode == "native" else None
        try:
            assert ar.read(name) == want
            for _ in range(REPEATS):
                # Force the logical member through codec-3 every iteration; dictionary state remains load-once.
                ar.cache.clear()
                t0=time.perf_counter_ns(); c0=time.process_time_ns(); got=ar.read(name); c1=time.process_time_ns(); t1=time.perf_counter_ns()
                assert got == want
                walls.append(t1-t0); cpus.append(c1-c0)
        finally:
            if state and state["handle"] is not None:
                assert lib.cmpct_codec_zstd_dict_decoder_free(state["handle"]) == 0
    print(json.dumps({"mode":mode,"wall_ns_median":int(statistics.median(walls)),"cpu_ns_median":int(statistics.median(cpus)),"maxrss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}))


def main():
    vector=json.loads(VECTOR.read_text())["vector"]; archive_bytes=base64.b64decode(vector["archive_base64"]); want=base64.b64decode(vector["logical_base64"])
    with tempfile.TemporaryDirectory(prefix="cmpct-zstd-reader-ab-") as td:
        path=Path(td)/"dictionary.cmpct"; path.write_bytes(archive_bytes)
        samples={"ambient":[],"native":[]}
        for _ in range(ROUNDS):
            for mode in ("ambient","native"):
                cp=subprocess.run([sys.executable,__file__,"--child",mode,str(path),vector["name"]],check=True,capture_output=True,text=True)
                samples[mode].append(json.loads(cp.stdout))
        summary={mode:{k:int(statistics.median(r[k] for r in rows)) for k in ("wall_ns_median","cpu_ns_median","maxrss_kib")} for mode,rows in samples.items()}
        summary["ratios"]={"wall":summary["native"]["wall_ns_median"]/summary["ambient"]["wall_ns_median"],"cpu":summary["native"]["cpu_ns_median"]/summary["ambient"]["cpu_ns_median"],"rss":summary["native"]["maxrss_kib"]/summary["ambient"]["maxrss_kib"]}
        print(json.dumps({"schema":"cmpct-zstd-reader-owner-ab-v2","scope":"frozen real codec-3 archive; decoded member cache evicted per read; dictionary state load-once","repeats_per_arm":REPEATS,"rounds":ROUNDS,"summary":summary,"raw":samples},sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--child":
        vector=json.loads(VECTOR.read_text())["vector"]
        _child(sys.argv[2],Path(sys.argv[3]),sys.argv[4],base64.b64decode(vector["logical_base64"]))
    else: main()
