# O12b — hostile Git clean-filter configuration can falsify source custody
Date: 2026-10-24 UTC. Follows successful O12 exact-head source witness at `4d1558eb9fd858781105bf57ed7df952f384796f`, run [40114237238](https://github.com/FCMO-AI/.CMPCT/actions/runs/40114237238). Preregistered **before O12b hosted adversarial test and protective edit**.

## Positive inherited evidence and unresolved assumption
O12 compared 2,375 source members on three genuine hosts: macOS/Ubuntu raw SHA-256 `388b2c88...`, Windows raw SHA-256 `71d91417...`; all Git-clean-filtered roster SHA-256 `d0215230038cda4d507b39946ee0b886786f0004281a7f892f92f257857431c4`. The entire 2,375-member Git-filtered roster matched across hosts while every raw file checksum differed on Windows. All 15 focused platform controls passed (5 per OS), and the cross-host job succeeded. These are hosted facts for that exact commit; no release or product credit.

An independent **local** disposable Git repo falsifier held the same source bytes and same Git HEAD but changed a local custom clean-filter configuration on a `filter=flaky` path. `git hash-object` returned `f09d5fcbeb7baa6fe50d9e39b3b1bb3237ee86cc` with a no-op filter and `83285cbcff0bd7aec28025c56520bacec63a9059` with an `a→z` filter. Raw file SHA-256 remained `0519840427130562f8b984c14bb1d36f0da764db0a442216ba522f2942b1e2b9`. The path's content and Git HEAD did not change. Thus candidate clean ID can silently depend on executable, mutable host configuration.

## New hypothesis and strongest simpler control
Allow Git-native end-of-line conversion, but **fail closed before hashing** on any selected path whose effective Git attributes assign `filter` or `working-tree-encoding`. Use one null-delimited batched `git check-attr --stdin -z filter working-tree-encoding` query over exactly the included roster; rejecting before Git hashes means a configured clean executable never runs for that path. Disallow unknown/malformed attributes, not just the known filter name. Do not change O11 physical-byte witness or existing manifest. A weaker control is merely reporting the filter, but that risks executing untrusted filter code before it can be reviewed.

## Disproof / limitations
- A selected `filter=flaky` path with a Git clean program configured must be rejected before invoking that program (verify side-effect file absent).
- A selected `working-tree-encoding` path must be rejected (cross-system availability/decoder differences).
- Ordinary `*.py text` EOL conversion must still pass LF/CRLF cross-host identity and dirty substantive/binary changes.
- Git's implicit core.autocrlf and text attrs remain a policy assumption, and Git SHA-1 OID dependence persists. Do not promote Git-clean O12 to release authority without a broader source-identity proof.
- Host CI first runs expected negative with new test on old helper; preservation of that red is required before fix. Do not weaken it to green.
- Resource accounting: one additional Git attribute subprocess and linear per-path parse; no product performance claim.
