"""Reject semantically ambiguous MessagePack maps before index information is consumed.

MessagePack authenticates bytes, not dictionary key-selection semantics. An
attacker can reauthenticate two identical keys with different values. Ordinary
Python msgpack maps keep the last value, while the native rmpv map lookup keeps
the first. Preserve unique-map semantics across the two readers.
"""

from __future__ import annotations


def unique_map_pairs(pairs):
    """Build a map only when every serialized key appears at most once.

    This is intentionally an unpack-time hook: inspecting an already-built
    dict cannot recover overwritten duplicate keys.
    """
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate CMPCT MessagePack index key: {key!r}")
        result[key] = value
    return result
