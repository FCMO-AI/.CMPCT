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

## First attribution pass — H1 partially falsified

The first causal hypothesis was that the office/analytics gap was mainly later v0.28/v0.29 resemblance/Mosaic discovery. The retained source-sealed product stats disprove that framing.

For the four largest practical r24-fallback losses inspected (`office`, `analytics`, `many_tiny_files`, `developer_repository`), the internal chain is:

`v0.30 r25 portfolio -> v0.29 -> v0.28 -> exact inherited v0.25 fallback`

The later graph candidates lose to the inherited v0.25 archive on all four rows. In particular:

- office: v0.29/v0.28 selected inherited v0.25 at `5,954,330 B`; the v0.28 graph was `11,747,181 B` and the attempt5/Mosaic graph `11,632,888 B`;
- analytics: inherited v0.25 `6,135,344 B`; v0.28 graph `9,720,003 B`, attempt5/Mosaic graph `9,720,105 B`;
- many tiny files: inherited v0.25 `443,583 B`; v0.28 graph `872,249 B`;
- developer repository: inherited v0.25 `750,662 B`; v0.28 graph `856,917 B`.

So the immediate owner is **not “restore more Mosaic search.”** The dominant missing shipping capability is older: proven EntropyGraph-v0.25 physical representation families remain research-only while the v0.30 release facade must publish r24 unless a new product-eligible terminal beats both r24 and the research floor.

### What v0.25 is exploiting on the dominant rows

The retained v0.25 stats narrow the structural classes further:

**Office workspace**
- `stream_pool = 3,791,492 B`
- `stream_slabs = 12`, `hot_stream_slabs = 10`
- `derived = 8`, `special = 5`
- `packs = 22`, `micro_groups = 3`

**Analytics/database**
- `stream_pool = 3,556,593 B`
- `stream_slabs = 8`, `hot_stream_slabs = 7`
- `derived = 1`, `special = 1`
- `packs = 58`, `micro_groups = 1`

By contrast, tiny-files and developer-repository have `stream_pool = 0`; their inherited-v0.25 advantage is dominated by compact packing/control-plane structure (`packs = 4`, `micro_groups = 3` for tiny files; `packs = 22`, `micro_groups = 15` for developer repository) rather than stream federation.

This creates two separable productization lanes rather than one vague “v0.29 density” problem:

1. **stream federation / derived-view productization** — dominant aggregate target, office + analytics;
2. **compact pack/control representation** — smaller aggregate target, tiny files + developer repository.

The current public EntropyGraph authority already describes v0.25's durable information model as exact compressed-stream federation, directional inverse views, exact object interning, compact micro-pack indexing, bounded context, hot/cold roots, authenticated metadata and operational recovery. Any v0.30 repair should productize the useful structure one reader-visible representation at a time instead of copying the entire CMPNX5 research container wholesale.

## Revised Mission Lock / falsifiable hypotheses

### H1R — productizing a bounded stream-federation primitive can recover most of the office/analytics gap without importing v0.25's entire research format

**Prediction:** a read-only byte attribution of the v0.25 office/analytics archives will show that a small bounded set of stream-pool/slab/derived-view records owns a material majority of the `13,748,754 B` combined v0.30 deficit on those two workloads.

**Disproof:** if the advantage is diffuse across unrelated format-wide metadata/entropy effects, or if the useful records require unbounded solid context / unacceptable random-access or recovery coupling, do not productize a stream-federation primitive from this evidence.

**Next experiment:** instrument the inherited v0.25 writer read-only to report physical stored bytes and reconstructed logical bytes per record family plus selective-read dependency/context. No archive-selection changes.

### H2 — the reactivated v0.30 implementation can recover high-yield v0.25 structures behind a cheap opportunity gate

**Prediction:** source-only observations can cheaply identify stream-federation/derived-view opportunities and avoid invoking expensive graph search on controls, retaining a material fraction of v0.30's creation-CPU advantage.

**Disproof:** if recovering the density requires broad v0.25/v0.29 portfolio construction or near-v0.29 search/proof work on hostile controls, the mechanism is not a v0.30 Pareto improvement; preserve the negative result.

**Measurement:** bytes eliminated per extra creation CPU second, wall second, RSS and source/proof bytes. Do not promote on stored bytes alone.

### H3 — tiny-file/developer gaps are a distinct compact-control/pack productization lane

Many-tiny-files loses `302,356 B` and developer-repository `126,265 B`. Their inherited-v0.25 stats show no stream pool, so they should not be used to justify the stream-federation mechanism. Investigate compact pack/control representation separately unless a genuinely shared lower-level primitive emerges.

## Constraints

- No workload-name/path/hash dispatch.
- No weakening the strict r25 publication floor.
- No relabeling the research v0.29/v0.25 fallback as a canonical v0.30 win.
- Preserve current locality ceilings, integrity, recovery, reader/native parity and hostile-resource requirements.
- Reuse ONE's Genesis lesson only at the method level: fused observation, sparse opportunity gating, cheap falsification, branch-and-bound, reusable discovery caches, and proof work proportional to expected information yield.
- Any candidate must face the nine rows where v0.30 already wins plus neutral hostile controls so the fix cannot simply trade one side of the matrix for the other.

## Next decisive action

Build a **read-only v0.25 physical attribution instrument** first. For `office_workspace` and `analytics_and_database`, quantify actual stored bytes and reconstructed logical coverage by stream-pool/slab, derived/special, packs/micro-groups, metadata/integrity and direct records; also record selective dependency/context and construction CPU. Run the same instrument on representative controls where v0.30 already wins.

Only after one bounded record family is shown to own a material share of the gap under acceptable locality/recovery cost should a v0.30 product primitive be implemented. The first hypothesis to test is stream federation / derived views, not later Mosaic resemblance.
