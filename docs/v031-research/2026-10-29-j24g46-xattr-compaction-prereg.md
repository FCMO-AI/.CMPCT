# J24G46 preregistration — native xattr conservation through revision-24 journal compaction

Date: 2026-10-29 UTC. **Prediction frozen before tests/workflow/result.**

## Exact starting surface and coordination
- Parent: #757 `agent/phased2-v031-j24g41-darwin-xattr-provider-20261029@911e66053bd997ad0c85895cf61da02f9ce06625` (Darwin native ordinary-xattr Builder/Reader candidate).
- Baseline published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / r24.
- Own only **cross-layer physical test/instrumentation and evidence** on a distinct branch. No modification of #757, #428, #745, format, release, evaluator, or test thresholds. No duplicate xattr provider or compact implementation.
- Prior J24G40 #752 establishes missing ordinary Darwin xattr capture; J24G41 #757 establishes native one-roundtrip capture/restore, **not** real journal→compact→rebuild conservation. J24G42 #761 distinguishes APFS compression xattrs from ordinary user xattrs, so do not test hidden `com.apple.decmpfs` as ordinary metadata.

## Primary question / predicted outcome
Can the exact existing r24 journal→`compact_archive`→Builder path, with **unaltered** transactions implementation and #757's Darwin-native xattr support, preserve real binary and empty-valued user xattrs on both a directory and a regular file? Does it preserve logical SHA-256, live member names and contents, while removing dead journal generations?

Prediction: Ubuntu+macOS real-native user xattrs survive Builder, journal update, compaction, final Reader fsmeta, and strictly requested extractall; independent OS reads match the source. Windows, where ordinary POSIX xattrs are unsupported, preserves content and does **not** earn a physical-xattr positive. Genuine early control: standalone #757 xattr roundtrip tests remain unchanged.

## Simpler controls / alternatives / cost
- Control 1: independent OS writer/reader proves each actual attribute exists *before* Builder, including zero bytes and a zero-length value.
- Control 2: `CMPCT.verify()`, r24 file row/metadata and direct source/output SHA, plus non-xattr Windows controls.
- Stronger route rejected: transplanting #757 provider into #745's POSIX stage or writing new compactor would mix owners and obscure the first causal question. Current #757 `transactions.py` is unchanged; use it verbatim.
- Alternative explanation if Linux passes/macOS fails: Darwin filesystem temp directory refuses ordinary xattrs despite source support; test native capability explicitly on both source and recreated physical output before attributing it to reader.
- A failure of `append_update` to preserve existing index xattr maps is a separate journal-index mapping failure, not automatically a Darwin-native error.

## Falsification and decision
- Kill/narrow: any observed xattr loss/alteration, missing empty attribute, incorrect original/compacted fsmeta mapping, unacceptable logical difference, absent/fake physical OS control, or unexpected source/target mutation. Preserve exact failing artifacts and logs. An OS that refuses initial fixture attributes is a fixture limitation, not product success.
- A positive is **integration-test evidence only**, not a general claim of APFS full physical-layout fidelity, adversarial concurrent-mutation safety, Windows ADS support, all ACLs, atomic strict extraction, power-failure durability, or product benchmark wins. This intentionally does not address #749 same-UID inode-rebinding threat, #764 empty-Zstd flaw, #769 RSS evidence owner.
- Evidence rung: installed-package 3-host targeted court with source identity, independent native xattr witness (macOS `/usr/bin/xattr`, Linux `os.getxattr`), authenticated r24 two-generation source and compact output, repeated real-file hashes, independent JUnit admission; no full benchmark unless local court says a promotion decision can change.
- No release/merge/version authority, no Discovery Engine policy change. Only update shared discovery state if a decision-changing result genuinely affects the global frontier; avoid stale cache rewrite.

## Prospective counterfactual discriminator
If one simple end-to-end `compact_archive` run after a single journal update exposes missing xattrs, it supersedes further isolated native API microtests as the earliest **product-level** disproof. If positive, next integrate #757 into legitimate compaction owner with the unchanged safety gates rather than add more local xattr variants.
