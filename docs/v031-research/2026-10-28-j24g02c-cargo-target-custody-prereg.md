# J24G02c — Cargo build-generated source must not enter prospective source identity (preregistration)

**FROZEN BEFORE PATCH / DRAFT ONLY.** Original J24G02b exact Git HEAD `04bf0f3517ed611071ca9ef8dc3453d7417f66ec`, prospective tool Git blob `4a8c0748b03f621add78810057d9f708f8050e06`, prospective manifest blob `8485f3f91ee3dc670bc42352a7c65e610605b060`.

## Unexpected contradiction from real hosted evidence

[Actions CMPCT tests #40626524790](https://github.com/FCMO-AI/.CMPCT/actions/runs/40626524790) **SUCCESS**: 806 pass / 1 skip, source receipt `04bf0f3517ed611071ca9ef8dc3453d7417f66ec`, candidate fingerprint `2966b15b8f1354906beadf595bf8f1380a376d36a215ccbbd64ce037a3f288fe`, **2,334 paths**. Downloadable [artifact 12789742706](https://github.com/FCMO-AI/.CMPCT/actions/runs/40626524790/artifacts/12789742706) was directly inspected.

Independent GitHub full Git-tree audit of **the same HEAD**, `truncated:false`, showed **2,327 tracked paths** matching the candidate globs. Exact artifact path comparison by top-level directory isolated *all seven additional runtime paths* under `native/cmpct-core/target/release/build/`: generated Serde/thiserror private.rs, zstd-sys flag_check.c and three zstd*.h headers. These are Cargo build artifacts **not in Git**, created when the `.[test,audio]` package is installed before the fingerprint job. Fingerprinting them violates the intended stable Git-source identity and introduces environment-dependent candidate fingerprints, even though source SHA and source Reader are unchanged.

## Causal mechanism / prediction

The prospective tool walks `glob.glob` over the mutable installed working tree. `native/**/*.rs`, `native/**/*.c`, and `native/**/*.h` match generated `native/**/target/**` paths. Prediction: explicitly excluding Cargo `native/**/target/**` from the prospective source walk will reduce the hosted **same tree/environment** receipt from 2,334 to 2,327 paths (unless independently generated additional eligible files arise). It must preserve all 60 Git-tracked native matches and the three recently added research source files, the four formerly inherited CI test purposes, the no-historical-lock modification invariant, and the Linux Reader product source.

## Stronger control / cheapest decisive court

Use a tiny temporary source tree with a real tracked-looking `native/crate/src/lib.rs` and `src/main.py`. Adding/mutating Cargo-generated `native/crate/target/release/build/serde/out/private.rs` (and `.c/.h`) should not alter the new prospective digest, while changing the non-target Rust source must. The old donor implementation includes the generated paths and changes its fingerprint; preserve that negative exact-head hosted receipt. The prospective tool itself remains testable without Git in fixture mode. Use one narrowly scoped skip; do not suppress all `native`, weaken required sources or change evaluator/release law.

## Falsifier / carry debt

Reject if original tracked native sources are excluded, if research scripts go missing, if stage-generated `target/` still changes the digest, if source identity jobs fail, or if historical v0.30 release lock / product Reader changes. Full CI/benchmark must run independently; release credit stays zero. A skip for a **generated Cargo target directory** is not a skip for a legitimate archive or test result. Source fingerprint is still not a cryptographic signature of a tracked Git tree; other generated-file families remain a future completeness risk until independently audited.
