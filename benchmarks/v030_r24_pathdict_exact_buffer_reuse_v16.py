from __future__ import annotations
"""v16 Builder/Referee: remove Python/native buffer churn from exact pathdict auditions.

Mission lock
============
v15 established that the v14 CDict proxy gate generalizes 15/15 while preserving
archive identity, but the remaining exact historical ``zcd`` calls still dominate
creation debt, especially Tiny Files. v11 already proved one reusable ZSTD_CCtx with
``ZSTD_compress_usingDict`` can reproduce historical product bytes, but it still
allocated/copied source, dictionary and destination buffers on every exact call.

Falsifiable hypothesis
----------------------
The residual exact-audition cost contains material avoidable allocation/copy work.
Keep the frozen v14 selector, proxy, raw dictionary, Zstd level 12 and historical
``ZSTD_compress_usingDict`` API, while reusing one CCtx, one dictionary buffer and a
geometrically grown destination buffer. Pass the immutable Python bytes directly as
the source pointer. No candidate decision may change.

Disproof / promotion law
------------------------
A proof build compares EVERY buffer-reuse exact frame byte-for-byte with
``cmpct.codec.zcd(data, dictionary, 12)``. Any mismatch retires the mechanism.
A separate performance build uses the identical coder without reference work; its
complete archive must equal both the clean pathdict artifact and the v14 proxy
artifact. Call/reject counts must also match v14. Mechanism credit requires >=15%
reduction in exact-call CPU and >=3% reduction in fused portfolio CPU on the frozen
five-target referee. Otherwise preserve the negative and do not tune thresholds.

Research only: no format, selector, dictionary sample, level, locality, recovery,
integrity, comparator, Genesis result, canonical Builder or release state changes.
"""

import ctypes
import hashlib
import msgpack
import time

from cmpct import codec as C
from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT
from benchmarks import v030_r24_pathdict_fused_encode_referee as V1
from benchmarks import v030_r24_pathdict_fused_encode_referee_v3 as V3
from benchmarks import v030_r24_pathdict_cdict_proxy_gate_v14 as V14
from benchmarks.v030_r24_pathdict_fused_encode_referee_v6 import CanonicalRecordingIndependentBuilder

_using_dict = C._z.ZSTD_compress_usingDict
_using_dict.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                        ctypes.c_void_p, ctypes.c_size_t,
                        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
_using_dict.restype = ctypes.c_size_t


