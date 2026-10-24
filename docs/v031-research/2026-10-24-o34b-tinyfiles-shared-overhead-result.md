# O34b — Tiny-files inherited product overhead (2026-10-24)

**Decision: 46,049 B genuine-r24 product-byte loss is shared by unchanged shipping v0.30 and frozen compact-r24; it is NOT a differential compact-policy regression on this row. O34's frozen no-promotion decision remains unchanged.**

## Source, verification and reproducibility

- Parent decisive frozen full-court failure: [O34 run 40138113211](https://github.com/FCMO-AI/.CMPCT/actions/runs/40138113211) on HEAD `17a000f150f68e724efb6cdcdd3d1dddb079c5ca`, job `121003877559`, failed at `neutral_hostile_v1/08_many_tiny_files` before full 15+15 summary.
- Bounded post-hoc **different** question, hosted [O34b run 40142620847](https://github.com/FCMO-AI/.CMPCT/actions/runs/40142620847) on HEAD `b21edb08aff2b6713309b4eef761c9fc90c9df4c`, job `121017345403`: **SUCCESS** with source/ancestry/six frozen source Git blobs passing.
- Artifact `12578949883`, archive ZIP SHA-256 `d92424f196691253eee189852a6baa8b35aadb6161251eb287b3950e3a88092e`, includes `o34b-three-way.json`, raw `o34b-run.log` and exit code.
- Input: exactly one accepted historical-identity `08_many_tiny_files` generator, 5,000 regular files. Pre/post historical SHA-256 equals accepted `a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f`.
- Three actual product archives were created and strongly verified via **independent fresh Python processes** against the *same unchanged source tree*. This matters because importing the frozen candidate mutates global policy owners in-process.

## Complete physical archive bytes

| Executed engine | Full bytes | SHA-256 / effective choice |
|---|---:|---|
| Genuine revision-24 `cmpct.builder.Builder` | **679,037** | `1df8a1442bf30451f221d91cc4b5cf1228b352f5b123f3e495e28fd542a8f7c6` |
| Unchanged v0.30 shipping front door | **725,086** | `128aa8bd34d8068d38bb37997e96d7a6a1839606cb7fcc9204a7431a8e3472c9`; `r24-fallback`, revision 24 |
| Frozen compact-r24 candidate `b878f40a...` | **725,086** | **same exact SHA-256** `128aa8bd34d8068d38bb37997e96d7a6a1839606cb7fcc9204a7431a8e3472c9`; `r24-fallback`, revision 24 |

All archives passed their corresponding explicit strong verification. Shipping and frozen candidate returned the same logical semantic tree identity `6c7c1ceb77a9c3a5950c973756f373bcbcb90951d74d477fb28e86e7ec03dae3`. The genuine-r24 control reconstructs the same input tree through the original revision-24 Builder/Reader.

**Measured difference: shipping minus genuine r24 = +46,049 B; compact minus genuine r24 = +46,049 B; compact minus shipping = exactly 0 B and byte-identical archives.** This is a single Linux/Python 3.11 hosted source-exact observation, not a noisy timing estimate.

## Causal scope and strongest counterevidence

This demonstrates the frozen compact policy did **not** introduce or amplify the many-tiny-files complete-byte overhead relative to the current shipping v0.30 product in this exact corpus. The overhead is already present under the shipping product's `r24-fallback` selection; **which specific shipping encoder-policy or metadata behavior caused it remains UNPROVEN**. It would be incorrect to attribute the 46,049 B to compact's 64-KiB Deflate rule or removal of medium-binary admission without a separate causal code diff / same-input A/B.

The **original O34 product gate still fails**: its frozen comparator is authentic `cmpct.builder.Builder` r24, not the shipping v0.30 branch. A measured negative against that control is not made positive by showing an inherited cause. The uncompleted 15+15 O34 matrix remains unmeasured in full; this post-hoc one-row test does not substitute a release or historical-compression claim.

Counterfactual value: an independent 5,000-tiny-file early product-parity canary would have flagged this exact-byte floor before ~45 minutes of full historical computation. Because this row was selected *after* observing the O34 failure, **prospective selection value for arbitrary future candidates is unproven** and no discovery policy modification is earned.

## Cost / integrity boundaries / next executable target

No new archive grammar, product change, promotion criteria, benchmark corruption or compression win; source custody passed and payload equality was independently verified. The three elapsed-wall single process observations are not comparable release timing evidence; full CPU/RSS/portability/selective recovery remain unmeasured.

**Actionable decision:** preserve compact as research seed where independent evidence warrants it, but do not promote this frozen candidate. If a materially different ownership/representation route requires this tiny-file overhead, first identify why the shipping r24 fallback exceeds the genuine r24 Builder on the same filesystem tree. Compare a minimal source-exact control and fully charge any proposed fix; do not garden thresholds or repeat the frozen matrix. Otherwise move to the higher-leverage v0.31 integration frontier.

This record is an append-only scientific result. Original O34 artifact, frozen science and promotion law remain immutable.
