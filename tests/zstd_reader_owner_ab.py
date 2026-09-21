from __future__ import annotations

import base64, ctypes, json, resource, statistics, tempfile, time, types
from pathlib import Path

from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests/conformance/v24-zstd-dictionary.json"
LIB = ROOT / "native/cmpct-core/target/release/libcmpct_core.so"
REPEATS = 80


def _lib():
    lib = ctypes.CDLL(str(LIB))
    lib.cmpct_codec_zstd_dict_decoder_create.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
    lib.cmpct_codec_zstd_dict_decoder_create.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_decompress.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    lib.cmpct_codec_zstd_dict_decoder_decompress.restype = ctypes.c_int32
    lib.cmpct_codec_zstd_dict_decoder_free.argtypes = [ctypes.c_void_p]
    lib.cmpct_codec_zstd_dict_decoder_free.restype = ctypes.c_int32
    return lib


def _native_decode(lib, archive: CMPCT):
    state = {"handle": None}

    def decode(self, comp: bytes, usize: int) -> bytes:
        with self._zdict_lock:
            if state["handle"] is None:
                if self.dict_idx is None:
                    raise IOError("missing Zstd dictionary")
                dictionary = self._blob(self.dict_idx)
                handle = ctypes.c_void_p()
                rc = lib.cmpct_codec_zstd_dict_decoder_create(dictionary, len(dictionary), ctypes.byref(handle))
                if rc != 0 or not handle.value:
                    raise IOError(f"native dictionary decoder init failed: {rc}")
                state["handle"] = handle
            out = ctypes.create_string_buffer(usize)
            out_len = ctypes.c_size_t()
            rc = lib.cmpct_codec_zstd_dict_decoder_decompress(state["handle"], comp, len(comp), out, usize, ctypes.byref(out_len))
            if rc != 0 or out_len.value != usize:
                raise IOError(f"native dictionary decode failed: {rc} {out_len.value}/{usize}")
            return out.raw[:out_len.value]

    archive._zdict_decode = types.MethodType(decode, archive)
    return state


def _run(path: Path, name: str, mode: str, want: bytes, lib):
    walls, cpus = [], []
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with CMPCT(path) as ar:
        native = None
        if mode == "native":
            native = _native_decode(lib, ar)
        try:
            # Warm initialization only; every timed read evicts decoded member bytes so codec-3 work is real.
            assert ar.read(name) == want
            for _ in range(REPEATS):
                ar.cache.clear()
                t0 = time.perf_counter_ns(); c0 = time.process_time_ns()
                got = ar.read(name)
                c1 = time.process_time_ns(); t1 = time.perf_counter_ns()
                assert got == want
                walls.append(t1 - t0); cpus.append(c1 - c0)
        finally:
            if native and native["handle"] is not None:
                assert lib.cmpct_codec_zstd_dict_decoder_free(native["handle"]) == 0
                native["handle"] = None
    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"wall_ns_median": int(statistics.median(walls)), "cpu_ns_median": int(statistics.median(cpus)), "maxrss_delta": int(rss1-rss0)}


def main():
    vector = json.loads(VECTOR.read_text())["vector"]
    archive_bytes = base64.b64decode(vector["archive_base64"])
    want = base64.b64decode(vector["logical_base64"])
    lib = _lib()
    with tempfile.TemporaryDirectory(prefix="cmpct-zstd-reader-ab-") as td:
        path = Path(td) / "dictionary.cmpct"
        path.write_bytes(archive_bytes)
        # Interleave complete arms to reduce drift while preserving each implementation's load-once state.
        samples = {"ambient": [], "native": []}
        for _ in range(5):
            for mode in ("ambient", "native"):
                samples[mode].append(_run(path, vector["name"], mode, want, lib))
        summary = {}
        for mode, rows in samples.items():
            summary[mode] = {k: int(statistics.median(r[k] for r in rows)) for k in rows[0]}
        summary["ratios"] = {
            "wall": summary["native"]["wall_ns_median"] / summary["ambient"]["wall_ns_median"],
            "cpu": summary["native"]["cpu_ns_median"] / summary["ambient"]["cpu_ns_median"],
        }
        print(json.dumps({"schema":"cmpct-zstd-reader-owner-ab-v1","repeats_per_arm":REPEATS,"rounds":5,"summary":summary,"raw":samples}, sort_keys=True))


if __name__ == "__main__":
    main()
