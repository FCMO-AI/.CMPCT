# J24C02 — prospective four-way Reader admission / publication composition

**2026-10-27 UTC, before source implementation or result-bearing execution.** Research/product-candidate evidence, not release authority. Exact parent J24C01 #567 `d3b12852511095d6e98803f55cfd700b8e9ac6b3`, Reader blob `930f90478a45201617e675e3d9bd0eb9b7c70f53`; O215 #568 source `3aad965da3b81eb47257e974e1bd86a21add45da`, Reader blob `73e4bfdab49af8c3302a313793ed594a8272b51d`. Source-of-truth is GitHub; this proposal is stacked on #567, not main.

## Primary falsifiable question

Can the **exact O215 same-effective-index S_CHUNKS admission delta** be composed into J24C01's one installed Reader, preserving O212 S_SPARSE, O214 S_CDC, J24W02 missing-fchmod Windows extraction, and J24F11/J24F12 Linux inode-owned fresh publication? O215's unchanged parent test produces an authenticated r24 S_CHUNKS descriptor with declared logical length five but only four authentic physical bytes, which J24C01's inherited constructor should accept, allowing an in-bounds short selective read. Candidate must reject *before mmap* without reopening a pathname.

## Baseline, controls and causal alternatives

- Original fixed-geometry owner #568 already demonstrated 12 cases including 4096 repeated references on three independently installed hosts. Reuse its original test verbatim, including immutable builder-independent r24 and valid 0-byte/repeated-reference controls, and verify Git blob identity. Do not rewrite oracle expectations.
- Re-run unchanged J24C01 installed-package O212/O214/fchmod courts on Ubuntu/macOS/Windows and existing J24F11/F12 plus joint genuine CDC physical-inode court on Linux; do not substitute separate-parent greens.
- On Linux, separately execute the unmodified J24C01 pre-change Reader against the O215 hostile case and demand the expected *in-bounds short selective read*, while full read/verify and strict preflight already reject; no false claim of post-verify corruption.
- Simpler alternative: run preflight on source pathname first; reject because #546/O208 proves a second-pathname read can check the wrong inode. Another alternative is a duplicated fixed-chunk validator; reject because `cmpct.validation._validate_storage` already provides the exact r24 contract.
- Source intervention must be limited to importing O215's *constructor-specific* gate/comments from its original Reader; all other J24C01 Reader methods and the canonical validator retain byte identity. The candidate must not silently discard Linux fd publication, 64-KiB immutable RAW windows or Win32 optional fchmod behavior.

## Kill/narrow criteria

Any inherited positive regression, changed existing Reader outside the bounded constructor, failure to reject authenticated fixed-short-read before mmap, resource budget failure or loss of valid chunk reuse defeats integration. O(number of references) cold-open scan debt is acknowledged and needs measurement before promotion. Host-specific O_TMPFILE semantics do not generalize to Windows/macOS; existing-target hostile overwrite #528 remains unresolved. Full ZIP64/CI/release-performance/legacy recovery are not covered by this narrow court.

## Concurrency / evidence custody

#568 owns fixed-chunk admission; #567 owns existing composed Reader. This independent **composition** changes neither owner's branch; review before merge. No force pushes; preserve SHA-bound parent source and test identities, original negative/positive measurements, CI run IDs and raw hosted artifacts. Discovery STATE.json is a staleable cache, not a claim lock, and remains unchanged absent a decision-changing global frontier transition. No changes to format r24, released v0.30.0, comparator, thresholds, benchmark inputs or version.

**Prospective acceptance:** one newly composed Reader with source-exact installed tests on three OSes and original Linux fd courts green, plus original pre-change negative, no unsupported full-product win claim.