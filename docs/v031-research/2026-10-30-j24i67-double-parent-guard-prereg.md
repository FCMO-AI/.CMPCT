# J24I67 — Two-pointer orphan camouflage: prospective installed-API control

Date: 2026-10-30 (UTC). **Independent research only**. Source parent [#856](https://github.com/FCMO-AI/.CMPCT/pull/856) HEAD `f29561c5e2d36a8f47aa35f61191911c0611be6b`; inherited shipping Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. No Reader/Writer/format/ABI/product/evaluator/version/merge/release mutation or claim.

## Existing O0 result — NOT prospective installed proof

A detached no-CMPCT-import local parser operating on the original three GitHub-hosted J24I56 64-footer physical archive ZIPs found that two changes to *unhashed predecessor pointer fields* can hide an authentic DELETE from a simplistic "latest footer must point to nearest checkpoint-rooted SHA-valid predecessor" condition. First change: F63.prev from F62 to F61 skips a real DELETE. Second: F62.prev from F61 to 0 makes the skipped SHA-valid DELETE unrooted. Original: 119 logical files; single/double changes: 120, including resurrected `f052.dat`. Only 3–4 physical bytes changed per archive; all 64 individual footer payload SHA digests and all 150 original CMA4 SHA/CRC records per host remained valid. The full archive SHA changes. The naive condition passes original, fails single, passes double. **This is wire-level O0 only**, not a claim about actual installed Reader/preflight or broader recovery.

## Prospectively frozen question / falsification

On three actual hosted systems (Ubuntu 24.04, Windows 2022 and macOS 15), with *fresh* N=16 and N=128 first-party Builder physical archives and exactly three real Writer DELETE commits F1,F2,F3, does the identical two-field modification `F3.prev=F1; F2.prev=0` produce:
- actual installed `CMPCT.read()/verify()` selecting the latest F3 and resurrecting precisely `f00001.dat` (N-2 live instead of N-3);
- installed strict `preflight_archive` agreeing;
- a separately defined nearest-rooted-SHA-footer heuristic rejecting the single-field variant yet accepting the two-field variant;
- unchanged payload hashes, same stored blob bytes, accepted original and corrupted-terminal-SHA recovery controls?

**Disproof**: any host rejecting the double rewrite, displaying nonmatching logical byte/content sets, violating the positive or recovery controls, failing source blob attestation, or showing the heuristic does reject double. Preserve all failures. Do not alter the tested source, thresholds, criterion, corpus or evaluators to rationalize a negative.

## Scope / stronger controls / concurrency

Original #856 one-field rewire is the simpler control. Distinct J24G93 owner branch `agent/phased1-v031-j24g93-valid-orphan-recovery-parent-control-20261030` independently tests *genuinely emitted Writer successor after unrooted orphan*; do not duplicate it or confuse this artificial two-pointer wire adversary with genuine Writer recovery. #857 is the shared integrity contract decision and #574 owns shared Discovery STATE. A valid whole-file externally authenticated manifest would detect either changed archive; footer SHA is not a MAC/signature. No format-level impossibility theorem, general malicious origin claim, or official performance/release credit is warranted. Work is a cheap guard-family falsifier; applying a fix requires real crash/orphan recovery, concurrency, resource-bounded rooted-frontier, native/Reader/preflight, multi-host and full product gates. CI results and artifact hashes are unknown at preregistration.