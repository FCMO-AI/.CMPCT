# v0.30 Office same-geometry compression-effort result — 2026-09-13

Status: **research attribution; no release credit**

Exact measured head: `a4bdb3dd46ed672f42081f26df32308260e082d4`
Hosted run: `34762111506`
Receipt artifact: `10319531337`
Artifact digest: `sha256:786817b0da5da25fb65b603a53a27bcfd5e314ebf6b8d5b7a5175c56d4378cf9`
Scientific verdict: **`OFFICE_EFFORT_DOMINATES_PHYSICAL_REGRET`**

## Fixed surface

The referee froze the current Office physical graph:

- Office tree: `ba72464747d4e3c129d91077c30f0c17c97fcb9bf5fc997cfe7001e234998934`;
- logical bytes: `16,063,803 B`;
- physical packs: `28`;
- stream packs: `19`;
- hot inverse-view stream packs: `10`;
- maximum raw decode unit: `524,288 B`;
- B explicit-control artifact: `6,439,405 B`;
- exact frozen Genesis-v0.29 surface: `5,954,929 B`;
- B regret: `484,476 B`.

The frozen comparator again executed `experiments/entropygraph_v029_residual_strict.py` from `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d` with fail-closed `cmpct.*` source provenance. It selected its inherited `v028-fallback`; that fallback reports the same high-level Office structure as the current line: `28` packs, `19` stream slabs, `10` hot stream slabs, `8` derived views and a `3,791,493 B` stream pool.

## Causal result

No pack boundary, raw pack byte, membership relationship, stream offset, locality unit, recovery layout, filesystem control, or reconstruction recipe changed. The referee decoded the current authenticated packs once and repriced those exact raw units at fixed Zstd efforts.

At level 19, preserving hot roots as raw while economically auditioning all other fixed units yields a B-equivalent counterfactual of **`5,954,686 B`**:

- bytes recovered versus B: **`484,719 B`**;
- recovery fraction of B regret: **`100.0502%`**;
- remaining regret versus frozen v0.29: **`-243 B`**.

So the current physical geometry is already sufficient to meet the mature v0.29 Office density floor. The dominant regression is the global v0.30 level-1 compression-effort cap, not missing filesystem semantics and not a need for wider decode units.

## Effort curve

### Existing compressed units only

| Effort | B-equivalent bytes | Recovered | Remaining regret | Re-encode CPU |
| --- | ---: | ---: | ---: | ---: |
| 1 | `6,439,405` | `0` | `484,476` | `0.0064 s` |
| 3 | `6,258,776` | `180,629` | `303,847` | `0.0151 s` |
| 6 | `6,181,569` | `257,836` | `226,640` | `0.0256 s` |
| 12 | `6,178,504` | `260,901` | `223,575` | `0.0360 s` |
| 19 | `6,086,887` | `352,518` | `131,958` | `0.2461 s` |

### Cold-audition, hot roots preserved raw

| Effort | B-equivalent bytes | Recovered | Remaining regret | Re-encode CPU |
| --- | ---: | ---: | ---: | ---: |
| 1 | `6,439,405` | `0` | `484,476` | `0.0075 s` |
| 3 | `6,186,542` | `252,863` | `231,613` | `0.0199 s` |
| 6 | `6,089,597` | `349,808` | `134,668` | `0.0352 s` |
| 12 | `6,084,067` | `355,338` | `129,138` | `0.0469 s` |
| 19 | **`5,954,686`** | **`484,719`** | **`-243`** | `0.3071 s` |

Allowing hot roots to participate does not improve the level-19 byte result; it only raises the measured re-encode CPU to ~`0.4800 s`. Thus no Office density win requires adding a second compression layer to latency-sensitive inverse-view roots.

The current shared physical build itself measured ~`0.1691 s` CPU / wall in this referee. Frozen v0.29 measured ~`23.405 s` CPU / `23.407 s` wall on the same current Office tree. The counterfactual high-effort work is therefore small compared with the mature comparator, but it is not yet a product creation measurement because it runs as a post-build attribution pass.

## Concentration of the opportunity

Four non-stream packs account for **`480,110 B`** of the `484,719 B` level-19 recovery:

- pack 5: `-141,024 B`;
- pack 6: `-140,228 B`;
- pack 4: `-129,782 B`;
- pack 7: `-69,076 B`.

These are not hot stream roots. Most remaining packs buy crumbs or nothing from high effort. This is exactly the shape where a cheap opportunity gate can preserve the v0.30 compute advantage instead of restoring level 19 globally.

A further useful pattern appears without fitting an Office-specific numeric threshold: for the four dominant packs, the sequence `1 -> 3 -> 6 -> 12 -> 19` keeps improving. Several low-yield packs plateau or worsen early. A threshold-free effort ladder that continues only while the next effort is non-worsening is therefore a legitimate mechanism to test next; it must generalize beyond Office before product credit.

## Interpretation

The parent `OFFICE_PHYSICAL_LOCALITY_DOMINATES_REGRET` verdict should now be read more precisely: the regret lived outside the filesystem control plane, but the same physical geometry itself is not deficient. **Compression-effort policy owns the dominant Office density debt.**

This is a favorable result for the reactivated v0.30 mission because it does not require weakening locality. Current Office remains around `4.001x` maximum member amplification with `512 KiB` maximum decode units. The problem can be attacked on the encoder side while keeping the reader/recovery geometry unchanged.

## Next Builder

Build a research-only adaptive effort candidate over the existing EG07 geometry:

1. keep level-1 behavior for discovery probes and metadata so group selection remains unchanged;
2. preserve hot inverse-view roots as their current raw units;
3. for non-hot final physical units, evaluate a fixed effort ladder `1,3,6,12,19`;
4. retain the best frame seen and continue through strict improvements or ties; stop at the first strictly worse step;
5. rebuild the same physical pack table with unchanged raw sizes, hashes, CRCs, membership and reconstruction recipes;
6. strong-verify, recover from tail metadata and re-run locality accounting;
7. measure the *actual rebuilt archive*, creation CPU/wall/RSS and selective-read behavior;
8. transfer the unchanged mechanism to Analytics and hostile/held-out structured workloads before promotion.

The ladder has no Office-derived byte threshold. Its only rule is whether additional effort demonstrably improves the same unit. That makes the causal claim falsifiable without turning this receipt into a corpus-specific selector.

## Preservation

No Genesis score, ONE evidence, release/version state, locality ceiling, recovery guarantee, reader semantics, or comparator setting changed. Counterfactuals in this receipt are not themselves product archives and receive no release credit.
