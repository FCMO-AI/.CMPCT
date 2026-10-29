# J24G41 — native Darwin xattr provider / prospective test (2026-10-29)

**Scope:** candidate integration on the exact O72 #428 HEAD `48b4a90487d5df6c1fe06896933689e7a8369f6d`; no format/version/release/benchmark promotion. Source law: AGENTS.md, PRE1_RELEASE_POLICY, Discovery Engine; issue #753 confirms an independently OS-readable macOS attribute omitted by default Python Builder. O65 #420 and O72 #428 own fail-closed semantics and strict Reader restoration; this child composes *their exact code*, not a forked error policy.

## Primary question and prediction

Can a bounded `ctypes` bridge to Darwin's documented `listxattr/getxattr/setxattr` APIs recover real macOS metadata in Builder and restore it under O72 Reader strict mode, without changing r24 wire, weakening O65 failure classification or the existing portable best-effort policy?

**Prediction:** on native macOS with CPython 3.11 lacking `os.listxattr/getxattr/setxattr`, an independent native system-call writer creates a named binary attribute on a regular source file; the installed Builder captures exact name/value in `fsmeta.xattrs`, and strict Reader restores it, with independently read equal value. On Linux, exact O72 tests remain passing and ordinary no-xattr archive bytes unchanged. Windows without either provider must preserve preexisting unsupported semantics. Reproducible mode probes no host xattr API.

## Strong controls / alternative hypotheses

1. Existing `os` wrappers on Linux are the simpler, stronger control; retain them without additional syscalls.
2. Native `xattr(1)` can establish macOS OS capability but must *not* be used by production hot-path code.
3. Missing metadata may instead be due to filesystem restrictions, name/encoding, protected/compressed xattrs or source mutation. Gate on a native OS roundtrip before attributing capture failure to CMPCT.
4. `ctypes` ABI and two-pass allocation may fail, overflow, race or mis-handle symlinks. Use Apple-documented signatures, nofollow, exact negative errno, bounded allocations and retries; reject ambiguous or invalid keys rather than silently dropping them.

## Kill / narrow criteria

- Any valid macOS native attribute omitted by non-reproducible Builder, or strict restore falsely succeeding after failed application.
- Any unchanged Linux/Windows control regression, existing historical r24 conformance/parity change, or O72 source/test compatibility regression.
- Unbounded allocation, exported buffer cost, silent UTF-8 decoding loss, wrong Darwin 6-argument getter ABI or symlink-follow behavior.
- Green CI without actually executing a native macOS physical positive counts as **evidence failure**.

## Evidence rung and economics

First: Apple syscall prototypes + isolated native bridge tests; next: installed package authentic r24 physical roundtrip on macOS and Linux, no-source-change fingerprint control on Windows. Only then broader source-bound full CI and same-input CPU/RSS/bytes if this candidate survives. Do not claim whole-tree snapshot atomicity, hostile same-UID staging security, native Windows support, arbitrary ACLs, or release readiness.

## Ownership and concurrency

PR #428 retains O72 source-capture/strict-restoration ownership; this branch owns only Darwin provider composition. Issue #753 is the defect reference. Reconcile source SHA and owner branch before late writes. Leave `docs/discovery/STATE.json` to its existing owner; record evidence here rather than duplicating project state.
