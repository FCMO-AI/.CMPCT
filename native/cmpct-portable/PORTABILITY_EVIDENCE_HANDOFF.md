# Portability evidence handoff

This file is an evidence-routing handoff, not a product or format input.

The v0.30 release fingerprint deliberately hashes the Android and native evidence workflows themselves. When an admission-only workflow repair changes that fingerprint, the exact candidate must be re-exercised by the substantive native and hosted-Android authorities rather than inheriting older green receipts.

`native/cmpct-portable/**` is an explicit trigger input to both authorities. This non-code handoff is intentionally outside the release fingerprint and exists so Custody can request one fresh exact-fingerprint receipt wave without changing the canonical archive grammar, product selector, native implementation, benchmark thresholds, recovery guarantees, or evidence fingerprint again.

The current handoff specifically requests a fresh wave after the native receipt schema was reconciled with the already-executed Logs inverse all-targets suite. The receipt must bind gzip/zstd inverse parity and bounded reads, redundant-metadata recovery/fail-closed behavior, and authenticated filesystem semantics to the same candidate fingerprint as the canonical, PrefixGraph, implicit-v4, and r24 native facts.

A green hosted emulator run remains hosted evidence only. It never substitutes for the separately required licensed physical ARM64 Android receipt.
