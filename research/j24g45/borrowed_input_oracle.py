#!/usr/bin/env python3
"""Independent Python ctypes source-pointer cost/identity oracle (not CMPCT product proof).

Run with `python research/j24g45/borrowed_input_oracle.py OUTPUT.json`. Public
synthetic immutable bytes; no user archive or large filesystem materialization.
"""
from __future__ import annotations

import ctypes
import gc
import hashlib
import json
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path


def measure(name: str, payload: bytes) -> dict:
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    obj = ctypes.c_char_p(payload) if name == "borrow" else ctypes.create_string_buffer(payload)
    cpu_ns = time.process_time_ns() - c0
    wall_ns = time.perf_counter_ns() - t0
    alloc_bytes = tracemalloc.get_traced_memory()[1]
    ptr = ctypes.cast(obj, ctypes.c_void_p).value
    assert ptr and ctypes.string_at(ptr, 256) == payload[:256]
    if name == "borrow" and platform.python_implementation() == "CPython":
        assert obj._objects is payload
        c_fn = ctypes.pythonapi.PyBytes_AsString
        c_fn.argtypes = [ctypes.py_object]
        c_fn.restype = ctypes.c_void_p
        assert ptr == c_fn(payload), "ctypes pointer unexpectedly differs from source bytes"
    del obj
    tracemalloc.stop()
    return {"mode": name, "peak_traced_allocation_bytes": alloc_bytes,
            "wall_ns": wall_ns, "cpu_ns": cpu_ns}


def main() -> int:
    data = bytes(range(256)) * 65536  # 16 MiB and plenty of NUL bytes
    assert len(data) == 16 * 1024 * 1024
    rows = [measure(name, data) for name in ("copy", "borrow", "borrow", "copy") * 4]
    def med(field: str, mode: str) -> float:
        return statistics.median(x[field] for x in rows if x["mode"] == mode)
    gap = med("peak_traced_allocation_bytes", "copy") - med("peak_traced_allocation_bytes", "borrow")
    assert gap >= 8 * 1024 * 1024, "no-copy mechanism did not avoid substantial allocation"
    result = {"schema": "cmpct-j24g45-standalone-borrowed-input-v1",
              "scope": "isolated CPython/ctypes source construction, not installed CMPCT RSS",
              "platform": platform.platform(), "python": sys.version,
              "implementation": platform.python_implementation(),
              "source_sha256": hashlib.sha256(data).hexdigest(),
              "source_size_bytes": len(data), "source_contains_nul": True,
              "traced_allocation_median_reduction_bytes": gap,
              "copy_wall_median_ns": med("wall_ns", "copy"),
              "borrow_wall_median_ns": med("wall_ns", "borrow"),
              "copy_cpu_median_ns": med("cpu_ns", "copy"),
              "borrow_cpu_median_ns": med("cpu_ns", "borrow"),
              "raw_samples": rows}
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "raw_samples"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
