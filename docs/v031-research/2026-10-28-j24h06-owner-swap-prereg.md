# J24H06 — Prospectively falsify hardlink-owner identity across a late output-directory mutation

**UTC 2026-10-28, prediction recorded before test code or hosted results.** Scientific investigation only. Existing product composition: [#629](https://github.com/FCMO-AI/.CMPCT/pull/629), exact parent `22fb832777211a5aa19ccb1c9df54fa4714ff22f`. On-disk r24 and release v0.30.0 unchanged. Do not alter the owner's branch, historical tests, format, or promotion law.

## Primary scientific question

Does the #629 owner-first hardlink extraction preserve its advertised verified *physical owner* when an untrusted, concurrently mutable destination replaces that owner after the extractor checks `os.path.isfile(target)` / `not os.path.islink(target)` but immediately before its pathname-based `os.link(target, alias)`? A successful negative control must demonstrate the original first-party Builder→Writer `append_rename` archive is authenticated, both rows read and verify, and an unmodified destination yields exact bytes and shared inode. This court concerns output-tree race custody, **not** archive signature forgery or remote exploitability.

## Baseline / mechanism / alternative

The #629 Reader computes and materializes owners first, but at `src/cmpct/reader.py` near its deferred-hardlink loop validates `target` by pathname and then calls `os.link` using that pathname without a stable owner inode/file descriptor. An adversary able to mutate the destination between these operations could substitute an external symlink, potentially causing an alias to represent a different inode or logical content, possibly a symlink itself. Existing issue #265 concerns *pre-existing ancestor symlinks*; #528 concerns *post-verification S_CHUNKS/S_CDC temporary inode substitution*. This is a narrower distinct cross-call owner-swap question, not a duplicate implementation.

A stronger simpler control is to leave the destination unmodified. A different explanation is that host OS `os.link` refuses substituted symlinks, that the Reader rechecks inode/type after linking, or that the authenticated content/identity remains exact despite the attempted swap. The experiment must record actual host semantics instead of assuming `follow_symlinks` behaves identically on Linux/macOS.

## Prospective instrument, prediction, and disproof

On Ubuntu 24.04 and macOS 14, install the **real exact-source #629 package** from checkout, use public `Builder`, `append_rename`, `preflight_archive`, `CMPCT.read/read_range/verify`, `extractall(metadata=True)`, and OS physical stat. Construct a file owner `b-owner`, hardlink `z-alias`, and Writer-renamed `a-alias`, plus unrelated **external** sentinel containing *different* bytes. A no-interference extraction must produce a regular owner and alias with identical authenticated payload and same inode, distinct from external.

Then repeat on the same immutable archive into a fresh output directory while deterministically triggering the race **only at the `os.link` boundary**, after real Reader guards: temporarily intercept `os.link` to atomically rename the materialized `b-owner` aside and install a symlink at its previous pathname to the external sentinel, and then delegate to the original OS `os.link` unchanged. Track invocation count, real OS link result, owner/alias `lstat` type, `stat` dev+ino, member bytes, external sentinel bytes and SHA, signed member SHA, exception/return, and exact archive SHA. Use `try/finally` to remove instrumentation.

**Prediction:** the control is exact. Under race injection, extraction either returns with an alias failing signed bytes and/or signed inode topology (material vulnerability in this hostile-destination concurrency scope), or raises a clear exception rather than silently publishing inconsistent extraction. If the OS refuses, do not call it a product failure. If it succeeds with a safe authentic owner despite substitution, the hypothesized race is falsified on that host. The test must accept no fake mocked successful link; OS must actually execute it. Preserve all outcomes, including unresolved or host-different outcomes.

## Evidence tier / resources / decision

A deterministic callback-injection test is a **controlled causal race demonstration**, not a stochastic exploitation-rate estimate, a full filesystem threat model, or an actual remote attack. This rung can decide whether a pathname identity gap exists. It cannot prove portability beyond tested hosts or justify a product fix until source-pinned real-world adversarial validation.

If the gap reproduces, mark #629 **not promotable under hostile/concurrently mutable destination semantics**, notify existing destination/race owners, and prefer reconciliation with an fd-/inode-owned extraction boundary instead of a second independent product implementation. If the safe control fails, diagnose the harness before claiming anything. Do not weaken earlier default metadata/inode/timestamp acceptance, and do not change `docs/discovery/STATE.json` as a lock. No version, merge or release credit from this research.
