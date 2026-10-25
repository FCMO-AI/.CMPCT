# O39 — Held-out high-cardinality hardlink Reader scaling (prospective preregistration)

Date: 2026-10-25 UTC. **PREDICTION ONLY; no O39 implementation or measurements existed at preregistration.**

## Authority and distinct lane
Canonical v0.30.0 / r24 remains released; v0.31 O31 Reader owner is [PR #385](https://github.com/FCMO-AI/.CMPCT/pull/385) at `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Git blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`. O38 fast-path product implementation is **already owned** by [PR #392](https://github.com/FCMO-AI/.CMPCT/pull/392), exact source `dffc6da03b588e209843f2fc6e219e5bce3a7800`, Reader blob `4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867`. Existing O33/O36/O38 courts use <=4,096 member archives. This **independent replication** tests a *different decision dimension*: scaling and canonical-fallback work at 8,192/32,768 members, not another 4,096 timing run or another implementation. Search of open PRs found no current narrow 32,768-member Reader scaling owner. Work exclusively on a new child branch, no edits to product, inherited tests, the O33/O38 original instruments, benchmarks, release thresholds or shared discovery state. Concurrent updates to O38 remain owner authority.

## Primary question and prediction
Can the committed O38 exact-key shortcut preserve exact semantics and linear-ish resource economy at large authenticated hardlink cardinality, particularly when a hostile but valid corpus *forces* noncanonical owner targets into the full fallback? If fast-path only survives the friendly 4,096 fanout, product generality is unearned.

Use exact O31 as stronger same-semantics baseline and O38 committed code as candidate. On each size 8,192 and 32,768 include four structural cases: ordinary regular files (no aliases); direct exact-key fanout; long exact-key alias chain (terminal owner reachable without recursion); and valid mixed-separator alias-to-owner targets `sub\\owner.bin` when the authenticated entry key is `sub/owner.bin` (forces full normalization). Reuse the authentic revision-24 signed physical fixture construction method from unchanged O33 (SHA-committed metadata, one physically stored RAW owner blob) only as a starting point for a separately named instrument. Every case must pass strict structural preflight and independent Reader read/range/logical-SHA/strong-verify checks before timing.

## Economic criteria (research triage, not release gate)
On a single Ubuntu runner, run >=8 fresh Python child processes per engine/corpus in ABBA/BAAB order, record **raw** constructor wall and CPU, whole process, RSS after constructor and HWM delta, archive SHA/size, Git source HEAD, Reader blob, native paths. The candidate should recover >=8.0 ms in constructor median on 32,768 exact-key fanout relative to O31. Noncanonical 32,768 aliases and 32,768 ordinary files must not regress on both >=10% and >=5 ms. Candidate post-open RSS must not exceed O31 by both >=10% and >=4,096 KiB on any case. A hang, recursion failure, semantic divergence, missing native/source custody, timeout, or valid mixed-separator rejection falsifies the hypothesis, regardless of attractive medians. Judge noncanonical case **neutral or regressed** honestly; speedup is not assumed for it.

The growth check compares 8,192 versus 32,768 constructor cost for each source in the same shape after subtracting 8,192-member baseline: disproportionate >6x growth under 4x input expansion is an exploratory warning, not a new hard official threshold. Identical bytes of archives must be used by both engines; sample checks plus strong verify happen **outside** timing. Single host and small single-payload wire fixture limit product claims; no installed-wheel, end-to-end extraction, selective multi-blob or 1.0 credit follows.

## BONK / controls / reversibility
- Baseline/control: original O31 code from Git SHA, not a synthetic imitation.
- Simpler alternative: keeping O31 is valid if O38 gains collapse or memory grows.
- Exported costs: total source archive bytes, cold import/process wall, CPU and resident memory; no changes to archive construction, decode, extraction or format are expected because neither engine alters the file.
- Held-out structural falsifier: mixed-separator owner target defeats the exact-key shortcut and checks whether the fallback still pays bounded cost.
- Opportunity cost: run one hosted bounded court; do not rerun the frozen 15-row product comparison or duplicate #392's 4,096 baseline.
- Carrying cost: research-only script/workflow with no runtime dependencies added to CMPCT.

## Counterfactual and decision handoff
Positive => offer source-bound held-out scaling receipt to #392 owner; still no merge/release credit until integrated exact-HEAD CI. Negative => preserve raw measurements, isolate whether it is correctness, CPU, memory or platform; recommend a bounded fix or keeping baseline, not threshold tuning. Do not modify discovery policy from a single result. Detailed evidence must cite runner/commit/artifact and account for negative cases. Never transfer the O33 instrument's old hard-coded O28/O31 labels into O39: provenance fields must name the **actual measured** O31/O38 sources and the paths checked at runtime.
