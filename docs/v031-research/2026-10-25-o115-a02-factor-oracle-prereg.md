# O115 preregistration — A02 orthogonal-factor model versus simple whole-file/residual controls

Date: 2026-10-25 UTC
Status: PROSPECTIVE / immutable prediction, before instrument/results.
Source: FCMO-AI/.CMPCT agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b, shipping v0.30.0, wire r24.
Owner: isolated Phased2 O115 research branch. No product, format, release, comparator or discovery-policy writes.
Authority: AGENTS.md; docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md; docs/ASSUMPTION_LEDGER.md A02; docs/discovery/DISCOVERY_ENGINE.md. Discovery state cache is stale; PR #440 owns its reconciliation.

## Question
Can a single latent base plus a bounded dictionary of **orthogonal byte-range factors** and a short per-file assignment plan strictly outperform a simple solid compressor and shared-base residual compressors on **fully charged bytes**, while retaining genuinely bounded member access? The oracle is gifted exact positions/assignments; source inference, model selection and production admission receive NO credit.

## Falsifiable mechanism/prediction
Independent high-entropy substitutions at **fixed disjoint offsets** recur in combinations across files. A codebook may share each substitution once rather than rediscover whole-file or XOR-residual redundancy. Pre-observation prediction: on the orthogonal crossed-choice family, factor representation will be <= best control's complete bytes, possibly saving >5%, and decode <= 2 object-lengths + full codebook; however on correlated-choice and independent-random controls a simple solid/residual representation should win, and the factor family must not be preferred. Held-out geometry (different lengths/axis count/offsets, different seed) must not reverse any generality claim. **This is exploratory headroom, not CMPCT's shipped performance.**

## Frozen family generation
Deterministic SHA-derived PRNG seed 115, 64 objects of 4096 bytes. Base bytes fixed high entropy. Three disjoint 256-byte slots. Four independent 256-byte token alternatives per slot. Files select orthogonal cross-product choices using a deterministic permuted sequence. Correlated control ties all slot choices. Independent-noise control uses 64 independent random files with no reusable factors; same prospective slot locations may be supplied to the factor oracle but literal correction residuals must carry all mismatches. Held-out structural transfer uses seed 191, 96 objects of 8192 bytes, four 384-byte nonoverlapping slots, five token alternatives, offsets not inherited from training. Distinct random seeds and geometry; NO tuning after outcome.

## Models / charged facts
Use the same zstd binary and level 19, one process per payload, on exactly the same objects. Compare: (S) solid all objects; (I) independent objects; (R) shared base + individually Zstd-compressed XOR residuals; (G) shared base + one solid-Zstd residual stream; (F) base + Zstd-compressed serialized factor dictionary, per-object assignment bytes and *lossless* exception residuals. Charge all actual compressed streams, explicit per-object offsets/length/hash common metadata, factor slots/alternative counts/assignments/codebook ownership, and per-member index; no uncharged oracle side information visible to decoder. Root may be an independent latent basis and MUST be counted. Each model must reconstruct every byte and pass independently computed per-file SHA-256. Record detailed per stream/raw lengths and elapsed compression times separately from product execution.

## Kill/decision law
If F >= min(S,I,R,G) on crossed-choice AND held-out families, retire A02 **this narrow factor-dictionary representation** as a storage win; do not tune slots, blocks, seeds, levels, thresholds, or controls. If F wins crossed-choice but not held-out, narrow to a data-dependent seed, not a portable structural win. If F wins both, preserve a research seed with independent detection/admission, parse safety, format overhead, cold open, full read, locality, exact portability and real CMPCT product costs as explicit debt. If a simpler residual control wins, do not hide it. Reject run as scientifically invalid if reconstruction, SHA, accounting audit, or same-input controls fail. Ordinary oracle/micro measures may kill but cannot promote.

## BONK competitors and counterfactual
Do not duplicate active Builder/Reader/CI repair owners (#269, #316, #328, #451, #455, #463). This changes the A02 representation/information frame, not the already-narrowed A03 post-residual transposition (PR #458). Strongest simple control is solid Zstd on complete originals, and especially **one solid stream of XOR residuals + charged base**. An earlier signal that F only beats a weak per-file comparator would have killed the hypothesis before productization. No changes to docs/discovery/STATE.json (PR #440 ownership).

## Evidence rung
Local exact reconstruction + charged oracle, then hosted CI if instrument can be installed through a legitimate branch. No release benchmark, deployment or release claims. Preserve raw outcomes even when negative.
