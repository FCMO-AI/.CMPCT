# ONE-G0.2 — automatic bounded translation Law + Surprise cone

**Status:** automatic extent rule passes edited-version positives and hostile MDL controls  
**Exact result-bearing source:** `01ac0d9b7b29dbb383a6f4d8b71bd66ec5591dad`  
**Workflow:** `33948408508`  
**Job:** `101258534904`  
**Artifact:** `9964047613`  
**Artifact digest:** `sha256:e5b6626b269067ab1ec41d146463119cdd24fcafa96f90da29bb79a46835dd46`  
**Experiment:** `ONE-G0.2`

## What changed from O0

O0 gifted the target-version extent. This experiment removes that gift. Once an existing exact candidate relation proves a positive translation delta `d = target_start - source_start`, the encoder proposes the largest forward cone that cannot self-reference: target `[d, min(2d, input_len))`, source `[0, cone_len)`. The extent therefore follows only from the proven Law delta and input bounds.

Every mismatch inside that cone is explicit Surprise. Admission is fully charged MDL: 32 B Law/control plus ULEB Surprise count plus ULEB position delta and one literal byte per Surprise. The Law is admitted only when that representation is smaller than literal cone bytes. Reconstruction must remain exact.

## Exact-head result

All **50 ONE semantic tests** passed. Frozen decision:

`advance_automatic_translation_law_surprise`

Gate failures: **none**.

### Positive edited-version cohort

All 64 frozen internally edited-version rows:

- obtained a correct exact candidate Law seed;
- inferred the correct 65,536- or 262,144-byte translation delta;
- derived the complete second-version cone without a target-extent gift;
- were admitted by MDL;
- reconstructed byte exactly;
- predicted at least the mature minimizer's exact reuse opportunity.

Aggregate density is unchanged from the honest O0 charge because the same representation is now discovered automatically:

- literal second-version bytes: **10,485,760 B**;
- charged Law+Surprise bytes: **6,222 B**;
- charged fraction: **0.05934%**;
- Law-predicted exact bytes: **10,484,400 B**;
- mature exact reuse opportunity: **10,036,655 B**.

The previously failing 262,144-byte / base #1 / 16-edit row is admitted at **87 B** charged representation, predicts **262,128 exact bytes**, equals the mature opportunity, and reconstructs exactly.

### Hostile partial-copy controls

Eight independent controls contain two unrelated random 64 KiB halves except for one copied 16 KiB same-offset island. This is deliberately dangerous: the existing sparse/epoch discovery path finds a genuine exact translation seed in **8/8** rows, so a naive “one seed means extend the Law” rule would overgeneralize.

The automatic cone instead sees roughly **48.9k Surprise bytes** per 64 KiB cone. Fully charged Law+Surprise cost is approximately **97.87–97.98 KiB**, versus **65,536 B** literal, so MDL rejects **8/8** false Laws while exact reconstruction remains possible.

### Independent random controls

Eight fully independent random-half pairs yielded no candidate Law seed and therefore no admitted Law: **0/8 false admissions**.

## Causal interpretation

This result removes the most important O0 gift and supplies a cheap falsification rule. The encoder need not know “this is a version.” A byte-proven translation relation proposes a bounded non-self-referential cone; explicit Surprise measures how much of that Law really survives; fully charged MDL decides whether to keep the Law or crystallize/literalize instead.

This is materially closer to the ONE principle than repeated minimizer re-discovery: one predictive Law remains active while sparse violations are Surprise, and a misleading partial Law dies because its Surprise bill is larger than literal.

## Hostile review / remaining debt

The cone rule is intentionally narrow. It assumes a positive translation Law whose source begins in the archive's earlier prefix and tests at most one non-self-referential continuation cone. Generic multi-version layouts, shifted/noncontiguous extents, overlapping cones, competing Laws, incremental updates and multiple bases are not yet solved.

The encoder still performs an exact mismatch scan over an admitted candidate cone. Its native elapsed/memory traffic and interaction with the fused fixed+epoch observer must be measured. Selective-read amplification and failure-blast-radius behavior of the compiled representation also remain debt.

No v0.29/v0.30 superiority, canonical release, native product-speed or generic-version authority is created.

## Terminal decision

**Promote the automatic bounded-cone + MDL rule as the current ONE-G0.2 temporal/versioned research direction.** Keep the edited-version negative against scalar epoch-min alone. Do not restore the rolling minimizer as a permanent fallback; next prove that this Law+Surprise result compiles through the existing generic ONE IR/wire/VM without a bespoke reader mechanism, then measure fused native discovery and reader/access cost.
