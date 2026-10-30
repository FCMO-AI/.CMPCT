# J24I50 — Public native complete-verification ABI/CLI, prospective preregistration

Status: **DRAFT / experimental product bridge**. Parent #803 exactly `f456370e75b71a619104f9e9bb6c622929ba8db8`, which in turn depends on #802/#788/#765. No merge, release, format revision, numeric version, benchmark gate or historical source-lock modification is authorized by this experiment.

## Baseline and bottleneck
J24I43/#788 demonstrates a single-pass bounded WAV/FLAC improvement inside `Archive::verify_complete()`; J24I49/#803 repairs inherited full tests/installed-package evidence. But neither the published r24 `cmpct-core` C header nor `cmpct-native` process CLI offers a complete-verification operation: the only public archive C function is `cmpct_entry_read_range`, whose small slices may have a strictly weaker integrity contract. Python `CMPCT.verify()` separately reconstructs in Python and is **not** automatically accelerated by native Rust measurements. The r24 portable ABI already offers a different `cmpct_portable_verify`, but wheels here package `cmpct-core`, not that dispatcher.

## Primary question
Can the already-implemented `Archive::verify_complete()` be exposed safely as one *read-only, failure-atomic* public C ABI call and an independent native CLI command, using the *same native archive handle* and preserving exact complete-verification semantics, including physical CMA4 CRC, direct WAV/FLAC SHA, source-inode custody and hostile-input rejection?

## Proposed minimal candidate
- `cmpct_verify_complete(const CmpctArchive*, size_t *out_verified)`: status=0 only after every supported content-owning member passes; explicit null-pointer refusal; count zeroed on entry/failure; match established `CmpctStatus` mapping; catch Rust unwind at the newly exposed boundary. Reuse existing `Archive::verify_complete`; **no new parser/decoder/semantics**.
- `cmpct-native verify ARCHIVE.cmpct`: emit JSON verified count/revision only on complete success; stdout remains empty on failure, exit nonzero; do not allocate a complete member in CLI.
- Test from non-Rust `ctypes` using fixed builder-independent WAV/FLAC golden; repeat with a one-bit physical CMA4 header SHA corruption that *opens* but cannot verify. Include null-pointer, count-out reset, CLI contract and a Builder-derived multientry archive if affordable.
- Run native-core format/clippy/test, Python ABI court and exact-head public CLI court. Distinguish native functionality from installed Python integration: **do not claim `CMPCT.verify()` speedup**.

## Controls / alternatives / falsifiers
Controls: unchanged `Archive::verify_complete` on exactly the same bytes, Python `CMPCT.verify` on fixed golden, public existing range ABI known limited semantics, and r24 portable verify as separate control only (not a replacement). Simpler alternative: add just a CLI `verify` command; rejected as insufficient to expose installed-library integration. Alternative: bypass checksum by CLI range concatenation; rejected because RAW/sparse partial integrity is weaker. Alternative: directly wire Python `CMPCT.verify()` to native ABI in the same change; rejected because fallback/packaging/semantic and performance claims require a separate verified integration.

KILL / NARROW if: symbol absent from built cdylib; mismatch against golden expected count or Python; corrupted fixed archive accepted; caller output nonzero after failure; null pointers invoke UB; CLI emits success JSON on incomplete verification; Rust lint/format or exact-head native core fails; cross-OS issues cannot be resolved without relaxed integrity. Do not reinterpret CI infrastructure loss as a codec failure. General Tests and Installed Native Package at parent are evidence boundaries, not automatically inherited to the new exact head.

## Scope, resource, release and source custody
No archive format, Builder, `CMPCT.verify()`, encoder choices, frozen evidence, hash semantics, source-inode ownership, performance thresholds, release manifests, or external benchmark is changed. This is a bridge to a future installed-API integration, not the final installed Python product improvement. Existing native owner #765 and #788 remain authoritative; this child changes a separate ABI/CLI adapter and tests. Historic v0.30.0/r24 is untouched.

## Counterfactual and next action
A public verification call + realistic non-Rust consumer test is a cheaper productization discriminator than another detached WAV decoder microbenchmark. If it passes, next owner should either integrate `CMPCT.verify` through the exact shipping native binding with honest fallback and ABI exposure or retain the Python baseline. Benchmark end-to-end only after identical security and startup semantics are proven.
