# O121 — Authentic O117 case-collision archive versus existing Win32/APFS Reader union

Date: 2026-10-25 UTC  
Status: **RESULT CONFIRMED, SCIENTIFIC COMPOSITION; UNMERGED CANDIDATE / NO RELEASE**  
Prospective preregistration commit: `447af8cb136cbf85239d10a2bf38cf190f341e45` (before court implementation).  
Original source: `FCMO-AI/.CMPCT agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.  
Candidate composed source: Win32 #332 + APFS #334 union #336 at `28d57e13a1b8e89a70f857f180b4403592b96e12`; Reader Git blob `550ddcc84a820fb3d06b7580dd544abb52e93f81`.  
Exact source of independent archive experiment: O117 script copied byte-identically from PR #466, blob `47a3caf5676447c3f9dd093ad542a45586a7775d`.  
Result-bearing hosted SHA: `7047310190d42a2b2d4bb288ad884d28f8c7bf66`; GitHub Actions [run 40237370713](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713): **all four jobs SUCCESS** (1 producer, three independent installed-host consumers). Later documentation/CI routing commits are not automatically entitled to that exact-head result; compare source/instrument blobs when using this receipt.

## Scientific question and decision

The O117 original Reader had a real demonstrated silent case alias loss on default Windows: two distinct logical members with case-distinct names overwrite one physical destination. PR #332 already implemented a Win32 prewrite guard and PR #336 composed it with APFS. Does the *existing candidate* eliminate the *actual O117 same-archive* loss without silently changing portable Linux archive semantics? **YES in the tested case**: exact matching physical archived bytes, original source, and independently installed candidate simultaneously establish the baseline loss, candidate zero-file early rejection on Windows and macOS, and complete three-file Linux fidelity.

This is **candidate product-composition evidence**. It does not mean v0.30 shipping Reader or canonical v0.31 branch has been repaired or the stacked union is ready for merge.

## Original physical data and identity

One independent Linux installed Builder created one real r24 CMPCT archive (not synthetic index rows). The same archive artifact was downloaded unmodified by all three hosts.

- Complete archive **1,126 bytes**.
- Archive SHA-256 **`303c3f212ddf1ab154c8240e5328c3b375142745bac7965fc8a1c740def9adf7`** (different from the earlier O117 file hash because independently rebuilt filesystem metadata can change authentic Builder archive bytes; no cross-job regeneration was performed).
- `Report.txt`: 1,974 bytes; SHA-256 `7db3beaf93286bab2b9eff505e7b774a846b12512805c2c9e65f43783ee41f02`.
- `report.txt`: 2,226 bytes; SHA-256 `845421693b4a1f1f066e06090718a6850b5cd9b3e1cf917172fb95a68e91f45e`.
- `other.txt`: 812 bytes; SHA-256 `dc64035d15fe93c3f53b64e23eeb6abaa13243d9ec03117e19a0b547a1d037f6`.
- All three members pass logical `CMPCT.read` and full `CMPCT.verify` in both installed engines on every host; installed Reader files checked byte-identical with each corresponding source checkout.

| Host / actual directory semantics | Original Reader (unchanged) | Candidate Reader (#336 exact) | Decision |
|---|---|---|---|
| Ubuntu 24.04 / case-sensitive | 3/3 exact extracted | 3/3 exact extracted | Portable valid-case fidelity preserved |
| Windows 2025 / case-insensitive | **2** physical files, lost `Report.txt`, no error | **0** physical files, managed `OSError: duplicate Windows archive path: 'report.txt'` | Previously silent loss now rejected **before** member writes |
| macOS 14 / case-insensitive | **2** physical files, lost `Report.txt`, no error | **0** physical files, managed `OSError: ambiguous macOS archive path: 'report.txt'` | Previously silent loss now rejected **before** member writes |

Each host's baseline and candidate consumed the **same** physical archive and probed the actual target filesystem case sensitivity. Original `read`/`verify` retained all logical bytes even where original extraction lost a member. Result-bearing audit markers: `O121_EARLY_REFUSAL_REHABILITATES_O117_ON_ALIASING_HOST` on Windows/macOS; `O121_INHERITED_EXACT_FIDELITY_PRESERVED_ON_CASE_SENSITIVE_HOST` on Ubuntu; `O121_INDEPENDENT_SAME_ARCHIVE_AUDIT_PASS` all three.

## Original raw artifacts / independent observables

Original [Actions 40237370713](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713) produced:

- Full real archive: artifact [12615048321](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713/artifacts/12615048321).
- Original producer provenance: artifact [12615103272](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713/artifacts/12615103272).
- Ubuntu original-versus-union JSON/logs: artifact [12615283411](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713/artifacts/12615283411).
- Windows original-versus-union JSON/logs: artifact [12615058522](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713/artifacts/12615058522).
- macOS original-versus-union JSON/logs: artifact [12615038489](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237370713/artifacts/12615038489).

The baseline loss is retained, not reclassified away. A green scientific run means both negative baseline and positive candidate guard predictions were observed in the narrow scope; no general tests, native conformance, release performance or full product promotion can be inferred from it.

## Controls, strongest alternative, negatives and missing evidence

A simpler explanation would be host path aliasing rather than an extractor problem. The actual host alias probe independently **confirmed** that explanation and exposed it as the unsafe interaction with original `extractall`; the candidate's *prewrite* validation makes the difference, while the exact archive/Reader object remained the same. The candidate intentionally fails to extract the entire archive rather than preserve its three files on default case-insensitive target filesystems: this is honest fail-closed preservation, **not a successful complete extraction**. A case-sensitive Windows/macOS destination that could represent both files may still be conservatively rejected; O121 does not establish optimal target-specific admission. No performance benchmark was executed and no archive-byte win was measured.

This court is three very small ASCII files, a static destination (not active adversarial reparse/symlink race), no native filesystem comparison for full Unicode/NTFS 8.3 or all APFS normalization rules. It establishes no power-failure safety, existing destination metadata protection, hardlink/source archive alias safety (#468), RAM/cold-read/CPU cost or larger-tree completeness. Full inherited general tests and official non-skipped ABBA remain prerequisites to promotion.

## Counterfactual and next owner action

A previous O117 experiment could have checked the already-open #332/#336 owners before proposing another extraction guard; source-authentic same-archive *integration* is the cheapest additional discriminator with genuine decision value. The mechanism was already present in #336, so a third implementation would create duplicate merge risk and no new benefit. No general Discovery Engine policy change earned; this is a transferable local decision: when scientific negative and unmerged repair address the same failure, test original real physical input against the existing candidate before implementing again.

Communicate this exact-source result to PR #336 and issue #467 owners. Reconcile #336 with Reader destination, prewrite, source-inode, fsmeta and native portability owners before any merge. Keep historical original O117 failure open as shipping/canonical truth until a legitimate integration and release covers it. No format change, core version bump, benchmark/evaluator relaxation, canonical merge, or release.

**Decision:** `O121_HOST_GUARD_COMPOSITION_CONFIRMED_IN_SCOPE` / product candidate only; promotion **NOT EARNED**.
