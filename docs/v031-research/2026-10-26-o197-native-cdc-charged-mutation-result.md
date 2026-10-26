# O197 — source-exact native CDC admission: low-rung mutation falsifier

**Date:** 2026-10-26 UTC  
**Status:** SCIENTIFIC DECISION / NARROWED; NO PRODUCT OR RELEASE CREDIT.  
**Owner:** existing Draft PR #516 (O185/O196); separate native owner PR #228/#501 remains unmodified.

## Pre-result question and immutable controls

The hypothesis, strongest simpler controls, kill condition, and economic caveats were preregistered in [PR #516 discussion](https://github.com/FCMO-AI/.CMPCT/pull/516#issuecomment-6420900457) **before** adding the experiment or running its hosted job.

O196/O196b proved the optional native C helper is **not packaged or loaded** in the ordinary tested CMPCT wheel or reproduced ABBA source-path arms. Thus a CDC-default-packaging decision needs a real discriminating gain, not just a TSan safety fix for opt-in native usage.

The independent question is whether source-exact native CDC boundaries dominate stronger simple fixed-size alternatives across both favorable shifted siblings and hostile unshifted edits. Comparing against only fixed-256 KiB would be too easy; compare against **the better of fixed-256 KiB and fixed-512 KiB on the exact same input**.

## Source-exact hosted execution

- **Result-bearing action:** [GitHub Actions #40357467062](https://github.com/FCMO-AI/.CMPCT/actions/runs/40357467062), job `source-exact-cdc-mutation`, **SUCCESS**.
- **Measured HEAD:** `2c9c2a050776f53bdc19080ef3d6d5368461f48a`.
- **Native C source:** `native/cmpct_cdc.c`, Git blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364` **checked in the workflow and by the experiment before compilation**.
- **Executable instrument:** `research/o197_native_cdc_mutation_court.py` (unmodified source-exact C compiled to temporary shared object; no substituted table or algorithm).
- **Raw artifact:** [#12665853204](https://github.com/FCMO-AI/.CMPCT/actions/runs/40357467062/artifacts/12665853204), `sha256:24f7c4ff7e6ac1817239d69025c404b903f04cf9ab6b0e73c75a9c1f44122179`.
- **Corpus:** each seed 197–208 produces independent 3 MiB deterministic SHAKE-256 bytes. At positions 1, 1,048,576 and 2,097,152, generate both a **one-byte in-place overwrite** and a **one-byte insertion with one-byte end truncation**; 36 cases per family, 72 pairwise cases total. All 3 policies use identical sibling bytes.
- **Integrity checks:** strict increasing bounded native chunk end offsets, end-at-input-size, byte-identical reassembly, SHA-256 keyed physical chunk reuse, explicit collision check. **No failures**.

### Raw charged *micro* accounting

For each pair the instrument computes `sum(len(unique_chunk)) + 64 * number_unique_chunks`. 64 B is the published revision-24 `BHDR` physical-record header size. This estimates **unique uncompressed payload + record headers** after SHA-based dedup. It is a **lower-level physical raw proxy, not the complete CMPCT archive**; it omits actual chosen compressed payload sizes, dual compressed indexes, codec metadata, cold/read cost, temporary copies and all admission/packaging overhead. No compression-ratio product claim is permitted.

| Corpus mutation | Native vs better fixed control: median saving | Range across 36 pairs | Native loses | Native wins |
|---|---:|---:|---:|---:|
| In-place one-byte overwrite | **−14.060593%** | −31.198015% to +3.531459% | **33/36** | 3/36 |
| One-byte shifted insertion | **+19.7916955%** | −23.349582% to +43.634683% | **8/36** | 28/36 |

These are **lower-rung source-exact measured raw-plus-header proxy differences**. They are not estimated full archive gains.

## Scientific disposition

**Hypothesis of universally stronger native CDC is falsified for this control family.** The same source-exact engine that recovers useful byte-aligned reuse after shifts can create larger unique physical chunks around unshifted edits, losing substantially to small fixed chunks. There are also genuine shifted controls where native loses. The source experiment therefore preserves both the positive structural headroom and the adverse carrying cost.

**Decision changed:** do **not** make the C helper a default distributed encoding policy solely because it fixes its optional lazy-initialization race or improves shifted-sibling dedup. Retain native CDC as an opt-in safety-correct candidate; any broader admission requires a new generic *prospective* discriminator between shifted and unshifted edit regimes, whose own search/copy/index/CPU/byte costs must be charged. Stronger candidates include a bounded representation portfolio or using fixed controls until genuine evidence justifies native selection. A fixture-name, extension or benchmark-identity selector is prohibited.

**Strongest negative/self-critique:** SHAKE-generated random pairs are not an exhaustive archive/file-system workload. An oracle over raw unique bytes lacks a real CMPCT compressed/metadata/archive accounting boundary. The 36 pairs in each family are structural perturbations of 12 seed families, not independent user-workload samples. The timing observations in the raw artifact are single-pass chunking measurements, **not reliable product throughput**. There is no source-exact installed Builder/Reader ABBA or portability proof from this run.

## Counterfactual and next cheapest decision

A cheap single-file native-vs-fixed comparative oracle on **unshifted edits** would have falsified the naïve default-native claim without spending any complete-product benchmark budget. This is a concrete prospectively recognizable falsifier, not reason to rewrite Discovery Engine policy from one episode.

The next safe step is **not** a new fixed threshold or full matrix. First bound the **candidate-specific admission signal/cost** on held-out unseen shifted and unshifted families; if there is no generally discoverable low-cost structural discriminator, retain the optional C fix and retire unconditional productization. If one survives, run actual source-exact *installed* Builder/Reader full archived-byte, creation CPU/wall, RSS/temp-I/O, decode/selective locality, and non-Linux loader/wheel evaluations before any product decision. Preserve O185's official ABBA reds and inherited O175 cache debt.

**quality-ratchet:** No format, Reader, Builder, native algorithm, historical source, release lock, frozen benchmark, comparator, threshold, or public performance claim was changed by this research.

**disproof:** A valid source-exact replication on the same seeds whose charged raw identity figures disagree, or real whole-product source-equal evidence reversing the economics, requires reopening the scoped conclusion. Distinct corpus/workload classes may support bounded opt-in admission even though unconditional replacement fails.
