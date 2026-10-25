# O131 — Four-guard Reader extraction convergence (preregistration)

Date: 2026-10-25
Status: PROSPECTIVE / NOT RESULT-BEARING
Repository: FCMO-AI/.CMPCT
Base: PR #472 @ `00c7367b5d90e1349e31098a9262ebadd059b2a8` (source inode + static destination guards)
Other owner: PR #336 @ `28d57e13a1b8e89a70f857f180b4403592b96e12` (Win32 + macOS namespace guards)
Canonical development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`
Release: v0.30.0 / format r24; unchanged.

## One falsifiable question

Can the exact existing Win32/APFS logical-name admission and the static destination/source-inode protections coexist in **one real installed Reader** without losing their original rejection/positive cases or weakening portable POSIX namespace fidelity?

## Prediction (before integration or testing)

Source-only additive composition should preserve the unchanged O124 12-cell source/alias court on Ubuntu/macOS and #336's Windows/macOS/portable owner tests on all three actual operating systems. Valid independent output must remain exact. Distinct archive names mapping to one case-insensitive host entry must be rejected before writing any member; any static output path pointing to the open archive must also be rejected before writing; existing outside symlink/hardlink targets must retain parent protections.

## Strong controls and skeptical alternatives

- Simpler control: #336 independently protects host name collisions but can still overwrite its own open archive; #472 protects its own archive but loses names on case-insensitive hosts. Separate green results cannot prove the conjunction.
- Alternative: redesign all extraction publication around descriptor-bound staging. That may be superior against TOCTOU, but is a separate owner/convergence campaign and changes hardlink and publication semantics.
- Historical negative: #472's latest macOS O124 workflow ([run 40239479273](https://github.com/FCMO-AI/.CMPCT/actions/runs/40239479273)) has **eight original parent tests PASS, one sparse-mode fixture FAIL**: the test demanded a direct-truncate storage kind but got another selected storage kind. Its 12-cell scientific source-identity audit independently passed. This red is not erased by O131; do not weaken or skip that original test to declare promotion.
- Comparator: baseline developer Reader and the two exact parent heads. All tests and archive/Reader identities must be attributable to their actual source.

## Disproof/retirement conditions

One genuine inherited regression, wrong-platform skipped-as-passed test, malformed/unsafe archive accepted, valid portable tree spuriously lost (outside the documented conservative host refusal), source-clobber, prewrite rejection with partial member publication, mismatch against original owner code segments, or a new uncategorized exact-head CI red blocks positive composition credit.

## Scope and budget

Implementation may change `src/cmpct/reader.py` and `src/cmpct/path_policy.py` plus new independent tests/workflow. Do not modify v0.30 release fingerprints, archive format, frozen benchmarks, existing owner tests, existing CI assertions, or the source-of-truth discovery cache under another owner (#440). No merge or release on research-only evidence. Preserve the source file's original explanatory comments.

## Evidence ladder and handoff

1. Mechanically verify byte-identical import of #336's canonical admission block, plus #472's unchanged archive-source/destination preflight block, and Python syntax.
2. Run all unchanged #336 Win32/APFS/portable owner tests on installed O131 in Ubuntu/macOS/Windows with the original documented Mac host-domain exception (not an O131 invention).
3. Execute unchanged O124 source/alias court and unchanged parent nine-case regression; preserve its known Mac failure unless product truth changes.
4. Reuse the authentic O117 transferred archive control from PR #470 when a same-HEAD installed court is feasible. Comprehensive product benchmarking and publication are separate gates.

Any scientific result must identify its exact candidate HEAD and which parents/tests were really exercised.