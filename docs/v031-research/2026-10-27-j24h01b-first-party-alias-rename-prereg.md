# J24H01b — First-party transactional generation of a valid forward hardlink

**Date:** 2026-10-27 UTC. **Prospective supplemental preregistration, before J24H01b instrument/CI.** Keep J24H01 original unchanged; its original exact-head run remains a distinct evidence event.

## New decisive fact from independent static review
The published Builder initially assigns the *first lexically seen hardlink* as physical owner. However, published `src/cmpct/transactions.py::append_rename` accepts a rename of an alias to any currently unoccupied root-level path. A renamed alias may then sort **before** the unchanged owner, while its original storage target remains valid.

This creates a potential **first-party runtime** path to the original J24H01 hypothesis, rather than relying on an independently reauthored synthetic index. Issue #237 already distinguishes owner renames (invalidating aliases) from alias renames (valid), but the current question is separate: whether an otherwise valid alias rename makes extraction fail solely through lexical ordering. PR #569 owns extraction implementation; #615 owns alias-size graph; neither branch will be modified.

## Predicted test
1. Create two real filesystem hardlinks `b-owner` and `z-alias`, with `b-owner` physically first in the source scan.
2. Build an ordinary r24 Builder archive. Record SHA-256, verify preflight/Reader/extraction and hardlink inode identity.
3. Invoke **unchanged public Writer** `append_rename(archive, "z-alias", "a-alias")` (alias only, no owner rename). This should append an authenticated generation with valid `a-alias → b-owner` dependency.
4. Without mutating the archive afterward, check strict preflight and complete Reader `read`, `read_range`, `verify`, and one new-destination extraction.
5. Predict strict/read/verify acceptance but `extractall` failure `hardlink target not yet extracted: b-owner`. Capture source SHA, archive SHA, footer depth and exact exception.

## Independent controls, falsification and constraints
Control is unmodified Builder output before rename. Falsify if `append_rename` rejects the alias move, strict preflight rejects the new archive, `read/verify` fail, or `extractall` succeeds. Preserve any inconclusive environment failure. No Reader, Writer, format, release, benchmark, comparator, source-fingerprint or state policy change. A Writer outcome that differs from this prediction narrows the claim, not permission to adjust the test retrospectively.

This prospective stronger witness materially changes product relevance: first-party Writer may create archives that Reader can open/verify but cannot extract. Still no performance claim, security-exploit claim, promotion authority or claim that ordinary Builder's initial snapshot is affected.

## Handoff if confirmed
Open one shared issue referencing both J24H01 and J24H01b rather than two redundant defects. Coordinate with issue #237 without duplicating its different owner-rename scenario. Product fix must preserve valid first-party append generations, cycles, referential integrity, data SHA, hardlink inodes, post-error destination safety and portability.
