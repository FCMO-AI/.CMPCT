# v0.30 EG08 ladder stopping-oracle result — 2026-09-13

Status: **all frozen shallow stopping predicates falsified; research negative evidence**

Exact measured head: `b4fa7bd0420f2ac7786990836b38ea123a6154e1`

Hosted run: `34765605838`

Job: `103745897300`

Artifact: `10320286223`

Artifact digest: `sha256:ca0523bc2cb74870fa806bd055e1a911d175fb927c3dd4f88df42cf055ba7929`

The counterfactual referee was valid: all nine frozen eligible surfaces built and strongly verified under EG07 and EG08, locality geometry matched, and full-ladder replay reconstructed the actual EG08 physical payloads before any stopping predicate was scored.

## Aggregate verdicts

| Predicate | Status | Pack mismatches | Stored-byte penalty | Avoided calls | Avoided call share | Avoided measured CPU share | Office RAW promotions |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P1 stop after level 3 with no strict win | **FALSIFIED** | 42 | +2,486 B | 996 | 25.75% | 38.28% | **breaks** |
| P2 stop after levels 3+6 with no strict win | **FALSIFIED** | 25 | +2,459 B | 774 | 20.01% | 37.94% | **breaks** |
| P3 stop after two consecutive storage ties | **FALSIFIED** | 25 | +2,459 B | 774 | 20.01% | 37.94% | **breaks** |
| P4 stop when levels 3 and 6 have same stored size | **FALSIFIED** | 537 | +41,836 B | 1,798 | 46.48% | 47.43% | **breaks** |
| P5 after non-winning level 3 skip 6+12 but still run 19 | **FALSIFIED** | 17 | +6 B | 808 | 20.89% | 28.05% | **preserves** |

No predicate is an exact-EG08 seed. Per the preregistered contract, no sixth threshold-tuned stopping heuristic is introduced in the same activation.

## Important counterexamples

### Office

The full oracle observed two RAW-incumbent promotions in the EG08 ladder domain. P1-P4 suppress at least one of them. A representative cold-stream pack remains RAW through the early ladder but is improved by level 19 from `63,972 B` to `61,553 B`, a **2,419 B** win. This is separate from the already-proven EG11 ordinary RAW-incumbent correction that recovered the much larger `129,782 B` Office loss seen in EG10.

P5 deliberately retains level 19 and therefore preserves the Office RAW promotions, demonstrating that the high-effort escape hatch is causally important.

### Analytics

P5 still fails one Analytics pack: the exact EG08 choice is a level-12 frame of `151 B`, while jumping from level 3 to 19 leaves `157 B`, a **+6 B** product loss. This is enough to falsify exact identity even though the aggregate byte penalty is small.

### Large Mixed

The low-yield attribution had shown that `97.5%` of measured ladder CPU was spent on bytes not retained. The oracle explains why shallow early stopping is nevertheless unsafe:

- P1 loses 40 packs / 56 B;
- P2/P3/P4 lose 24 packs / 40 B;
- P5 preserves total stored size on 16 mismatched packs but produces different same-size Zstd frames because EG08 selected level 6 while the jump reaches another equal-size representation.

A same-size frame is not byte identity. Under the exact-EG08 contract those 16 rows remain mismatches rather than being relabeled wins.

### Hostile false neighbours

P4 is especially unsafe outside the low-yield examples: it breaks **512** packs in the hostile false-neighbour family and costs **39,377 B**. Equal early candidate sizes therefore do not establish future futility.

## Interpretation

The previous attribution remains valid: low-yield creation cost is overwhelmingly proof traffic. This oracle adds a second, equally important result: **that proof traffic cannot be removed safely by a shallow rule over the first one or two compressed sizes.** Future improvement needs either:

1. reuse of work/state across effort levels while preserving the exact selected bytes; or
2. a genuinely stronger opportunity/lower-bound signal that can prove a later effort cannot improve the incumbent without executing the full frame.

The repository already contains counterexamples to RAW-stop, tie-stop and intermediate-level skipping. Reintroducing those ideas under slightly different constants would be threshold tuning, not new mechanism evidence.

No Genesis/R4 score, v0.29 comparator, locality/integrity/recovery law, format revision, numeric version or ONE status changes from this negative result.
