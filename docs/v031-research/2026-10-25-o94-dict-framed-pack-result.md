# O94 — Source-exact hosted dictionary-frame representation result

Date: 2026-10-25 (UTC)  
Status: **RESEARCH H1 FALSIFIED / GROUPED VARIANT NARROWED**; **NO PRODUCT OR RELEASE CREDIT**.

## Preregistration and authority

Prospective hypothesis frozen **before coding** in `docs/v031-research/2026-10-25-o94-dict-framed-pack-prereg.md` at commit `a265272c4ac4d9a9f4dcc1c80607e7dd7f1ac470`. Branch was created from current canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; shipping release v0.30.0 / revision-24 and frozen comparators untouched.

Actual **installed/system-libzstd research oracle**, *not* CMPCT Builder/Reader product: source module `research/v031_o94_dict_frames_oracle.py`. Exact result-bearing head `598bcdea1b9ed6af8243c553963d0d1f2394873e`, [GitHub Actions run 40214415477](https://github.com/FCMO-AI/.CMPCT/actions/runs/40214415477), job `121232342906`, **SUCCESS**, raw artifact `12606692990`. Independently audited raw receipt `o94-evidence/raw.json` SHA-256: `346438926400dab1eddceff84937417fbb2773729c64b514af2c8703efff0d95`. 7 rotating in-process trials for each of 5 authentic Zstd arms on each of 3 same-input deterministic corpora; SHA-checked full decode/selected logical bytes. Host Linux Ubuntu 24.04 Python 3.11; local Linux Python 3.13 repeated exact stored-byte values, not exact host timings.

## Full-charged complete representation bytes

All arms encode *exactly identical ordered source files* per corpus. Complete oracle accounting includes every compressed frame byte, 48-byte per-frame owner/index/integrity metadata, 24 bytes per logical member, and one fully exported dictionary payload with additional 48-byte root overhead. These are **projected research physical organization bytes**, **not** real materialized CMPCT archive sizes.

| Corpus (256 files) | One monolithic Zstd | Per-file plain Zstd | Per-file trained 8192-B dictionary | Groups of 16 plain | Groups of 16 trained dictionary |
| --- | ---: | ---: | ---: | ---: | ---: |
| Template, 196,608 raw B | **92,479 B** | 217,600 B | 111,280 B (**+20.33%**) | 147,002 B | 95,390 B (**+3.15%**) |
| Independent entropy, 196,608 B | **202,815 B** | 217,600 B | 220,193 B (**+8.57%**) | 203,680 B (**+0.43%**) | 204,637 B (**+0.90%**) |
| Variable-size/ordering holdout, 323,826 B | **184,345 B** | 344,818 B | 226,034 B (**+22.61%**) | 277,766 B | 202,309 B (**+9.74%**) |

**Prospectively required H1 (< = +5% bytes and >=10x reduced selected decode unit on positive corpus) fails for independently decodable dictionary-per-file owners across all regimes.** The strongest simple monolithic control remains the storage-byte winner in these corpora. Per-file compression context independence is expensive even with a genuinely learned dictionary; a dictionary alone does not inherit all cross-object model state for free.

A **bounded 16-member+dictionary research seed** narrowly meets the positive-family byte criterion (+3.15%) and reduces the selected *owned payload* decode unit from 196,608 B to 12,288 B (16x), but **fails held-out** by +9.74% storage and incurs creator wall debt. The structurally simpler 16-member no-dictionary control is stronger for high-entropy data (+0.43% vs +0.90% charged overhead), exposing dictionary overfitting/carrying cost. No global winner, no transfer-proof admission rule, and no justification to garden thresholds.

## Selected-read and creation costs

Source-bound hosted micro measurements (medians; in-process `libzstd`; startup and cold-cache omitted):

| Scenario | Monolithic selected wall | Per-file dictionary selected wall | Grouped16 dictionary selected wall | Monolithic create wall | Grouped16 dictionary create wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Template | 111.428 μs | 9.855 μs | 16.605 μs | 0.652 ms | 1.015 ms |
| Holdout | 178.999 μs | 10.386 μs | 21.342 μs | 1.067 ms | 1.644 ms |

For the template group16+dictionary, requested member payload is 768 B; decoder must decode 12,288 B *and use the 8192-B dictionary*. If all decoder-visible dictionary bytes are charged once for a cold read, physical information touched is **20,480 B** versus monolithic 196,608 B: **9.6x**, not the misleading **16x** payload-decoded-only amplification. Per-file dictionary is 768+8192=8960 B => 21.94x vs monolithic rather than nominal 256x. Actual cache warmth and dictionary-authentication work remain unmeasured. The raw selected wall times do **not** time verifying or cold-loading dictionary SHA and are optimistic for equivalently authenticated access.

## Safety and semantic negative — ownership changes integrity scope

The monolithic physical owner may strongly authenticate a full packed blob on a requested selected read. Independently framed owners authenticate their own payload and dictionary, but **do not automatically authenticate unselected owners**, so substituting per-frame SHA for a whole-packed-source SHA is a different failure-detection contract. No Reader integration may advertise equivalent integrity until it either proves a compatible contract or charges/provides the missing proof. Our SHA checks verify the returned owners and complete full decode of untampered data; corruption, filesystem races, pack lifetime and cold I/O are unmeasured. This lower-rung oracle is **not revision-24 CMPCT materialization**, a product win, a release gate pass or a format proposal.

## Counterfactual and next scientific fork

A generous fully charged family oracle resolves the primary question **without** implementing a new reader or spreading a cache. The predictor that would have killed the per-file variant earliest is the per-owner frame/header/index burden **plus a physically exported trained dictionary**, compared against a monolithic genuine Zstd source control. For future exploration, require a discoverable, broad prior-data regime where grouping or similarity selection earns both held-out bytes and actual create/read economics after cold dictionary proof; otherwise retire this local representation family and return to the distinct product promotion/safety frontier. No policy self-modification earned; no `docs/discovery/STATE.json` edit since it is owned separately in PR #440.

## Exact-head status and limits

At result-bearing commit `598bcdea`, focused O94 hosted workflow **SUCCESS**, CI topology **SUCCESS**, version discipline **SUCCESS**, R36 **SUCCESS**, engineering evidence **FAIL** due missing prescribed PR-body headings, and general tests were pending at analysis cut. PR-body documentation repair may address engineering evidence without modifying the evaluator, but a later doc-only source HEAD requires its own checked evidence status. Public v0.30 release unchanged; no merge, no version/format/benchmark threshold change.
