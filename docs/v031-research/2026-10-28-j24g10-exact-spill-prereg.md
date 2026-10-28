# J24G10 preregistration — exact disk-backed invalid-footer proof for arbitrary spacing
Date: 2026-10-28 UTC
Status: FROZEN PREDICTION BEFORE PRODUCT SOURCE EDIT. DRAFT SCIENCE / NO MERGE OR RELEASE.

## Source and scope
Parent: PR #661 at `11963e53947829ce141e9910fdd4adf0d866fb5f`, Reader blob `ec0335268d0486e41b460f14b1a3543b7cb1a589`. Published `main` remains v0.30.0 / revision 24. This is an independent experiment on a dependency-safe child branch; do not change the PR #661 owner branch or frozen instruments. No concurrency protocol is present at this base path. Question: can a **lazy disk-backed exact position set** eliminate above-cap replay for *non-arithmetic* signed orphan-footer ancestry without assuming any relationship between physical offsets?

## Grounded baseline
- PR #650 16,400 signed linked orphans: 278,665 genuine decode attempts above 16,384-set capacity; old checkpoint recovered.
- PR #661 exact arithmetic-run proof: 16,401 decode calls on regular spacing, but **278,665** on alternating-size same N. A max-16,384 Python set cannot prove arbitrary larger invalid-position sets. PR #658 forbids replacing recovery with a chain-depth abort.
- Preliminary detached 16,400-key micro (not product evidence): ordinary set build/check medians ~1.4/2.3ms; SQLite FILE proof build/check ~18.3/38.9ms; ~155,648B physical DB. This estimates a viable overhead but excludes actual SHA/decode/memory/IO and can be overturned by hosted product evidence.

## Hypothesis, controls, alternative
Hypothesis: once an authentic invalid ancestry has been individually observed and fully failed, retaining its **exact** integer footer positions in a temporary SQLite B-tree (stdlib, lazily imported) allows all later candidate positions to be rejected safely, regardless of spacing. Keep in-memory set <=16,384; use existing AP certificate first for perfect AP chains; spill ONLY otherwise. Compare exact unchanged #661 source on *identical* genuine Builder + signed generated tail, and the stronger simpler control of an unbounded ordinary Python set (research oracle, not shipping). The latter may dominate SQLite in elapsed wall; disk is only justified for bounded proof-store memory and accounted temp I/O.

## Prospective court (cheapest honest evidence)
1. Paired same-process real installed Reader A/B on 16,400 SHA-valid orphan footers with alternate 81/82-byte spacing. Predict original 278,665 decoder invocations versus candidate exactly 16,401, checkpoint/bytes/range/verify unchanged. Repeat >=3, alternate run order, preserve raw CPU and wall.
2. Held-out nonperiodic deterministic irregular spacing with the same N, plus uniform AP positive, flat independent signed footer, same-size no-magic bytes, and actual first-party `append_rename`. No false positives and no newly accepted footers.
3. Standalone exact membership oracle: 30,000+ arbitrary positions including collisions, out-of-range and neighboring offsets; 0 false positives, 0 false negatives; temp proof DB physically deleted by close; track file bytes and transient process/trace memory separately.
4. Investigate original vs candidate and unbounded set with source SHA / Git blob tied to HEAD. No historical comparators rewritten; no dropped negative.

## Kill / narrow criteria
- Any wrong checkpoint, logical content, SHA, read_range, verify, valid Writer transaction, or exact set membership **kills** this implementation.
- If irregular N=16,400 does not fall to <=16,450 genuine decoder calls, reject the mechanism.
- If flat and valid-case median wall slows >25%, reject as broadly uneconomic, even if hostile speed wins.
- If temp storage exceeds 32 bytes per retained position at N=16,400, revisit B-tree or compression choice; distinguish allocator/temp/SQLite page overhead.
- If same-host spill cost approaches or exceeds the old replay cost, retire this route. If unbounded set dominates material economics and RAM is acceptable, preserve external spill only as a capacity-policy option.
- Python stdlib SQLite availability, I/O errors, tempdir permissions, cleanup and concurrency/mutable-source contract are release debts. This test cannot claim global bounded RSS because the inherited per-chain `seen` / `chain` still grow with chain length; it bounds only the **cross-candidate proof store**.

## Distinct alternatives and BONK
Simpler unbounded set pays memory proportional to seen offsets; exact AP seed is already proven but fails alternating; increasing the cap only moves a discontinuity; probabilistic Bloom admission risks skipping legitimate authenticated footers; #365 early abort changes fallback selection; recursive decode without cross-candidate negative proof is superlinear. Disk index is different ownership of proof storage, not another AP threshold.
No number of green tests authorizes promotion; require separately bounded per-chain memory, source-snapshot contract, OS portability, same-runner full economics and inherited gate parity before any merge/release. Independent proof/custody remains mandatory. No discovery policy edit earned by a single result.

## Decision to record after hosted evidence
Select: viable bounded-memory proof-store seed, disproved/uncompetitive, or ambiguous. Preserve exact measured negatives and name the cheapest next path, such as external proof + streaming ancestry or an explicit bounded recovery semantics proposal.