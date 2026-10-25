# O64 — NTFS directory named streams: fail-closed admission prospective hypothesis

Date: 2026-10-25 UTC. **STATUS: PREREGISTERED; no implementation/result yet.** 

## Authority and frozen baseline

Child branch `agent/phased1-v031-o64-win32-directory-ads-admission-20261025` is based on O57 [PR #413](https://github.com/FCMO-AI/.CMPCT/pull/413) exact `d9f9fa724c139c6281f0e2a92c66601bee912618`; Builder blob `7a13545c7dc22ea973f90930fae6cf053f13f1f2`; helper blob `23207ac06797fb21322cf327e97928fdbb5241c2`. The original O57 tests are immutable controls. The independent [O61-D / O61-D2 PR #416](https://github.com/FCMO-AI/.CMPCT/pull/416) reproduces stable NTFS directory ADS loss and a valid plain-directory rejection from naive regular-file helper reuse. Shipped r24/v0.30 unchanged.

## Question, prediction, falsification

Can a directory-aware Win32 stream check reject a **stable** non-empty named $DATA stream on a nested directory (and optionally source-root directory) *before writing a falsely complete revision-24 archive*, while accepting normal directories whose FindFirstStreamW enumeration returns ERROR_HANDLE_EOF=38 and retaining O57's existing regular-file/hardlink fidelity? 

Prediction: change only directory admission, preserve regular-file exact behavior and output bytes on all supported static trees. Native Windows 2025 installed package court must prove nested named stream refusal, empty directory acceptance, root named-stream refusal (if supported by host), inherited O47/O48/O50/O57 invariants, intact prior output, positive content and hardlink topology. Any legitimate directory refused, any named ADS silently accepted, physical alias conflation, unsupported stream enumeration error silently swallowed, or output clobber falsifies candidate. A host incapable of root ADS must classify that test UNSUPPORTED and not claim it as PASS.

## Cheapest evidence and alternatives

Cheapest independent source oracle is genuine Windows FindFirstStreamW/FindNextStreamW plus direct open of stable directory ADS; use CMPCT installed outside checkout to avoid accidental source substitution. Original O61D showed 676-byte loss; O61D2 demonstrated ERROR_HANDLE_EOF=38 is legitimate when enumerating an empty NTFS directory. A naïve global use of regular guard is ruled out. An r25 wire extension for named streams is a much larger portability/reader obligation; a fail-closed r24 gate is reversible and preserves format. A second cloned Win32 implementation is inferior to sharing helper code if file-specific behavior remains identical. Modifying or weakening historic source-locked tests is not allowed.

## Scope and negative obligations

Static-source fidelity only. Concurrent pathname pivots, descriptor binding, reparse behavior, Win32 network volumes, and post-enumeration mutation remain outside proof; safe rejection on unknown enumeration errors. Do not call a green unit suite release approval. Measure actual installed Windows, Linux, macOS and CPU/wall create cost on many nested directories before release. No frozen corpus, comparator, threshold, code fingerprint or version change. Do not update the Discovery Engine cache merely to mark an activation.

## Decision record

TBD after executed source-verified Windows/native tests and CI. Preserve every failed run and its interpretation. Product promotion requires full inherited product gates, exact-head CI and performance release economics.
