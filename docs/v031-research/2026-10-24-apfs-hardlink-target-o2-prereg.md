# O2 preregistration: APFS hardlink source alias must name a real logical archive owner

Date: 2026-10-24
First completed question: PR #334 O0/O1 NFC/NFD physical member collision. Proven baseline host + same-method negative run 40072645196; candidate source e953866021dcb6c8dec7b2f5700586f75270ceb7.
Status: prospectively unexecuted second narrow question; independent of the member-path collision now guarded.

## New prediction
With a **single** regular-file logical row `café` (NFC) and a distinct hardlink logical row `alias` whose source field is `cafe\u0301` (NFD), the present macOS-only member-namespace guard sees no duplicate member names. `CMPCT.extractall` resolves NFD physically to the NFC file after first creating it, and succeeds even though the hardlink source name does not exist in the authenticated logical index. This is a parser/extractor interpretation divergence, not a claim of bytes corruption.

## Frozen discriminator
Run authentic `CMPCT.extractall` on the exact current PR #334 O1 source with **two in-memory rows only** (avoid builder and native codec). Stub `read(NFC)` to give known independent bytes, then request hardlink to NFD alias. Positive control: real Mac filesystem alias `os.path.samefile(NFC,NFD)`. Require fail-closed before any member write. Verify the unchanged Linux control fails for a missing physical owner as expected. If the Mac source actually rejects it, kill this hypothesis without implementation.

## Minimal repair after negative
On macOS, preflight a hardlink source's canonical logical name against the **complete canonical set of archive member names**, not against the post-extraction physical host path; reject missing exact source before any write. Do not silently replace NFD with NFC because that would give archive metadata a different meaning. Preserve legitimate canonical owner hardlinks and case-sensitive Mac positives. No wire format, Builder or native changes.

## Debt
This does not establish all hardlink graph validity, link cycles, owner-kind identity, mutation-generation consistency or security against concurrent path races. The test uses authentic extractor behavior, not a fully signed on-disk goldens corpus; product promotion still requires existing inherited release/performance/Reader composition gates.
