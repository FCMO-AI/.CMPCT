# J24C01 — Prospective geometry × publication-custody composition

**FROZEN BEFORE PRODUCT/TEST CHANGES.** 2026-10-27 UTC.

## Authority / exact source

CMPCT released v0.30.0/r24 remains unchanged. Start only from J24F12 #559 exact `dd723d128b5a020f154b4c9f7d37c6eedc929f24`; `src/cmpct/reader.py` blob `83c6600fa6cc951c1e6a136d239a39bb2c5d836b`. This inherits J24F11 Linux fresh-leaf `O_TMPFILE`/fd-bound no-clobber publication and J24F12 `O_PATH` write+search-only destination. Independent source: O214 #564 `d90dab60d2fe646dbda9e61de3b5080ca83c7b7e`, Reader blob `4d651674adfa39068e8faa1aaa44107776342a52`, stacking O212 #560 `3249a7d6d09a9890cfa65b03e239a7973bf92614`. Existing `cmpct.validation._validate_storage` remains authoritative for S_SPARSE and S_CDC geometry. Do not modify its semantics. The PR is a *draft composition*, not replacement ownership or release.

## One primary question / baseline

Can the **same genuine installed Reader** simultaneously (a) reject authenticated-but-inconsistent S_SPARSE/S_CDC declared lengths at first open, from the same effective index used for reads, **before mmap**; and (b) preserve J24F11/J24F12 Linux descriptor-identity publication for authentic valid chunked leaves, including mode-0300 write+search directories and late final-leaf collision refusal? These are distinct invariants sharing `CMPCT.__init__` and `_extract_chunked_verified`. Separate passing PRs do not prove their composition. The #559 baseline lacks same-index geometry admission; #564 lacks Linux publication custody.

**Prediction:** transplant exactly O214's bounded `__init__` admission/failure-cleanup into J24F12 without changing other Reader methods; independent O212/O214 r24 wire tests and inherited J24F11/J24F12 real-process Linux courts all pass on *one* source tree. Host Ubuntu/macOS/Windows support for CDC/sparse validation should hold; Linux-only fd publication evidence must remain scoped to Linux and unprivileged UID.

## Controls, falsifiers and simpler alternatives

- Strong control: unchanged J24F12 #559 and O214 #564 each preserve their original isolated evidence; test both inherited negative/positive courts, not a newly weakened oracle.
- Correctness negatives: authenticated descriptor declared-length contradictions, missing blobs, bool/negative geometry, later-index contradictions must reject at open. Genuine valid blobs across ranges must reconstruct exactly. Inherited Linux successful fresh-leaf extract must preserve inode and SHA; late EEXIST must preserve another actor's destination.
- **Falsify** if any previously accepted valid r24 vector fails, hostile declared-length file reaches selective read, any valid chunked output publishes an unverified inode, an existing-target overwrite is presented as secure, any inherited tests fail, or exact HEAD/source/provenance cannot be established. Any unsupported-platform error is evidence debt, not product success.
- Simpler alternatives rejected: separate `preflight_archive(path)` then reopen (known O208 path-identity gap); validate only extraction (leaves silent read_range corruption); replace Linux fd publication with named temp (reopens J24F02); rewrite validator or platform path code (unnecessary broader surface).
- **Scope/expenses:** no format/version/threshold/release change; no new native ABI. Measure specialized test pass/fail, source bytes, platform errors and any CI cost. RSS/CPU/wall/full official benchmark not established; explicit debt. Same-inode truncation/source mutation, existing-target post-SHA overwrite, ancestor namespace races, non-POSIX filesystem behavior and whole 4GiB product economics are outside the claimed result.

## Execution and decision

1. Keep inherited Reader except transplant O214 first-open same-effective-index admission, using the existing validation function; maintain cleanup of descriptor on failure.
2. Copy independent O212/O214 exact test files with source hashes; do not alter expected outcomes or weaken platform gates. Run native-package tests outside source checkout.
3. On Ubuntu run inherited J24F11/J24F12 real-installed courts under their original source-identity contract (for Linux unprivileged use), on all three hosts run independent geometry controls. If a result is inconsistent, isolate the owner and preserve the red.
4. Preserve raw logs/exact SHA, CI run identity and scoped negatives; do not merge, release or claim full portability without independent exact-head approval.

**Decision thresholds:** `COMPOSED_CANDIDATE` only if all named inherited controls pass on exact HEAD with unchanged judges. Otherwise `COMPOSITION_BLOCKED` and diagnose. Result-bearing data belongs in an append-only result note; this preregistration must never be edited after source mutation.
