# PR #209 custody owner reconciliation

**Date:** 2026-09-27  
**Authority:** coordination/evidence note only; no product or promotion credit.

Current Git reconciliation found an existing implementation owner for the nested r24 candidate-custody repair:

`agent/v030-r24-compact-source-replication@9014cfa5d2b854299670a213f2386fe469d9a312`

It is 9 commits ahead / 0 behind authoritative `94f3309011ca6f6014b1f61ce6058e8ce01ca00f`.
No PR or PR-triggered workflow run is currently attached to that exact head.

The branch explicitly carries the compact candidate into the byte-owning r24 child through a worker-module seam,
adds a candidate-owned prebuild worker that attests effective Builder-visible policy, and adds a structural test
showing that the child changes the expected final r24 storage decisions rather than merely reporting candidate
constants.

This Phased2 branch therefore does **not** own a second repair implementation. Its role is the accepted
Incremental Backups three-arm falsifier plus durable custody diagnosis. Future work should consume the existing
source-replication owner.

Cheapest decisive sequence:

1. Execute the source-replication child-custody structural test on exact head `9014cfa...`.
2. If green, run the unchanged global compression parity once with that correctly bound candidate.
3. If that complete-product compression run is red, retire the compact-r24 policy family without cutoff or packing
   threshold gardening.
4. If green, advance to the inherited runtime/RSS/selective/native/recovery/platform gates; do not infer release
   authority from compression alone.

Unexecuted source is not evidence of a passing candidate.
