# T01 — Native r25 / portability completion

- **Owner:** v0.30 sole executor
- **Priority:** P0
- **State:** CLAIMED
- **Branch:** `agent/v030-authoritative-integration`
- **Dependencies:** final authority must run on the same exact reconciled candidate used by T00–T04.

## Objective

Make every representation that the final v0.30 selector can publish independently readable and verifiable through the shared native/portable surface, with the same recovery/resource semantics as Python and with no second incompatible parser architecture.

## Scope

- canonical r25 G0–G4 Geometry native/shared reader parity;
- canonical r25 PrefixGraph native/shared reader parity;
- exact r24 fallback delegation to the mature existing core;
- deterministic builder-independent golden archives/vectors;
- primary/tail recovery parity and hostile metadata/resource checks;
- single-member/selective read parity and <=8x policy observability;
- ZIP/export interoperability for new profiles;
- native ABI/CLI integration using the repository's shared memory-safe core design;
- platform/Android acceptance infrastructure required by existing policy.

## Preferred implementation area

Prefer `native/**`, native-specific tests/vectors, `docs/NATIVE_CORE.md`, `docs/PORTABILITY.md`, and narrowly necessary canonical profile adapters. Because one executor owns the full release, adjacent product code may be changed when required to close a proven interface defect, but compression-selection thresholds and benchmark floors remain frozen unless the release policy itself explicitly requires a stricter gate.

## Must not regress

- r24 reader compatibility and ABI;
- exact canonical archive bytes unless an intentional format-profile correction is documented and rebenchmarked;
- bounded MessagePack/resource admission;
- recovery semantics;
- Python/native tree and member identity.

## Completion evidence

1. Python writer -> native verifier/read/extract golden parity for each promoted r25 profile.
2. Builder-independent committed golden archives decode identically in Python and native implementations.
3. Primary-damaged/tail-valid and tail-damaged/primary-valid recovery parity; both-corrupt fails closed.
4. Hostile/fuzz/resource/path cases green.
5. Native CLI/ABI selective member reads demonstrate the same logical bytes and locality contract.
6. ZIP export from each selected representation round-trips through stock tooling.
7. Existing native/core regression suite remains green.
8. Relevant portability/format/native docs are accurate, not aspirational.
9. Android/platform acceptance required by repository policy is tied to the exact release candidate, including the shared portable dispatcher rather than an independent parser.

## Current exact continuation state

The canonical implicit-v4 filesystem-control seam is already implemented in the shared portable reader and Android instrumentation. The remaining boundary is evidence/productization, not a second parser implementation.

The authoritative branch now contains a stronger `tests/native_v030_implicit_manifest.py` recovery matrix. For both builder-independent G04/PrefixGraph implicit-v4 goldens it independently damages primary metadata, tail metadata, both copies, and payload bytes. A single valid metadata copy must still reconstruct the exact public tree; both metadata copies or payload corruption must fail closed. The live canonical writer's admitted implicit-v4 archive is subjected to the same matrix so fixed goldens cannot hide writer/framing drift.

The native-authority workflow now emits a fingerprint-bound strict JSON artifact after the full Python/Rust/golden/recovery/selective-read matrix succeeds. That artifact records only the facts this lane proves (`g04_native_parity`, `prefixgraph_native_parity`, builder-independent goldens, native/implicit-v4 recovery, r24 fallback verification and shared-core use). Logs-specific parity/recovery facts remain owned by their separate evidence and must not be inferred from the native artifact.

Hosted Android evidence now uses exact-head preserved-running custody plus a newest-commit classifier. This repairs the observed failure mode where unrelated commits on the long-lived integration PR cancelled a 60-minute emulator run mid-build. Its durable artifact explicitly records canonical-r25 and implicit-v4 portable dispatch alongside Logs inverse and compact-control dispatch. The physical ARM64 lane will accept hosted evidence only when all four dispatch facts, candidate SHA and release fingerprint match exactly; it still requires a real non-QEMU ARM64 Android device and cannot synthesize that receipt. A deliberate `v030-physical-arm64` label now also admits the hosted Android prerequisite for that exact PR head, allowing a stale hosted fingerprint to be regenerated without a no-op source commit after unrelated release-critical files move.

A D5 portability audit found a separate JNI text-boundary defect: `libcmpct_portable` exposes authenticated archive paths as standard UTF-8, while JNI `NewStringUTF`/`GetStringUTFChars` use Modified UTF-8. Supplementary Unicode code points therefore were not guaranteed to survive either member-name delivery to Java or Java archive-source filenames passed into the native opener. The JNI shim now converts Java UTF-16 to validated standard UTF-8 explicitly (rejecting embedded NUL/unpaired surrogates and bounding expansion) and decodes native standard UTF-8 bytes through Java's UTF-8 decoder rather than treating archive bytes as Modified UTF-8. The ordinary logs-inverse Android product vector carries a U+1F680 hardlink alias, and instrumentation stores the archive itself under a U+1F680 filename, strong-verifies it, resolves the exact alias and compares its member bytes to the regular owner. This changes no archive grammar and adds no Android parser. It is implementation/regression evidence only until a substantive exact-fingerprint hosted Android run completes; physical ARM64 remains mandatory separately.

