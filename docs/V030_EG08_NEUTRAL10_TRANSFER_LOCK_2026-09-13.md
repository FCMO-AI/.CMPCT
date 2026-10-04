# v0.30 EG08 adaptive-effort neutral10 transfer — mission lock

Date: 2026-09-13
Status: preregistered hostile/held-out transfer; **no promotion from Office alone**.

## Frozen mechanism

The exact EG08 mechanism that passed Office is frozen for this transfer:

- EG07 builds the representation, control plane, integrity/recovery layout and locality geometry;
- hot stream roots are derived only from authenticated `inflate_stream` recipes and are left unchanged;
- all other final physical packs begin from their current level-1/raw storage choice;
- fixed effort ladder: `3, 6, 12, 19`;
- retain the best storage choice seen;
- continue after a strict improvement or exact tie;
- stop at the first strictly worse next rung;
- no path, extension, workload identity, content type or corpus-derived byte threshold.

No rule may change after seeing transfer results.

## Falsifiable hypothesis H-EG08-TRANSFER-1

Selective effort generalizes as a non-regressing encoder-side improvement: it preserves EG07 reader/recovery semantics on every deterministic neutral workload, buys material density on at least one held-out workload besides Office, and does not turn low-opportunity workloads into broad CPU/RSS regressions.

## Fixed transfer surface

Run all ten deterministic neutral/hostile-v1 workloads from `v030_current15_stable_corpus`:

1. developer repository;
2. office workspace;
3. media library;
4. analytics/database;
5. logs/telemetry;
6. incremental backups;
7. incompressible/encrypted-like;
8. many tiny files;
9. ML artifacts;
10. large mixed binary.

Office remains in the matrix only as a same-mechanism repeat; the other nine are transfer/held-out evidence.

For every workload run EG07 and EG08 in separate fresh processes and record stored bytes, creation CPU/wall, peak RSS, locality, effort attempts/stops/selected levels and exact strong verification. EG08 must also survive authenticated tail recovery after deliberate primary-metadata corruption.

Run the exact frozen Genesis-v0.29 product surface on Analytics only, because Analytics is the second-largest frozen Genesis density deficit and is the next decisive target. Other workloads use EG07 as the direct causal baseline; no old aggregate row is substituted into the transfer.

## Hard blockers

`EG08_NEUTRAL10_TRANSFER_PASSES` requires all of:

- 10/10 EG08 builds and strong verifications complete;
- 10/10 tail-recovery checks pass;
- 10/10 preserve EG07 member count, maximum decode unit and maximum member amplification exactly;
- **0 stored-byte regressions** versus same-run EG07;
- Analytics EG08 is strictly smaller than same-run EG07;
- Analytics EG08 creation CPU remains at least `10x` faster than exact frozen v0.29;
- no workload exceeds `1.50x` EG07 creation CPU **when it gains fewer than 4 KiB**.

The last rule is not a product selector threshold. It is an adversarial exported-cost test: spending >50% extra CPU for a sub-4-KiB research gain is evidence that the current post-build implementation is too wasteful on low-opportunity inputs. If it fails, the mechanism may still survive but requires a cheap pre-gate before broader transfer.

Peak RSS has no synthetic pass threshold in this first transfer. Report absolute and delta RSS for every workload; any large increase becomes explicit regression debt and blocks promotion until attributed.

## Analytics decision

The exact same Analytics tree is compared to frozen v0.29 using `experiments/entropygraph_v029_residual_strict.py` from SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`, with fail-closed `cmpct.*` provenance.

Analytics beating EG07 proves general density value. Analytics beating v0.29 would be especially important but is **not required** for this transfer pass; the frozen Genesis gap there is large enough that one mechanism need not close it alone.

## Preservation

No numeric release/version, format revision, locality limit, reader semantics, recovery guarantee, Genesis score or ONE evidence changes. `research/cmpct1` remains untouched.
