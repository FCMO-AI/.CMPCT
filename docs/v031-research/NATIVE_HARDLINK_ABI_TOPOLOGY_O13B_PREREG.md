# O13b — held-out distinct-content hardlink-target perturbation (preregistered)

Date: 2026-10-24 UTC. Status: PREDICTION FROZEN BEFORE O13b TEST MODIFICATION. Not a reinterpretation of O13; O13's complete original result remains immutable at exact source `e702764a2b83f6ff791efa482187ffebd5efa917`, GitHub Actions run `40086106599`.

## Motivation and independent alternative explanation

Original O13 real-Builder positive found a native C indistinguishability pair for `z_alias.bin` linked to `a.bin` vs `b.bin` when the two roots have identical logical bytes. A stronger alternative explanation remains: identical content alone might explain indistinguishable native observations. Current source analysis suggests the missing link-owner target is the actual cause: hardlink `Storage::Unsupported` yields the same status, independently of target contents.

## Frozen stronger prediction

Repeat the exact source/ABI procedure with a **held-out pair of distinct regular-file contents of equal byte length**, deterministic and not selected from an archive fixture. Both archives contain exactly the same `a.bin` and `b.bin` source bytes, but `sha256(a.bin) != sha256(b.bin)`. Only `z_alias.bin` points to a vs b. Both files have identical permission, normalized timestamp and size. Confirm independent POSIX dev/inode partitions and exact Python Reader results: alias bytes equal a vs b respectively; signed r24 index target owner paths differ; the archive bytes differ. Verify that the fully enumerated public native C observation (all entry metadata, range statuses/output and pack-owner statuses) remains identical across the two archives, and alias range read continues to return UNSUPPORTED for both.

## Decision / disproof

**Disproof:** a single public native observation differs across this held-out pair; source files and entry metadata are not precisely parity-controlled across archives; alias logical reads under Python Reader do not differ exactly as predicted; the builder collapses distinct roots to same inode; or the test requires product modification. Retain original O13 if O13b fails. Do not weaken either court. Other source variants, all Windows/APFS semantics, native extraction, security, performance and release remain unproven.

## Cheapest evidence and opportunity cost

Modify only the existing test to repeat O13 with one held-out distinct-content pair after the identical-content control. Use same exact-head workflow, original O13 mandatory, no new library ABI/format/benchmark behavior. If positive, any putative workaround that infers hardlink ownership by comparing content hashes becomes impossible even in the easier case of different root contents, because the public C ABI refuses alias bytes. Product conclusion is still narrow: the API must expose the hardlink mapping or let a trusted native tree extractor own reconstruction, rather than duplicating signed-index parsing in every client.

No release credit or Discovery policy change.