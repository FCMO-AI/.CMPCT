# v0.31 research: POSIX byte-identity namespace wire bounds (2026-10-23)

**Scope:** independent, detached, falsifiable *representation-design* oracle for [Issue #252](https://github.com/FCMO-AI/.CMPCT/issues/252). This is NOT a proposal to reinterpret revision-24 archives, an implementation of the real Reader/Builder, a release benchmark, or evidence of Windows portability.

## Current authority and baseline

- Development base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; shipping project: v0.30.0, revision 24.
- The canonical native revision-24 parser (`native/cmpct-core/src/lib.rs`, blob `463c50633be74423e92a074b7d7577db6a4b0cf9`) requires every member's path to be a UTF-8 MessagePack string. It rejects binary row paths. Current Builder string identities fail to encode POSIX surrogateescaped source names/xattr keys.
- Existing PR #251 owns **symlink target bytes**, stored in an existing `S_BLOB`; do NOT duplicate its implementation or mistake targets for member *names*. The stale `docs/discovery/STATE.json` is not ownership/CI authority.
- No format, validator, comparator, benchmark threshold, release gate, or user-facing Reader semantics is changed by this research PR.

## Alternatives and predictions (exploratory local pilot before hosted court)

A. **Explicit byte-key wire variant** for genuinely byte-valued path segments / xattr keys: MessagePack `[1, raw_bytes]`, with UTF-8-compatible values retained as strings. This requires a version-gated new parser contract and explicit POSIX extraction semantics. Predict stronger storage efficiency for binary/unicode-mixed sample sets, but extra parser complexity.

B. **Reversible ASCII-tagged logical spelling**, reserving `~Z0_` for literal valid UTF-8 names beginning with `~Z` and `~Z1_` for invalid-UTF-8 or POSIX backslash-containing raw names. Predict simple string-only transport, but significant expansion and destination casefold hazards. Unknown tags and noncanonical alternative encodings must fail closed.

Controls: ordinary valid UTF-8 names, literal tag-looking names, raw non-UTF8, hardlinks, symlinks, nested names, xattr invalid bytes, and POSIX xattrs containing `/` and `../` as **metadata keys**, not filesystem path components. Domain-sensitive validation matters: reusing path-component slash rejection for xattrs would wrongly reject a legal Linux xattr key.

**Kill/narrow condition:** any name collision or lossy byte reconstruction; r24 silently misinterpreting a new grammar; expansion exceeding authorized bounds; or native/Windows extraction renaming a member. Scientific PASS alone does NOT authorize product integration.

## Observed local exploratory result (not independent hosted CI)

- Deterministic seeded set of 4,330 different POSIX component byte strings: both detached encodings are injective and round-trip. Raw MessagePack packed binary variant: **179,565 B**; escaped text: **242,377 B** (different variant layout; not complete archives or a codec-controlled release comparison).
- Deflate-9 over the complete two sample arrays: binary **173,891 B**, escaped **176,334 B**. These figures measure only the encoding arrays, not r24/r25 archive creation, decode, memory or index overhead.
- 19 deliberately noncanonical/unsafe spellings rejected in the local pilot instrument. The hosted script has a similar but not identical set: its own count is authoritative for that run.
- Linux local physical checks: raw file names, nested names, hardlink inode identity, byte-exact symbolic target and raw/slash-containing xattr keys passed in this environment.
- **Decisive format bound:** 16 components × 255 bytes + 15 separators = **4,095 raw path bytes**; tagged base64 text occupies **5,519 bytes** for the same raw components, crossing the historical 4 KiB-class path guard. Text escaping is not a universally zero-cost retrofit to an unchanged path cap.
- **Concrete destination collision:** physical POSIX names `b'\\xff'` and `b'~z1__w'` produce distinct wire names `~Z1__w` and `~z1__w`, which collide after case-folding. Generic cross-platform extraction must detect and reject such aliases; it must never silently choose one.
- The field-domain split is essential: Linux accepted `user.slash/name` and `user.path/../frag` as xattr names. These are not path components and must not inherit directory traversal parsing.
- The prospective GitHub-hosted court runs the repository-committed source under UTF-8 and ASCII filesystem locales. The hosted source/corpus differs from the exploratory local pilot: report the actual head and actual results independently rather than pretending identity.

## Decision

**NARROW:** a simple string-escaping trick does not justify preserving revision 24 unchanged. New data semantics require an explicit negotiated revision/feature, a byte-aware native/parser interface, a source-to-wire-to-platform collision proof, reader-visible byte identity, a separate xattr-key domain, bounded extraction and cross-platform fail-closed behavior.

**Next cheapest action:** inspect the exact-head hosted scientific court, then build *one* bounded prospective revision-25 path/metadata decoder inside an isolated test-only instrument that rejects aliases before I/O and proves current r24 archives remain unaffected. Do not start a product-format rewrite until that court falsifies the obvious collision/overhead traps. A stronger simpler control (r24 fallback for ordinary UTF-8 names) remains mandatory.

## Unmeasured / loss disclosure

This court does **not** run CMPCT Builder/Reader, full stored bytes, create/extract wall or CPU, peak RSS, selective amplification, recovery, native C ABI, Unicode-normalization edge cases, malicious archive parsing, or Windows/macOS extraction. A deterministic oracle may kill a representation but cannot earn product/release credit. Scientific history, code and CI remain separate from frozen performance gates.
