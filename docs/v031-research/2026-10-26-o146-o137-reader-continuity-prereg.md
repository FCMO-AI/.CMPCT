# O146 — Forward-binding inherited Reader courts after O137 (preregistration)

**Frozen starting source:** `FCMO-AI/.CMPCT` draft PR #487 at `b5901b9d6b5a23c98bd6a74939f5df82a7d1bd56`; Reader Git blob `e5301ccf24a63577cfbfa169be9c1e452a0d14bd`; path-policy blob `91fc335eea8fb18c3899511f416c8abe96c48f80`; physical revision 24, released v0.30.0 unchanged. This research lives on an independent child branch, not the owner branch.

## Decision question

Can the O137 static safe-mode FIFO rejection **coexist** with the O131 four-guard Reader/host-namespace protections and original source-alias tests in one actually installed product on Ubuntu, Windows and macOS, despite the inherited O131/O124 workflows intentionally binding their earlier Reader blob `5ce013f80c0220c7e7771041c60740a7111fff8a`?

## Baseline and falsifiable prediction

- O131 original unchanged tests passed 144 / 44 skipped across three hosts at original O131 code; that source-exact workflow rejects the new O137 Reader blob *before testing* by design. O124 original instrument passes its 12 scientific cells under original code but retains an existing macOS sparse-fixture 8 PASS/1 FAIL which must **not** be concealed.
- O137 focused genuine product run `40261741471` passed 11/11 Ubuntu and macOS on the new Reader blob; Windows unavailable for POSIX FIFO scenarios.
- **Prediction:** the unmodified O131 owners' tests, run against installed O137 Reader and unchanged namespace policy, remain green under the same per-host selection/exclusions as original O131. O137 focused FIFO test additionally remains green on POSIX. If any previously green O131 test fails or any protected invariant regresses, composition is **NOT PROVEN**; do not retrofit exclusions to obtain green.
- **Strong simpler control:** run original test modules directly with the installed O137 product and explicit exact-head/Reader/test-blob provenance; no reinterpretation or code reimplementation. An O131 workflow source-hash red alone cannot answer the behavioral question.
- **Alternative explanation:** O137’s extra type check could alter ordinary regular destinations, atomic CHUNKS/CDC replacement or host-specific aliases; a real newly failed test takes priority over attribution theories.

## Scope and evidence ladder

New exact-source GitHub Actions *continuity* workflow: Ubuntu, Windows and macOS run original O131 tests with identical platform-domain selection, source/test blob verification and pytest reports; Ubuntu/macOS also run original unchanged O137 FIFO test as a byte-identical copy outside unrelated historical `tests/conftest.py`. No changing the original O131/O124 courts, no product/source edits, no frozen benchmark/threshold changes. Original O124 macOS red remains separately open.

Required result: source SHA, installed import outside checkout, unchanged owner tests, all actual pytest output/JUnit, host identity and durable artifact. Tests passing cannot authorize release: performance #487 official run `40261741459` is **RED** for `combined/cli/create` +5.25% / +23.451ms; a preregistered exact-source independent replication was dispatched separately and remains evidence debt. No general benchmark credit from this focused court.

## Causal action & kill

- **Accept scientifically** only when all three hosts' O131 court passes unchanged; POSIX O137 court also passes; evidence source exact.
- **Narrow** if host-specific fixture or infrastructure fails before product testing; record failure and repair instrument without modifying inherited source/expectations.
- **Falsify** if an inherited previously-green protection fails against O137 source.
- **No release/promotion** until official performance, broad CI, source custody and macOS inherited red are adjudicated.

No new Discovery Engine policy lesson is claimed in advance. Detailed outcomes must be appended after actual CI.
