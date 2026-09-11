# ONE-G0.3 block-adaptive Statistical Law result

**Date:** 2026-09-11  
**Status:** `ADVANCE_BLOCK_ADAPTIVE_STATISTICAL_LAW` — information/coding-model evidence only; not Genesis authority and not product promotion  
**Preregistered design:** `docs/one/prereg/ONE_G03_BLOCK_ADAPTIVE_STATISTICAL_LAW_PREREG_2026-09-11.md`  
**Diagnostic source:** `9b61c0f247ec33472191779c7d4122a05b82bc1f`  
**Hosted workflow:** run `34599182119`, job `103262050961`  
**Artifact:** `10263632833`, zip SHA-256 `fcf883ea8610b25b34ebaab714901a5247eaac73513a3abfdebdef08a97f79d9`

## Mission lock

The hypothesis was that a reader-reproducible, block-local previous-byte Statistical Law can recover a material part of the information that frozen ONE-G0.2 leaves in Surprise, without storing a learned model and without a second source pass.

The disproof gate was fixed before execution: exact 15 Genesis identities; one source observation pass; 64 KiB resets; symmetric KT alpha=0.5; 8 bytes framing charge per non-empty block; zero stored learned-model bytes; at least two of the three target workloads at or below 0.75 modeled ratio; at least one target saving at least 5 MiB; and the two incompressible controls at or above 0.98 ratio.

Hosted CI returned `ADVANCE_BLOCK_ADAPTIVE_STATISTICAL_LAW`. This is evidence for the Law family, not a real compressor result.

## Exact result

| workload | logical B | charged modeled B | modeled ratio | modeled saving B | observation CPU s |
|---|---:|---:|---:|---:|---:|
| neutral / 01_developer_repository | 2,624,373 | 1,573,063 | 0.599405x | +1,051,310 | 0.2154 |
| neutral / 02_office_workspace | 16,063,798 | 15,902,392 | 0.989952x | +161,406 | 0.1329 |
| neutral / 03_media_library | 28,841,872 | 29,151,269 | 1.010727x | -309,397 | 0.2429 |
| neutral / 04_analytics_and_database | 31,265,767 | 16,743,238 | 0.535513x | +14,522,529 | 0.1350 |
| neutral / 05_logs_and_telemetry | 16,994,250 | 8,719,542 | 0.513088x | +8,274,708 | 0.0633 |
| neutral / 06_incremental_backups | 14,006,619 | 12,414,720 | 0.886347x | +1,591,899 | 0.2140 |
| neutral / 07_incompressible_and_encrypted_like | 10,182,899 | 10,520,669 | 1.033170x | -337,770 | 0.2947 |
| neutral / 08_many_tiny_files | 736,546 | 754,952 | 1.024990x | -18,406 | 0.8107 |
| neutral / 09_ml_artifacts | 18,172,774 | 15,001,437 | 0.825490x | +3,171,337 | 0.1231 |
| neutral / 10_large_mixed_binary | 33,554,432 | 15,325,835 | 0.456745x | +18,228,597 | 0.1618 |
| resemblance / 01_shifted_versions | 33,525,242 | 32,172,951 | 0.959663x | +1,352,291 | 0.3062 |
| resemblance / 02_false_neighbors | 39,524,435 | 37,040,755 | 0.937161x | +2,483,680 | 0.4202 |
| resemblance / 03_boundary_churn | 9,744,144 | 2,809,361 | 0.288313x | +6,934,783 | 0.0444 |
| resemblance / 04_deflate_family | 126,270 | 60,994 | 0.483044x | +65,276 | 0.0030 |
| resemblance / 05_incompressible | 10,606,293 | 10,950,830 | 1.032484x | -344,537 | 0.1028 |

Across all 15 identities, the diagnostic modeled `209,142,008 B` from `265,969,714 B` logical (`0.786338x`) after its explicit block-framing charge, for `56,827,706 B` modeled saving. That aggregate is **not** a product claim: it excludes a real entropy-coder wire format, archive/ONE control metadata, integrity structure, selective index, coder finalization overhead, and production reader cost.

The three preregistered targets all cleared the 0.75 ratio gate:

- analytics/database: `0.535513x`, `14,522,529 B` modeled saving;
- logs/telemetry: `0.513088x`, `8,274,708 B` modeled saving;
- large mixed binary: `0.456745x`, `18,228,597 B` modeled saving.

Combined target opportunity is `41,025,834 B` under this model. Boundary churn also showed a large `0.288313x` opportunity (`6,934,783 B` modeled saving).

Both incompressible controls correctly stayed above unity: `1.033170x` and `1.032484x`. The media workload also slightly expanded (`1.010727x`), and many-tiny-files expanded (`1.024990x`). These negatives are useful: a product writer needs opportunity gating and Surprise fallback rather than applying this Law universally.

## Compute and state

The diagnostic read every workload source byte once. Summed observation CPU was `3.270488 s`; summed wall time was `3.270865 s`. Peak process RSS observed across rows was about `482.2 MB`, but this is a Python/NumPy process measurement and must not be presented as the intrinsic Statistical Law state footprint.

The bounded target model is one 256x256 count table plus row totals, reported as `263,168 B`; state resets at every file and every 64 KiB block. No learned probability table is serialized. The diagnostic's NumPy implementation may use larger transient memory and extra internal memory traffic; that debt is deliberately unpaid here.

## Interpretation

This materially changes the causal reading of the G0.2 negative. G0.2 accepted zero root-level Laws over 9,253 roots, but this test demonstrates that a large amount of predictable local statistical structure exists on the same fixed Genesis inputs and can be represented by a single generic causal Law family rather than by a legacy codec opcode.

It does **not** show that ONE has closed the Genesis density gap. The result is an ideal prequential coding-length model plus explicit block framing, not emitted authenticated ONE bytes. A real implementation can lose materially to arithmetic/rANS normalization, frequency-table mechanics, metadata, Crystallization/indexing, branch decisions, small blocks, integrity, and reader implementation cost.

## Hostile review / strongest negative

The main remaining falsifier is productization cost. A model that looks excellent in codelength can still be the wrong mechanism if the writer/reader spends too much CPU, memory traffic, or wire overhead to realize it. In particular:

- the Python/NumPy observer is not a production cost model;
- a 256-symbol adaptive coder per context needs a fast bounded frequency/update representation;
- selective reconstruction requires explicit block Crystallization/index semantics;
- media and incompressible rows prove unconditional application is wrong;
- many-tiny-files remains dominated by fixed costs and should not inherit a heavy Statistical Law path without a cheap opportunity gate.

## Next decisive experiment

Implement the smallest real generic Statistical Law path, still within ONE ontology:

1. 64 KiB independently reconstructable blocks;
2. previous-byte adaptive KT-style predictor with no stored learned model;
3. a real bounded entropy coder and deterministic reader;
4. cheap preflight opportunity gate that can choose Surprise without paying full coding work;
5. exact wire-byte accounting including Law description, block framing, integrity and selective index;
6. creation CPU/wall/RSS and decode/selective-read work measured against Surprise-only G0.2 on the same fixed inputs.

Promotion requires causal gain after **real bytes and real compute** are charged. Until then the correct claim is only: `ADVANCE_BLOCK_ADAPTIVE_STATISTICAL_LAW`.