### Physical ARM64 runner availability constraint

The first real physical-device request is preserved as a scoped platform-availability negative rather than a product failure: workflow run `33556716464`, job `100019229108`, targeted exact source `0d08feff7d8ad272ad9a81b95cd0204c7c722178`, remained queued without executing any job step and was ultimately cancelled roughly 24 hours later. The run therefore proves neither Android success nor Android semantic failure; it shows that the required self-hosted `[linux, arm64, cmpct-android-physical]` execution resource was not obtained during that request window.

Do not repeatedly spend scarce evidence windows re-requesting physical acceptance while the release fingerprint is still moving. Re-request it only after matching hosted Android evidence is green and the candidate is otherwise frozen enough that a physical receipt can survive. If the dedicated runner/device is still unavailable then, preserve that as an external release blocker; never substitute emulator, QEMU, cloud ARM or inferred ABI evidence for `physical_arm64_android_green`.

These changes are **not yet completion evidence merely because they are committed**. Do not move T01 to `DONE` until the substantive current-fingerprint native authority, hosted Android, ZIP portability, recovery/fuzz/resource and required physical ARM64 receipts are genuinely complete and machine-checkable. Classifier-only greens, queued jobs, cancelled runs and historical fingerprints earn zero completion credit.

### Exact-fingerprint revalidation request — 2026-09-03

The first revalidation wave in this activation proved native and ZIP authority on candidate fingerprint `e88b5de2ce76acabdf7bc412c2a42c2931f870d9c43bdbdda9cfa445f441e548` at exact source `45b96580a7ffe80926a717973eb68019024f9555`; those result-bearing jobs completed green and their evidence/receipts were preserved.

T00 then discovered that canonical `main` had moved by 29 commits and reconciled it semantically at merge commit `0313258a25f1a87f78fdddfbb445d4a41e25f734`, reaching 0 commits behind main `dd0c12cd6ee2dbb859464ea5c6be221ad34b9fdf`. Because the imported 0.29.l public surface includes fingerprinted paths (`SURFACE_REVISION` and `site/src/**/*`), the earlier `e88b5de2...` receipts are now historical mechanism evidence rather than final exact-candidate release credit.

The post-main native and ZIP revalidation on source `298a348647e783c672dbe2515dc1a6ac8bd144ee` completed green, but its fingerprint `8abe67c6c9a93e72eeed61dba13cfc990c21652c43749dfa36d213b658c8358e` is now historical because the Android evidence workflow itself required a release-critical custody correction.

Hosted Android run `33770937020` was semantically green through multi-ABI build, portable-JNI dependency checks and emulator instrumentation, but its emitted fingerprint `bc760c7b0e9e018da0f2dac150a75c30c284159cc748cf0e2ff6b36ba478b5da` was invalid as candidate identity. Root cause: the workflow generated exact conformance vectors under fingerprinted `tests/conformance/**` and only afterward calculated the release fingerprint, thereby hashing its mutated CI worktree rather than the clean checkout. This is a measurement/custody failure, not an Android product failure.

Commit `6de1900d938ce4de12048f1bd5f0202943483ef2` corrects that ordering: hosted Android now captures the clean exact-candidate fingerprint before any generated conformance vector can mutate a fingerprinted path, and evidence later reuses that immutable captured value. Because `.github/workflows/android.yml` is itself in the release fingerprint, this fix intentionally invalidates every older strict receipt. Do not rebind `8abe...` evidence to the new fingerprint. Rerun native, ZIP, hosted Android and all other normative receipts from this corrected fingerprint floor.

This coordination-state write is intentionally outside the fingerprint and is also the explicit admission request for fresh native and ZIP authorities, both of which path-scope `docs/v030-coordination/tasks/T01-native-portability.md`. A fresh physical ARM64 request must target the same post-fix source SHA as its hosted prerequisite; queued or stale pre-fix hardware runs earn zero credit.

### Post-generalization-custody revalidation request — 2026-09-04

The authoritative generalization workflow's CI custody model was corrected at release-critical commit `2b67c94c5277699fdfa42b2e09651fa640b0552c`. Because `.github/workflows/v030-release-generalization.yml` participates in the release fingerprint, the existing `8abe67c6...` native and ZIP receipts are intentionally stale even though their underlying mechanism evidence remains useful.

This T01 update is the repository-designed fingerprint-neutral request hook for a new **result-bearing** native-authority and ZIP-portability revalidation wave on the post-custody fingerprint. Do not infer completion from classifier-only greens. Preserve the emitted candidate fingerprint and candidate SHA from each substantive job, and mint/refresh strict receipts only if the complete native/ZIP matrices finish green and match one another exactly.

No product code, archive grammar, benchmark threshold, locality bound, recovery rule, or platform requirement is changed by this request.

### Frozen-dependency revalidation request — 2026-09-04

