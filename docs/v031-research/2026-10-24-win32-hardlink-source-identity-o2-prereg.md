# O2 — Win32 hardlink source identity, beyond syntactic path safety

Date: 2026-10-24 UTC. Status: PROSPECTIVE, before negative test or source mutation.

## Current exact source and external control

Combined Windows/APFS integration O1 at `182d6cdf0eb5c04ba615086342cec7f97b7fe754`; original union run `40077116609` GREEN across Linux/macOS/Windows for the original sources. Windows source owner PR #332 `dff03d03fa7d9c7e8b3c26c002e74c8cd49fa2af` checks canonical syntactic safety of hardlink `row[6][0]` but does not require this source key to name an existing logical archive member. APFS source owner #334 already added exact logical membership on macOS after a related signed-adversarial O2 negative. This experiment does not alter either original test suite.

## Prediction, simpler control and falsifier

On real default case-insensitive Win32 filesystem, file `Alpha` in the archive and hardlink alias `link` declaring source `alpha` will be accepted by current combined Reader even though `alpha` is absent from the authenticated logical archive. Windows resolves the physical case alias. Rejection should occur **before any archive member write**, as the original macOS exact-owner safeguard does. The simpler control is checking the safe Windows path spelling alone; predicted insufficient. Counter-control: hardlink naming exact `Alpha` remains accepted; path `D:outside` continues rejected by original test; Linux Byte-distinct and native Mac suites remain unchanged.

Kill/narrow if the actual Windows runner is case-sensitive, current Reader already rejects missing source before writing, a more specific prior branch already owns/fixes the same mechanism, or the case alias is not a physical match. Do not interpret a Linux `ENOENT` after partial writes as the same safety guarantee.

## Candidate repair if observed

At Windows destination admission, precompute exact canonical logical owner set for this archive and require each hardlink's *canonical* source key to exist before writing any member, without changing the Windows comparison/casefold collision policy. Preserve Mac's existing independent check. A shared unqualified global rule may be better eventually but must not be silently broadened into Linux compatibility without testing.

## Limits

Not a complete Win32 hardlink semantics model. This concern is logical identity/canonical index custody, not physical symlink TOCTOU or compression. No on-disk format, Builder/Writer/native ABI/benchmarks/release criteria changes. Genuine Windows exact-head negative before code, then unchanged adversary on fixed source, are required for a product claim.
