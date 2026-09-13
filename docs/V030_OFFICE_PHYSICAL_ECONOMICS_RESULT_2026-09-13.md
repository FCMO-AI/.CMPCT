# v0.30 Office physical-economics attribution result — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `efd33ff0dbf3b270ff9491f0490c1fc56da9418a`
Hosted run: `34761870549`
Receipt artifact: `10319555971`
Artifact digest: `sha256:6c9844e2c7f90cff29950f9a33e8a931c0a7008e260c3bb4f88fec1d389f6fcc`
Scientific verdict: `OFFICE_PHYSICAL_LOCALITY_DOMINATES_REGRET`

## Comparator repair

The first Office attribution run correctly source-sealed a frozen v0.29 checkout but invoked the shipping `cmpct.builder.Builder`. That was the wrong historical product surface and produced `15,454,453 B`; its automatic causal verdict was therefore withdrawn.

The repaired referee recovered the exact Genesis authority from `benchmarks/one/one_genesis_historical_product_worker.py` at harness `7e14e6867a329bc3281e9016e673c46dc3feb081`. Genesis defines frozen v0.29 as:

- source SHA `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- product module `experiments/entropygraph_v029_residual_strict.py`;
- fresh-process build through that module;
- fail-closed provenance for every loaded `cmpct.*` module under the frozen checkout.

The repaired Office receipt records that exact module path and frozen `cmpct`, `cmpct.mosaic`, and `cmpct.resemblance` import roots. The resulting frozen v0.29 artifact is `5,954,929 B`, selected through the inherited EntropyGraph-v0.25 fallback inside the accepted v0.29 portfolio. This is the same contender semantics as Genesis, executed on the current deterministic Office tree rather than substituted from an old numeric row.

## Same-payload control-plane ablation

Office tree:

- logical bytes: `16,063,803 B`;
- tree SHA-256: `ba72464747d4e3c129d91077c30f0c17c97fcb9bf5fc997cfe7001e234998934`.

B and C were produced from one immutable physical archive. Their physical-region SHA-256 and membership SHA-256 are identical; only the authenticated filesystem-control bytes differ.

| Stage | Stored bytes | Control raw | Metadata compressed | Max amp | Max decode unit |
| --- | ---: | ---: | ---: | ---: | ---: |
| frozen v0.29 Genesis surface | **5,954,929 B** | — | — | historical research surface | — |
| B — same physical + explicit filesystem control | `6,439,399 B` | `1,798 B` | `2,343 B` | `4.00113x` | `524,288 B` |
| C — same physical + implicit-v4 | `6,437,555 B` | `243 B` | `1,421 B` | `4.00113x` | `524,288 B` |
| D — current EG07 product-valid research candidate | `6,437,719 B` | `241 B` | `1,503 B` | `4.00113x` | `524,288 B` |

B -> C saves exactly **1,844 B** while holding physical payload and membership fixed.

B regret versus the exact frozen v0.29 surface is **484,470 B**. The control-plane substitution therefore recovers only **0.3806%** of that same-run regret, far below the preregistered 10% disproof threshold.

Both B and C preserve:

- exact filesystem reconstruction;
- strong physical verification;
- primary/tail recovery;
- the existing locality bound;
- identical physical membership and payload bytes.

The measured selective geometry is already substantially inside the release ceiling: maximum member amplification is ~`4.001x`, versus the `8x` ceiling, and maximum physical decode unit is `512 KiB`.

## Interpretation

The result falsifies filesystem-control compression as a material owner of the remaining Office gap. Further implicit-v4/v5/v6 wire-format work cannot plausibly close hundreds of kilobytes while the same physical representation remains in place.

The remaining B regret is overwhelmingly physical: B's physical region alone is `6,434,597 B`, already ~`479.7 KiB` above the entire frozen-v0.29 artifact before charging B's filesystem control and duplicate authenticated metadata.

This result does **not** prove that the 484 KiB is caused specifically by the locality ceiling. The current candidate also deliberately caps the inherited EntropyGraph encoder's Zstd requests at level 1 to preserve v0.30 creation speed, while the mature inherited v0.25 path uses stronger compression effort on ordinary packs. `OFFICE_PHYSICAL_LOCALITY_DOMINATES_REGRET` is therefore a mission-lock classification: the regret lives outside the filesystem control plane, in physical representation / packing / compression-effort economics. The next referee must separate those causes before changing pack geometry.

## Next falsifiable question

Hold the current Office pack membership and raw pack bytes fixed, then recompress those exact decode units at the current level-1 effort and at the mature inherited effort. Measure the counterfactual stored-byte floor and CPU cost without changing relationships, grouping, locality, recovery semantics, or filesystem control.

If stronger compression on identical physical units recovers most of the ~484 KiB regret, the next mission is cheap opportunity gating / selective high effort, not wider packs. If it does not, the remaining owner is representation/geometry and a locality-aware counter-invention is justified.

## Preservation

- Frozen Genesis scores are unchanged.
- `research/cmpct1` and all ONE evidence remain untouched.
- No numeric version, tag, release claim, locality limit, comparator setting, integrity rule, or recovery guarantee changed.
- The invalid shipping-Builder comparison remains negative harness evidence and is not relabeled as a product loss.
