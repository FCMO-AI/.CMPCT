# O149 preregistration — transactional ZIP export publication (2026-10-26 UTC)

**Evidence tier:** prospective CMPCT product-repair hypothesis. **No product implementation existed on this branch when this preregistration was committed.**

## Exact parent and owners
- Stack on O140 #488 `d8b69758dbcbb66fe28fa7cf59598916df160d2d`, Reader blob `e46e6121842d485cb209118576ebf3ba3719080d`, inheriting O135 #483's source-archive inode refusal, O140's static nonregular destination refusal, #284/#260's ZIP writer/direct-Deflate/ZIP64 behavior.
- Negative original science O143 #489, exact `bd63a33b7279816275d68571f9d27e9f7658eaa6`; Ubuntu/macOS 4/4 intentional destructive witnesses Actions 40264781450. Do **not** edit or rerun defect-expecting tests as a positive repair court.
- Released floor v0.30.0, physical revision 24; no version, format, historical lock, core benchmark or gate mutation.

## Question, mechanism and disproof
Can a regular ZIP export guarantee that **if any exception occurs before successful publication**, an already-existing valid destination remains byte-for-byte unchanged and keeps its previous inode, while successful outputs retain exact ZIP contents and inherited source/special-leaf refusals?

Proposed mechanism: perform existing admission on the **requested** path first. Create a private same-directory staging regular file. Produce a complete ZIP using the identical existing writer into this private sibling. After the output writer closes without exception, atomically replace the requested pathname; clean up staging on every prepublication error. Preserve a separate writer helper so format/Deflate/ZIP64 decisions are not recoded. Avoid a second archive-wide input preverification pass.

Competing routes: (1) preverify all inputs before direct output open: inadequate for mid-write ENOSPC and doubles decode; (2) in-memory full ZIP buffer: unbounded memory for large archives; (3) in-place rollback: cannot undo partial persistent writes reliably and destructive under failures; (4) staging/replace: selected with explicit disk and inode semantics.

**Predicted falsifiers / kill:** corrupted independent RAW CRC or Builder-generated late member destroys/modifies existing ZIP; fault inside writer leaves partial target; leaked staging files; clean ZIP changes logical member bytes or retained Deflate stream; O135/O140 fail; unauthorized created output survives a failed write; cross-platform incompatibility; confirmed official performance regression beyond release gate. Inherited original 0.30 parity and same-input controls remain mandatory.

## Physical policy and limits
- Failure before replacement preserves old output bytes and inode; successful replacement **does not** preserve destination inode or hardlink identity. Existing hardlink aliases keep old content; successful output points to new inode. No guarantee against concurrent path swaps, parent-directory replacement, crash/power-loss durability, metadata preservation, or external filesystem rename semantics yet.
- Temp file in output's directory, temporary storage up to full exported ZIP size; ZIP content written once into staging (no second data-copy), one rename and potentially extra metadata/fd work. Expected archive payload bytes identical but must measure/compare; CPU/wall/RSS/temp I/O not yet measured.
- Clean-up uses `finally`; no directory fsync durability claim. Windows open file handle must close before replacement. `safe` static admission not TOCTOU protection.
- Negative inherited evidence remains immutable and retains original meaning. New repair court must be source-bound and hosted separately; no fixture identity-specific special cases.

## Planned evidence ladder
1. Local adversarial mechanism and unit test including injected writer failure; original ZIP SHA and inode before/after, exact output on clean path, old hardlink unchanged on successful replacement.
2. Immutable O143 independent RAW vector reproduced using a new positive repair test; optional late-member Builder-generated corruption.
3. Cross-platform GitHub Actions source-bound installed Reader acceptance, JUnit, original control integrity, negative results preserved.
4. General tests, native/fuzz, official same-runner A/B benchmark; only latter can support promotion.

**Decision at preregistration:** hypothesis OPEN; implementation, hosted tests, official performance and release all UNMEASURED.