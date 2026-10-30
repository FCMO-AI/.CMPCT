# J24P05c — Post-exploration prospective hosted verification of installed RECORD custody

**Science-only / source-exact stacked #854.** Original normalized path witnesses were preregistered separately in J24P05/J24P05b. This new question was observed first in a *local exploratory* test on 2026-10-30; do **not** claim it was predicted in those earlier records.

## Prior observable
In an isolated **Linux cross-target installation of an authentic physically dual-architecture official-style wheel** plus four alternative ZIP-path aliases, pip installed an inert later alias over the native binary (19 bytes instead of 3,112,736), but the installed dist-info/RECORD line for canonical native pathname remained the original 3,112,736 byte SHA-256 and size. All four installed targets thus have 1 stale native hash record. A separate missing `../../bin/cmpct` cross-target script entry is normal for `--target` path relocation and is **not** native evidence.

## New prospective host hypothesis
On macOS 15 and Ubuntu 24.04 with the already frozen J24P05 synthetic (152B nominal native, 43B inert replacement), the installed `cmpct-0.30.0.dist-info/RECORD` line for canonical native pathname will still identify the original 152B bytes when an alias overwrites them, despite `pip` returning success, whereas unmodified and unrelated controls preserve both bytes and matching installed RECORD. Count/report exact native entry's claimed SHA, size, physical SHA/size, and match boolean (not importer behavior). **Falsifier**: pip rewrites the installed RECORD to correspond to actual post-install bytes or removes conflicting row; record host difference and narrow claim.

## Execution and safety
Only inspect the installed RECORD and SHA bytes in the same disposable target; no mutated native import, no unsafe root/file writes. Independently parse stored bytes through a detached referee, preserving original installed RECORD as physical evidence. Production wheels show no observed aliases. This is a packaging trust-boundary problem, not proof of a signed distribution compromise or direct exploit. Promotion and Discovery state unchanged.
