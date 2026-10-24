# v0.31 bounded-salvage × prospective source custody: independent same-corpus parity court

**Date / preregistration:** 2026-10-23 (America/Mexico_City). This prediction is frozen *before* the proposed dedicated hosted A/B executes. No benchmark outcome is claimed here.

## Source and concurrency custody

- Canonical repository: `FCMO-AI/.CMPCT`. Released checkpoint: `v0.30.0`, on-disk revision 24.
- Candidate: exact composed PR #302 source `2825253a2b40386df173b7f5497abffbe6539f91`. It integrates the bounded physical-salvage scanner from PR #293 with the prospective v0.31 fingerprint repair from PR #266.
- Real comparison base: **PR #266 HEAD `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`**, which already passes the general tests. This intentionally answers the *incremental scanner-product economics* question rather than comparing to PR #293 (whose inherited source-custody CI is red) or to PR #302's declared PR base.
- The candidate and control diverge from `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. The real Builder/Reader and canonical `benchmarks/zip_parity_bench.py` must have the same physical SHA-256 between these two selected sources; abort the court if not. The intended runtime difference is bounded forensic recovery (plus CLI recovery behavior). No version/format change is proposed.
- This is a **separate dedicated parity research lane**. PR #302 retains integration ownership, PR #293 scanner ownership, PR #266 fingerprint ownership, PR #306 comparator input-validation ownership. Do not modify or supersede their files; their exact-source original results remain authoritative.

## Decision-changing question

Does composing the bounded forensic scanner with otherwise compatible source custody preserve ordinary archive **size, create and extract** economics relative to the corrected v0.31 fingerprint baseline when the scanner is *not called*?

**Mechanistic prediction:** same Builder/Reader files and source-driven admission imply **zero deterministic archive-byte differences** for all eight canonical release-parity corpora, at both library and CLI layers; create/extract times should remain neutral within shared-runner noise. No improvement is predicted: bounded salvage is an independent recovery capability, and dormant code is not entitled to performance credit.

## Cheapest capable court / strong controls

Execute the repository's **unchanged candidate** `benchmarks/zip_parity_bench.py` against one generated, frozen, fingerprinted corpus tree, applying the same harness to the pinned PR #266 baseline and the PR #302 composition. Normalize controllable timestamps; preserve inputs, dependency environment, Python interpreter, cache semantics, CLI process boundaries and actual per-run logs. Use ABBA ordering `base/candidate/candidate/base` on one hosted runner, `CMPCT_PARITY_REPS=3` per individual invocation, then the unchanged `tools/aggregate_parity_runs.py` aggregation, with all eight canonical corpora and both library/CLI layers. This is intentionally a **low-cost product A/B diagnostic** relative to full 14-observation-per-engine release parity, and must not be relabeled official promotion evidence.

Guard against the existing comparator false-green hazard in PR #306: independently validate positive integral stored bytes and finite positive wall seconds for both base and candidate layers before interpreting `tools/check_performance_regression.py`. Preserve any failure instead of correcting, dropping, changing or relabeling the corpus row. Carry process stdout, raw and aggregated JSON and environment/source receipts as Actions artifacts even on failure.

## Prospective prediction, falsifiers and causal alternatives

- **P1 deterministic:** archive bytes identical in all eight corpora / two layers. Any single extra byte contradicts P1 and blocks promotion. A smaller result is potentially interesting only after verifying same semantics, since no representation improvement is expected.
- **P2 time:** no reproducible confirmed create/extract slowdown exceeding BOTH >5% and >3 ms under identical runner/process boundaries. Any observed red is a candidate regression signal, not permission to loosen thresholds. Ambiguous close/noisy timing requires deeper same-runner ABBA, not narration.
- **P3 evidence:** both installed modules resolve to the pinned tree, with identical Builder/Reader/harness content and one shared immutable corpus fingerprint. If a check fails, this is infrastructure/evidence invalidity, **not** a CMPCT performance loss or win.
- **Negative control:** #302 and #266 should differ in the bounded physical-recovery implementation. Explicitly inspect the relevant `transactions.py` hashes; if they match unexpectedly, this would be a useless A/A, not proof of an improvement.
- **Strong simpler control:** #266 alone with green full CI, no new salvage functionality; #293 standalone has a positive focused scanner memory result but inherited general CI reds. The exact-source union #302 has already passed 819 general tests, which proves functional compatibility but **does not prove timing economy**.

## Promotion boundary / stopping

This court can eliminate the unmeasured ordinary create/extract cost risk or expose a specific performance debt. It cannot establish Windows/macOS support, full RSS/I/O economics, authenticated salvage (scanner still emits unverified headers), guaranteed consistency under concurrent filesystem mutation, release parity against the canonical direct release base, or authorization to merge/release.

If clean: hand the focused A/B to #302/#293 owners and request full normative exact-head ABBA before product promotion. If red: preserve original raw measurements and diagnose the mechanism or noise with an independent replication, not benchmark gardening. If CI cannot execute: leave the frozen question and exact source refs intact with provider/run and blocker evidence.

No `docs/discovery/STATE.json` update without decision-changing measured truth. No release/version/format/frozen-evaluator mutation.
