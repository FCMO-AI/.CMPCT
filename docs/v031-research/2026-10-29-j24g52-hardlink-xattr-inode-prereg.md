# J24G52 — explicit hardlink-inode xattr contradiction: prospective test

Date: 2026-10-29 UTC. Source owner: #778 exactly `47c9a4d61cd764aa4252cad741f4b22537106c60`, experimental branch `agent/phased2-v031-j24g52-hardlink-xattr-inode-preflight-20261029`. Published main v0.30.0/r24 is not altered. This is a bounded correctness candidate stacked on #778, motivated by independently reproduced #780 / issue #781; do not copy state or modify the owner branch.

## Primary question
Can additive revision-24 structural preflight reject *two explicit, different byte values for the same xattr key on two names sharing one terminal regular-file inode*, before extraction side effects, while accepting equal requirements on hardlink aliases and distinct same-content regular inodes?

## Baseline and falsifiable mechanism
#780 exact-source Ubuntu/macOS demonstrated `preflight_archive()`, `verify()` and strict extraction accept the hostile physically self-checksummed file. Later metadata restoration overwrites the earlier alias on the shared inode. The current `_validate_index` validates hardlink paths and sparse fsmeta ordinals independently. Resolve each hardlink to terminal `K_FILE` (never by payload hash); compare only explicitly signed xattr key/value requirements within each terminal owner. Raise `ValidationError` before output construction on conflicting explicit values.

## Simpler controls and alternatives
- Reject any hardlink xattr record: too restrictive; equal values are physically representable and historical archives are at risk.
- Compare content SHA/blob id: false inode equivalence for independent same-content files.
- Compare sparse absence to an explicit value: not yet justified by revision-24's inherited omission semantics; omit this stronger claim.
- Validate only at extraction: misses independent `preflight_archive()` and may have already written destination.
- Recursive resolution: avoid depth-proportional Python recursion and quadratic nested alias chains; cache terminal owners through an iterative graph walk.

## Kill conditions / admission
The candidate fails if equal explicit inode attributes or independent equal-content inodes are rejected; if a multi-hop alias conflict escapes; if one explicit opposite value on same key is allowed; if a malformed ordinal/key/value causes uncaught behavior or a large fan-out yields pathological repeated traversal. No performance credit until measured. For correctness, require preflight to reject before a destination is created and keep original J24G51 negative evidence unedited, regardless of whether that historical repro court now reports failure by design.

## Evidence rung
First test helper semantics with synthetic graph permutations and hostile nesting in-process; then use actual first-party Builder archive plus independently modified self-checksummed index, and source-exact installed package on Linux/macOS/Windows when practical. The standalone physical xattr restoration experiment in #780 remains authoritative as inherited negative evidence; green test cannot erase it. Report code SHA, CI identity, failures and exported O(F + E + X) memory/work. No release, format, benchmark, threshold, comparator or state change.

## Scope and concurrency
Only `src/cmpct/validation.py`, a new isolated accept/reject test, research document and dedicated workflow on this stacked branch. Keep #778/#773 code and discovery state intact. Reconcile owner head before final shared comments; do not merge or promote without owner and frozen gates.
