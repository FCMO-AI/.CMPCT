# J24G40 — portable extended-attribute fixture admission and compaction conformance (preregistration)

Date: 2026-10-29 UTC. Classification: source-locked diagnostic science and evidence-enablement; **not** a product fix, release, or alteration of the inherited evaluator.

## Authority, ownership and observed baseline

Published main remains v0.30.0/r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. Parent of this independent court: unmerged PR #745 at `3e6b1c75a303ba638d420e49b658b90c7b573773`. #741/#745 own POSIX compaction and its product mutations. Do not edit their branches or code. Existing J24I06 inherited court at `tests/research/j24i06_compaction_product_court.py` (unchanged) creates xattr with the literal `user.cmpct-j24i06` and suppresses any `OSError`; subsequently it requires captured xattrs. Exact host [Actions #40838968037](https://github.com/FCMO-AI/.CMPCT/actions/runs/40838968037) shows Ubuntu inherited PASS, macOS inherited FAIL at line 84 `xattr source control not captured`. This is **not** proof of a compaction bug; that assertion occurs before compact_archive is invoked.

## Primary question

Is the macOS inherited red caused by a platform-specific **fixture admission** failure (literal Linux `user.*` attribute rejected before CMPCT can read it), rather than loss by Builder/Reader/compaction? Could a semantically equivalent, OS-native attribute key make a strictly **stronger, non-vacuous** three-layer test pass without changing the original evaluator or any product code?

## Competing explanations / controls

- H1 fixture-key mismatch: `os.setxattr(file,"user.cmpct-j24i06",...)` fails on macOS, while `com.fcmo.cmpct-j24i06` succeeds. On Linux the ordinary `user.*` key succeeds.
- H2 host capability: both candidates fail on macOS (filesystem or permission limitation, not product loss).
- H3 product capture bug: a key is successfully set/read by independent OS APIs but the built archive lacks it.
- H4 product preservation bug: the Builder captures a successfully set/read key, but compaction changes the authenticated xattr metadata.
- Control: `reproducible=True` intentionally drops host xattrs; check only the fidelity-preserving `reproducible=False` contract.
- Falsifier: if the OS-native attribute is actually supported but lost by Builder or compaction, reject H1-as-complete-explanation, do not weaken the checker. If both keys work or both fail, classify the result accordingly.
- Adversarial audit: independently compare OS set/list/get with archived metadata dictionary before/after compaction, digest source and verify contents. Preserve original J24I06 failure, never silently skip an unsupported fixture.

## Planned evidence rung and ownership

Cheapest decisive **hosted OS + installed-product** court on Ubuntu-24.04 and macOS-14, exact source/branch SHA and immutable original test fingerprint, retaining machine-readable per-key errno, raw output and comparison. Run outside the historical test script, without changing `tests/research/j24i06_compaction_product_court.py`, frozen benchmarks or product files. A green *diagnostic workflow* is not a green inherited suite; the independently observed assertion is reported separately.

Before any later test-fixture remediation, require a positive real OS set/list/get control and a positive archive-capture control on each host; do not replace an assertion with a skip. No merged release, no Windows xattr portability claim, no change to format or source. Once proven, report the shortest safe fixture correction to #741/#745 owners; separate normative xattr policy belongs to their owner.

## Cost / scope / counterfactual

This is high-leverage precisely because it discriminates a repeatedly inherited macOS CI red that prevents unambiguous release-candidate analysis. It introduces one small independent research test and its CI court, not another compaction implementation. Measured costs limited to tiny synthetic file roundtrip, wall time, byte identity and metadata; no full-product benchmark, native ABI, crash consistency or same-UID custody safety credit. Counterfactual: logging `os.setxattr` errno instead of swallowing it at fixture creation would have diagnosed a fixture precondition before spending multiple integration runs. This lesson is prospective only if hosted evidence confirms it.

## Concurrency and completion boundary

Read-only against #741/#745 and other research owners; PR branch isolated from exact #745 head. Current Discovery STATE is a staleable cache under #574 ownership; do not write it. Evaluate the result, preserve negative/inconclusive evidence, notify owners. No version, license, comparator, format, release-gate or published-site mutation.