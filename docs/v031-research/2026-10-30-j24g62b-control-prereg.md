# J24G62b — Prospective matched-ownership control for the replay-only speed result

Date: 2026-10-30 UTC. **New test, registered after J24G62 original hosted results. Preserve that earlier evidence exactly.** Current source HEAD before change: `b1167960195eed84028ef629668fe7b367710080`. Previously observed J24G62 exact-head evidence `e3948f6dee571b7b682f72ae5016caf4b6e95d83` and GitHub Actions #41001063304 (5.587× Ubuntu, 7.369× macOS, 5.170× Windows) remain unchanged as first observation, not silently retroactively corrected.

## New control question
J24G62 original comparison uses a `copy.deepcopy` of each journal operation list **inside its original-helper loop**, whereas production Reader on actual MessagePack-decoded rename lists calls the helper directly without making those per-operation copies. For 63 one-op *rename-only* deltas (strings only), the original helper is read-only with respect to the deltas. This research-only extra allocation in the baseline may slightly inflate estimated speedup. We must measure the stronger simpler comparison before spending product engineering cost.

## Predicted result and kill
Introduce a **separate reference** `original_replay_physical_no_op_copy` that deeply copies the base index once, but passes each genuine physical rename operation list to `_apply_journal_ops` directly (as Reader does). Leave the original baseline and all 2,200 mixed/adversarial tests untouched: mixed `put` row aliases can otherwise mutate op inputs, so they require defensive copies to preserve their original differential semantics. Benchmark the no-op-copy reference A/B/B/A against exactly the same factored function, 8 blocks, all original source pins, three hosts. Store 32 new raw observations per host and compare with earlier historical J24G62, not overwrite its receipt.

**Positive** if real physical final-index identity, source attestation and all original safety tests pass and new baseline vs candidate still >=3×, with memory overhead <=2 MiB traced Python peak. **Falsify/narrow** if no-op-copy control materially changes result or fast method loses, or any original input is modified, or the supposedly pure renaming operation mutates its decoded ops; preserve negatives. Do not change old prereg thresholds to rescue a claim.

## Scope and nonclaims
No product file, on-disk format, Writer/Reader, release manifest, frozen comparator or performance release threshold changes. This is a **separate post-result research stratum** to repair possible measurement bias. No inference about total Reader cold-open, physical RSS, sparse fsmeta, mixed put/delete operations, recovery or final release. Original #804 result and all artifact IDs remain immutable source-bound history. #795 retains generalized product ownership.
