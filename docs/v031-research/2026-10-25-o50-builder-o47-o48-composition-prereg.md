# O50 preregistration — independent O47 × O48 Builder composition court

**Date:** 2026-10-25 UTC. **Status:** prospective, before O50 product/test/workflow mutation.

## Authority and exact custody

- Canonical development baseline: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- O47 source-owner branch: PR #401, `29d9688ae6bff6d1eccc27f019893866abe5b5c3`, Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`. O47 repairs Win32 regular-file physical hardlink detection using `os.stat`.
- O48 source-owner branch: PR #402, `55c9309d9c94bc29d258c2595ea69279cf7c1b63`, Builder blob `4c13d7b6a890ef27ba5a92bf3afe152345cf1078`. O48 rejects unsupported special filesystem entries rather than reporting lossless success.
- This branch is an **independent integration instrument**, not a replacement for either owner. It uses O47 as immutable parent and imports only O48's fail-closed type dispatch (and the original O48 test). The tests are not weakened; frozen release/corpus rules remain intact. No merge/release/version/format grant.

## Question

Can the two independently supported Builder correctness fixes coexist without changing supported-tree bytes, losing physical hardlink topology, or allowing successful partial archives for unsupported entries?

## Pre-result predictions and alternatives

- **Candidate:** compositional Builder = O47 `os.stat` identity repair plus O48 unsupported-type refusal.
- **Stronger simpler control:** avoid product composition for now; O47 and O48 focused courts remain independently credible but cannot establish joint-source semantics. A source-diff-only proof is insufficient if the tests expose order interactions.
- **Prediction:** original, unchanged O47 source hardlink tests pass with one K_HARDLINK owner alias, genuine same-inode extraction and equal-payload distinct negative on Ubuntu/macOS/Windows. Original, unchanged O48 FIFO+socket+regular+CLI tests pass on POSIX and correctly skip only POSIX fixtures on Windows. A new mixed hardlink+FIFO source must **refuse before output publication or overwrite**, whereas removal of the FIFO must produce one alias, exact output, repeated archive SHA and no accidental physical merge of equal bytes.
- **Alternative explanation:** negative could arise from platform fixture limitations or install/pytest collection rather than Builder conflict; record job output, original test counts and exact imported package path. Positive on only Linux cannot prove Windows.
- **Kill/narrow:** Any supported-tree byte difference from the O47 parent, physically lost hardlink, copied-independent false alias, silent special omission, overwritten sentinel, skip miscredited as pass, divergent test content, wrong installed-source SHA, malformed hostile input accepted, or unsupported platform changes disqualifies composition credit. Full native/fuzz/parity/release gate failures remain blockers, not optional.
- **Evidence rung:** genuinely installed Python CMPCT 0.30/r24 Reader+Builder; three hosted OSes, isolated source-bound pytest, raw JUnit/logs, exact git head and product blob. Product source modification is only the O48 fail-closed dispatch re-applied on O47; new integration test is an independent combined control.

## Scope and costs

No on-disk revision/ABI change; no new compression claim. Extra regular-file stat already belongs to O47's Win32 path; unsupported type branch from O48. No holistic CPU/RSS/ZIP parity measurements will be inferred from focused passing tests. CI cost: 3 hosts, one installed package each. Concurrency: do not alter #401/#402 or shared Discovery state; re-read both owner source heads before late writes and inform them of the independent result.

## Decision unlocked

If exact-head combined source passes, return a reproducible joint-source receipt to both owners for future authorized convergence, **not a merge recommendation without full inherited gates**. If it fails, isolate the interaction and keep original owner patches untouched.
