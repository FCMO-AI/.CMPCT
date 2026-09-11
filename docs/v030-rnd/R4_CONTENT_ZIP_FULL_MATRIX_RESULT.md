# v0.30 R4 content-driven ZIP full-matrix result

**Status:** POSITIVE RESEARCH SEED / HARDENING + ECONOMIC-ADMISSION DEBT OPEN  
**Authority branch:** `agent/v030-authoritative-integration`  
**Exact source head:** `b77daaf169baef02ccbd9fa474338f14d2fd305f`  
**Hosted run/job:** `34639636073` / `103395939123` — SUCCESS  
**Artifact:** `10279427706`, digest `sha256:f0a1f8c615dac7d835b77890a2032ca334d2923ac19471bbabda0911e28de02c`  
**Shipping credit:** none

## Mission lock

The Office oracle proved that six content-valid OOXML containers can use the already-existing revision-24 `S_VZIP` representation at original paths and recover about 8.98 MB with exact extraction and exact selective ranges. The full-matrix question was whether broad content-driven discovery generalizes across the exact repaired 15-workload substrate without silently regressing unrelated data.

Hypothesis:

> Bounded content discovery into the unchanged `S_VZIP`/existing container representation can retain the Office breakthrough across the full frozen workload matrix with exact trees, exact sampled VZIP ranges and zero deterministic byte regressions.

The experiment compares the unchanged shipping `Builder` directly with the research-only `ContentZipBuilder`; it does not modify the shipping Builder, reader grammar, on-disk format, accepted v0.29 authority or Genesis result.

## Result

Aggregate over 15 workloads:

| Metric | unchanged Builder | ContentZipBuilder | Delta |
|---|---:|---:|---:|
| complete archive bytes | **181,603,038 B** | **172,617,215 B** | **-8,985,823 B / -4.9481%** |
| creation CPU | **7.7748 s** | **10.2818 s** | **+2.5070 s** |
| byte-regressed rows | — | **0/15** | — |
| strictly improved rows | — | **2/15** | — |

Correctness/access invariants:

- exact reconstructed product tree: **15/15**;
- exact sampled 4 KiB start/middle/end ranges for every emitted `S_VZIP`: **pass**;
- format revision: unchanged;
- reader grammar: unchanged;
- shipping Builder: unchanged.

Only two rows became smaller:

### Office workspace

- baseline: `15,445,452 B`;
- candidate: `6,460,538 B`;
- saving: **8,984,914 B / 58.1719%**;
- creation CPU: `0.2964 -> 2.2956 s` (`+1.9992 s`);
- six hidden content-valid ZIP containers discovered and represented as `S_VZIP`;
- all six retain original `.docx/.xlsx/.pptx` logical paths;
- exact selective checks: 18/18.

This reproduces the prior Office mechanism-level result without path rewriting and recovers almost the entire frozen Office density deficit.

### Analytics/database

- baseline: `10,392,496 B`;
- candidate: `10,391,587 B`;
- saving: **909 B / 0.00875%**;
- creation CPU: `1.3451 -> 1.8337 s` (`+0.4887 s`);
- one hidden content-valid container, `features_compressed.npz`, was virtualized.

This is a decisive economic warning: validity alone is not a sufficient admission predicate. The representation is correct but the marginal yield here is roughly 1.9 KiB saved per extra CPU second, orders of magnitude below Office.

### Controls / unchanged rows

The remaining 13 rows are byte-identical to the unchanged Builder. `incremental_backups` already had one ordinary `.zip` on the existing route and stays byte-identical. `deflate_family` contains 14 valid explicit ZIPs and remains byte-identical under the existing >=8-container pack policy. Media, incompressible, ML, shifted, false-neighbor and other controls do not acquire new hidden ZIP representations.

## Relation to the completed Genesis gate

The frozen v0.30 product remains `150,055,575 B` versus accepted v0.29 `137,499,525 B`; this diagnostic does **not** replace that product measurement.

For triage only, if the two measured r24-level deltas could later be retained by the full v0.30 product with no other changes, they would remove about `8,985,827 B` from the frozen product and reduce the `12,556,050 B` Genesis gap by about **71.6%**, leaving roughly `3.57 MB`. That is a projection, not release evidence; it must be re-measured after integration with canonical r25 product selection, integrity/recovery/native parity and full performance accounting.

The full-matrix harness's own `closes_at_least_50pct_of_gap_to_v029` flag is false because its direct baseline is the unchanged r24 Builder (`181.6 MB`), not the already-stronger frozen v0.30 product portfolio. Do not reinterpret that flag as falsifying the Office mechanism.

## Hostile reviewer / debt

The seed is strong enough to preserve, but not ready for the shipping Builder.

1. **Economic admission is missing.** `features_compressed.npz` buys only 909 B for about 0.49 s of extra CPU. A generic content-validity test cannot be the final admission law.
2. **Parser-resource bounds are incomplete.** The research detector rejects non-`PK` files after four bytes, but plausible ZIP candidates still invoke Python central-directory parsing. A shipping scanner needs explicit caps/early rejection for entry count, directory size, suspicious ratios and proof work.
3. **Cohort policy can change access economics.** Discovering additional containers can cross the existing >=8-container threshold and select `S_PACK` instead of per-container `S_VZIP`. The present matrix verifies exact VZIP ranges but does not yet report S_PACK selective amplification, peak RSS or failure blast radius.
4. **Research implementation duplicates `Builder.scan()`.** That is acceptable for an oracle, not for promotion; shipping integration should factor a bounded opportunity predicate into the canonical scan path rather than maintain a second walker.
5. **Timing is one hosted observation per row.** The CPU deltas are diagnostic, not a release-performance receipt. Repeated same-runner/fresh-process measurements remain required.

## Causal interpretation

The positive mechanism is not “Office extensions compress well.” The current Builder already has an exact, range-aware virtual-container representation but discovers it primarily by `.zip`/`.whl` suffix. Content-valid containers with other names can therefore bypass a representation that is already part of the reader contract.

The Office result shows a high-yield opportunity class. The Analytics result shows why *recognition* and *admission* must remain separate: a file can be a perfectly valid virtualizable ZIP while still being economically worthless to virtualize.

A promising cheap predictor is **cross-container member correlation** observable from central-directory metadata before full recipe construction. Repeated `(CRC32, uncompressed-size)` member signatures across multiple candidate containers can cheaply predict exact member reuse; collisions are harmless as admission hints because final recipe proof remains exact. Office versioned documents should produce a strong signal, while a lone NPZ container cannot. This predictor must be falsified independently before any shipping policy is changed.

## Decision

**Preserve content-driven existing-S_VZIP discovery as a breakthrough research seed and advance to an economic-admission + hardening experiment. Do not modify the shipping Builder yet.**

Next decisive experiment:

1. compute bounded central-directory-only candidate metadata for plausible ZIP containers;
2. preregister a workload-blind correlation/opportunity predicate before result-bearing execution;
3. compare `all valid hidden ZIPs` versus `correlation-gated hidden ZIPs` on all 15 workloads;
4. require the gated policy to retain >=99% of the Office byte saving, avoid the Analytics low-yield proof path, preserve zero byte regressions and exact trees/ranges;
5. measure bytes inspected, recipe/proof CPU, complete creation CPU/wall, peak RSS and selected-read amplification;
6. add malformed/truncated/huge-entry-count/ZIP-bomb-like structural controls with explicit resource ceilings.

Only after this survives should canonical Builder integration be considered.
