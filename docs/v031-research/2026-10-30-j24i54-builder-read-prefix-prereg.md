# J24I54 — preregistered Builder-prefix vs read-only-prefix causal fork

Date: 2026-10-30 UTC. Status: **PREDICTION BEFORE EXPERIMENT**, no outcome claims. Parent #819 at exact `418c60708a06583e970612340eef0f79b50c40f4`; release source v0.30.0/r24 unchanged.

## Why this is the cheapest new question

Two independent #819 results support ~7.85–8.64% wall and ~6.20–6.53% CPU penalty when `tiny→source→media` archives are built in the same Python process before creating `binary`. #816 tested a source-identical native codec A/B and found no intrinsic slowdown, while #807 official library-binary creation still fails two release comparisons (+16.18%, +14.55%). No result yet distinguishes **prior source-byte reading/cache activity** from **Builder-specific prior allocations/compression/concurrency state**. This experiment is a narrower discriminator; it does not clear the official release gate.

## Primary falsifiable question

Holding the exact source, binary corpus and process structure fixed, does a **read-only traversal of the same three prefix corpus trees**, consuming their file bytes but creating no archive or native compression jobs, produce a penalty comparable to the genuine Builder prefix? The critical three conditions are FRESH, READ, BUILD. Same binary warmup, same timed closure, same real Builder, same installed native library.

- H_read: READ and BUILD both materially slow subsequent full `binary` Builder wall and CPU vs FRESH, supporting an input-cache/IO-history explanation as sufficient under these conditions.
- H_builder: BUILD materially slows later Builder wall and CPU but READ does not; therefore prior reading alone is insufficient, and the remaining owner is Builder-specific work, native compression, allocation, concurrency or downstream side effects—not necessarily a mutable Python global.
- H_ambiguous: READ has an intermediate or inconsistent effect, or fresh A/A sham has material drift; avoid forced categorization.
- H_null: no material BUILD penalty in this independent transfer; inherited #819 findings remain valid but transfer is not reproduced here.

## Strong controls and competing causes

Use the original `universal_bench.make_corpora()` frozen **within each hosted run**; record path/mode/mtime/byte SHA fingerprint, all actual source SHA and the loaded native binary SHA. `READ` must visit the same `tiny/source/media` input trees in the same order, read complete regular-file contents in bounded chunks, touch symlink link text without following links, and create no archives. Record bytes read and prefix wall/CPU. BUILD executes the original prefix three `Builder(src).build(dest)` calls, removes outputs, records output sizes and hashes. FRESH has no prior prefix. All conditions perform the same one untimed `binary` warmup, then three timed complete binary Builder calls; archive hashes/sizes must be identical within the hosted court. Process startup and post-timing SHA hashing are outside the timed closure.

Four separately balanced groups (one each condition in multiple slot order permutations, plus a FRESH/FRESH sham) on one runner, bounded <=24 workers and <=96 complete Builder calls, CPU/wall measured independently and original repeats retained. The former #819 exact-source FRESH/BUILD effect is the inherited positive control. The A/A sham is an independent run-order/noise check. Do not retroactively change the preregistered 5% **AND** 3ms materiality rule for both CPU and wall, or any official release threshold. Require same direction in independently reversed groups for a claim stronger than exploratory.

## Decision gates

- If BUILD materially exceeds FRESH and READ stays within +/-3% and +/-3ms of FRESH for CPU and wall, conclude **READ_INSUFFICIENT_BUILDER_CONTEXT_SUPPORTED** in this host/corpus only.
- If both READ and BUILD materially exceed FRESH for CPU and wall and both group signs agree, conclude **READ_HISTORY_SUFFICIENT_IN_COURT**, not proof of kernel page-cache causality.
- If BUILD loses its effect or the sham materially drifts, conclude **NOT_REPRODUCED_OR_AMBIGUOUS**.
- In all other cases report **INTERMEDIATE_AMBIGUOUS** with raw samples. No gate weakening; no claims beyond same-source hosted science.

## Oracle and physical evidence

Commit instrument+workflow only after this preregistration exists as an ancestor. Hosted Ubuntu 24.04 Python 3.11 runs exact source, installed native codec, raw per-child observations, a sha256-verified physical CMPCT archive, same-input/native fingerprints and a separately computed cross-check. Workflow must upload an evidence ZIP even when a scientific hypothesis is rejected; failure should mean broken measurement/custody rather than disappointing result.

Read-only prefix is not equivalent to Builder's compressed bytes, I/O, allocation or CPU load. A positive READ effect does not isolate page cache, and a negative READ effect does not isolate Python global state. Cross-run metadata normalization must happen before measuring if attempted; do not rewrite receipts or source after seeing a result. Cross-OS/general-corpi/release parity remain unmeasured. No changes to product, on-disk format, ABI, safety, recovery, benchmark evaluator, performance gate or release.

## Ownership / PARETOBONK

This branch is a declared, narrow dependent follow-on to #819, not concurrent implementation of #819 or #807. #574 owns shared discovery state. Neighboring scheduled agents must not rewrite these experiments or treat running workflow as unlocked evidence. Cheaper route than another full 45-minute release matrix; if BUILD-specific effect survives, next target is phase attribution with per-phase function tracing (without editing source or official evaluator). If READ explains the effect, investigate controlled cache/IO history before changing codec. A contradictory result narrows rather than deletes the prior evidence.

No merge, no version bump, no release and no automatic user-facing performance claim.
