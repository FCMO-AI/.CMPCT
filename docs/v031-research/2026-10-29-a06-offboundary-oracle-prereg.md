# A06-O0 — exact off-boundary shared-region opportunity (prospective preregistration)

**Frozen before measurement, 2026-10-29 UTC. Research-only; no product, format, benchmark, comparator, release or Discovery Engine mutation.** This A06 question in `docs/ASSUMPTION_LEDGER.md` is separate from prior A16 positional sharing (#683/#685) and from O94 dictionary-framed PACK (#452). Source is released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / format r24. No currently visible PR owns a narrow A06 off-coordinate exact-region oracle (search 2026-10-29T12:00 UTC); recheck before late writes. Do not conflate this branch with a claim to implement CMPCT's CDC, Mosaic or product Reader.

## Scientific question
Can byte-identical regions shared by *different* natural files but occurring at *different offsets* carry enough **honestly charged** information headroom to justify an independent A06 physical-ownership representation, rather than repeating A16's position-aligned negative?

## Baseline and stronger controls
Use complete files, not 64KiB prefixes. Select three disjoint 32-file cohorts deterministically by SHA256(path) ordering from public installed `/usr/include` header trees; pin each selected path, size and SHA256. Treat this host environment as a reproducibility boundary rather than a public frozen benchmark. Compare a streaming exact-region lower rung against (1) no cross-file reuse, (2) identical whole-file dedup, (3) exact same-position 4KiB sharing, (4) zero-copy optimistic ownership with each decoder-visible reference descriptor charged, and (5) a same-input Zstd-19 solid byte control where available. The strongest existing CMPCT CDC/delta mechanism is an **external inherited mechanism** not reproduced by the lower-rung detector; therefore no superiority over CMPCT or product claim can be earned in O0.

## Oracle and sufficient negative condition
A deterministic content-only rolling-hash witness scans all offsets for 64-byte anchors satisfying a fixed low-bit predicate, stores a bounded number of previous-file anchors per hash and byte-confirms every proposed match; extend exact matches up to 64KiB and require length >=128B. Record actual bytes matched to earlier files without double-counting each target byte. This is an *incomplete* discovery oracle: a miss is not an impossibility theorem. At minimum charge 16 bytes per COPY descriptor and 16 bytes per file plus the full unmatched literal bytes; also disclose an unrealistically generous zero-cost decoder-visible source map separately. The weak O0 oracle is not an archive and may not receive product credit.

**Kill/narrow:** if all three cohorts show <=2% of raw logical bytes cross-file-covered even by the gifted matched region profile, retire this *bounded anchored detector* on the natural-header regime; do not extrapolate to arbitrary data or all possible A06. If one cohort shows >=10% cross-file coverage and at least 3% theoretical savings versus same-input compressed-independent total under a generous compressed model, preserve as an O1 candidate for a full charged exact encoding; otherwise mark insufficient headroom/ambiguous and prioritize convergence rather than building another representation. The acceptance is *science opportunity only*, not product promotion. Never move this condition after results.

## Falsifiers and controls
- Independent rolling-hash proposals must be checked byte-for-byte; exact unshared random files should yield no matches.
- An intentionally offset-shifted synthetic control must be detected (and position-aligned 4KiB control should lose); a boundary-mutated control checks false-positive discipline.
- Path identity/extension must not influence matching or admission; source provenance is included for reproducibility only.
- Repeat sample selection twice to detect accidental duplicates; report source file SHA256, libc/zstd and process/platform version, compressor settings, exact CPU/wall and peak RSS where available.
- Distinguish completely gifted logical copy coverage from valid stored bytes, especially compressed controls, descriptor overhead, chunk/reconstruction amplification, integrity, and reader portability. No claim about these unmeasured dimensions.

## PARETOBONK / concurrent work
Dominant product debt is existing multi-PR Reader/compaction safety/performance (#569, #741, #749, #750), already owned. Comparing a cheap, distant A06 information model can prevent future costly blind implementation; a full product implementation is unjustified absent a substantial O0 signal. A16 #685 has a **different position-locked ownership predicate** and did not demonstrate this offset-free variant. A06 is unclaimed as of preregistration; no shared STATE or owner files are touched.

## Expected outputs
A deterministic runner, raw JSON with per-file source fingerprints and exact match receipts, independent randomized/shifted controls, host/evidence boundary, compact result and a decision: O0_HEADROOM / NARROW / RETIRE_DETECTOR / AMBIGUOUS. Include a script replay command and SHA256 artifact fingerprint, not merely prose.