Native dependency resolution is now part of the candidate rather than ambient CI state. The portable lock and native-core lock are both committed, both are guarded by `cargo metadata --locked`, and both must remain byte-identical through their release-facing builds. The native-core lock is the exact Cargo-generated artifact recovered from run `33900084492`, with SHA-256 `007f963ed4e135c6dcacb09cd353064ddda87453af481990ca17f7a221402cc1`; manual reconstruction of generated lock bytes is explicitly disallowed by the failed `zmij` checksum attempt preserved in CI history.

This coordination-only mutation is the fingerprint-neutral admission request for the current native-authority and ZIP-portability result-bearing jobs after the lock/custody corrections. Native-core has the same T01 hook and must also finish its full matrix. All three lanes must agree on the same release fingerprint before their receipts can advance T01. Hosted Android and physical ARM64 remain separate mandatory receipts; a physical request cannot substitute for matching hosted Android v2 evidence.

No format byte, product code, benchmark corpus, threshold, locality ceiling, recovery rule, integrity rule, or platform requirement changes here.

### Post-v16 exact-fingerprint revalidation request — 2026-09-13

Mission lock: the current authoritative product fingerprint should already contain the landed implicit-v4 Python/native/recovery implementation; the remaining question is whether the normative native-authority and ZIP-portability matrices still pass together without any product mutation. The disproof condition is strict: any substantive matrix failure, candidate-fingerprint disagreement, exact-tree/member mismatch, recovery/locality regression, or result-bearing receipt failure blocks credit. Classifier-only greens and stale historical receipts do not count.

This T01-only mutation is deliberately fingerprint-neutral and exists solely to request fresh result-bearing native-authority and ZIP-portability execution on the current product candidate after the v16 research negative. It changes no archive bytes, selector rule, benchmark corpus, threshold, locality ceiling, integrity/recovery requirement, native parser contract, Android requirement, or release score.

If both lanes finish green, record their exact candidate fingerprint and source custody before advancing any portability claim. If either lane is red, preserve the failure and diagnose it before touching product code; missing runners, dependency outages, timeouts and custody defects are infrastructure evidence rather than product losses.

### Post-hardlink-custody exact-fingerprint revalidation request — 2026-09-13

The hardlink metadata parity repair is already present in the product candidate, and native-authority has independently completed green on release fingerprint `e617b854ae2af6997dce59d1d69a7dec583c03355e637a7c3a3b8749318e98c3` at source `bb75d1912499e4660b2ef319894131885f4fb4db`. Its strict artifact reports a stable fingerprint and green G04, PrefixGraph, Logs inverse, implicit-v4, recovery, genuine r24 fallback, builder-independent golden and shared-core facts.

This coordination-only mutation does not participate in the release fingerprint. It is the deliberate request to execute the full result-bearing ZIP-portability matrix (and any other T01-scoped classifier that requires this hook) on the same unchanged product fingerprint so T01 can distinguish a real exact-candidate parity result from stale historical receipts.

Disproof remains strict: any ZIP round-trip/member-tree mismatch, candidate-fingerprint disagreement, dependency-lock drift, locality/recovery regression, or substantive matrix failure blocks portability credit. Classifier-only green, stale receipts, or a harness/provider failure do not count as a product result. Diagnose infrastructure/custody failures before touching product code.

No archive grammar, product code, selector rule, benchmark corpus, threshold, locality ceiling, integrity/recovery requirement, platform requirement, release score, or version is changed by this request.

### Post-Android-route exact-fingerprint revalidation request — 2026-09-14

The persisted `native-r25` and `zip-portability` receipts bind fingerprint `e617b854ae2af6997dce59d1d69a7dec583c03355e637a7c3a3b8749318e98c3` to evidence produced before later release-critical Android workflow changes. After source `0a9447d0b3dbedd289ca661418386031e689021a`, `.github/workflows/android.yml` and `.github/workflows/android-physical-arm64.yml` changed; both paths are explicitly part of `docs/V030_RELEASE_LOCK.json` fingerprint scope. The strict release front door must therefore treat the persisted `e617...` receipts as historical mechanism evidence for current release authority. They must not be rebound to the current candidate.

The current branch head before this coordination-only request was `23314823ec15e4c12a34f33c3dc2904d5eca99bc`. This task file is intentionally outside release fingerprint scope and is the repository-designed admission hook for a fresh result-bearing native-authority and ZIP-portability wave on the unchanged current product candidate. The purpose of this request is to recover the actual current candidate fingerprint from execution, not to infer or type it from history.

Credit remains fail-closed: mint or refresh strict receipts only if the full native and ZIP matrices finish green, independently emit the same current fingerprint, bind their exact source/evidence hashes, and preserve every existing recovery/locality/dependency-lock assertion. Hosted Android and real physical ARM64 acceptance remain separate mandatory evidence and are not implied by native/ZIP success.

No archive byte, product implementation, selector rule, benchmark corpus, comparator setting, threshold, timing boundary, locality ceiling, integrity/recovery rule, platform requirement, version or release score changes in this request.

## Current continuation rule

Work directly on the authoritative branch. Preserve useful earlier implementation/evidence provenance where it still applies, but rerun every normative native/platform receipt on the final reconciled fingerprint. Historical or pre-fingerprint greens prove mechanisms only.

Move T01 to `DONE` only when the implementation and all release-lock evidence obligations are durably closed on the authoritative branch.