#!/usr/bin/env python3
"""Minimal pure-Python J24C16 math discriminator; no CMPCT or archive imports.

Lower evidence rung than research/j24c16_installed_mutable_hint_court.py.
This only demonstrates how a frozen prefix list can become stale after a
caller changes publicly mutable in-memory chunk references.
"""
from bisect import bisect_right

owners = (b"A", b"BB", b"")
refs = [1] + [0] * 255 + [2] + [0] * 255
assert len(refs) == 512
signed_bytes = b"".join(owners[j] for j in refs)
assert len(signed_bytes) == 512
marks = tuple(sum(len(owners[r]) for r in refs[:i]) for i in (0, 256))
assert marks == (0, 257)
refs[0], refs[256] = refs[256], refs[0]
live_bytes = b"".join(owners[j] for j in refs)
assert len(live_bytes) == 512
assert sum(len(owners[j]) for j in refs[:256]) == 255

def select(start, length, prefixes):
    stop = start + length
    if prefixes:
        position = bisect_right(prefixes, start) - 1
        i = position * 256
        prefix = prefixes[position]
    else:
        i = 0
        prefix = 0
    parts = []
    while i < len(refs):
        payload = owners[refs[i]]
        end = prefix + len(payload)
        if end > start and prefix < stop:
            parts.append(payload[max(start, prefix)-prefix:min(stop, end)-prefix])
        prefix = end
        i += 1
        if prefix >= stop:
            break
    return b"".join(parts)

assert live_bytes[257:258] == b"A"
assert select(257, 1, ()) == b"A"
assert select(257, 1, marks) == b"B"
print("J24C16_NO_CMPCT_MODEL_PASS signed_size=512 cached_prefix=257 true_prefix=255 expected=A stale=B")
