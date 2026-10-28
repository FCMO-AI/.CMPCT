# J24G02b — Discovery of uncharged research instrument source in candidate fingerprint (preregistration)

**Status: PRE-IMPLEMENTATION / FALSIFIER FROZEN / DRAFT ONLY.** Written after J24G02 original exact eight-blob transplant but before altering its prospective manifest or test code.

## Direct observed baseline

J24G02 imported donor PR #266 exact source fingerprint manifest (`docs/V031_CANDIDATE_FINGERPRINT.json` Git blob `f806d96dba4750dead6746e078e596e848e6f201`) onto source-FD product PR #636 (`Reader` Git blob `fe0706ce00a425edb6572ff6cd2032f9be413468`). Current J24G02 head before this experiment is `178aac131e125c86b161b56c9cc18db6d6b5b90f`. The historical v0.30 lock stays `988a7b05ad4e0833fac0453de74133b38f890f87`.

Independent enumeration of exact current Git tree `0dceb3dd27c2d68d6a13096a0917e24725193241` using GitHub Git trees API (`recursive=1`, `truncated=false`) returned 2,368 tracked blobs. A path-vs-pattern audit using recursive-globstar matching counted 2,322 covered and 46 uncovered; 41 of the remainder are under docs, most frozen historical result/receipt JSONs; only three are under the *research source* directory:

- `research/discovery_episodes.jsonl`
- `research/j24h07_linux_owner_fd_court.py`
- `research/j24h07b_linux_multi_owner_court.py`

The three current research records are 12,373 bytes. None matches any donor pattern. The two Python files are the actual active Linux fd-owned hardlink tests for #636, and a changed test would not alter the **manifest-derived source fingerprint**. Git commit SHA changes separately; this gap does not prove CI can be fooled about the Git head, nor that past release gates were compromised. It falsifies completeness of a prospective fingerprint used *without an independent exact-head check* for research evidence.

## Primary causal question

Can two minimally scoped manifest patterns `research/**/*.py` and `research/**/*.jsonl` close the present science-instrument custody gap, including future nested research scripts, without importing irrelevant data or modifying any frozen historical release record, evaluator, product implementation or scientific tests?

**Prediction:** the actual Python source-identity tool will include all three named files after the change. A new independent test should show that changing the byte content of a synthetic research script or jsonl episode modifies the source fingerprint, and renaming a script changes it. The original donor's mandatory-path checks and all four inherited CI reconciliation assertions should still execute, not be skipped.

## Stronger controls, alternatives and decisive rung

1. Use *exact current original donor* manifest as control, with a temporary tree containing a research script and JSONL: the original pattern set does not include them; adding only those files leaves fingerprint unaffected (or no source selected, if isolated). Do not conflate source-head SHA with fingerprint.
2. Use only two source-scoped globs as candidate. Avoid `research/**/*`: blindly charging arbitrary binaries/generated artifacts would increase risk and expense without proving relevant source identity.
3. Actual Git tree audit plus a tiny isolated Python unit oracle is cheaper and more causally decisive than complete product benchmark.
4. Preserve the donor implementation byte-identical; modify **only** the prospective manifest, add a separate test for coverage/tamper/rename and fix PR body headings required by unchanged engineering-evidence validator.

## Falsifiers and admission constraints

Reject the claim if candidate tool ignores either active J24H07 test, if byte mutation in `.py` or `.jsonl` leaves the derived digest unchanged, if test requires weakening inherited checks, if historical v0.30 lock or Reader blob changes, if src/tool fingerprints are attributed to the wrong exact head, or if generated content silently contaminates the source identity. Original donor #266 retains ownership and will receive a source-bound notice rather than being overwritten.

This is **research/evidence-architecture**, not compression, extraction hardening, new on-disk format or release credit. The full system still needs actual hosted fast CI, J24H07 product court, native/fuzz, performance ABBA, hostile/adversarial/portability gates. No arbitrary redesign of release policy or Discovery Engine. Counterfactual prospective lesson will require repeated evidence to change policy.
