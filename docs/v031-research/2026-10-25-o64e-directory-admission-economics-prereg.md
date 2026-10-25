# O64-E — Source-exact Win32 directory-stream admission economics preregistration

Date: 2026-10-25 UTC. STATUS: PREREGISTERED, **no results yet**.

## Context and fixed mechanism
Parent O57 [#413](https://github.com/FCMO-AI/.CMPCT/pull/413) SHA `d9f9fa724c139c6281f0e2a92c66601bee912618` vs child O64 [#419](https://github.com/FCMO-AI/.CMPCT/pull/419), verified product code Builder blob `b02a30d4ad1b26ea8eea49e11159113caebd6006` and helper blob `61d8cab1545c491da76b23ea89d4ca85d3030c5d`. O64 adds one native Win32 directory-stream enumeration for every nested directory plus the source root, retaining the original regular-file check.

## Prospective question / controls / potential disproof
On the **same stable synthetic Windows NTFS tree**, how much genuine end-to-end Builder wall/CPU cost does directory ADS fail-closed admission add relative to identical O57 source? This is deliberately a product-economic **negative-discovery-capable** question, not a reason to weaken the static fidelity gain. Empty dirs isolate enumeration cost; dir+tiny-file mixes check realistic proportional cost. The strongest simple control is actual O57 product source, not Python no-op or a conjectured cost.

Predict measurable per-directory CPU overhead, potentially material above 2048 directories; no complete CMPCT stored-byte difference for supported static trees. Compare at least 256 and 2048 empty directories and a >=256 directory/tiny-file mixed regime, with actual O57 and O64 sources, same identical physical input, fresh processes per sample, alternating ABBA order, four samples/version/case or more, raw times, in-child wall/CPU vs whole-process startup, complete output SHA/bytes. No separate random trees. CPU source of cost cannot be conclusively attributed without separate function profile.

## Decision rules and safeguards
A candidate slowdown exceeding **both** 5% relative **and** 3 ms absolute in repeated medians is a promotion-risk signal under current normative release timing law, not a standalone official-gate failure. Any archive-byte mismatch on identical source is a hard functional regression regardless of timings. Material memory regression or overlarge service cost should be reported and bounded, not hidden. Source code must come from exact pinned Git identities; no shadow reimplementation or Python-level fake of Win32 enumerator. No script outcome can grant release credit; full frozen ABBA, correctness, portability and remaining source-mutation work stay mandatory. Linux/macOS no-op tests are separate and already controlled by the O64 functional court.

## Alternatives
A hypothetical Python-only microbenchmark would miss native syscall and full-Builder interactions. Running large official release matrix now is expensive and has a different question/corpus. The bounded same-host end-to-end A/B is the cheapest relevant quantitative rung. The candidate can remain a research fix if overhead is real; the safe first response is architecture/admission-cost isolation rather than relaxing the fail-closed rule.

## Decision
Pending actual result-bearing Windows GitHub Actions and retained raw samples. No numbers or claims prerecorded.
