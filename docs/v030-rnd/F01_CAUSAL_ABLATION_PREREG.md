# F-01 causal ablation preregistration

Status: **Foundry causal test / frozen when committed / research only / no release credit**.

This experiment follows the accepted F-01/O0.1 `ADVANCE_COMPOSITION` receipt. It does not add operators, change the frozen O0.1 cost model, change the accepted witness corpus, or reinterpret the old result.

## Question

> Are the operators participating in the accepted O0.1 composition wins actually causally necessary for those exact byte savings, and does the existing LANE parameter set contain removable search liabilities on the tested regime?

The experiment is deliberately narrower than O0.2. It must answer causality before vocabulary growth.

## Frozen witness

The accepted O0.1 witness is fixed to:

- O0.1 evidence source/seed: `c3ef298bcc3fb7f95a65245c9341f112581aa175`;
- schema: `cmpct-v030-foundry-f01-o01-v2`;
- corpus fingerprint: `6b6438aff98e7a9e69ee834fe3f2135cc03acde0babac42100c544519e56c574`;
- material composition winners:
  - `discovery_mixed_lane_records`;
  - `discovery_mixed_lane_widths`;
  - `transfer_postfreeze_mixed_shifted`.

The causal experiment must regenerate these exact bytes from the public deterministic generators and assert the expected O0.1 synthesized/manual byte counts before interpreting any ablation.

## Allowed intervention

Only **operator removal from the already-frozen grammar** is allowed.

For each accepted material witness:

1. remove SPLIT by forcing the exact whole-target one-stage manual frontier;
2. remove LANE from the candidate set when the winning motif contains LANE;
3. remove DELIM from the candidate set when the winning motif contains DELIM.

The remaining grammar/search/cost semantics are unchanged. Search stays exact within the same 4 KiB split grid and uses no heuristic pruning.

A second scoped liability pass removes each existing LANE width `{2,4,8,16}` one at a time across the complete accepted O0.1 case set. No new width or transform is introduced.

## Causal metric

For an accepted winner and removed operator family `F`:

`unique_contribution_F = best_bytes_without_F - accepted_full_bytes`

Because serialized bytes are deterministic, any strictly positive value is exact evidence that `F` participates in the minimum description inside the frozen grammar on that witness.

For SPLIT, the stronger expectation is that the ablated result equals the accepted one-stage manual control, thereby erasing the complete composition gain.

No percentage threshold is invented post hoc; the original O0.1 materiality threshold already established that the full composition gain matters.

## LANE-width liability rule

A LANE width is a **scoped search liability** only if removing it changes neither:

- exact best synthesized bytes; nor
- exact best synthesized motif

on **any** accepted O0.1 discovery, hostile, or transfer case.

This is a conditional result for this frozen regime only. It does not prove the width globally useless and does not authorize product removal. Reopening requires new structural evidence showing that width affects a materially relevant exact optimum.

## Decisions

### `CAUSAL_SEED`

Return when:

- SPLIT has strictly positive contribution on every accepted composition winner and its removal restores the exact manual-control size;
- every non-SPLIT structural family appearing in a winner has strictly positive unique contribution on that witness;
- exact reconstruction remains true for every ablated winner;
- the accepted witness counts/fingerprint match exactly.

Interpretation: compositional headroom is not merely a bookkeeping artifact; proceed to broader structural transfer/AOM/carrying-cost work. Scoped lane-width liabilities may be pruned from later search instruments only through a new superseding freeze.

### `SIMPLER_PRIMITIVE_SIGNAL`

Return when SPLIT is necessary but one participating transform family has zero unique contribution on a supposed winner, indicating that the result can be explained by a simpler composition than the accepted motif suggests.

Interpretation: distill/restate the causal primitive before more transfer work.

### `CAUSAL_RESULT_CONFLICT`

Return when the regenerated accepted witness does not match the immutable O0.1 byte counts/fingerprint, exact reconstruction fails, or SPLIT removal does not restore the accepted manual-control result.

Interpretation: stop thesis advancement and investigate evidence/instrument drift. Do not edit O0.1 history.

## Oracle Gift Ledger

Gifted:

- ablation search wall time.

Never gifted:

- program/control bytes;
- terminal bytes;
- exact reconstruction;
- accepted O0.1 comparator/witness bytes.

Deferred debt remains O1/O2 discovery economics, archive framing/index, locality, recovery, hostile parser/fuzz, native/platform, product runtime, AOM and global mechanism carrying cost.

## Strongest hostile explanation

The three winners may simply encode a manually obvious segmentation of two known transforms. Even a `CAUSAL_SEED` result therefore does not justify canonicalizing a compiler. It only proves that composition itself has exact description value inside the frozen regime. Later work must test structural transfer and whether a smaller distilled primitive captures the value with less carrying cost.

## Immutability

Once this file, the causal instrument and its workflow are committed and result-bearing execution begins, material changes require a new superseding preregistration/freeze. An unfavorable result may not alter these decision rules.
