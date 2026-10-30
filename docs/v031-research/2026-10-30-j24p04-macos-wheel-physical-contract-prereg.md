# J24P04 — Prospective wheel physical-ABI publication guard (preregistration)

**Date:** 2026-10-30 UTC. **Status:** prospective, no result yet. **Authority:** released main `80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, revision 24). **Ownership:** isolated new pure-stdlib verifier and tests; no edits to concurrent native-loader #843, installed-package #850, or wheel causal oracle #852. **Class:** productization / CI evidence enablement, not a product codec or release.

## Problem and baseline

Authentic direct macOS CMPCT wheel from #852 declares `macosx_11_0_universal2` but physically contains only arm64: actual Intel runner rejects native load. The shipping-style sdist-first dual-ARCHFLAGS wheel contains both slices and runs on Intel. The inherited installed-package workflow on main does assert both slices using `lipo`, but has no gate for each slice's *minimum macOS version* nor RECORD-bound identity, and does not prohibit metadata/architecture disagreement on other packaging paths. #852's independent adversary shows a true universal2 file can be modified to advertise a later x86 minimum OS while basic lipo and WHEEL-tag checks still pass.

## Primary question / hypothesis

Can an ordinary cross-host Python stdlib offline guard, before any package import, reject all of: (A) falsely universal2 arm64-only native, (B) physically genuine fat binary whose minimum OS is newer than its wheel tag for at least one architecture, (C) fat-header/embedded-CPU disagreement, (D) damaged RECORD identity; while admitting both exact authentic dual-ARCHFLAGS / shipping-style wheels from 2026-10-30 artifacts? Is it bounded enough to use as a packaging hard gate without requiring macOS tooling?

**Strongest simple control:** current `lipo -info` + WHEEL tag assertions; it catches (A) but not synthetic (B) or (D). **Alternative explanation:** the old macOS 14 runner and pip build route may have caused the observed issue, not the wheel metadata; that affects incidence, not the correctness of a wheel-specific admission predicate.

**Predictions:** known bad 602,531-byte direct wheel rejected for missing x86; known good 1,238,788-byte wheel and released-style macOS wheel accepted; forged high-minOS wheel rejected while lipo-like arch predicate still accepts; path+SHA-valid RECORD rewrite cannot hide bad minOS; malformed/truncated/misaligned Mach-O and non-generic CPU subtypes rejected.

**Kill / narrow:** if a *known authentic* supported wheel is rejected for a reason inherent to valid PEP 427/Mach-O behavior, repair the parser or narrow its applicability before integration; if accepted forged high-minOS remains possible, do NOT claim a publication guard; if only synthetic fixtures pass, award no hosted-platform/product credit.

## Tradeoffs and charge

Guard is read-only, bounded by ZIP/member limits and expected one packaged native extension; cost is one ZIP read/hash plus Mach-O header/load commands per packaging decision. It does not make executable runtime/code-signing/SDK/Intel-launch proofs, replace native delivery tests, change compiler flags, alter format, improve bytes, or authorize merge/release. Real wheel distribution can change; reject, report, and adapt consciously rather than weakening proof.

## Decision and counterfactual

If known positive and hostile controls survive, the verifier can be reused by #850's owner as an *additional* release gate (not an unreviewed change to the active concurrent workflow). If it fails, preserve exact negative. Cheaper lesson: a build filename and `lipo` are not a complete deployment-target certificate; parse the physical slices and load commands before claiming ABI compatibility. No global Discovery Engine policy change without repeated evidence.
