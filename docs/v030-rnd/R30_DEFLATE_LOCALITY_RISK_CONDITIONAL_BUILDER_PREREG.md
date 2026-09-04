# R30 — Deflate Locality-Risk Conditional Retention Builder Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

Trigger evidence: valid R29 terminal `PARTIAL_OWNER` on Incremental Backups. In the same run, restoring the mature 64 KiB Deflate-reuse threshold reduced release-r24 by **32,418 B / 62.3591%** while retaining 1.0x locality for the measured complete member. The remaining release-r24 gap was 19,568 B. R29 explicitly did not authorize a global threshold rollback.

Historical rationale matters: release r24 changed the mature 64 KiB threshold to zero because virtual ZIP/WHL mode-2 regeneration can decode a much larger raw constituent in order to reproduce a small exact Deflate stream. The shipping policy therefore protected the <=8x decoded-context law, not archive ratio. R30 tests the lowest-sufficient generic replacement for that blanket safeguard.

This is Forge D2 -> R1/R2 conditional-elision work. It changes no grammar and grants no release credit by itself.

## Worldview under test

The blanket rule “retain every exact Deflate stream” may be stronger than the actual invariant. For a mode-2 regenerated stream, the causal locality risk is the relationship between the raw constituent that must be decoded and the exact compressed stream it reconstructs.

A conservative content-derived rule can therefore retain exact streams when either:

1. the exact stream is already at least the mature **65,536 B** cutoff; or
2. `raw_constituent_bytes > 8 * exact_deflate_stream_bytes`.

Otherwise the stream may use the mature deterministic level-regeneration path. This rule uses only representation bytes known during Builder selection. It does not inspect workload name, source path, filename, extension, corpus identity, hashes, benchmark metadata or competitor results.

The raw/stream test is deliberately conservative: it charges the full uncompressed constituent as potential decoded context. It may retain more streams than strictly necessary, but it must not buy bytes by assuming cheaper locality accounting than the public r24 member operation observes.

## Frozen targets

Two paired targets are generated from the same repaired deterministic `neutral_hostile_v1/06_incremental_backups` source instance:

1. **full-backups** — the complete frozen Incremental Backups product tree;
2. **nested-only** — a diagnostic projection containing only the exact `snapshot_2.zip` bytes copied unchanged from that same generated tree. This second target is not product benchmark truth; it isolates the virtual-container tradeoff and prevents the many raw snapshot files from hiding a nested-read regression.

The generated full-backups tree must match the canonical generator-provided expected tree identity. `nested-only/snapshot_2.zip` must be byte-identical to the source member.

## Frozen arms

All arms use the current shipping-r24 pack/chunk/medium-binary policy and the promoted dead-dictionary post-selection elision. Only exact-Deflate retention differs.

1. **release-all-exact** — shipping `deflate_reuse_min=0`.
2. **mature-64k** — mature `deflate_reuse_min=65,536`; byte/control arm only, not presumed lawful globally.
3. **locality-risk-v1** — retain a chosen/secondary exact stream iff `stream_bytes >= 65,536` OR `raw_bytes > 8 * stream_bytes`; otherwise use deterministic mode-2 regeneration.

No threshold sweep is permitted. R30 is a causal test of the release invariant, not parameter search.

## Frozen measurements

Each target/arm runs in **three fresh processes**. Record every repetition and medians for:

- complete archive bytes and SHA-256;
- build wall time;
- peak RSS;
- strong verification and reconstructed tree identity;
- count/bytes of canonical and secondary exact streams retained where observable;
- count/bytes of exact streams dropped to deterministic regeneration where observable.

For every source `.zip`/`.whl` logical member, call the public canonical product member-read surface and record actual operation-derived decoded-context bytes and amplification. `nested-only` must contain at least one such measured member. Missing locality data fails the experiment.

Hard locality ceiling remains **<=8.0x** for every measured virtual member.

Runtime materiality uses the existing release noise rule: a regression is material only when it exceeds **both 5% relative and 3 ms absolute** against the paired release-all-exact median on the same target. Size has **0-byte regression tolerance** against release-all-exact.

## Frozen interpretation law

Correctness/identity failure, missing virtual-member locality, or product-substrate drift => `SUBSTRATE_OR_CORRECTNESS_FAILURE`.

Otherwise:

- **PROMOTE_CONDITIONAL_TO_GLOBAL_BUILDER** — `locality-risk-v1` is <= release-all-exact bytes on both targets, has no material build-time regression on either target, exceeds no release-all-exact peak RSS by >10%, and every measured virtual member remains <=8x; additionally it must save >0 complete bytes on full-backups. This authorizes only a superseding all-protected-workloads/global carrying-cost Builder, not a product edit.
- **BYTE_WIN_LOCALITY_FAIL** — locality-risk-v1 saves bytes but any measured virtual member exceeds 8x.
- **BYTE_WIN_RUNTIME_OR_RSS_DEBT** — bytes/locality pass but runtime/RSS export exceeds the frozen limits.
- **NO_MATERIAL_CONDITIONAL_WIN** — locality-risk-v1 saves 0 bytes on full-backups or is larger than release-all-exact on either target without a locality failure.

The mature-64k arm is interpreted only as a control showing the maximum simple-threshold byte opportunity and any locality/runtime debt. It can never be directly promoted by R30.

## Required next step after a positive result

A positive R30 must be followed by a global/protected-workload Builder that includes every strict product workload containing virtual ZIP/WHL plus the relevant builder-independent virtual-ZIP conformance vectors, and must measure full archive bytes, create time, RSS, <=8x locality, recovery/integrity/native implications and global mechanism carrying cost. Only that later experiment can authorize productization.

## Anti-cheating / immutability

After first result-bearing execution, this target construction, three arms, constants, repetition count, 8x ceiling, runtime/RSS law and interpretation law are immutable. An unfavorable result may not be repaired in place. No workload-name/path dispatch, benchmark relaxation, competitor change, recovery/integrity borrowing, archive-size tolerance, or hidden third full product candidate is permitted.
