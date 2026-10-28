"""Optional CPython stable-ABI S_CHUNKS positive-only admission.

This is a performance accelerator, NOT an alternate format validator. An absent,
incompatible, malfunctioning or negative native predicate must call the original
strict Python per-file validation in CMPCT.__init__. Never bypass structural
checks on another storage kind, path, archive record or physical owner.
"""
from __future__ import annotations

try:
    from ._fastscan_abi3 import scan_refs as _scan_refs
except Exception:
    # Package must remain usable without a C compiler, on Python <3.11,
    # and whenever an optional native wheel cannot be loaded.
    _scan_refs = None


def native_chunk_ok(storage, blobs, size) -> bool:
    """True only for a fully native-proven exact built-in fixed-chunk map."""
    scanner = _scan_refs
    if scanner is None or type(storage) is not list or len(storage) != 2 or type(storage[1]) is not list:
        return False
    try:
        return scanner(storage[1], blobs, size) is True
    except Exception:
        # A native failure must never make an untrusted archive admissible.
        return False

# Separate from admission: this witness only accelerates selective reads AFTER
# the original strict/native positive-only constructor validation.
try:
    from ._fastscan_abi3 import uniform_stride as _uniform_stride
except Exception:
    _uniform_stride = None


def native_uniform_stride(storage, blobs, size) -> int:
    """Return exact positive uniform-prefix chunk size or 0 for safe fallback."""
    proof = _uniform_stride
    if (proof is None or type(storage) is not list or len(storage) != 2
            or type(storage[1]) is not list or type(size) is not int):
        return 0
    try:
        witness = proof(storage[1], blobs, size)
        if type(witness) is not int or witness <= 0 or witness > size:
            return 0
        refs = storage[1]
        if not refs or type(refs[-1]) is not int:
            return 0
        last = blobs[refs[-1]][1]
        # Independent constant-time arithmetic check on a positive C witness.
        if (type(last) is not int or last <= 0 or last > witness
                or witness * (len(refs) - 1) + last != size):
            return 0
        return witness
    except Exception:
        return 0
