"""Admissible zero-copy wrapper for ONE-G0.2 relation writer envelope V3.

Preserves the corrected three-pair C triplet gate, but obtains read-only pointers to the
existing Python bytes buffers without copying whole versions before the sparse probe.
"""
from __future__ import annotations

import ctypes
import benchmarks.one.one_g02_relation_writer_envelope_v3_corrected as corrected
import benchmarks.one.one_g02_relation_writer_envelope_v3 as v3

_pybytes_as_string = ctypes.pythonapi.PyBytes_AsString
_pybytes_as_string.argtypes = [ctypes.py_object]
_pybytes_as_string.restype = ctypes.c_void_p


def _gate_nocopy(source: bytes, target: bytes):
    if not isinstance(source, bytes) or not isinstance(target, bytes):
        raise TypeError("V3 zero-copy gate requires immutable bytes")
    if len(source) != len(target):
        raise ValueError("paired versions must have equal length")
    n = len(source)
    out = v3.GateOut()
    ap = ctypes.cast(_pybytes_as_string(source), ctypes.POINTER(ctypes.c_uint8))
    bp = ctypes.cast(_pybytes_as_string(target), ctypes.POINTER(ctypes.c_uint8))
    rc = v3._gate_lib().paired_triplet_gate(ap, bp, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(rc)
    op = "add8" if out.op == 1 else "xor" if out.op == 2 else None
    return op, (int(out.value) if op else None), out


# corrected import has already installed the charged l0=0 C kernel.
v3._gate = _gate_nocopy

if __name__ == "__main__":
    raise SystemExit(v3.run())
