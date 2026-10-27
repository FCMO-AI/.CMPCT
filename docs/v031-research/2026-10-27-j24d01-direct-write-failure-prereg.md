# J24D01 — Direct-member extraction fault atomicity (prospective preregistration)

Date: 2026-10-27 UTC. Repository: `FCMO-AI/.CMPCT`. Freeze **before** writing or executing the research instrument. Base: released `main@80c358f8824ec1b20d349c92ed94c898090969b0`; Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Published v0.30.0, on-disk revision 24, unchanged.

## One question

When an otherwise valid direct `S_BLOB` revision-24 member has been authenticated by `read()`, does `extractall()` preserve a pre-existing destination if its actual output write fails mid-member? Is its failure behavior materially different from the existing verified staged `S_CHUNKS/S_CDC` extraction?

## Baseline/source audit and mechanism

The released `src/cmpct/reader.py` direct-member branch calls `self.read(rel)`, then `os.open(full, O_WRONLY|O_CREAT|O_TRUNC)`, then `os.write(fd, view)`, without staging or rollback. The chunked branch creates a sibling temporary file, authenticates all bytes and only then calls `os.replace`. A write fault after the direct `O_TRUNC` should destroy pre-existing bytes despite the archive itself being authentic. Unlike the sparse SHA defect #572, this can occur **after successful authentication of an ordinary regular direct member**.

## Prospective discriminator

Use original independent frozen `tests/conformance/v24-direct-codecs.json` (RAW; optionally Zstd/Deflate) and `v24-chunk-maps.json` (S_CHUNKS/S_CDC), with exact fixture/archive SHA-256 checks and the original installed Reader. Place a nonempty, distinct pre-existing canary at the output member path. Interpose **only** `os.write` in the isolated extraction invocation: execute one real short kernel write of at most seven bytes, return its positive byte count, then raise `OSError(errno.ENOSPC)` on the next write. Leave all archive input, authentication, parser, SHA and Reader code unchanged. Verify the injected syscall actually occurred. Preserve direct output inode, canary SHA before/after and per-case outcome. Also run unmodified clean extraction as a strong control.

**Prediction:** all clean controls reconstruct exact original SHA; faulted direct member raises ENOSPC but the pre-existing canary is truncated/overwritten; faulted chunked member raises ENOSPC but the pre-existing canary survives, with no leftover CMPCT-part stage. If direct pre-existing bytes remain identical, **falsify this issue**. If chunked control also destroys prior bytes, expand the problem scope rather than blaming representation. Any source/fixture misidentity or a fault not actually triggered invalidates the trial.

## Claim limits and adversarial review

Fault injection is a deterministic negative availability/recovery oracle, **not** a measured real-world disk-full frequency, no-op kernel behavior or 3-platform portability proof. A staged fix may affect existing hardlink/metadata semantics; do not propose one without paying that product debt. This research must not modify product, format, comparators, historical validators, release policy or `docs/discovery/STATE.json`. Record positive/negative receipt evidence and contact related safety owners after a valid result. Existing #528 is a separate post-SHA stage-name substitution threat; #572 is sparse logical SHA and existing-target corruption on pre-auth failure; distinguish both.
