"""ONE-G0.2 native exact relation-span verifier research module.

This preserves `relation_span_growth.grow_relation_spans` semantics while moving the exact
byte proof into a bounded native kernel.  The native kernel is still proof, not discovery:
callers provide nominations and successful runs still compile through ordinary ONE Laws.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

from experiments.one.relation_span_growth import RelationGrowthResult

_C = r'''
#include <stdint.h>
#include <stddef.h>
#if defined(__SSE2__)
#include <emmintrin.h>
#endif

typedef struct { uint64_t start, length; } run_t;

/* Return bytes inspected. `*ok` is 1 only if the complete requested width matched.
   On mismatch, inspected includes the mismatching byte exactly like the Python oracle. */
static size_t verify_exact(const uint8_t *a, const uint8_t *b, size_t start, size_t width,
                           uint32_t op, uint8_t value, int *ok) {
    size_t i = 0;
#if defined(__SSE2__)
    const __m128i vv = _mm_set1_epi8((char)value);
    for (; i + 16u <= width; i += 16u) {
        const __m128i va = _mm_loadu_si128((const __m128i *)(a + start + i));
        const __m128i vb = _mm_loadu_si128((const __m128i *)(b + start + i));
        const __m128i expected = op == 1u ? _mm_add_epi8(va, vv) : _mm_xor_si128(va, vv);
        const unsigned mask = (unsigned)_mm_movemask_epi8(_mm_cmpeq_epi8(expected, vb));
        if (mask != 0xffffu) {
            const unsigned bad = (~mask) & 0xffffu;
            unsigned lane = 0u;
            while (((bad >> lane) & 1u) == 0u) ++lane;
            *ok = 0;
            return i + (size_t)lane + 1u;
        }
    }
#endif
    for (; i < width; ++i) {
        const uint8_t expected = op == 1u ? (uint8_t)(a[start+i] + value)
                                          : (uint8_t)(a[start+i] ^ value);
        if (b[start+i] != expected) { *ok = 0; return i + 1u; }
    }
    *ok = 1;
    return width;
}

int grow_relation_spans_native(
    const uint8_t *a, const uint8_t *b, size_t n,
    uint32_t op, uint8_t value,
    const uint64_t *noms, size_t nom_count,
    size_t seed_bytes, size_t extension_bytes,
    run_t *runs, size_t run_cap,
    size_t *out_count, uint64_t *out_compared, uint64_t *out_accepted, uint64_t *out_rejected
) {
    if (!out_count || !out_compared || !out_accepted || !out_rejected ||
        (n && (!a || !b)) || !seed_bytes || !extension_bytes || (op != 1u && op != 2u)) return 2;
    *out_count = 0; *out_compared = 0; *out_accepted = 0; *out_rejected = 0;
    uint64_t covered_until = 0;
    for (size_t ni = 0; ni < nom_count; ++ni) {
        const uint64_t seed = noms[ni];
        if (seed > (uint64_t)n || seed_bytes > (size_t)((uint64_t)n - seed) || seed < covered_until) continue;
        int ok = 0;
        size_t cost = verify_exact(a,b,(size_t)seed,seed_bytes,op,value,&ok);
        *out_compared += cost;
        if (!ok) { ++*out_rejected; continue; }
        uint64_t start = seed, end = seed + seed_bytes;
        while (end < (uint64_t)n) {
            const size_t width = (size_t)(((uint64_t)n-end) < extension_bytes ? ((uint64_t)n-end) : extension_bytes);
            cost = verify_exact(a,b,(size_t)end,width,op,value,&ok);
            *out_compared += cost;
            if (ok) { end += width; continue; }
            end += cost ? (uint64_t)(cost-1u) : 0u;
            break;
        }
        if (end > start) {
            if (*out_count && runs[*out_count-1].start + runs[*out_count-1].length == start) {
                runs[*out_count-1].length += end-start;
            } else {
                if (*out_count >= run_cap) return 3;
                runs[*out_count].start=start; runs[*out_count].length=end-start; ++*out_count;
            }
            covered_until=end;
        }
    }
    for (size_t i=0;i<*out_count;++i) *out_accepted += runs[i].length;
    return 0;
}
'''

class _Run(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint64), ("length", ctypes.c_uint64)]

@lru_cache(maxsize=1)
def _lib():
    d = Path(tempfile.mkdtemp(prefix="cmpct-one-native-proof-"))
    src, so = d / "proof.c", d / "proof.so"
    src.write_text(_C)
    subprocess.run(["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(src), "-o", str(so)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lib = ctypes.CDLL(str(so))
    fn = lib.grow_relation_spans_native
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                   ctypes.c_uint32, ctypes.c_uint8, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
                   ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_Run), ctypes.c_size_t,
                   ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_uint64),
                   ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64)]
    fn.restype = ctypes.c_int
    return lib

_pybytes_as_string = ctypes.pythonapi.PyBytes_AsString
_pybytes_as_string.argtypes = [ctypes.py_object]
_pybytes_as_string.restype = ctypes.c_void_p

def grow_relation_spans_native(parent: bytes, child: bytes, *, op: str, value: int,
                               nominations: tuple[int, ...], seed_bytes: int = 64,
                               extension_bytes: int = 4096) -> RelationGrowthResult:
    if type(parent) is not bytes or type(child) is not bytes or len(parent) != len(child):
        raise ValueError("native relation proof requires equal immutable bytes inputs")
    if op not in {"add8", "xor"} or not 0 <= value <= 255 or seed_bytes <= 0 or extension_bytes <= 0:
        raise ValueError("invalid relation geometry")
    total = len(parent)
    # If the seed itself cannot fit, the Python oracle skips every nomination without reading.
    if seed_bytes > total:
        return RelationGrowthResult((), 0, 0, 0)
    # Match the Python oracle for every representable and non-representable Python int.
    # Any negative or seed > total is guaranteed to be skipped by the oracle, so discard
    # it before the bounded uint64 ABI rather than risking marshaling overflow.
    normalized = {int(x) for x in nominations}
    ordered = tuple(sorted(x for x in normalized if 0 <= x <= total))
    # An extension larger than the finite input is semantically equivalent to `total`:
    # Python takes min(extension_bytes, total-end). Clamp before the bounded size_t ABI.
    native_extension = min(extension_bytes, max(total, 1))
    noms = (ctypes.c_uint64 * max(len(ordered), 1))(*ordered) if ordered else (ctypes.c_uint64 * 1)()
    runs = (_Run * max(len(ordered), 1))()
    count = ctypes.c_size_t(); compared = ctypes.c_uint64(); accepted = ctypes.c_uint64(); rejected = ctypes.c_uint64()
    ap = ctypes.cast(_pybytes_as_string(parent), ctypes.POINTER(ctypes.c_uint8))
    bp = ctypes.cast(_pybytes_as_string(child), ctypes.POINTER(ctypes.c_uint8))
    op_id = 1 if op == "add8" else 2
    rc = _lib().grow_relation_spans_native(ap,bp,len(parent),op_id,value,noms,len(ordered),seed_bytes,native_extension,
                                           runs,max(len(ordered),1),ctypes.byref(count),ctypes.byref(compared),
                                           ctypes.byref(accepted),ctypes.byref(rejected))
    if rc: raise RuntimeError(rc)
    # Match the authoritative Python oracle's representation exactly: runs are plain
    # `(start, length)` tuples, not a native-only wrapper type.
    out = tuple((int(runs[i].start), int(runs[i].length)) for i in range(count.value))
    return RelationGrowthResult(out, int(compared.value), int(accepted.value), int(rejected.value))