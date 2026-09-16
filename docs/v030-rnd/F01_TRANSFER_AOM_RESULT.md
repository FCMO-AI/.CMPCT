# F-01 structural transfer + AOM result

Status: **accepted frozen result — `TRANSFER_FAIL`; hostile thesis review required; research only; no release credit**.

Authority:

- preregistration: `docs/v030-rnd/F01_TRANSFER_AOM_PREREG.md`;
- exact source: `0f1acdd91a11169c87c41bc2a384046c785b5dcb`;
- workflow run: `33471421991`;
- job: `99741875994`;
- artifact: `v030-foundry-f01-transfer-aom-0f1acdd91a11169c87c41bc2a384046c785b5dcb`;
- artifact ZIP SHA-256 reported by Actions: `1475579970f850826bd26fc4a1b54b33bb9c4eda8e250b67bf2326e9edd8f929`;
- corpus fingerprint: `0e56cccb5068f9bb17958a9bc5f52203333e97062d83ad411b7066773a31c5dd`;
- causal source bound by the instrument: `2876698d311b13f296a6f11f23d89eaab51cd09c`;
- accepted causal artifact digest: `sha256:e910165ad51b2501f44a8531dab39ccbd697a1a1b150f9d958fb03290d33f2b6`.

The workflow independently re-checked the frozen metadata, exact source head, unchanged grammar, case-family contract, zero heuristic pruning, AOM bounds, carrying-cost fields and Oracle Gift Ledger before accepting the artifact.

## Frozen decision

The preregistered instrument returned **`TRANSFER_FAIL`**.

This is not a claim that composition has no value. It is the narrower and more useful result that the current F-01 grammar/predicate cannot advance as a general structural-transfer thesis under its own hostile-transfer law.

The decisive failure condition was met because a preregistered hostile negative — the deliberately off-grid positive-structure case — received a material composition win. The `{8,16}` lane-width pruning A/B also failed its exact-optimum preservation requirement.

Per the frozen preregistration, the old grammar, challenge generator, thresholds and interpretation remain immutable. Operator expansion is not an automatic remedy.

## Positive evidence that survives the failure

The transfer test did not collapse on the intended positive structures:

- **6** material positive-family transfer wins survived;
- winners span both `lane+record` and `lane+lane` families;
- winning scales span **32, 64, 96 and 128 KiB**;
- material saving over winner bytes was **11,378 B**;
- synthetic positive-structural addressable byte fraction was **1.0**;
- conditional saving fraction inside material winners was **0.2304591764** (~23.05%);
- synthetic addressable gain estimate was **120,826.98 B**.

Representative exact full-grammar wins versus the one-stage manual control:

- `tr_lr_32_a`: 4,273 -> 2,581 B, **-1,692 B / -39.60%**;
- `tr_lr_64_b`: 6,980 -> 3,313 B, **-3,667 B / -52.54%**;
- `tr_lr_128_n`: 9,527 -> 4,512 B, **-5,015 B / -52.64%**;
- `tr_ll_64_ab`: 8,661 -> 8,217 B, **-444 B / -5.13%**;
- `tr_ll_96_ba`: 9,855 -> 9,625 B, **-230 B / -2.33%**;
- `tr_ll_128_u`: 10,075 -> 9,745 B, **-330 B / -3.28%**.

The correct interpretation is therefore not “composition was a mirage.” It is that the current grammar has real mixed-structure headroom but its intended structural admission boundary is not yet trustworthy enough for generalization.

## Hostile failure / scoped negative constraint

The hostile `offgrid-lane-record` case was preregistered as outside the frozen 4 KiB split-grid reach expectation. Nevertheless the full grammar found a material composition win:

- manual control: **6,991 B**;
- synthesized full-grammar result: **3,091 B**;
- saving: **3,900 B / 55.79%**;
- motif: `SPLIT@grid(LANE[4]+DELIM[103])`.

This created:

- hostile material false-win count: **1**;
- hostile material false-win bytes: **65,536 B**.

Scoped constraint: **the current synthetic structural labels and frozen split-grid interpretation do not separate “intended transfer” from a materially compressible hostile/off-grid structure.** A future thesis may reopen this only with a new causal account of what the compiler is actually exploiting; merely relabeling the hostile case or moving the grid after seeing this result would invalidate the test.

This is a classification/admission failure, not a byte-accounting failure: program/control/terminal bytes and exact reconstruction remained charged.

## Carrying-cost result

Full grammar:

- lane widths: `[2,4,8,16]`;
- generated states: **2,064**;
- costed states: **2,064**;
- exact-bound prunes: **160**;
- nominations per logical MiB: **2,752**.

Preregistered pruned A/B:

- lane widths: `[8,16]`;
- generated states: **1,311**;
- costed states: **1,311**;
- exact-bound prunes: **165**;
- nominations per logical MiB: **1,748**.

The pruning does reduce generated/costed work by **753 states (~36.48%)**, but **does not preserve every exact optimum**. Several positive cases changed optimum motif/bytes because LANE[4], previously inactive on the causal seed, became active under structural transfer. Therefore widths 2/4 may not be silently removed from the frozen research grammar on the basis of the earlier causal seed.

This is an important anti-overfit result: an optimization that looked causally redundant on the seed failed to transfer as a safe global simplification.

## Oracle Gift Ledger

Gifted:

- search/discovery wall time.

Never gifted:

- program/control/terminal bytes;
- exact reconstruction;
- structural AOM labels.

Still deferred and therefore unsupported:

- independent/public real-data AOM;
- generic admission economics;
- canonical framing/index;
- locality/recovery/integrity;
- native/platform;
- product runtime;
- full release matrix.

Because the decision is `TRANSFER_FAIL`, those debts are **not** automatically scheduled for F-01 productization.

## Hostile thesis review

Strongest surviving positive interpretation:

> Exact composition is genuinely useful for heterogeneous regions across substantial structural variation; the failed test may be exposing a wrong *causal predicate* rather than a useless representation primitive.

Strongest hostile interpretation:

> F-01 is currently a search procedure that can exploit any convenient split-aligned heterogeneity, while our human structural labels are post-hoc and insufficiently predictive. The six positive wins do not justify a general compiler if the same mechanism materially “wins” a preregistered hostile case and the seed-derived simplification rule fails transfer.

The hostile interpretation wins for state-transition purposes because the preregistered falsifier fired.

## Thesis decision

**F-01 leaves `CAUSAL_SEED` and enters `TRANSFER_FAIL / HOSTILE_REVIEW_REQUIRED`.**

Do not add operators, move split grids, relax hostile labels, or proceed to real-data AOM under the old thesis. The next Foundry action is a doctrine-level hostile thesis review using this result plus the Assumption Ledger. Any continuation must be a **new superseding thesis/freeze** with a different causal claim and explicit reopening predicate, not an edited replay of F-01.

A valid future reopening path would need to explain, before new result-bearing execution, why the off-grid case is causally inside or outside the hypothesized opportunity class and why that distinction is observable without benchmark identity or gifted decode/search semantics.

## Forge separation

This Foundry failure does not revoke independently proven Forge mechanisms. In the same activation the r25 implicit-v4 filesystem-control seam crossed its D5 canonical Python landing boundary. That productization work continues independently through native/recovery/Android/release authority.