class BufferReuseProxyGateBuilder(V14.ProxyGateBuilder):
    def __init__(self, *a, verify_frames: bool = False, **kw):
        super().__init__(*a, **kw)
        self._verify_frames = verify_frames
        self._exact_ctx = None
        self._exact_dict_key = None
        self._exact_dict_buf = None
        self._exact_dst = None
        self._exact_dst_cap = 0
        self._reuse_exact_calls = 0
        self._reuse_exact_cpu_s = 0.0
        self._reuse_exact_wall_s = 0.0
        self._frame_checks = 0
        self._frame_mismatches = 0
        self._dst_grows = 0

    def _ensure_exact_state(self, dictionary: bytes, src_len: int) -> None:
        key = (len(dictionary), hashlib.sha256(dictionary).digest())
        if self._exact_ctx is None:
            self._exact_ctx = C._z.ZSTD_createCCtx()
            if not self._exact_ctx:
                raise MemoryError('ZSTD_createCCtx failed')
        if self._exact_dict_key != key:
            self._exact_dict_buf = ctypes.create_string_buffer(dictionary)
            self._exact_dict_key = key
        need = int(C._z.ZSTD_compressBound(src_len))
        if need > self._exact_dst_cap:
            # Geometric growth prevents reallocating when candidate sizes rise gradually.
            cap = max(need, max(65536, self._exact_dst_cap * 2))
            self._exact_dst = ctypes.create_string_buffer(cap)
            self._exact_dst_cap = cap
            self._dst_grows += 1

    def _zcd_exact_reuse(self, data: bytes, dictionary: bytes) -> bytes:
        if not data:
            return b''
        self._ensure_exact_state(dictionary, len(data))
        # c_char_p keeps the immutable bytes object alive for the native call and avoids
        # create_string_buffer(data), while size remains explicit so embedded NULs are safe.
        src = ctypes.c_char_p(data)
        c0 = time.process_time(); w0 = time.perf_counter()
        n = C._zck(_using_dict(
            self._exact_ctx,
            self._exact_dst,
            self._exact_dst_cap,
            src,
            len(data),
            self._exact_dict_buf,
            len(dictionary),
            12,
        ))
        self._reuse_exact_cpu_s += time.process_time() - c0
        self._reuse_exact_wall_s += time.perf_counter() - w0
        self._reuse_exact_calls += 1
        out = self._exact_dst.raw[:n]
        if self._verify_frames:
            ref = C.zcd(data, dictionary, 12)
            self._frame_checks += 1
            if out != ref:
                self._frame_mismatches += 1
        return out

    def _encode_candidate(self, h, c):
        if self.dict_hash is not None and h == self.dict_hash:
            return CODEC_RAW, c.raw, b''
        normal = self._fused_normal_encode_cache.get(h)
        if normal is None:
            self._fused_misses += 1
            d = self.dictionary; self.dictionary = b''
            try:
                normal = super(V14.V9.TimedFusedPathBlindDictionaryBuilder, self)._encode_candidate(h, c)
            finally:
                self.dictionary = d
        else:
            self._fused_hits += 1
        if h in self.secondary_stream_hashes or h in self.canonical_deflate:
            return normal
        codec, comp, meta = normal; d = self.dictionary
        if d and h in getattr(self, '_pathblind_dict_hashes', set()):
            proxy = self._zcd_compiled(c.raw, d)
            dm = msgpack.packb([12], use_bin_type=True)
            normal_n = len(comp) + len(meta)
            if len(proxy) + len(dm) >= normal_n:
                self._proxy_rejects += 1
                return normal
            exact = self._zcd_exact_reuse(c.raw, d)
            # Keep v14's externally visible gate counters for direct equality checks.
            self._exact_calls += 1
            if len(exact) + len(dm) < normal_n:
                return CODEC_ZSTDDICT, exact, dm
            self._exact_rejects += 1
        return normal

    def reuse_stats(self):
        return {
            'exact_calls': self._reuse_exact_calls,
            'exact_cpu_s': self._reuse_exact_cpu_s,
            'exact_wall_s': self._reuse_exact_wall_s,
            'frame_checks': self._frame_checks,
            'frame_mismatches': self._frame_mismatches,
            'destination_grows': self._dst_grows,
            'destination_capacity': self._exact_dst_cap,
        }

    def close_native_state(self):
        if self._exact_ctx:
            C._z.ZSTD_freeCCtx(self._exact_ctx)
            self._exact_ctx = None
        self._exact_dict_buf = None
        self._exact_dict_key = None
        self._exact_dst = None
        self._exact_dst_cap = 0
        super().close_native_state()


def _build(builder, out):
    try:
        return V1._build_obj(builder, out)
    finally:
        builder.close_native_state()


def _clone(seed, source, cache, verify=False):
    b = V3._clone_seed(seed, BufferReuseProxyGateBuilder, source)
    b._fused_normal_encode_cache = cache
    b._verify_frames = verify
    return b


