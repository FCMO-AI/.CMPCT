# O70 — Eight-ZIP cohort admission versus exact same-input non-cohort oracle

Date: 2026-10-25 UTC. Status: **preregistered before executing the result-bearing experiment**.

## Authority and isolated question

CMPCT released v0.30.0, on-disk revision 24. Baseline unreleased `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.

Existing Builder `scan()` selects a **single S_PACK physical blob for all deferred ZIP/WHL files as soon as the cohort reaches eight**, even if several are already-compressed, unrelated, and a single small member is frequently read. This may reduce header overhead or exploit redundancy, but transfers the other cohort members' physical decode work to each selective access. O40 investigates mixed-size S_PACK selected-member locality, O68 owns VZIP inflation; O70 is distinct: **the creator's eight-member admission boundary, including complete archive bytes and create cost, on identical data and metadata**. No product mutation is authorized by this research.

## Falsifiable primary question

For one structurally heterogeneous, deterministic eight-ZIP source tree (six independently random-content medium ZIPs and two tiny valid ZIPs), does the current **whole-cohort** admission force a cold 64-byte read of a tiny ZIP to decode >20x the physical-group bytes required by a *same-input* non-cohort policy oracle? The alternative differs only in the eligible count condition `if len(deferred)>=8:`, which is turned off in an isolated in-memory copy of the **actual installed Builder source**. Every other algorithm and verification invariant is unchanged. This is an intentionally generous policy oracle, **not** a product change or a benchmark winner. Require the exact original file names, source bytes, source metadata and index reconstruction semantics for both.

## Measurements and controls

- Construct an authentic deterministic corpus using Python `zipfile`; freeze it once, then run the original Builder and control Builder on the **same** directory.
- Exact r24 archive open, `verify()`, read and `read_range()`, entire tree extraction and complete content-byte equality for both.
- Full stored bytes, create wall and CPU, controlled selected-member cold open/read timings, observed blob indices / actual uncompressed and compressed bytes decoded (instrument calls to real `CMPCT._blob`), and process RSS where supported.
- Preserve raw per-run observations and source SHA. Separate process startup and host disk caching; readings are same-host, not guaranteed cold-cache physical disk.
- Strong control: a 7-member physical source is a *structural perturbation only*, never an equal-input performance comparison; the actual A/B uses the same **8** files in both branches.
- Counterhypothesis: the cohort may reduce complete archive size/create cost materially enough to justify its selective-read export; or the oracle may use an equivalently large VZIP skeleton or raw payload and show no material decode disparity.
- **Kill/narrow:** no >20x differential in actually invoked blob decoded bytes; non-cohort failure of authentic exact reconstruction; uncontrolled source mismatch; or an existing claimed experiment that already proves precisely this fork.

## Coordination and evidence scope

Open PR/issue search 2026-10-25 UTC: #394 O40 addresses mixed-size packed reads, #424 O68 addresses inflated VZIP member costs, #423 O67 measures late fallback economic debt. No observed owner of the eight-deferred-member creator admission discontinuity. This branch modifies only a focused experiment, workflow, and evidence text. No format change, source/benchmark/release-gate mutation, version bump, merge or release. Product evidence requires real shipped Builder edits and full gate. Negative evidence must be retained; a successful oracle changes only the decision whether bounded generic cohort admission merits productization.
