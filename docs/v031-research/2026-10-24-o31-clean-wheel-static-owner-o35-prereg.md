# O35 — Clean-installed O31 Reader: static destination safety and hardlink owner semantics (preregistration)

Date: 2026-10-24 UTC. Evidence tier: product-installed safety/conformance, not release or compression research.

## Baseline / exact ownership
- Released CMPCT v0.30.0, physical r24 unchanged; development owner O31 PR #385 at `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`.
- O31 preserves O25 hardlink cycle/owner rejection, O27 pre-existing symlink preflight, O10R signed-generation bounds and fixed O29 canonical hardlink spelling, but its installed-package CI #40135788544 skipped every effective build/install/CPython/aggregrate job.
- Independent exact original O32 PR #386 at `a4962f9e6abc65ec231bbb8c7fc3824711e96f59` (installed smoke Git blob `34e50149ced1cfede9159bd2184727cccd02428e`) demonstrated clean-installed static symlink containment only for O27 Reader, **not** O31.
- O33 scientific PR #387 showed real O31 4,096-hardlink fanout constructor CPU/wall debt (+3.008ms / +33.1%). This expense is NOT erased by installed-wheel evidence.

## Primary hypothesis and disproof
Can the **unchanged** O31 product tree survive actual sdist→wheel→isolated-install→real r24 reconstruction on Linux/macOS/Windows, preserving at least O32's physical POSIX pre-existing destination symlink rejection, legitimate symlink/hardlink inode preservation, native dependencies and signed archive-symlink tests? Predict exact original O32 smoke will pass on both POSIX hosts when run from the installed wheel, and all three wheels/15 CPython jobs and source-bound aggregate will pass.

Falsifiers: a symlink pivot accepted, an ordinary member written before rejection, external inode/SHA changed, a legitimate hardlink no longer sharing its physical inode, wheel import escaping isolated prefix, signed symlink hostile case accepted, any Windows/macOS/Linux package failure, source SHA/fingerprint discrepancy, or a supposedly successful workflow whose real package jobs are skipped.

## Stronger/simple controls and competing routes
Existing #385 in-tree 3-host O31 safety and general suite prove source behavior, but not shipping wheel behavior. Existing O32 shipping-wheel green proves O27-only semantics, not O31 composition. Cheapest decisive route is to reuse **exact unchanged O32 instrument** and its build/aggregation controls on a child of #385, without another Reader implementation, benchmark threshold, fixture weakening or format change. Full official performance/RSS/release tests are independent and cannot be inferred.

## Implementation boundary and cost
Only transplant O32 test and its incremental workflow routing/positive verification into #385 child branch; keep all other native, signed-symlink, and CPython checks identical. Preserve O31 Reader blob unchanged. One fresh exact-head 21-job installed package matrix, CPU/build minutes and wheel artifacts are an evidence expense; no new runtime code or extra archive bytes. Do not modify PR #385 or O32 owner.

## Promotion/hand-off
A pass changes **only** the O31 installed product-safety evidence frontier. It does not solve O33 fanout CPU regression, source-lifetime atomicity, external hardlink inode alias, concurrent destination TOCTOU, universal metadata, complete r24 official performance, or authorize merging/releasing. Failed cases remain verbatim in Actions; reject any test/evaluator weakening. Record exact run/source/artifacts and deliver result to owner #385.
