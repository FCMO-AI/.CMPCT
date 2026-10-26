# O199 — prospective bounded CDC pair-admission falsifier (PR #516)

**Date:** 2026-10-26 UTC. **Status:** FROZEN PREDICTION BEFORE O199 IMPLEMENTATION / RESULT. **Evidence level:** discovery + charged source-exact research proxy only; no product claim.

## Current authority and prior evidence

Source base `agent/phased1-v031-o185-cdc-reader-cache-convergence-20261026@891b818c1135ccc0b938d5bce4b52c6cae56b080`; published v0.30.0 / r24, optional native CDC blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364`. O196/196b proved ordinary wheel/ABBA paths use fixed fallback; O197 proved high-entropy shift reuse but local edits lose; O198 source-exact zlib-6 proxy showed high-entropy shifts +19.05% median vs *gifted best fixed* and mixed-overwrite −50.15%. All O185 official performance reds and O175 cache RSS/warm-scan debt remain binding, unrelated negatives. Neither corpus labels, filenames nor mutation flags may enter prospective admission logic.

## One falsifiable question

Can a **cheap prospective, pair-local, content-only** signal conservatively admit CDC on shifted, poorly compressible related files, while rejecting no-shift, compressible, and unrelated controls, at cost far below the measured potential byte headroom? Pair discovery in a filesystem-scale universe remains unsolved and must not be gifted silently. This experiment assumes only that a *single candidate pair* has been supplied and explicitly charges detector work; it cannot claim generic builder admission or product economics.

## Frozen detector, before looking at held-out results

1. Sample three **64-byte source anchors** at offsets one-quarter, one-half and three-quarters of the original byte length; for each, search for that exact pattern only within **±4096 bytes** of its original offset in the candidate sibling. Count all 3 probes and scanned bytes; no filename, directory, extension, seed, family or mutation identity enters logic.
2. Declare a shifted relationship only if **at least two distinct anchors match, one or more matched anchors has a nonzero displacement, and every nonzero displacement agrees in sign and magnitude**. The detector is deliberately conservative; blind spots near the file tail and offsets >4096 are expected negatives, not exceptions.
3. Independently sample **twelve 4096-byte windows** across the first file at uniformly spread interior locations; compress each with zlib-6. The sum of compressed sizes / sampled input sizes must be **>=0.90** to call the candidate *poorly compressible*. Do not tune this threshold after results.
4. Admit native CDC iff both properties hold; otherwise keep the fixed incumbent. Original fixed256 is the shipping-control proxy. A hindsight min(fixed256,fixed512,fixed1024) is an additional deliberately stronger gifted reference, NOT an implementable free portfolio. Native CDC is the exact owner C implementation, compiled and authenticated.

## Prospective test and strict controls

Use deterministic unseen seeds **711, 712, 713**, not O198 451/452; three structures (high-entropy, repetitive, mixed), three modification positions (byte 1, 1/3, 2/3), edits (overwrite 1 byte, insert 1 byte and trim last byte, insert 256 bytes and trim 256 bytes), plus a near-tail shift and unrelated cross-seed pairs as adversarial controls. At each tested pair, calculate the detector decision **before comparing or calculating policy-specific compressed-chunk economics**. For each scenario charge exact zlib-6 unique chunk payload +64 B/unique record +32 B/logical reference for each of fixed256, fixed512, fixed1024, authentic C CDC. Verify chunk-length bounds and **both exact SHA-256 reconstructions**. Measure detector CPU/wall, window bytes and lookup scan bytes; explicitly note that CPU is one-shot, not official repeated performance evidence, and that pair discovery/index/candidate count is missing.

## Predictions and disproof

- The gate rejects all unshifted overwrites and all unrelated controls; **one false positive invalidates the conservative claim**.
- It rejects compressed repetitive/mixed variants in most shifted cases but should admit a material share (>=50%) of high-entropy shifted pairs of <=256-byte displacement.
- On admitted high-entropy shifted pairs, median source-exact charged CDC savings versus hindsight strongest fixed control are predicted **positive**; any material negative admitted result is a counterexample to simple safe admission.
- It should reduce false positive storage cost versus unconditional native CDC across all tested regimes. If not, retire this simple detector; do not garden thresholds or relabel data.
- Cost criterion is directional only: detector time and bytes must be reported and compared against possible headroom, not converted to fictitious final archive credit. Scan costs and cross-file discovery are not paid in full here; passing tests cannot authorize general product admission.

## Alternatives and BONK

A simple compressibility-only gate cannot distinguish high-entropy overwrite from shift (O198); shift-only loses on compressed siblings (O198); exhaustive dual-encoding of every pair is a costly gifted oracle. A bounded shift+compressibility gate is cheaper, reversible, and can be falsified by unrelated and structural-hostile data before any Builder/Reader changes. Failure must return to representation/search ownership or retire this route rather than adding more case-specific exceptions.

## Concurrency and publication

Stay on existing owner Draft #516, reread its head before late writes, preserve prior O198 source and all frozen comparators unchanged, avoid touching `docs/discovery/STATE.json` (staleable shared cache). Keep exact-head instrument, raw JSON, native source identity and disproof in hosted CI when possible. New research artifacts are public synthetic only. No merge, version, format or release mutation.
