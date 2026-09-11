# ONE-G0.2 interval packed authenticated-range proof — pre-result hostile review

Date: 2026-09-08
Status: pre-result; thresholds frozen
Experimental version: `ONE-G0.2`

## Mission / causal claim

The prior packed proof is a preserved HOLD. This candidate does not move a leaf threshold or switch algorithms by request size. It removes one specific source of Python control work: selected nodes are a contiguous interval, so scanning/materializing selected and needed `set`s at every binary-tree level is unnecessary. Only interval boundaries can introduce sibling hashes.

## Correctness argument checked before timing

For selected leaf interval `[lo,hi]`:

- if `lo` is odd, `lo-1` is the sole missing sibling on the left;
- if `hi` is even and `hi+1 < width`, `hi+1` is the sole missing sibling on the right;
- every interior node's sibling is also selected, so it cannot enter the proof;
- after moving to parents, the selected ancestor interval is exactly `[lo//2,hi//2]` and remains contiguous.

Left-boundary index is always below the right boundary, preserving the reference's sorted sibling ordering. Odd final widths naturally suppress a non-existent right sibling.

Unit coverage includes empty requests, request-at-end, leaf-boundary crossings, odd source/tree widths, large multi-leaf ranges, exact equality against `prove_range()`, and verification against the native root.

## Hostile findings / claim limits

1. **The old HOLD remains authority for the old candidate.** Changing implementation after a negative does not rewrite its result. This is a separate preregistered rehabilitation attempt with a stricter 14/16 decisive non-regression bar.
2. **No size-gated fallback is permitted.** The candidate must stand on all frozen requests. A post-hoc 'use packed only for 64 KiB' policy would require another experiment and, if it needed a materialized Python tree for small reads, could defeat the packed-state memory goal.
3. **Payload slicing remains identical high-level work.** The candidate still materializes one Python payload object per selected leaf because `RangeProof` semantics are unchanged. A HOLD after removing set traversal would point toward this payload-object boundary or digest slicing rather than justify more threshold tuning.
4. **Tree construction remains outside timing symmetrically.** The native creation win cannot hide proof latency.
5. **Digest traffic remains exact.** One 32-byte packed digest is read per emitted sibling; selected leaf hashes are not read because verification recomputes them from payloads.
6. **No full-tree expansion.** Candidate proof generation must not call `levels()`.
7. **No verification claim.** `verify_range()` is correctness-only here. Its hash/object construction can become a separate speed owner later.
8. **No canonical format claim.** Packed memory layout remains a research sidecar shape; disk placement, crash recovery, portability and remote-I/O behavior are separate gates.
9. **Pre-fix interval timings are inadmissible.** Review found that `_paired()` retained the prior arm's `RangeProof` in the local `result` name and then replaced that object only after the next arm's clocks had started. Its destruction could therefore be charged to the following arm. The repair at `7dd6d9c9862b48310efe8d0d3b095820bd958336` clears the owning reference before either wall or CPU timing begins and keeps the new result alive until both clocks stop. This is especially material because the claimed small-read signal is only a few percent. No semantic code, workload, repetition count, or decision threshold changed. Any interval-proof timing produced from a source before that repair must not influence promotion.
10. **Matrix cardinality alone was insufficient.** The first adjudicator checked 32 rows and 16/16 scale counts but did not prove that every `(size, leaf_bytes, start, length)` cell was unique and present. A duplicate row could theoretically hide a missing cell while preserving counts. The hardened decision at `14c7fa48643e01c75da8c1e4750b8c4d22958d24` compares the observed key set with the exact frozen matrix, and `0dff093f20b5e63241bd59f29b52a5943cd4870e` adds the hostile duplicate-row regression test. Thresholds and the candidate mechanism remain unchanged.

## Frozen interpretation

- `ADVANCE_INTERVAL_PACKED_AUTH_PROOF`: interval arithmetic removes the prior broad small-read regression strongly enough to keep packed sidecar proof generation broadly non-regressing under the stricter gate.
- `HOLD_INTERVAL_PACKED_AUTH_PROOF`: preserve the causal negative; stop polishing the same Python proof traversal and move the next attempt to a genuinely different boundary (native/batched proof extraction, payload-view representation, or integrated selective-open measurement).
- `INVALIDATE_INTERVAL_PACKED_AUTH_PROOF`: semantics, matrix or digest-traffic contract failed.
