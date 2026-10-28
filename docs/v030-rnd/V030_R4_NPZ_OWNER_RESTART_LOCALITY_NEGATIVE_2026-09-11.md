# v0.30 R4 Analytics NPZ-owner restart locality — negative result — 2026-09-11

Status: **FALSIFIED AT FIXED 27 KiB SPAN; PRESERVE NEGATIVE; NO PROMOTION**

Exact evidence authority:
- branch: `agent/v030-authoritative-integration`
- source commit: `1b164e41775fd4de9659de4210f338bd01d91139`
- workflow run: `34668101957`
- job: `103484080373`
- artifact: `10288859617` (`v030-r4-npz-owner-restart-locality-1b164e41775fd4de9659de4210f338bd01d91139`)
- artifact ZIP SHA-256: `fd6020ae0c8e0b755e2ab7af842346951bc57db03f44779042d925d576884bd1`
- benchmark: `benchmarks/v030_r4_npz_owner_restart_locality.py`
- schema: `cmpct-v030-r4-npz-owner-restart-locality-v1`

This is negative research evidence. It changes no shipping format, selector, comparator, or release version.

## Mission lock

The full dual-view repair proved that authenticated segmentation can repair locality but that duplicating an exact NPZ view costs too many bytes. The opposite ownership boundary was therefore tested:

> Keep the exact NPZ as the single physical owner and make the derived external NPY locally readable with compact Deflate **inflater** restart state rather than trying to restart an exact compressor.

Before hosted measurement the experiment fixed:
- checkpoint spacing: **27 KiB output**;
- request size: **4 KiB**;
- no spacing/threshold sweep;
- actual Deflate match distances measured by a byte-exact research parser;
- per-checkpoint minimum pre-checkpoint history suffix inferred from matches in the locality window;
- each history independently zstd-compressed;
- Huffman states deduplicated;
- compact index fully charged;
- conservative **1 KiB authenticated-index allowance per cold read**;
- start-of-stream probe charged by incremental compressed-stream consumption rather than hidden full decode.

Advance required all of:
1. exact NPZ-owner semantic tree;
2. candidate stored bytes < accepted v0.29 Analytics `6,135,172 B`;
3. max cold physical amplification <=8x;
4. max reconstruction amplification <=8x.

## Exact hosted result

| Metric | Result |
|---|---:|
| exact NPZ-owner bundle before restart state | `4,453,186 B` |
| restart state | **`1,753,535 B`** |
| candidate | **`6,206,721 B`** |
| accepted v0.29 Analytics | `6,135,172 B` |
| density margin vs v0.29 | **`-71,549 B`** |
| exact Deflate feature stream | `3,556,442 B` |
| external NPY logical bytes | `3,840,128 B` |
| checkpoints | `138` |
| max cold physical amplification | **`8.62744140625x`** |
| max reconstruction amplification | **`9.052978515625x`** |
| exact NPZ-owner semantic tree | PASS |

Restart-state anatomy:
- raw required histories: `1,866,420 B`;
- independently zstd-compressed histories: **`1,729,091 B`**;
- maximum required history at one checkpoint: `29,656 B`;
- unique Huffman states: `138`;
- compressed Huffman states: `19,242 B`;
- compact index: `5,106 B`.

Hypothesis outcome:
- exact tree: **PASS**;
- below v0.29 Analytics: **FAIL by 71,549 B**;
- physical <=8x: **FAIL (8.627x)**;
- reconstruction <=8x: **FAIL (9.053x)**;
- supported for product prototype: **FALSE**.

## Interpretation

This is a near miss in absolute terms, but it is still a clean failure of the preregistered law. The project must not round `8.627x` or `9.053x` down to 8x, hide `71,549 B`, or choose a new checkpoint span retrospectively and call the original hypothesis supported.

The causal attribution is unusually sharp: Huffman state plus index are only about `24.3 KiB`; **history dominates the restart budget**. The remaining problem is therefore not index serialization. A materially better restart design must reduce how much pre-checkpoint output history is persisted or how often independent histories are repeated.

The observed required-history total (`1,866,420 B` across 138 checkpoints) is substantially smaller than the naive `138 * 32 KiB` full-window budget, validating the mechanism idea, but independent checkpoint histories still duplicate overlapping information heavily. That is the next causal target.

## Decision

`REJECT_FIXED_27K_INDEPENDENT_HISTORY_RESTARTS; INVESTIGATE_SHARED/HIERARCHICAL_HISTORY_ONLY WITH PREREGISTERED HELD-OUT LAW`.

A follow-up is justified only if it attacks the measured redundancy mechanism rather than sweeping checkpoint spacing until Genesis turns green. Plausible general mechanisms include:
- shared/delta-coded restart histories anchored in authenticated nearby state;
- independently decodable chunks whose dictionary/history state is owned once per group rather than once per checkpoint;
- a hierarchical restart representation where common history suffixes are referenced rather than copied.

Any follow-up must preserve <=8x physical and reconstruction laws, charge all shared-state references/proofs, and be validated beyond the single Analytics fixture before product promotion.

## Frontier context

The exact composed Mode2 + Office SFV2 gate remains:
- same-run v0.30: `150,059,822 B`;
- composed candidate: **`138,616,788 B`**;
- frozen v0.29: `137,499,525 B`;
- gap: **`1,117,263 B` (~0.813%)**;
- creation tree CPU improvement versus same-run v0.30: **`321.894083 s`**.

This negative does not weaken that density result. It says the tested locality rehabilitation is not yet economically or physically acceptable.

## Frozen ONE context

The ONE Genesis verdict remains unchanged. v0.30 remains primary; ONE remains preserved secondary evidence. The relevant ONE lesson is to eliminate repeated state/work. The next restart-state experiment should therefore target duplicated history itself, not add more proof traffic or a second full representation.
