# J24G103 — Content-defined root blocks: source-exact physical result and post-result falsifier

**Date: 2026-10-31 UTC. Evidence class: research O0 (no CMPCT product, benchmark, format, version, merge or release credit).**

## Problem and inherited baseline
Released CMPCT is `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/revision-24. Existing parent #879/J24G102 charged fixed 4/16-KiB SHA-keyed physical block roots at 1.062–1.115× one root on four authentic Builder + 63-DELETE Writer histories, but a single early byte insertion raised retained size to 2.005–2.035×. J24G99's non-rebasing rolling-tail control was smaller (1.004–1.019×) for a *different* append-only operation and remains the stronger simpler route where applicable. #876 governs root rebase, #869 publication, #823 Reader, #574 discovery authority. No owner collision or discovery state rewrite.

## Frozen prediction and unchanged comparator
Immutable *prospective* preregistered experiment at [`7a0ecce92cae0b65080f092eda3a2e21b93aa396`](https://github.com/FCMO-AI/.CMPCT/commit/7a0ecce92cae0b65080f092eda3a2e21b93aa396), preceding the oracle/referee/workflow. Exact same four original physical source pairs and the same full-byte charges as J24G102:
- Ubuntu-origin original provider ZIP SHA-256 `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b`
- Windows-origin original provider ZIP SHA-256 `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab`
- both produced by `129edec976efe8bb604584517de39553487fec34`, Action #41120248525, 4096/8192 members each, physically reconstructed old checkpoint and same-data terminal checkpoint.

Deterministic 256-entry SHA-derived Gear table, cut min=target/4, max=target*4, mask=target-1, target=4096 or 16384; no knobs fitted after results. Charge **full distinct payload bytes + 44B per distinct SHA-keyed block + 32B per root reference + 64B per root manifest**. Verify exact physical byte reconstruction, source SHA, all 63 DELETE journal semantics, footer payload SHA, and tamper/ref detection. The frozen eight-arm gate requires original/early insert <=1.25× and midpoint insert/early delete <=1.30× the larger of two roots, plus no original CDC representation >15% larger than the equal-target fixed-block control.

## Result-bearing hosted evidence (exact pre-result-doc implementation)
[GitHub Actions #41167036937](https://github.com/FCMO-AI/.CMPCT/actions/runs/41167036937) **SUCCESS** on source HEAD `199fe4355059d82f67934992375c225a509606a8`. Original result-bearing artifact [#13029900166](https://github.com/FCMO-AI/.CMPCT/actions/runs/41167036937/artifacts/13029900166), GitHub-provider ZIP SHA-256 `8ffbb228a99d3f8ca251343badd4a5215634a0d0c78ef66db952b5ebe4403c39`. The artifact was downloaded separately; a differently rooted referee, without importing CMPCT or the primary chunker, re-parsed all four physical sources, recomputed eight models and forty geometric perturbations, verified charges and frozen pass flags, and **rejected four hostile receipt alterations** (byte cost, source SHA, shift cost, pass flag). Hosted receipt SHA-256 `4f1efece04bea2b66b1428495e2f5545869dd269adee8027959d9104d3bee9f3`.

| Physical source | Target | CDC original / one-byte early insert | Fixed original | Byte-gate |
|---|---:|---:|---:|---|
| Ubuntu 4,096 | 4 KiB | 1.0499× / 1.0616× | 1.1146× | PASS |
| Ubuntu 4,096 | 16 KiB | 1.1117× / 1.1700× | 1.0942× | PASS |
| Ubuntu 8,192 | 4 KiB | 1.0476× / 1.0556× | 1.1088× | PASS |
| Ubuntu 8,192 | 16 KiB | 1.0427× / 1.0662× | 1.0928× | PASS |
| Windows-origin 4,096 | 4 KiB | 1.0456× / 1.0516× | 1.0765× | PASS |
| Windows-origin 4,096 | 16 KiB | 1.0835× / 1.1377× | 1.0657× | PASS |
| Windows-origin 8,192 | 4 KiB | 1.0531× / 1.0604× | 1.0778× | PASS |
| Windows-origin 8,192 | 16 KiB | 1.0602× / 1.0958× | 1.0623× | PASS |

**All 8/8 frozen O0 BYTE gates pass.** Not a product metric or even a physically allocated reflink metric. All new experiments ran on Linux, even when inputs originated in Windows; there is no three-OS execution claim. Random unrelated payloads in the frozen court still show about 2× overhead; no generic data dedup guarantee.

## Important negative: separate exact charged construction time
On the same hosted Ubuntu runner, warm in-process **Python** creation of the whole CDC two-root representation measured **110.40–133.43×** the median fixed-block constructor wall time, across the eight comparisons (three measured samples each). CDC ~134–303 ms vs fixed model ~1–2.5 ms. Independent local same-source repeat reported ~158–220×. This is dominated plausibly by the Python bytewise Gear loop and fixed slicing/hashlib native operations; it is **not evidence that optimized native CDC is 100× slower** or that Reader/Writer would share these exact timings. However, the mechanism cannot be called product-economical without a native/whole-system cost and selective-read measurement. A small extra 8-byte per-reference offset sensitivity left original-source charged ratios below 1.25×; it does not charge entire lookup tables, indexes, GC, crashes or metadata ownership.

External strong implementation control: [Xia et al., *FastCDC*, USENIX ATC 2016](https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia) demonstrates CPU-oriented optimized native Gear-family CDC, showing why a Python-loop result must not be generalized to a competent production implementation. The J24G103 cut rule is **not the published FastCDC normalized algorithm**; no cross-implementation speed/dedup win is asserted.

## POST-RESULT structural hostile: fixed gate survives; broader claim narrows
After the hosted frozen result, an additional deterministic positional sweep sampled **16 insertion + 16 deletion positions** on each of the eight source×target combinations: **256** geometric perturbations. This is *not preregistered*, cannot rewrite or replace the eight frozen PASS outcomes, and receives no product/promotion credit. Its independent-source reproducible script is `research/j24g103_posthoc_shift.py`; local report SHA-256 `ba287a54f31ced0ef200f754e00e5326f7a7d00a1f0fc6b53416b96efc8a215a` (script revision output; a separately earlier exploratory equivalent had SHA `347fded319bb47e9d74bd8139527edafd67ef565d2773a484ec3fc20a76d7101`). **2 of 256 extra perturbations exceed 1.25×**: the Ubuntu-origin 4096-member/16KiB target insertion and deletion at ~one-third of the new root (offset 156388), both **1.27613×**. The chunk set drops from 14 shared SHA keys under early insertion to 13 there; about **49.7 KiB of additional payload** explains the changed cost. This is a genuine structural-generalization negative, despite the preregistered narrow screen PASS. The 4KiB target stayed below the same 1.25× comparator in every added case. No threshold was adjusted.

**Counterfactual lesson, not policy change:** one cheap preregistered interior position at one-third of the root would have caught the 16KiB instability earlier than broad optimism about shift tolerance. Incorporating one deterministic offset other than the extremes and midpoint into a future CDC falsifier is a prospective candidate, not yet repeated evidence warranting a Discovery Engine policy rewrite.

## Outcome, debt, decision and next unclaimed action
**`O0_FROZEN_BYTES_SURVIVE_WITH_POSTHOC_SHIFT_COUNTEREXAMPLE — CPU_COST_UNRESOLVED — NO_PRODUCT_PROMOTION`.** The original fixed-block 1-byte failure is *not* an information-theoretic impossibility for all shift-resilient chunking: this distinct boundary model preserved large sharing on four real sources, so retain the reproducible seed. But nontransitive chunks, the two 16KiB posthoc failures, ~110–133× Python construction economics, and lack of a whole-system use case against the simpler J24G99 append-owner and #823 Reader optimize make new threshold/gear-table tuning low-value. **Park CDC root rebase as a bounded research option, not an active product lane**. Reopen only for genuinely mixed rooted updates and a measured competent native implementation with full byte/create/open/read/RSS/dependency/recovery/GC/multiwriter/OS proof.

Product focus returns to already claimed #823/#878/#882 Reader replay integration (PUT/RENAME/hardlinks/xattrs, hostile and native), and separately #857 ancestry, #290 multiwriter, #749 verified inode publication. No product/release/format/version change, no hidden comparator alteration, no Discovery STATE overwrite. Existing hosted artifact has finite 30-day retention: the source, frozen prediction, result and SHA pointers are committed here; GitHub artifact must be reacquired or separately preserved before expiry if byte evidence is required beyond that window.
