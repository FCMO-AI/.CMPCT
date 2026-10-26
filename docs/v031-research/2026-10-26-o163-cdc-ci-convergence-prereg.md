# O163 — preregistered CDC race × prospective CI custody convergence (2026-10-26 UTC)

## Exact inherited sources
- Canonical v0.31 development: `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, unchanged at preregistration.
- Independent source-custody owner: PR #266, exact HEAD `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`; its latest historical GitHub Actions general tests, native core, CI topology and other checked workflows reported SUCCESS.
- Independent native CDC-race owner: PR #228, exact HEAD `6c0930dec5001760e3b1d1ef45fa2ce1f69d92f4`; one changed file `native/cmpct_cdc.c`, blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364`. Its independent local TSan witness confirmed a data race in the original mutable lazy gear table, and the candidate preserves observed CDC cuts. Its general CI did not pass on that HEAD.
- Existing source on PR #266 is original native blob `bf51984f6ca7dec5e5041aa9f8dcccbed75221da`.

## Primary question and predicted outcome
Can the source-exact const-gear native CDC replacement coexist with the already-green v0.31 prospective source-fingerprint/historical-custody baseline on **one** installed product HEAD without weakening the historical release lock, CDC ABI, partition boundaries or performance gates?

Prediction: replacing exactly the one original native C blob with the complete candidate blob from PR #228 should remove the unsynchronized first-call race mechanism without altering CDC cut choices or r24 archives; #266's candidate fingerprint should correctly change to reflect the new C source, remain self-consistent, and exact-HEAD general/native/CI checks should pass **if** all existing gates are covered. No claims of product performance or release until full same-source evidence.

Strong simpler control: PR #266 alone (green CI but mutable race remains); alternate control PR #228 alone (race removed but inherited full-PR CI reds persist). The combined candidate must improve both without preserving duplicate implementations.

Alternative explanations: historical/source-custody changes might hide a genuine regression; constant data might not exactly match SplitMix64; host-native tests can pass while C/ABI boundaries change; CI may skip the true performance job. Explicitly inspect source SHA, exact test jobs, raw output, archive identities, timing and manifest/fingerprint where available.

Kill/narrow condition: a single reproducible CDC cut mismatch, reader incompatibility, data race, formatter/ABI change, source identity gap, or deterministic archive-size regression blocks product promotion. CI green with substantive performance skipped is not sufficient to claim measured nonregression. Host/platform omissions and baseline inherited failures must remain visible, not silently accepted.

## Scope / concurrency
This is an **independent integration/composition**, not a rewrite or competing native implementation: preserve the exact implementation of PR #228 and CI changes of PR #266. Never overwrite either parent. Root output is a single branch/PR directly targeted at `agent/v031-development`. Re-read any shared file before writes. No changes to v0.30 historical release lock, format, benchmarks, validators, thresholds or frozen evidence.

## Decision and next gate
Obtain real exact-head GitHub Actions, source/ABI/content equivalence and official substantive parity when applicable. If clean, route back to both original owners for integration into one canonical v0.31 branch rather than maintaining three permanent variants. No automatic numeric release.
