# J24I57 — Prospective v0.31 source custody × repaired signed-journal ordinal proof

Date: 2026-10-30 UTC. PRE-IMPLEMENTATION PREREGISTRATION. DRAFT EVIDENCE INTEGRATION ONLY; NO PRODUCT/RELEASE CLAIM.

## Exact starting state and ownership
- Base is J24I56 PR #828 head `4bbf543e75b43f3bd48a09a417dc9dbef3095ed3`. It proved 3-host physical hardlinks across 63 journal generations, but General Tests exact-head #41051639335 returned 877 pass, 5 fail, 2 skip.
- Four failures assert obsolete v0.30 frozen manifest entries or surface revision, despite active v0.31 source: `test_performance_base_native_release_custody`, `test_public_attribution`, `test_v030_ci_topology_split_receipts`, `test_v030_release_fingerprint_surface`. Independent PR #266 (head `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`) already provides an independently validated *prospective* fingerprint repair. PRs #785 and #803 reused it on DIFFERENT product stacks; this experiment explicitly tests that donor on the J24I56 physical-Windows-owned Reader stack.
- Fifth failure `test_v031_j24g52_journal_replay_discriminator` demands the *historic bad* preflight ghost ordinal 2; current shared `journal_replay.py` (blob `03743ca2a06c022c2ec64243a90fe373cf91e899`) and validation now correctly renumber sparse xattrs after a signed delete. PRs #783/#786/#795 and #827 own this journal behavior. This lane changes **only the stale test's assertion to require agreement and correct physical path binding**, never their implementation.
- No shared discovery STATE mutation; #574 owns it. Current main has no CONCURRENCY_PROTOCOL. No release, benchmark threshold, native ABI, format, Reader/Writer/Builder change planned.

## Hypothesis and fail conditions
H1: compositing exact #266 prospective candidate fingerprint files with the present #828 source, and replacing the J24G52 negative historical invariant with a *positive* strict replay equality assertion, removes exactly five inherited General Tests failures without altering published `docs/V030_RELEASE_LOCK.json`, product code, or legacy CI authority.

Required success:
1. Original published v0.30 release-lock blob remains `988a7b05ad4e0833fac0453de74133b38f890f87`, candidate fingerprint computed from complete actual v0.31 source and refuses dropped/renamed/mutated, symlink/escape and missing mandatory custody inputs.
2. Signed delete results in xattrs bound to owner at ordinal 0 and alias at ordinal 1 in **both** bounded preflight and Reader; no phantom ordinal 2, no lost value or misassigned path. Change only test expectation, not evaluator implementation/semantic corpus.
3. Exact-head GitHub General Tests now has zero failures with unchanged full-suite collection and meaningful increased asserted coverage. The J24I56 3-host product proof remains inherited from #828; exact-head new run is required before claiming composition on revised head.
4. Preserve all unrelated O72 historical hard-coded source-pin failures; they are not product regressions or authorization to rewrite frozen tests.

Kill/narrow:
- Any prospective identity failure, changed historical lock, lost coverage, or mismatch between replay and preflight is FAILURE.
- A red General Tests after transplant is real debt until resolved, never silently skipped.
- Green tests do not assert product speed or safety beyond inherited proof; r24/ZIP must run materially before release. #320/#822 own full-PR scope and benchmark integration.

## Strong alternatives
- Editing v0.30 lock to include new files corrupts historical release truth and is forbidden.
- Altering immutable test fixture values or weakening integrity/Writer replay would hide the real invariant.
- Copying an unrelated donor implementation beyond the eight exact #266 files is unnecessary.
- Keeping one intentionally stale discrepancy assertion permanently red would misclassify a repaired invariant as a product failure.

## Evidence plan
Prereg commit precedes donor import. Make a separate DRAFT PR targeted at #828, run exact-head full suite, prospective identifier and PR's existing physical tests, preserve failures. If all pass, this is evidence-enablement only; promotion remains independently gated.

## Costs and scope
No on-disk bytes, archive performance, extraction CPU, memory, I/O, compatibility, or C ABI changes anticipated (source exclusively tests/workflow/receipt manifest and utility). Computing a full prospective source fingerprint adds bounded O(source bytes) CI work, not archive runtime work.

## Next action
Import donor source and modify one stale negative test; run full General Tests and report exact-head evidence. 
