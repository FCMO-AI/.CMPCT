# v0.30 reactivation — Genesis density deficit map (2026-09-11)

Status: **primary near-term research line reactivated after CMPCT1 / ONE Genesis gate**

Exact reactivation base: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

This note is a mechanism-level triage record, not a new benchmark or release claim. It uses the completed same-input Genesis matrix only to identify where the reactivated v0.30 line should investigate first. It does not authorize workload-name dispatch or gate-specific tuning.

## Frozen Genesis aggregate

Same physical logical input: `265,969,714 B`.

- v0.29: `137,499,525 B`
- frozen v0.30 product: `150,055,575 B`
- v0.30 net gap to v0.29: `+12,556,050 B`
- v0.30 density wins vs v0.29: `9/15`
- v0.29 density wins vs v0.30: `6/15`

v0.30 nevertheless beats v0.29 creation CPU on all 15 Genesis rows. The near-term objective is therefore **recover density without surrendering the large compute advantage**, not to re-run v0.29's expensive search indiscriminately.

## Six v0.30 density losses

| Workload | v0.29 | v0.30 | v0.30 deficit |
|---|---:|---:|---:|
| `02_office_workspace` | 5,954,026 | 15,445,458 | **+9,491,432** |
| `04_analytics_and_database` | 6,135,172 | 10,392,494 | **+4,257,322** |
| `08_many_tiny_files` | 420,318 | 722,674 | +302,356 |
| `01_developer_repository` | 744,337 | 870,602 | +126,265 |
| `07_incompressible_and_encrypted_like` | 10,193,958 | 10,218,575 | +24,617 |
| `04_deflate_family` | 14,597 | 17,754 | +3,157 |

Gross loss across these six rows is `14,205,149 B`. The nine winning rows recover `1,649,099 B`, yielding the `12,556,050 B` aggregate gap.

**Office + analytics alone account for ~96.79% of the gross deficit.** They exceed the entire net aggregate gap because v0.30's nine winning rows partially compensate them. This makes them the first causal research targets; tiny-file metadata is second-tier by aggregate impact even though it remains architecturally important.

## Product-selection evidence

The frozen release product exposes a recurring pattern on all six losing rows: the published archive is `r24-fallback`, even when the internal r25 research portfolio can construct a much smaller v0.29-derived research floor.

Observed first-sample selection facts from the source-sealed v0.30 dossier:

| Workload | published r24 | internal v0.29 research floor | r25 selected candidate |
|---|---:|---:|---|
| developer repository | 870,602 | 750,662 | v0.29 fallback |
| office workspace | 15,445,458 | 5,954,330 | v0.29 fallback |
| analytics/database | 10,392,494 | 6,135,344 | v0.29 fallback |
| incompressible/encrypted-like | 10,218,575 | 10,198,278 | v0.29 fallback |
| many tiny files | 722,674 | 443,583 | v0.29 fallback |
| deflate family | 17,754 | 14,833 | v0.29 fallback |

The release-product claim boundary requires a canonical r25 candidate to be strictly smaller than both the concurrently built canonical-r24 product and the accepted v0.29 research floor. Merely reconstructing the v0.29 floor inside the portfolio is therefore intentionally insufficient for publication.

This means the immediate problem is **not simply “the selector forgot to choose the smaller internal candidate.”** Promoting the research fallback as product without satisfying r25/native/recovery/format authority would weaken the release contract and manufacture a win. The correct research question is what general predictive/physical structure can make a product-eligible v0.30 candidate beat that floor under the existing locality/integrity/recovery rules.

## Mission Lock / falsifiable hypotheses

### H1 — office + analytics dominate because the shipping r24 physical representation misses cross-member / resemblance structure already captured by the v0.29 research floor

**Prediction:** a mechanism-level decomposition of the internal v0.29 floor on these two rows will attribute most of the 13.75 MB combined gap to a small number of general relation/packing classes rather than broad entropy-coder differences.

**Disproof:** if attribution shows the advantage is mostly a format/accounting artifact, metadata-only delta, or a diffuse collection of unrelated gains with no reusable structure, do not build a new generalized mechanism on this premise.

**Next experiment:** instrument the frozen v0.29-floor builder on these two rows to emit byte-attribution by accepted engine/record type, including direct payload, resemblance/delta, pack/locality metadata, preflate, manifest/index, integrity bytes and fallback reason. Run held-out controls from the nine v0.30-winning rows to reject a gate-specific policy.

### H2 — the fastest route is not to copy v0.29 search wholesale, but to recover its high-yield nominations behind a cheap v0.30 opportunity gate

**Prediction:** candidate-generation/proof traffic can be restricted to a sparse set of high-yield opportunities while retaining most of the v0.29 density recovery, preserving a material fraction of v0.30's creation-CPU advantage.

**Disproof:** if recovering the byte advantage requires near-v0.29 search/proof work on broad hostile controls, the mechanism is not a v0.30 Pareto improvement; preserve the negative result.

**Measurement:** bits/bytes eliminated per extra creation CPU second, wall second, RSS and source/proof bytes. Do not promote on stored bytes alone.

### H3 — tiny-file loss is likely a fixed-control/metadata productization problem, but it is not the first aggregate blocker

Many-tiny-files loses `302,356 B`; this is important but only ~2.13% of the six-row gross deficit. Investigate after the office/analytics owner is localized unless a shared control-plane fix emerges naturally.

## Constraints

- No workload-name/path/hash dispatch.
- No weakening the strict r25 publication floor.
- No relabeling the research v0.29 fallback as a canonical v0.30 win.
- Preserve current locality ceilings, integrity, recovery, reader/native parity and hostile-resource requirements.
- Reuse ONE's Genesis lesson only at the method level: fused observation, sparse opportunity gating, cheap falsification, branch-and-bound, reusable discovery caches, and proof work proportional to expected information yield.
- Any candidate must face the nine rows where v0.30 already wins plus neutral hostile controls so the fix cannot simply trade one side of the matrix for the other.

## Next decisive action

Build a **read-only attribution instrument** first. It must not change archive selection. On `office_workspace` and `analytics_and_database`, decompose the internal v0.29-floor savings relative to shipping r24 into mechanism/record classes and account discovery/proof CPU. Run the same instrument on representative v0.30-winning controls. Only after a dominant reusable cause is proven should implementation begin.
