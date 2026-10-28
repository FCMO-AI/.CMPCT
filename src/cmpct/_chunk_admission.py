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
