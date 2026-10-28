# J24G14 — adaptive ownership boundary, prospective research preregistration

Date 2026-10-28 UTC. Independent *scientific* child of J24G13 #674 at `0684f5d694afc1abccc397ced3bcd1ef3356cb81`. Inherited source #671/#668 Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`. No `src/`, format, version, release, benchmark or existing-owner mutation.

## Primary falsifiable question

J24G13 [hosted run #40687049749](https://github.com/FCMO-AI/.CMPCT/actions/runs/40687049749) changed the candidate economics: untraced guarded ancestry was +12.0% CPU on legitimate 512 deltas, -33.3% CPU and -29.0% full child RSS on chained orphan-4096, and +12.3% CPU on independent orphan-4096. The hypothesis is that a **payload-byte-budgeted adaptive lifetime** can preserve eager **one-pass valid replay** on shallow legitimate chains and independently failing small chains, but discard retained objects only after a bounded prospective raw-payload budget is exceeded, allowing a deep invalid chain to retain most of the guarded resource advantage. The objective is not to tune a cache threshold: this changes the ownership/decode/replay mode at a specified resource budget.

## Prediction, independent controls and kill condition

Use `_index_from_footer` *research subclasses* on identical Builder/Writer r24 bytes: original eager, existing J24G12 guarded, new adaptive. The adaptive arm parses every signed delta immediately for malformed errors. It retains parsed objects and original payload until a **fixed prospective 1 MiB cumulative raw-delta payload limit**. Beyond this, it discards parsed objects and retains authenticated `(footer offset,payload SHA)` tuples, then re-decodes/rechecks if it finds a valid checkpoint. The 1 MiB limit is a **raw retention** cap, not a proof of Python RSS bound; Python nested objects and ancestor offset sets remain potentially unbounded.

Cases frozen before outcome: first-party Writer rename, a valid-64 control, valid-512, **valid-2048 crossing the budget**, linked orphan-4096, independent orphan-4096, and signed-malformed SHA-authentic MessagePack tail. Three fresh-child untraced repetitions per arm and case (one on malformed), fixed alternating order. All normal cases must reconstruct exact selected footer, depth, full/range reads and verify; malformed must fail in all three. Host wall/process CPU and Linux total child peak RSS, per-case archive SHA/bytes and any retained/deferred decision counts. No process startup inside measured CPU. Negative is preserved.

**Kill adaptive as an admission/control candidate** if byte/metadata/selected checkpoint/error semantics differ, if shallow valid-512 has >10% and >0.05ms CPU regression versus original eager, if linked orphan-4096 fails to save >=15% total child RSS versus eager, if invalid CPU exceeds eager by >20%, or if the strongest control is globally faster and no resource economy survives. The first-pass inference is evaluated only on this authored family; do not extrapolate to arbitrary archives. A long valid-2048 deep-chain cost is explicitly measured even if it loses, not relabeled as an outlier.

## Alternatives and BONK

Already falsified unconditional naive skip (changes malformed errors) and unconditional guarded (untraced legitimate +12%). Packed negative-footer storage changes are saturated. Simpler control is original eager; stronger memory-oriented control is guarded. A bounded adaptive raw payload budget should be a cheap O1 causal falsifier before any production merge or external-memory full architecture.

This new branch is stacked on #674 but leaves the previous science intact. No other PR currently owns J24G14, and the active #668/#671 ownership remains separate. No discovery policy/STATE modification, no release credit. Only a hosted, source-exact successful experiment can justify further productization, and the full release performance/safety/parity gates remain unchanged.
