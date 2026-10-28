# v0.30 r24 locality-derived micro-pack current-fingerprint 15 transfer — 2026-09-12

Status: **Mission Lock / Hostile transfer / research-only**.

## Scope

The frozen Genesis15 identity is partially unreproducible in the current hosted toolchain. This experiment therefore asks a different question without borrowing Genesis score authority:

> On the **current freshly generated** 10 neutral-hostile + 5 resemblance-hostile workloads, does locality-derived micro-packing remain a same-grammar causal win across the complete 15-workload population?

The generated corpus gets a new fingerprint in the receipt. It is never substituted for frozen Genesis.

## Frozen mechanism and comparator

Same as the prior causal referee:

- independent r24 with micro-packing disabled;
- locality-derived r24 using `sum(group raw bytes) <= 8 * smallest logical member bytes`;
- both compared under the exact same `membership-v1` control grammar;
- zero-group rows must be exact no-ops;
- inherited baseline locality debt on zero-group rows is not reattributed to this mechanism.

No path/workload identity, no new thresholds, no selector tuning.

## Falsifiable hypothesis

Across all 15 current-fingerprint workloads:

- every workload with new derived groups is strictly smaller than the same-grammar independent control;
- every zero-group workload is byte-identical;
- all new groups satisfy `<=8x`, exact tree reconstruction and authenticated tail recovery;
- aggregate complete bytes strictly improve.

A grouped loss means exact economic admission is required before broader integration. A new locality/recovery/exactness failure attacks the mechanism.

## Required receipt

- current corpus fingerprint derived from ordered `(suite, name, files, logical_bytes, tree_sha256)` rows;
- every workload identity;
- same-grammar independent/derived bytes and deltas;
- group/member counts;
- max/weighted member amplification and max decode unit;
- build and control-transform CPU/wall diagnostics;
- exact/recovery invariants;
- aggregate bytes, grouped wins, zero-group ties and failures.

No frozen Genesis score, isolated RSS, release throughput or version credit is authorized.

## Verdicts

`CURRENT15_MICROPACK_GENERALIZES`
: every grouped row wins, every zero-group row ties, all invariants pass and aggregate improves.

`CURRENT15_MICROPACK_NEEDS_ECONOMIC_ADMISSION`
: invariants pass but one or more grouped rows tie/lose, or a zero-group row changes.

`RETIRE_CURRENT15_MICROPACK_TRANSFER`
: the candidate introduces an exactness, recovery or locality violation.
