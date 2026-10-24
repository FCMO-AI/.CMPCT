# v0.31 native S_PACK explicit operation-scoped batch — O3 prospective contract

Date: 2026-10-24. Status: **PREREGISTERED / NO O3 RESULT**.
Parent independent research: PR #319 (O1 measured native Zstd shared PACK N=256 42.24 ms versus 0.283 ms one-snapshot oracle; O2 confirmed same-open physical mutation rejection).
Source baseline: exact independent r24 S_PACK conformance PR #307 at `256a263748b9f65b4bc00dd572799e4f00ae06e7`. This experiment is independent of PR #316/#321 parser-hardening work and will not rewrite it.

## Question and competing mechanisms

**Can an explicit, opt-in, bounded native ABI operation return multiple ranges from one authenticated Zstd PACK while decoding and strong-SHA-verifying that physical PACK only once, preserving existing independent-call source freshness and exact member semantics?**

A: current `cmpct_entry_read_range` for N different same-PACK entries, authenticating independently per call.
B: one operation-scoped `cmpct_pack_read_batch` (same handle / same index / one file lock / one codec decode / one strong physical SHA), with arbitrary per-entry offsets and lengths, compact contiguous result in specified request order. No persistent cache or reused decoded state survives the call.
C: independent fixed archive vectors and deliberate same-handle source mutations; compare ordinary single-read before and after as a truth control.

**Prediction:** B will remove >90% of repeated decoded byte work for N=128 and N=256 on 192 KiB Zstd PACK; A remains preferable for isolated one-member lookups because B has request/validation overhead. If B cannot beat A materially under same source/semantics, retire this batch design. Entire source input and all outputs must match byte-for-byte with fixed independent golden witnesses and per-entry read controls.

## Invariants, bounds, adversarial disproof

- **Opt-in API only**. Old `cmpct_entry_read_range` API is untouched, preserving its per-call reauthentication semantics.
- Entire batch belongs to one Zstd PACK; mixed owners, RAW/other physical codecs, unsupported representations and bad ranges **fail closed** without publishing partial output. RAW remains ordinary range-local through existing API.
- Request count 1..1024; decoded PACK <= 16 MiB (smaller than inherited 256 MiB native direct-decode cap); aggregate output <= 16 MiB; all checked additions and target length/capacity prior to decoding.
- All index/path/physical framing and physical decoded SHA checks remain inherited; complete logical member reads retain logical SHA checks. No output buffer modification before the entire batch is validated, decoded and authenticated.
- Source edits after one batch must be observed by another on the **same open native handle**. Changes inside a single decode remain bounded by the existing single-read trust model: there is no promise of atomicity against noncooperating concurrent writers.
- A physically valid archive containing two PACK owners must reject mixed-owner requests. A forged index tuple or invalid physical SHA must fail. Bound copy/allocations; zero-length output is explicitly defined.
- ABI pointer-lifetime/overlap constraints must be explicit; no aliases may permit undefined behavior. `out_read=0` on failure.
- Preserve revision 24, Reader/Builder output bytes, codecs, VZIP/fixed/CDC/sparse behavior, existing native ABI exports and independent conformance goldens.
- Rust compile/clippy/format and Linux hosted C ABI integration gates required before product claims. Windows/macOS and RSS production effects remain debt, not assumed passes.

## Price/decision

Measure N=1,16,128,256, seven ABBA blocks where possible on same installed Rust binary and same-source archive; report all raw observations, create/extract boundary separations and one decoded-buffer RSS floor (196,608 B in O1). Charge memory, FFI request packing, physical compressed reads, total logical decoded work and the absence of cross-call caching. Compare to strong simple baseline A and invalid-input controls. A one-batch success alone does not establish release or end-to-end extraction acceleration: there is no consumer integration yet.

If O3 confirms large headroom and adversarial parity, keep as **experimental native capability** and next test an actual caller or explicit CLI batch surface, plus full product/portability benchmark. If any physical corruption or mixed/invalid request causes nonzero bytes to escape, block productization and repair/retire. Do not lower release gate/format/conformance/evaluator strength.

## Concurrency and ownership

Issue #315 is the owner of the measured product question; PR #307/#314 own fixed-wire/hostile index conformance; PR #316/#321 own duplicate-map reader hardening. No Discovery STATE update unless O3 changes a decision. Source files will be re-read immediately before late writes. This branch is an independent productization candidate rather than mutation of other owners' PRs.
