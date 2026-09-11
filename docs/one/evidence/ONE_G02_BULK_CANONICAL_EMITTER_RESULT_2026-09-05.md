# ONE-G0.2 bulk canonical emitter — terminal negative result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

## Frozen authorities

- `docs/one/evidence/ONE_G02_BULK_CANONICAL_EMITTER_PREREG_2026-09-05.md`
- `docs/one/evidence/ONE_G02_BULK_CANONICAL_EMITTER_METHOD_AMENDMENT_2026-09-05.md`

The timing amendment was frozen before consuming result authority and changed only measurement order to paired alternating A/B-B/A. No workload, threshold, round count, representation or decision law changed.

## Exact CI receipt

- authoritative branch head: `a568ccb4ef62e0a7116f00f81409c7093dcb8779`
- pull-request merge test SHA: `f6e9926493ebd4f37c9465a6e9a060070f9702fb`
- workflow run: `33992371038`
- job: `101376754622` (`bulk-canonical-emitter`)
- workflow conclusion: **failure by frozen performance gate**
- artifact: `9977011939`
- artifact ZIP SHA-256: `0cd0dbd0410bddd67e397986101c41fdff0ee5cb437c4cd8eca375ed5e52e0cb`
- ONE semantic/hostile tests: **93 passed**
- semantic gates: **pass**
- terminal decision: **`retire_bulk_canonical_emitter`**

## Result

The candidate preserved the canonical ONE0 bytes and `WireStats` exactly on every frozen row, decoded through the ordinary reader and reconstructed every `previous` / `current` root byte-exactly. The new direct semantic tests also pinned all six ONE operations, canonical root sorting, varint boundaries and the existing validation boundary.

The sized single-buffer strategy did reduce the median prevalidated canonical-emission cost on the productive relation Programs:

- productive median candidate / baseline: **0.7796418663x** (~22.04% lower median elapsed);
- productive rows <=0.90x: **15/21**, versus the frozen requirement of >=18/21;
- productive size-class medians:
  - 4 KiB: **0.902104x**;
  - 8 KiB: **0.856287x**;
  - 16 KiB: **0.824346x**;
  - 32 KiB: **0.805988x**;
  - 64 KiB: **0.770851x**;
  - 128 KiB: **0.764744x**;
  - 256 KiB: **0.777486x**.

However the candidate did not satisfy the no-regression / broad-transfer law:

- worst productive row: **1.053195x**, exceeding the frozen 1.03 ceiling;
- worst control size-class median: **1.299110x**, exceeding the frozen 1.03 ceiling;
- the 128 KiB `fragmented_every32` literal control was especially hostile: **1.972102x** candidate/baseline, while the same-size independent-random control was **0.626117x**. This spread is evidence that the current two-pass size-then-fill shape is not a stable universal replacement for the existing growable-bytearray emitter.

The decisive 256 KiB hierarchy-required `fragmented_every96` productive row did improve from 9,839,272 ns to 7,649,896 ns, **0.777486x**, while preserving the exact 297,504-byte wire and 264,876 Surprise bytes. The candidate therefore contains a real control-heavy allocation/copy signal, but that gain is not safely global.

## Causal interpretation

The parent cost-owner result remains valid: prevalidated canonical byte emission is a major post-segment owner. This experiment falsifies a narrower hypothesis: **exact pre-sizing plus a single fixed bytearray is not a generally safe way to remove that cost in Python.**

The mechanism appears to help most on control-dense Programs where the baseline creates many temporary varint/ref/node bytearrays. It does not reliably help simple blob-dominated Programs. The candidate also pays a complete sizing walk before writing; on programs with only a few controls and large Surprise blobs, that extra pass has little small-object allocation to amortize.

Do not rescue this exact implementation with corpus or size thresholds. A threshold such as "bulk above N KiB" would be contradicted by the large-control spread and would encode the observed matrix rather than the mechanism.

A causally different follow-up is justified: retain the baseline's growable output buffer (therefore no global sizing pass) while eliminating temporary per-varint/per-ref/per-node bytearrays by writing canonical controls directly into the growable buffer. That isolates the small-allocation mechanism without importing the two-pass cost that caused the present debt. It is distinct from the already-rejected segment-to-control direct-streaming experiment: the Program remains fully materialized, validated and canonical before wire emission.

## Claim boundary / negative evidence

This is Python research-harness evidence, not native/product writer authority. It changes no ONE representation, reader semantics, stored bytes, integrity contract or format revision. It creates no v0.29/v0.30 superiority claim.

**Scoped negative:** retire the universal `size entire Program -> allocate exact bytearray -> fill` emitter shape under the tested Python ONE0 regime. Reopen only with a causally different implementation or evidence that removes the sizing-pass/exported-cost mechanism; do not reopen by tuning size thresholds to the frozen corpus.