# F-01 structural transfer + AOM preregistration

Status: **Foundry transfer freeze / research only / no release credit**.

This experiment follows the accepted F-01 `CAUSAL_SEED` result. It does not add operators or change O0.1 serialization/search semantics. It asks whether the causal composition capability transfers across structural variation and whether its addressable gain plausibly pays for its search vocabulary.

## Frozen grammar

Unchanged from O0.1:

- DIRECT terminal;
- LANE widths `{2,4,8,16}`;
- DELIM candidates from the existing deterministic ranker;
- one SPLIT/CONCAT at the existing 4 KiB grid;
- exact reconstruction;
- all representation/program/control/terminal bytes charged;
- search wall time may remain gifted as Foundry evidence only.

A scoped-pruning A/B may remove LANE[2] and LANE[4] because the accepted causal result classified them as liabilities on the old regime. That A/B is evidence, not a silent grammar mutation.

## Structural-transfer challenge

The transfer generator is post-causal-freeze and must not reuse frozen case names, bytes or hashes. It varies causal dimensions rather than seeds only.

Positive structural families:

1. **mixed lane + delimited records** with new arithmetic generators, varying:
   - scale: approximately 32, 64 and 128 KiB;
   - active lane width: 8 or 16;
   - delimiter byte/frequency;
   - low-rate deterministic noise;
   - split location on different 4 KiB grid points.
2. **adjacent heterogeneous lane fields** with new arithmetic generators, varying:
   - 8->16 and 16->8 ordering;
   - unequal region sizes;
   - deterministic low-rate perturbation;
   - split location.

Hostile/negative families:

- random-like bytes with identical size envelope;
- false delimiter density without record structure;
- homogeneous single-lane data where composition should not be needed;
- mixed structure whose causal boundary is deliberately off the frozen 4 KiB split grid.

The off-grid cases are not expected to win. They measure a known representational reach limit rather than justify moving the split grid after seeing results.

## Materiality

Reuse the frozen O0.1 materiality rule:

- saving >=128 bytes; and
- saving >=0.5% versus the exact one-stage manual control.

A `material_transfer_win` requires the exact best program to start with SPLIT and satisfy both thresholds.

## Initial Addressable Opportunity Mass

For this deterministic transfer corpus report separately for positive and all cases:

- logical bytes;
- cases/bytes satisfying the intended structural predicate by construction;
- cases/bytes with a material exact composition win;
- addressable byte fraction;
- conditional saving fraction inside material winners;
- `addressable_gain = material_win_bytes × conditional_saving_fraction`;
- hostile false-win count and bytes;
- corpus-bias/confidence label.

This first AOM estimate is **synthetic and low-confidence by design**. It cannot satisfy HANDOFF_READY alone. A surviving thesis must later face independent/public real-data opportunity scanning before product handoff.

## Search carrying cost

For both the full frozen grammar and the preregistered `{8,16}` lane-width-pruned A/B, report:

- candidate states generated/costed;
- exact-bound prunes;
- split points;
- search wall time (gifted, diagnostic only);
- exact optimum bytes/motif per case;
- total nominations per logical MiB.

The pruning A/B is successful only if it preserves exact optimum bytes and motif on every transfer/hostile case while reducing total generated/costed states. If any case changes, widths 2/4 remain part of the research grammar for future freezes.

## Decisions

### `TRANSFER_ADVANCE`

Return only if all hold:

- at least four material transfer wins;
- material wins span both positive structural families;
- at least two non-seed causal dimensions vary among winners (e.g. ordering/scale/noise/boundary placement);
- hostile material false wins = 0;
- exact reconstruction passes all cases;
- at least 25% of positive structural logical bytes are material winners;
- conditional saving over material-winner bytes is >=2%;
- the pruned `{8,16}` A/B preserves every exact optimum and reduces generated/costed states.

Interpretation: advance F-01 to `TRANSFER`, preserve the concept-compression option, and next obtain independent/public real-data AOM plus admission/carrying-cost evidence before HANDOFF_READY.

### `TRANSFER_NARROW`

Return when exact material wins exist but any `TRANSFER_ADVANCE` breadth/AOM/pruning condition fails without hostile false wins or evidence conflict.

Interpretation: narrow the structural predicate or distill a simpler primitive. Do not add vocabulary to rescue breadth.

### `TRANSFER_FAIL`

Return when no material positive-family transfer win survives, or any hostile negative receives a material composition win.

Interpretation: preserve the scoped negative and subject F-01 to hostile thesis review; operator expansion is not an automatic remedy.

### `TRANSFER_EVIDENCE_CONFLICT`

Return on deterministic generator/fingerprint drift, exact reconstruction failure, or inability to reproduce the accepted causal seed metadata required by the instrument.

Interpretation: stop and repair evidence custody only under a superseding freeze.

## Oracle Gift Ledger

Gifted:

- search/discovery wall time.

Never gifted:

- program/control/terminal bytes;
- exact reconstruction;
- structural predicate labels used for AOM accounting.

Deferred after this freeze:

- real/public corpus AOM;
- cheap generic nomination/admission;
- canonical framing/index;
- locality/recovery/integrity;
- native/platform;
- product create/extract/verify economics;
- full frozen release matrix.

## Strongest hostile explanation

The causal seed may simply encode two hand-obvious regions using known transforms. Transfer breadth and carrying-cost evidence must therefore favor a compact reusable segmentation capability; a large reader-visible compiler/DSL is not the default product conclusion even if this test advances.

## Immutability

Once result-bearing execution begins, material changes to challenge generators, thresholds, decisions, grammar or accounting require a new superseding freeze. Unfavorable evidence cannot alter this contract.
