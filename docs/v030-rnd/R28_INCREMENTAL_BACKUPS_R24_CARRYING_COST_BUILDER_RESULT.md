# R28 — Incremental Backups r24 Carrying-Cost Builder Result

Status: **TERMINAL — SUBSTRATE_OR_CORRECTNESS_FAILURE; NO SCIENTIFIC OR PRODUCT CREDIT**

Frozen preregistration: `docs/v030-rnd/R28_INCREMENTAL_BACKUPS_R24_CARRYING_COST_BUILDER_PREREG.md`.

Execution:

- workflow run: `33828582239`
- exact result-bearing head: `b32ad9c9de6c45d11c9f357b599900a6de1ecc6d`
- release fingerprint at execution: `e8438b46b1e09cc0fdcc09ba19f9b953695018c5c6fb9da05a48e47763319831`
- immutable artifact: `9920861648`
- uploaded artifact ZIP SHA-256: `5d80d94d3b5c34835a107ddc7a45a5d0ace52dbd4be1cc469cff380aaf16886f`
- result-bearing six-arm step: **PASS**
- frozen completeness/interpretation guard: **FAIL**, as required by the preregistered law

## Terminal reason

R28 froze the R27 same-run gap as exactly **52,024 B**. The superseding run regenerated the same deterministic content tree but observed:

- genuine r24: **8,036,545 B**
- release r24: **8,088,563 B**
- observed same-run gap: **+52,018 B**
- frozen expected gap: **+52,024 B**
- cross-run discrepancy: **−6 B**

The instrument therefore emitted `SUBSTRATE_OR_CORRECTNESS_FAILURE`, and the workflow's explicit `== 52024` assertion failed. Under the frozen law, no one-factor arm may be promoted or interpreted as causal evidence from this run.

The six-byte discrepancy is small but scientifically decisive because R28 itself preregistered exact equality. The old grammar is not edited after seeing the result.

## Observed arms — hypothesis generation only

These measurements are retained to guide the next superseding freeze, **not** as evidence of ownership:

| Arm | Complete bytes | vs release-r24 | vs genuine-r24 | locality |
|---|---:|---:|---:|---:|
| genuine-r24 | 8,036,545 | — | — | 1.0x |
| release-r24 | 8,088,563 | — | +52,018 | 1.0x |
| mature Deflate threshold | 8,056,135 | -32,428 | +19,590 | 1.0x |
| mature micro-pack target | 8,091,190 | +2,627 | +54,645 | 1.0x |
| mature micro-pack max-file | 8,110,715 | +22,152 | +74,170 | 1.0x |
| no medium `.bin` pack admission | 8,091,140 | +2,577 | +54,595 | 1.0x |

The mature-Deflate arm is therefore the leading **reopening hypothesis** because it was the only frozen one-factor arm that moved materially toward the genuine-r24 floor; it removed 32,428 B of the same-run positive gap (~62.3%). The other three arms moved away from the floor. This observation cannot authorize a product change.

## Causal interpretation of the failure

R27 and R28 both regenerate the corpus in fresh processes and compare complete archive bytes. Product-tree identity and 1.0x selected-member locality survived. The exact +52,024 B value, however, was not stable to a later fresh regeneration despite unchanged product/corpus code. This means the **cross-run absolute gap was an over-strong custody assumption for the R28 attribution question**. It is not evidence that the underlying D2 floor disappeared: the release-r24 arm remained lawfully larger than genuine r24 by ~52 KB in the superseding same-run comparison.

The next experiment must not weaken product truth. It should instead bind the deterministic content identity and require a positive same-run release-r24/genuine-r24 gap, while making the causal decision entirely from paired arms built from the **same regenerated source instance**. That is the minimum repair to the diagnostic instrument, not a benchmark relaxation.

## Decision and reopening predicate

**R28 is closed as invalid for interpretation.** Preserve artifact and failure permanently.

A superseding Builder may reopen attribution only if it:

1. preserves the same target content/tree contract and exact product substrate;
2. compares every arm against genuine-r24 and release-r24 from the same source instance/run;
3. requires release-r24 to remain strictly larger than genuine-r24;
4. preserves strong verification and <=8x locality;
5. does not freeze the historical gap to one exact cross-run byte count;
6. keeps the one-factor arm definitions unchanged, so the only scientific repair is the invalid cross-run equality assumption.

No release threshold, product no-regression law, competitor, locality ceiling, corpus semantics, integrity/recovery rule or selected archive criterion is relaxed by that superseding freeze.
