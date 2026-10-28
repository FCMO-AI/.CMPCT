# J24C22 — full physical-owner working-set falsifier (prospective, FROZEN BEFORE INSTRUMENT)

**Status: SCIENTIFIC PREREGISTRATION ONLY; no product/format/version/release credit.** 2026-10-28 UTC. Evidence-only child of J24C21 PR #687 at exact `249ff35aac5bb04924b439dd3e042cc067bc6bc1`. This file is the frozen question and acceptance criteria, written before any J24C22 instrument. Previous J24C21 source/results remain unchanged and are historical controls; do not retrospectively relabel its Q32 work as full physical decode.

## One precise question

Does the sealed checkpoint Reader #676 retain material **complete-session** speedup over actual published v0.30.0 when each workload necessarily reads all 4,096 unique 4KiB physical owners (16MiB) from an authentic signed revision-24 archive, instead of the 18–32 distinct owners previously sampled by J24C21's spaced Q6/Q32?

## Source-exact baseline and concurrency

- Published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / r24. Strongest simpler real-product control.
- Unsafe original fused #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`; timing control *only*, J24C16 mutable-cache wrong-byte remains disqualifying.
- Sealed #676 `3b6a73f9205f40f11124cd9ff332407e52cebb93`; fixes that specific mutable-reference counterexample but adds +13–24% versus #662 in source-locked tests and may alter public list API.
- J24C21 #687 `249ff35aac5bb04924b439dd3e042cc067bc6bc1`, including its exact signed `large_distinct_8k.cmpct` fixture SHA-256 `eb695e0236db6d8d7e7896fcc8d3a2b69a47a66f601e47c8c333879176f58067` (stored 17,072,796 bytes; 8,192 refs; 4,096 4KiB distinct owners; 32MiB logical). **Reuse its original generator and archive bytes.** No modified physical inputs or Reader source.
- Existing PRs #662/#676 own Reader implementations, #574 owns shared discovery state, #690 owns signed-negative extraction budget, #255/#270/#573 own sparse extraction, #691 owns MessagePack projection; this PR modifies only its own new research, workflow and result files. No competing implementation.

## Mechanism and alternative explanation

J24C21 demonstrated Q32 selectivity gain versus the released Reader but found only 32/4,096 unique owners touched (128KiB) despite 16MiB stored. At full physical touch, payload materialization and I/O may dominate fixed-chunk descriptor traversal; savings could vanish or reverse. The opposite mechanism hypothesis is that repeated O(N) Python prefix walks in the published Reader still cost enough to justify fused checkpoint indexing when many large window reads amortize admission. **The result may legitimately favor baseline.**

## Fixed held-out workloads

Use the **same physical archive** `large_distinct_8k.cmpct` and single shared signed manifest from #687 (generate once, never per arm). Owner function is SHAKE256(`b"CMPCT-J24C21-owner-"` + 4-byte-big-endian ID) producing 4096-byte physical owners; refs map `(i*2053+17)%4096`. Because gcd(2053,4096)=1, any consecutive 4,096 references touch each of the 4,096 distinct owner IDs exactly once. Two complementary full-owner cases:

- `Q16_front_full`: 16 consecutive **nonoverlapping** 1MiB ranges at offsets `i*1048576`, i=0..15; exactly 16MiB returned, every unique physical owner visited once.
- `Q16_tail_full`: 16 consecutive nonoverlapping 1MiB ranges at offsets `16777216+i*1048576`, i=0..15; again all 4,096 unique physical owners visited once, but starting from the latter half of the reference index (more prefix-walk work in the released Reader).
- `Q1_early` inherited control from J24C21 unchanged (one early 8KiB range), explicitly separate from full-sweep cases.

**Both full cases must be complete**; absence, truncation, duplicates, changed owner-visit coverage or changed archive/Reader SHA invalidates the court, never a negative performance decision. The sealed Reader's admitted reference mapping is unchanged from its source. All answers are byte-exact oracle SHA-256 verified. Materialized logical bytes = 16MiB per Q16 case. Unique physical payload = 16MiB (though filesystem/page cache and repeated runs mean this is not measured actual disk I/O).

## Execution and measurements

Use installed wheels built separately from exact published, fused and sealed sources in isolated CPython 3.11 environments on one Ubuntu 24.04 runner. One shared unsigned-manifest-independent archive SHA and original J24C21 signed manifest. Six fresh subprocess repetitions per arm/shape, balanced permutations; 54 source-verified session observations. Precompute expected SHA-256 outside timed sessions; check file/manifest hashes outside timed sessions; in timed Reader session measure open/list/read/close and full session wall/CPU; observe peak RSS where supported, total returned bytes, process startup/outer wall separately, and wheel bytes if available. Preserve raw per-process readings, not only medians. Independent referee must reconstruct 4,096 SHAKE owners and query answers without importing CMPCT, check both 16MiB owner coverage sets, verify source/installed-reader fingerprints and original signed archive identity, and reject tampered receipts.

## Prospective decision law (scientific only)

- **PASS research transfer** for each full Q16 case separately only if median sealed session improves over published by **both >=5% AND >=3ms**, in both in-process wall **and** CPU. Failure = NO_MATERIAL_FULL_OWNER_TRANSFER on that case, even when Q32 historical speedup was real.
- **Q1 veto** remains separate: sealed Q1 on same fixture >=5% and >=3ms slower in wall or CPU is a promotion blocker; no averaging Q1 with Q16.
- Record any sealed-vs-published RSS increase >8 MiB (unavailable/unreliable RSS is unknown, not zero); record physical archive bytes/owners and exact output volume.
- Repeat-level sign inconsistencies should be disclosed even if medians pass. If runner budget is exhausted, results remain unmeasured; do not fabricate speedups from analytical reference counts.
- Different hostile-input admission guarantees make this valid-signed-input *economics*, not universal security-equivalent product proof. No complete create/extract benchmark, CDC, Zstd, recovery, Windows/macOS or publication claim.

## BONK / independent evidence / next fork

The cheapest strong discriminator is to reuse the already signed J24C21 source-identical archive and Reader installations with workloads that cover all owners, not implement another list/tuple conversion or build new codecs. A strong product loss here narrows/retire any claim of broad physical-decode gain from the checkpoint family, without erasing selective Q32 gains; prioritize #690 correctness or other unclaimed product debt. If full-sweep passes, the next essential gate is a true larger-physical contiguous/cold/codec workload plus correctness and API admission; Q1 may still veto promotion. No discovery policy edit from one falsifier. Keep the expected result open until exact-head artifact/referee exists.

## Counterfactual test planned

An owner-working-set cardinality calculation before J24C21's complete CI would have revealed the structural gap sooner: fixed query strides can alias a permutation. It was prospectively recognizable from ref mapping + selected positions. Record only this scoped lesson, without modifying scientific policy, thresholds, frozen results or shared discovery state.