def _one(source, root):
    root.mkdir(parents=True, exist_ok=True)
    clean_i = V1._build_obj(V1._new(V1.SAME.NoMicroPackBuilder, source), root/'clean-independent.cmpct')
    clean_d = V1._build_obj(V1._new(V1.PathBlindDictionaryBuilder, source), root/'clean-dictionary.cmpct')

    seed = V1._new(V3.ScanSeedBuilder, source)
    c0=time.process_time(); w0=time.perf_counter(); seed.scan()
    scan_cpu=time.process_time()-c0; scan_wall=time.perf_counter()-w0
    rec = V3._clone_seed(seed, CanonicalRecordingIndependentBuilder, source)
    ri = V1._build_obj(rec, root/'fused-independent.cmpct')
    cache = rec._normal_encode_cache

    baseline = V3._clone_seed(seed, V14.ProxyGateBuilder, source)
    baseline._fused_normal_encode_cache = cache
    try:
        bd = V1._build_obj(baseline, root/'v14-baseline.cmpct')
    finally:
        baseline.close_native_state()

    proof = _clone(seed, source, cache, True)
    pd = _build(proof, root/'v16-proof.cmpct')
    proof_stats = proof.reuse_stats()
    proof_gate = proof.gate_stats()

    candidate = _clone(seed, source, cache, False)
    cd = _build(candidate, root/'v16-candidate.cmpct')
    cand_stats = candidate.reuse_stats()
    cand_gate = candidate.gate_stats()

    baseline_portfolio_cpu = scan_cpu + ri['cpu_s'] + bd['cpu_s']
    baseline_portfolio_wall = scan_wall + ri['wall_s'] + bd['wall_s']
    candidate_portfolio_cpu = scan_cpu + ri['cpu_s'] + cd['cpu_s']
    candidate_portfolio_wall = scan_wall + ri['wall_s'] + cd['wall_s']
    baseline_exact_cpu = baseline.gate_stats()['exact_cpu_s']
    baseline_exact_wall = baseline.gate_stats()['exact_wall_s']

    identity = {
        'independent_exact': clean_i['sha256'] == ri['sha256'] and clean_i['bytes'] == ri['bytes'],
        'baseline_dictionary_exact': clean_d['sha256'] == bd['sha256'] and clean_d['bytes'] == bd['bytes'],
        'proof_dictionary_exact': clean_d['sha256'] == pd['sha256'] and clean_d['bytes'] == pd['bytes'],
        'candidate_dictionary_exact': clean_d['sha256'] == cd['sha256'] and clean_d['bytes'] == cd['bytes'],
        'proof_all_frames_exact': proof_stats['frame_checks'] == proof_stats['exact_calls'] and proof_stats['frame_mismatches'] == 0,
        'gate_calls_equal': baseline.gate_stats()['exact_calls'] == proof_gate['exact_calls'] == cand_gate['exact_calls'],
        'proxy_rejects_equal': baseline.gate_stats()['proxy_rejects'] == proof_gate['proxy_rejects'] == cand_gate['proxy_rejects'],
        'exact_rejects_equal': baseline.gate_stats()['exact_rejects_after_proxy_accept'] == proof_gate['exact_rejects_after_proxy_accept'] == cand_gate['exact_rejects_after_proxy_accept'],
        'cache_miss_free': candidate._fused_misses == 0 and proof._fused_misses == 0,
    }
    exact_cpu_ratio = cand_stats['exact_cpu_s']/baseline_exact_cpu if baseline_exact_cpu else None
    exact_wall_ratio = cand_stats['exact_wall_s']/baseline_exact_wall if baseline_exact_wall else None
    portfolio_cpu_ratio = candidate_portfolio_cpu/baseline_portfolio_cpu if baseline_portfolio_cpu else None
    portfolio_wall_ratio = candidate_portfolio_wall/baseline_portfolio_wall if baseline_portfolio_wall else None
    earned = all(identity.values()) and exact_cpu_ratio is not None and portfolio_cpu_ratio is not None and exact_cpu_ratio <= 0.85 and portfolio_cpu_ratio <= 0.97
    return {
        'clean': {'independent': clean_i, 'dictionary': clean_d},
        'baseline_v14': {'dictionary': bd, 'gate': baseline.gate_stats(), 'portfolio_cpu_s': baseline_portfolio_cpu, 'portfolio_wall_s': baseline_portfolio_wall},
        'proof_v16': {'dictionary': pd, 'reuse': proof_stats, 'gate': proof_gate},
        'candidate_v16': {'dictionary': cd, 'reuse': cand_stats, 'gate': cand_gate, 'portfolio_cpu_s': candidate_portfolio_cpu, 'portfolio_wall_s': candidate_portfolio_wall},
        'identity': identity,
        'identity_pass': all(identity.values()),
        'exact_cpu_ratio_vs_v14': exact_cpu_ratio,
        'exact_wall_ratio_vs_v14': exact_wall_ratio,
        'portfolio_cpu_ratio_vs_v14': portfolio_cpu_ratio,
        'portfolio_wall_ratio_vs_v14': portfolio_wall_ratio,
        'mechanism_earned': earned,
    }


V1._one = _one


def main():
    # V1 owns the frozen five-target corpus, receipt schema and strong verification.
    V1.main()


if __name__ == '__main__':
    main()
