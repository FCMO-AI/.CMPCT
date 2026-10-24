# O29 prospective negative — canonical hardlink target spelling equivalence

**Time UTC:** 2026-10-24T21:16Z. **Status:** preregistration, no experimental outcome.
**Exact source parent:** O28 PR #381 commit `9c9cecc6c21dc741e57188076ea43dc0ede6425b`; Reader blob `c7850c08c7bb27563955c6e2294b8c17c140d0a2`; strict preflight and `path_policy` inherited unmodified.
**Owning issue:** #382 (source-only hypothesis; not yet a product finding).
**Released baseline:** CMPCT v0.30.0/r24 unchanged.

## Scientific question

Does strict preflight accept signed hardlink targets with backslash spelling as canonically equivalent to forward-slash regular-file paths while ordinary Reader resolves the target only by raw string and refuses an otherwise admissible archive?

## Prediction / falsifier

Create two *real* revision-24 files with the same physical RAW bytes and equivalent logical filesystem meaning:
- control: owner row path `sub/owner.bin`, alias storage target `sub/owner.bin`;
- adversarial variant: same owner row path, alias storage target `sub\\owner.bin`.

Recompute MessagePack, compressed primary and tail indexes, SHA-committed header and footer for both variants. **Prediction:** `preflight_archive` accepts both; ordinary `CMPCT` reconstructs control but rejects variant with missing owner because `self.by` uses raw keys. This confirms a strict preflight/Reader policy discrepancy; it is not a codec corruption.

**Kill:** if strict preflight rejects the variant, or ordinary Reader reads both, the specific discrepancy does not exist on this HEAD; preserve the actual result and do not patch. A mismatched physical archive/hash, invalid size or test-only monkeypatch voids the claim.

## Independent controls

The source policy implementation `canonical_logical_path` treats backslash as separator but rejects dot/parent/empty/absolute components. Genuine `preflight_archive`, `CMPCT` and `read` are used without mocks. Ensure exact raw SHA and payload semantics. Run on Ubuntu, macOS and Windows, bind Git blob identity, preserve both positive and negative cases.

## Scope/decision

This lane is **science/evidence only** and must not modify Reader, validator, path policy, format, tests of owner O25/O27, CI performance/release thresholds or `docs/discovery/STATE.json`. An actual negative would warrant a separate minimal canonical-owner lookup fix with hostile duplicate and platform-key controls; no release/merge credit from this research PR.
