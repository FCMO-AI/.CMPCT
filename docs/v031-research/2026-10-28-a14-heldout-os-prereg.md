# A14-O1a — naturally occurring OS corpus: falsify indiscriminate CRC admission

Date: 2026-10-28 UTC. Independent prospective child of A14-O0 research PR #670. No product/release authority.

Freeze before examining held-out outcomes; **do not edit O0 preregistration or original 7-vector evaluator**.

## Question
Does the bounded O0 detector spuriously label ordinary, naturally occurring opaque bytes as a regular per-record CRC32 code, and what fraction of a diverse independent public OS corpus is admitted? This is an **admission/external-validity check**, NOT a representative estimate of prevalence of all formats using derived fields.

## Source selection, bounded and prospective
Use the present Linux container's installed public system resources, no user/private files:
- up to 64 regular nonsymlink executable ELF files under `/usr/bin`;
- up to 64 `.py` Python stdlib files under `/usr/lib/python3.13`;
- up to 64 regular nonsymlink `.so*` system shared objects under `/usr/lib/x86_64-linux-gnu`;
- up to 32 `.json` public resource/schema files under `/usr/share`.
Each must be between 8 KiB and 2 MiB, deterministically chosen by sorted POSIX path. If fewer exist in a category, use all. Do **not** publish raw bytes or entire filesystem paths. For each source, scan three 4096-byte windows at start, midpoint (4096-aligned to middle) and end. Use identical frozen O0 candidate search, unchanged 32-sample cap + all-record check. Ignore objects shorter than 8 KiB. Record per-category file/window counts, eligible candidate counts and every accepted candidate (if any); for accepted results additionally strong roundtrip/hash before claiming a match. Preserve an aggregate SHA-256 of the selected source-size/SHA manifest, OS version, code identity and total CPU/wall.

## Disproof and interpretation
Any false-positive classification (a detected field whose full candidate does not reproduce exact original) kills O0 admission safety. An unexpected *true* CRC relationship would be positive held-out scope evidence but requires independent double-check, not product credit. Zero detections on this sample is a negative prevalence observation and does NOT prove universal absence, false-positive probability, or rarity among real CRC-framed protocols. 4096-byte windows can disrupt real record alignment; track and disclose the bias explicitly. This additional experiment does not revise O0's frozen synthetic positive/negative decision.

## Boundaries
No new dependency, no frozen gate change, no raw bytes publication, no edits to the released archive. Source inventory is contingent on the current Linux image; a later host must not be assumed to have same corpus. A positive may justify controlled format-family research; a negative parks broad natural-prevalence claims pending better source-specific evidence.
