# v0.30 H-EFFORT-5 RAW-Terminal Held-Out Result — 2026-09-13

Status: **`RAW_TERMINAL_INSUFFICIENT_TRANSFER`; valid held-out negative/insufficient evidence; no encoder/product/release credit**.

## Evidence identity

- Frozen mission lock: `docs/V030_RAW_TERMINAL_GATE_MISSION_LOCK_2026-09-13.md`
- Exact result-bearing head: `adf37b9949faf2e7127cc26f1319de0686f93303`
- Hosted run: `34784490051`
- Artifact: `10326685054`
- Artifact digest: `sha256:680b335d8fce1f32e4a4bdfacef347cf170c78624d0fbf3c9b6ac10f7768fe00`
- Referee exit code: `2`, the preregistered code for insufficient transfer rather than a product/harness crash.
- Stderr: empty.

## Result

The five-family `resemblance_hostile_corpus_v1` court produced **777 physical packs**:

- **80** level-1 RAW packs;
- **697** level-1 non-RAW packs;
- RAW logical bytes: **10,606,293 B**;
- RAW packs appeared in only **one** workload family: `05_incompressible`;
- **0** RAW packs had a later smaller payload at levels `3,6,9,12,19`;
- closest later result was a **0 B tie** versus the level-1 RAW payload;
- historical post-L1 effort on those 80 packs consumed median-summed **0.600502302 s CPU** and **0.600668794 s wall** that a correct hard terminal would avoid.

The hard-terminal hypothesis therefore survived every applicable pack in this court, but the preregistered transfer requirement demanded applicability on at least two distinct held-out workload families. It did not earn that breadth.

**Verdict: `RAW_TERMINAL_INSUFFICIENT_TRANSFER`.**

## Why this is not a win

The only applicable family is intentionally incompressible random data. That is an excellent hostile control but an unsurprising place for every Zstd effort level to remain RAW. Calling this a transferable selector result would overstate the evidence.

The correct conclusion is narrower:

> No held-out counterexample was found across 80 new RAW packs / 10.6 MiB, but this court does not establish structural-family transfer beyond incompressible data.

The frozen zero-counterexample gate remains unchanged. Do not relax it, infer transfer from pack count alone, or convert this result into product policy.

## Next admissible step

The repository contains other deterministic hostile suites created for unrelated mechanism families. A **new superseding preregistration** may test the same unchanged `codec == RAW` hard-terminal predicate on one of those independent suites. The new court must be frozen before result-bearing execution and should require applicability across multiple distinct workload families, not merely more random packs.

A counterexample at any later level still kills the hard-terminal claim. A second court may add breadth; it may not retroactively change this result to PASS.

## Product-credit boundary

No encoder, archive bytes, reader grammar, format, recovery, locality, integrity, platform code, version, benchmark score, or release authority changed. This result is evidence about the opportunity gate only.