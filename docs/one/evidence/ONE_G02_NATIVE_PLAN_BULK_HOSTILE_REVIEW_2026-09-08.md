# ONE-G0.2 Native Plan Bulk — hostile review before result

Status: preregistered; no hosted performance verdict yet.

The candidate is intentionally causal: Python ref slicing remains, generic Plan work accounting remains, root hashing remains, and only XOR/add8 byte arithmetic changes implementation. Therefore a large arithmetic win cannot be credited to eliminating graph validation, slice copies or integrity work.

The first implementation source `8d7a2b6315b861db0faa845992f543f0e8b96257` introduced the workflow but produced no dedicated result lane. Before forcing a result, hostile review added an explicit fail-closed check for unknown internal bulk operations. That source is not used as performance authority; the next descendant containing this check is the admissible lineage. No threshold or matrix criterion changed.

Hostile checks include all six generic families, embedded NUL bytes through the ctypes pointer boundary, modulo-256 add8 wraparound, unknown operation rejection, bad operand widths/counts, bad root authentication, exact matrix identity and threshold-edge tests.

Strongest surviving objection: `ctypes.c_char_p` is a CPython-oriented research boundary, not a portability decision. A green result proves the value of a native/SIMD-friendly bulk data plane, not this exact binding. A canonical reader should expose an ordinary portable contiguous-byte view to a compiled kernel.

Second objection: this experiment deliberately preserves Python slice materialization, so it may understate the eventual bulk opportunity and does not claim memory-traffic reduction. If arithmetic advances, a later experiment may test operand views/direct offsets separately; that work must be independently preregistered rather than folded into this result.

Third objection: runtime C compilation is warmed outside the timer. This is acceptable only because the claim is hot data-plane execution; production code would ship compiled. Startup/build-system/portability costs remain unclaimed.

A green result does not authorize a hidden codec zoo: XOR/add8 are already part of the minimal ONE grammar and the same generic plan remains authoritative.