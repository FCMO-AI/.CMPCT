"""Independent hostile resource-bound probe for the shared native ONE0 writer."""
from __future__ import annotations

import ctypes
from hashlib import sha256

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import Segment
from benchmarks.one.one_g02_shared_native_writer_transfer import _build_writer_native, _digest_array


def run() -> None:
    fn, free_fn, td = _build_writer_native()
    try:
        n = 4096
        source = bytes((i * 17 + 3) & 0xFF for i in range(n))
        target = bytes((i * 29 + 7) & 0xFF for i in range(n))
        src = (ctypes.c_uint8 * n).from_buffer_copy(source)
        dst = (ctypes.c_uint8 * n).from_buffer_copy(target)
        segs = (Segment * n)()
        for i in range(n):
            segs[i].kind = 1
            segs[i].start = i
            segs[i].length = 1
        pd = _digest_array(sha256(source).hexdigest())
        cd = _digest_array(sha256(target).hexdigest())
        out = ctypes.POINTER(ctypes.c_uint8)()
        olen = ctypes.c_size_t(); surprise = ctypes.c_size_t(); alloc = ctypes.c_size_t()
        depth = ctypes.c_size_t(); nodes = ctypes.c_size_t()
        rc = fn(src, n, dst, n, segs, n, pd, cd, 1,
                ctypes.byref(out), ctypes.byref(olen), ctypes.byref(surprise),
                ctypes.byref(alloc), ctypes.byref(depth), ctypes.byref(nodes))
        if rc == 0:
            free_fn(out)
            raise AssertionError("native writer accepted a program exceeding max_nodes")
        if rc != -12:
            raise AssertionError(f"expected max_nodes rejection -12, got {rc}")
        print("shared-native-writer hostile max_nodes probe: PASS")
    finally:
        td.cleanup()


if __name__ == "__main__":
    run()
