# O38 — Productize exact-hit canonical hardlink owner lookup (prospective, 2026-10-24 UTC)

**Status at freeze: prediction only. No O38 source change, exact-head CI, size, timing, release or product credit yet.**

## Authority and ownership

Released canonical v0.30.0 / r24 remains immutable. Work exclusively on a new child of O31 product owner [PR #385](https://github.com/FCMO-AI/.CMPCT/pull/385), exact starting commit `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader Git blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`. Do not update #385, #390, main, the v0.31 development ref, shared discovery cache, frozen evaluators or benchmarks. [PR #390](https://github.com/FCMO-AI/.CMPCT/pull/390) is the independent research oracle, **not** a product commit. This O38 lane uniquely attempts product convergence after oracle evidence; owner #385 decides whether to adopt.

## Baseline and mechanism

O33 independent cold Reader constructor control: authentic 4,096-member hardlink fanout O28 **9.083 ms** vs O31 **12.091 ms** (+3.008 ms/+33.1%), while ordinary-file control was nearly neutral. O36 tested one disposable exact-hit shortcut on authenticated SHA-committed r24 trees in 96 fresh Python processes and 25 unchanged hostile/positive tests. Its real source-exact hosted run [40141754876](https://github.com/FCMO-AI/.CMPCT/actions/runs/40141754876) reports fanout-4096 constructor **12.867→9.927 ms** (2.940 ms saved), chain-4096 **12.518→9.777 ms**, plain-4096 **7.490→7.585 ms**, and fanout post-construct RSS 26,556→26,498 KiB. O36 is research-only and does not transfer product/release credit. O31 [child #389](https://github.com/FCMO-AI/.CMPCT/pull/389) independently established installed-wheel canonical hardlinks on Linux/macOS/Windows, 21 effective jobs, and an official **PASS** against its configured r24 parity control on exact `b1ba91ac598e8311328dfd0299347814093321dc`. That pass does **not** transfer to source-mutated O38.

Hypothesis: O31 repeatedly canonicalizes a target that is already an exactly matching key in the Reader's canonical-admitted file table. For **only** that exact-key case, reuse the raw string directly, avoiding expensive duplicate lexical normalization. Every nonexact spelling (including backslashes), hostile path, unknown key, or mutation still executes the original canonicalization/fallback; retaining extraction-time owner verification is mandatory. A false positive bypassing validation kills the mechanism.

## Stronger controls and alternatives

Simpler control: retain unmodified O31 as secure baseline. Alternatives: unconditional trust of hardlink target (forbidden), rejecting mixed-separator names (breaks admitted r24 grammar), cache/index rewrite or second graph (memory/complexity without evidence), repeat disposable O36 experiment without materialization (no new product evidence). Selected one narrow code-fragment replacement, unchanged grammar, same source/corpus.

## Prospective falsifiers and decision law

1. Assert base Reader blob exactly `de9accf6607aca7cf70dfe71d7b299a02e298a2d` and the old resolver fragment appears **exactly once** before editing; no other product source change, no Builder/Writer/native/validator/format/benchmark/evaluator modifications.
2. Pass original O31 + O25 + O27 + O28 signed r24 controls, canonical collision/error priority, altered-after-open rows, symlink/tree/hardlink semantics, hostile owner cycles/path escapes. Reject any semantic change (earlier/later refusal allowed only if same already-preserved strongest safety law).
3. Pass **full** General Tests, source-exact official r24/ZIP performance (0-byte size floor; timing fail if both >5% and >3ms), supported platform conformance, native/fuzz and clean-installed-wheel controls on this **new exact HEAD**. Mark skips as missing evidence, not success.
4. Given O36 measured >=2ms constructor recovery on 4,096 fanout, product continuation is justified only if no materially worse plain-file/open cost, CPU/RSS, security, exactness, or maintenance. Do not declare an O38 speedup until an O38 source-exact A/B executes. O36 remains research evidence.
5. If a product gate fails, preserve failure and diagnose cause; keep this draft unmerged. Even all-green per-PR gates are not automatic v0.31 release authorization.
6. Observe external/same-format semantics, selective read, integrity, hardlink inode topology, source mutation and destination TOCTOU boundaries honestly. This shortcut does not fix unrelated security families.

## Current decision

**ADVANCE_TO_PRODUCT_CONVERGENCE_EXPERIMENT**, not promote. One owner-scoped source change with reusable release tests is the cheapest honest rung after a successful exact disposable oracle. The operator must report exact HEAD, actual CI and negative evidence. No discovery-policy modification unless repeated causal process evidence later warrants it.
