# J24I42 — direct in-archive bounded FLAC stream oracle (prospective)

**2026-10-29 UTC — DRAFT SCIENCE; no product code, merge, release, format or benchmark change.**

## Authority and ownership
Base exactly J24I39 #776 HEAD \`0047e45e92793ca58a50251847e3cf1adb9c6d90\`; current published \`main@80c358f8824ec1b20d349c92ed94c898090969b0\` v0.30.0 / revision 24. Native production verifier belongs to #759/#765, WAV admission to #225; this experiment changes neither owner. Independent existing J24I38 authentic Builder fixtures and auditor, J24I39 verified file-backed Claxon logic, and J24I39b hostile encoded tails are the inherited controls.

## Question and competing mechanisms
Can a Claxon decoder read the encoded FLAC **directly from one bounded byte range of its original physical CMPCT file** using a seekable, offset/length-limited Reader, reconstruct the exact Builder WAV logically, and avoid materializing another FLAC copy? The earlier J24I39 performance result depended on a detached \`.flac\` file; therefore direct physical-origin operation remains unproven. A bounded range-reader is cheaper to evaluate than changing the full product's \`Archive::verify_complete\` ABI/validator ownership.

**H1 (positive):** On original 8-MiB and 32-MiB PCM16 Builder archives, bounded original-file FLAC read returns exactly the same SHA256, CRC32, logical length and STREAMINFO as the detached J24I39 baseline; a truncation of the accessible encoded range by 64 bytes is rejected even when the original archive physically contains the missing data after the artificially imposed EOF. Extra *physical* reads of encoded bytes should remain close to one full encoded stream; RSS should remain bounded by decoder allocations, not by whole WAV size.

**H0 (negative):** Claxon cannot initialize or consume the seek/read-limited view, escapes the codec payload boundary, fails identical digest semantics, or materially exports memory/CPU cost. Treat as a scoped productization blocker; preserve source/fixture evidence and revisit decoder architecture.

## Controls and disproof
- Use unchanged J24I38 Builder generator and independent MessagePack/Zstandard/libsndfile physical audit. Verify exact source SHAs, archive SHA and both indices *before* any measurement.
- Independently derive the FLAC absolute byte offset and encoded byte count from the verified CMA4 physical header, with no CMPCT imports. Do not assert that an index's checksum authenticates external origin; it proves only internal consistency.
- Compare on identical archive bytes: existing native \`Archive::verify_complete\`, existing detached J24I39 Claxon probe, and candidate bounded-in-archive Claxon probe. Distinguish unequal semantic coverage; perf is a micro-mechanism result and **never product equivalence**.
- Hostile A: known-good original range passes. Hostile B: end-of-range reduced by 64 encoded bytes, with intact archive file still containing those 64 bytes; bounded Reader **must** return EOF and decoder must reject, not silently read the adjacent index. Hostile C: replace first FLAC byte in a disposable physical archive copy; bounded decoder must reject while original source SHA guard stays intact. No archive validation claims for B/C.
- Negative if a valid file fails; SHA/CRC/length mismatches; corrupt/truncated range is accepted; any seek escapes the bounded span; source drift; missing artifact; or measurement that conceals RSS/read amplification.

## Exported cost and limits
A \`Read+Seek\` bounded file view adds seek arithmetic and an extra copy of metadata into the Rust process (small, explicit). It is not a complete authenticated Reader. Sidecar manifest derives from an independent audit, not a cryptographic signature of external source. No source-FD inode race hardening, full parser budget, ABI, Windows/macOS, archive recovery, private FLAC MD5 consistency, physical CRC conflict, sparse/chunk/pack, large-amplification future workload or full release matrix is proved here. \`rchar\` is Linux process character reads, not physical disk sectors; per-process \`VmHWM\` is not a universal decoder memory limit. Explicitly account for artifact size, benchmark repetitions and real resources when obtained.

## Decision
If the bounded original-container mechanism is accepted with equal logical digest and hostile rejection, propose it to #765/#759 as a **bounded integration option**, not as a merge-ready patch. If negative, preserve a counterexample and consider changed physical ownership or native callback decoder. Re-read current owner PRs before any shared mutation. No Discovery policy or \`STATE.json\` change without repeated decision-changing evidence.
