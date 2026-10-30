# J24P03 — Direct macOS wheel: isolated ARCHFLAGS causal A/B
Date: 2026-10-30
Status: PROSPECTIVE PREREGISTRATION, before instrument or hosted evidence.

## Baseline and authority
Canonical released CMPCT `main@80c358f8824ec1b20d349c92ed94c898090969b0` is v0.30.0, revision 24. Issue #851 records a **real direct-wheel architectural mislabel**: macos-15 arm64 `pip wheel .` emitted a `universal2` wheel containing only arm64 native code (run 41107888352). PR #850 independently observed a **different build route** (sdist-first, two Rust targets, ARCHFLAGS explicitly dual) producing a real fat Mach-O (run 41108255587). It has not isolated the cause. PR #843 owns pre-CDLL candidate selection; #850 owns the shipping sdist workflow. This PR owns **only a controlled direct-wheel A/B**, no product/packaging/other owner modifications.

## One primary scientific question
On the **same macos-15 arm64 runner and exact source commit**, with both Rust Apple targets installed in advance, can changing *only* `ARCHFLAGS` from unset to `-arch arm64 -arch x86_64` change the direct source-tree wheel from falsely universal2-arm64 to correctly universal2-fat?

## Frozen hypotheses, controls, outcomes
- H1: unflagged direct wheel repeats `universal2` tag / native `{arm64}`; flagged direct wheel produces the same advertised `universal2` portability with native `{arm64,x86_64}`.
- H0/alternative: prior observations differ because sdist vs tree build, toolchain/env, stale build outputs, target availability, temporary source state, setuptools-rust orchestration, or nondeterministic host. Both arms use the same direct `python -m pip wheel --no-deps --wheel-dir ... .` syntax. Both targets are installed before either build; same checkout SOURCE_SHA, Python, pip, SDK, package build inputs and environment, except ARCHFLAGS and **isolated Cargo target directories**. Wheel builds are separate clean worktrees; no shared build outputs.
- Stronger control: require baseline noflags **actually** reproduces arm64-only mislabel. If it does not, classify `NOT_REPRODUCED` (not a positive causal claim). The flagged arm gets credit only if the physical wheel member contains **both** slices AND filename/WHEEL tags agree.
- Kill condition: baseline different, dual flags fail, metadata/native mismatch, source not exact, source tree differs, or environment between arms differs beyond intentional isolation. A single run cannot establish broad repeatability across SDKs.
- Frozen evidential rung: two real wheel builds on one macOS runner (not a simulated oracle), physical Mach-O `lipo -archs` and stdlib wheel ZIP/WHEEL/RECORD/sha identities, positive minimal installed native smoke. Preserve both original wheels and `receipt.json`, even if the outcome falsifies H1. No releases/merges authorized.
- Forbidden: retagging, changing extension code, ignoring a failed assertion, tuning workload, lowering portability bounds, interpreting an A/B build label as an Intel runtime execution test.
- Resource budget: macos-15 host, two Rust builds and two wheels; record timings, wheel bytes and source fingerprint. No storage/create/extract/RSS product performance credit; this is a portability-root-cause court.
- Related work: #851 classification remains unresolved pending A/B; #843/#850 should be notified of actual result without editing their branches.

## Counterfactual prospective discriminator
A direct A/B with identical source/build method but two ARCHFLAGS settings could have isolated whether the previous apparent sdist-vs-direct discrepancy is fundamentally an *architecture flag* boundary. If both arms differ as predicted, prefer a packaging configuration that derives advertised tags from actual native slices and/or enforces dual compilation, instead of indiscriminately altering package tags.
