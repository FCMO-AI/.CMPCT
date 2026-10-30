# J24G90 — Terminal checkpoint versus replay-prefix source-alignment court

**Date:** 2026-10-30 UTC. **Prospective, BEFORE instrument/workflow.** Research only; no product change, format/version promotion, baseline/comparator weakening, or implicit release authority.

## Exact starting authority and non-overlap
Parent: CMPCT PR #845 at exact `4c54979abd86a051354c4b8e941a0ac697861e8f`; published `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0 / r24. Reader Git blob on published main `e716233403dabd0966863c45635e18fa5ac6afb8`. The existing J24G89 O0 explicitly audits 63 DELETE generations from original physical 65-footer J24G83 sources, whose *newest generation is itself a complete checkpoint*. It already disclaims an actual Reader benchmark. This experiment does not overwrite J24G89 or any #823 owned Reader implementation.

## One primary question
How does a genuine revision-24 Reader's *actual latest-generation selection* change complete open CPU/wall when it can use a newest fully signed checkpoint, compared with exactly the same logical index reached by replaying 63 individually signed operations? Can tampering the checkpoint footer force the intended identical-state fallback without selecting an inconsistent index?

## Mechanism and controls
Build a deterministic 4,096- and 8,192-member ordinary CMPCT archive using source-exact public Builder; apply 63 distinct public append_delete operations. The physical prefix A ends at signed generation 63 (63 deltas). Construct B by appending the same authenticated in-memory index as a zero-logical-change full checkpoint via existing `_append_generation` (research-only valid r24 grammar, not a normal public mutation). B is A plus a bona fide signed checkpoint and **has identical logical files/content**. Construct C by corrupting only the last checkpoint footer hash; Reader must recover generation 63, equal to A. Open A/B/C by the released Reader with balanced warm repeated measurements. Verify A/B/C path/row equality, sample content equality, archive index digest equality and exact `delta_depth` (63/0/63); verify complete physical byte sizes, repeated raw wall/CPU timings and checkpoint bytes. Make no claim for an alternative v0.31 Reader.

## Prospective prediction and kill/narrow condition
Hypothesis H1: B's source-exact median ordinary Reader open wall is at least 2x faster than A in both sizes (and no slower on CPU), while checkpoint's full bytes are charged. H2: C recovers A's exact index and open depth 63. A negative or ambiguous H1 is recorded, not retuned; any A/B/C inconsistency or failed recoverability is a hard correctness red. A measured baseline Reader win is **not** product evidence for a proposed ordinal checkpoint: it may have much higher stored-byte cost, and the existing #823 owned Reader may already make replay cheap. A no-op checkpoint makes this an isolation court, not a shipping performance test.

## Stronger simpler control and alternative explanation
The plain A state is the real public default; B is existing format, no new ordinal grammar. The prior #845 offline simulation compares a hypothetical depth-63 replay budget but its input file ends at full generation64; it is not the timing of a latest-full-checkpoint open. A/B/C controls distinguish current terminal materialization from corruption fallback. Alternative explanation: opening a larger B incurs enough SHA/decompress/index cost that savings are small; changing host filesystem cache or generation depth can induce apparent wall effects, hence balanced orders, CPU and raw samples.

## Evidence rung and exported costs
Cheap hosted source-exact Reader court (no official release matrix). Use original source, source-checkout hash, immutable prereg ancestry, deterministic tree inputs, signed r24 produced by actual Writer, measured full stored bytes, 2 sizes, balanced orders, complete raw sample receipts, independent structural oracle where feasible. No changes to format, benchmark thresholds, Writer semantics or release gate. RSS, recovery adversary variety, three-platform portability, concurrent Writes and v0.31 Owned Reader remain unmeasured unless actually executed.

## Decision unlocked
Distinguish three temporally different claims: replay cost at depth63, healthy newest-full-checkpoint open at depth0, and degraded recovery-to-depth63 cost. If H1 survives, a valid checkpoint is economically meaningful to *released* Reader but must still pass byte budget/other Reader alternatives before productization. If not, prioritize authentication/index allocation and retire unsupported replay-only broad claims. Share findings with #845/#823 without replacing their scientific evidence.
