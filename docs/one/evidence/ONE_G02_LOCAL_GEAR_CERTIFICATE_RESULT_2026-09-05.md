# ONE-G0.2 local Gear certificate repair — result

**Status:** ADVANCE structural evidence; native fused-cost debt remains open  
**Source:** `0b5b60a651a909fa9bdc3aff90dbfdd45073ed23`  
**Workflow:** `ONE-G0.2 local Gear certificate validation` run `33969862974`  
**Job:** `101316332877`  
**Artifact:** `9970590436`  
**Artifact ZIP SHA-256:** `63727f8c264bc86933367ce8107aa10a1a85a1daa675ea9344ee5c6ab5f4a07e`

## Referee question

The immediately preceding shared-observer-only experiment was falsified by a generator-distinct 4 KiB `damage_quarter` positive: the exact relation dispatcher accepted the +1 Law, but prefix-dependent Gear source identity emitted no cross-object exact-reuse witness. The question was whether a tiny content-local witness class, using the same canonical Gear table and the same fused observation pass, can close that evidence hole without constructing a second relation index.

## Builder

The frozen Builder adds one content-local rolling Gear certificate:

- 32-byte rolling buzhash from the existing Gear byte table;
- eight lowest source-window hashes plus 32-bit source positions;
- exact 32-byte equality before nomination;
- OR-composition with the already-promoted shared-observer source-identity evidence;
- the existing exact safe relation proof remains the sole authority for relation acceptance.

Modeled incremental native state is **136 bytes**. No reader-visible ONE operation changes and no reader discovery is introduced.

## Frozen result

The frozen matrix covered 5 source sizes × 3 fresh seeds × 7 cases = **105 rows**:

- sizes: 4, 8, 16, 64 and 256 KiB;
- seeds: 5, 23 and 47;
- ordinary +1 shift;
- quarter-damaged +1 shift;
- mutation every 96 bytes;
- the existing four-edit fixed-band hostile positive;
- a certificate-targeted positive that corrupts one byte inside every one of the eight stored certificate windows;
- mutation every 32 bytes negative control;
- independent-random negative control.

Result:

- `required_positive_misses = []`;
- `certificate_targeted_misses = []`;
- `false_nominations = []`;
- decision = `advance_local_gear_certificate_hybrid`;
- **83/83 ONE semantic and hostile tests passed** before the result-bearing benchmark.

The certificate repaired the exact regimes that motivated it. In 4 KiB `fragmented_every96` rows, for example, shared source identity emitted zero nominations while the certificate found an exact local witness and correctly nominated the pair. The same happened on the fresh-seed small-root debt throughout the frozen matrix.

The certificate-targeted hostile case is especially important. It deliberately destroys every stored certificate window, so the certificate itself emits no nomination. The existing shared observer nevertheless nominates every such exact-positive row. This is evidence that the two writer-side witness classes are complementary rather than two encodings of the same brittle signal.

No exact-negative `fragmented_every32` or independent-random row was nominated by either the hybrid or the certificate, so the structural expansion did not export false-proof debt on the frozen envelope.

## Hostile review

This is **not product-speed evidence**. The target certificate can scan nearly the whole target before finding a witness or deciding there is none; the benchmark deliberately charged those window updates but Python elapsed is not a useful native performance authority. The remaining question is whether the rolling content-local signal can be fused into the promoted native Gear observation pass cheaply enough to justify its 136-byte state and per-byte rotate/xor work.

The finite bottom-8 certificate is also not a proof of complete arbitrary relation discovery. An adaptive target can destroy all eight certificate windows, as the frozen hostile case demonstrates. The present result survives that attack only because the existing shared observer supplies an independent witness. A future corpus can still evade both evidence classes; therefore exact relation proof remains downstream authority, and absence of a nomination is an opportunity decision, not a semantic proof of incompressibility.

## Decision

**ADVANCE the hybrid evidence class to native fused-cost measurement.** Do not promote it into a product writer, density claim, or release claim yet.

The next decisive experiment must implement the rolling certificate in native code inside/alongside the promoted Gear observation loop and compare total writer observation cost, memory traffic and retained state against the promoted observer alone. The experiment must include incompressible/random, already-compressed, repeated/versioned, tiny and hostile cases. If the 136-byte certificate materially increases end-to-end observation cost without sufficient downstream proof avoidance/opportunity recovery, retire or redesign the carrying-cost shape rather than tuning the frozen structural matrix.