# ONE-G0.2 relation root fusion — pre-result hostile review

Date: 2026-09-08
Research version: ONE-G0.2

## Hostile reviewer findings

1. **No hidden codec.** The candidate receives the exact existing Program built by the relation-granularity frontier. `add8`, `xor`, `fill`, `surprise` and `concat` retain their existing semantics. The sink is an execution lowering only.
2. **Full validation remains mandatory.** Reference preflight runs before fusion and validates unreachable stored nodes as well as reachable ones. Unsupported reachable geometry fails closed.
3. **Fill is virtual, not free.** Its byte value is encoded in the unchanged node/control stream. The fused executor avoids materializing a block-sized repeated operand, but relation arithmetic is still charged per derived byte.
4. **Translation is bounded implementation machinery.** `bytes.translate` creates one relation-block temporary. Peak temporary accounting includes that block. It may not be described as zero-copy.
5. **Program immutability is checked.** The benchmark verifies the candidate object is unchanged by fusion; wire-density claims remain inherited from the exact frontier, not recomputed under a different encoding.
6. **Timing cannot rescue semantics/accounting.** Any semantic/root mismatch or matrix defect invalidates before performance is considered.
7. **A scoped ADVANCE is not a system win.** The promotion bar allows up to 1.50x literal because this experiment isolates whether 2.33x/2.5x geometry can be removed. The report must separately disclose whether the stronger <=1.05x literal target is met.
8. **No relation-only future by default.** If this succeeds only by exploiting a terminal constant relation shape and does not generalize to other Law cones, the next step is not more special cases; the research must move to a general bounded reconstruction compiler.
9. **Python/C implementation caveat.** `bytes.translate` is CPython-native bulk work, not a portability decision. A green result proves an execution opportunity, not a required runtime backend.
10. **No comparator movement.** v0.29/deferred-v0.30 authority and the September 11 gate do not move from this experiment.
