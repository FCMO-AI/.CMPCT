# O126 / A08 — Prospective windowed temporal-ownership oracle (2026-10-25)

## Authority and question

Canonical released v0.30.0 / on-disk r24; prospective `agent/v031-development` at `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. This is Foundry A08 (temporal/generation lineage as a compression dimension), **not** a Builder/Reader or release-format change. Prior A02 (#465), A03 (#458), A05 (#469) work investigates factors, residual factoring and short reversible programs, not *bounded temporal checkpoints*. No A08 PR found before claim. Discovery STATE is stale; #440 owns its update. No edit to that cache.

**Primary question:** Does a file-owned, four-generation checkpoint followed by exact XOR temporal residuals produce a meaningful *storage/access Pareto* point on fixed-version file histories versus all of: independent per-generation Zstd-19 snapshots, solid Zstd-19 of every generation, unwindowed per-file raw and XOR histories, per-generation XOR journal, and same-window untransformed file histories?

## Prospective prediction and disproof

Predict a **scoped win** on at least two distinct evolving-state families (independent local sparse mutations and correlated epoch-shared mutations): fully charged stored bytes >=5% below the strongest control with selective generation decode work <=4x the full target snapshot, while the candidate itself stays <=4x and reconstructs every generation byte-exact. Predeclared different-worldview held-out cases are moving/rotated structures and fully independent generations; these need not win but must be shown without deletion. Retire/narrow if either positive family loses to the strongest admissible control or exported execution cost is so large no credible product admission remains. A smaller solid/unwindowed representation with >4x selective amplification remains evidence and is not erased by the locality constraint.

## Frozen basic experiment

- Deterministic data: 12 generations, 8 named fixed 4096-byte files per generation. Four families: per-file stationary sparse mutations; shared sparse epoch mask; shifting/permuting windows; independent fresh seeded bytes. Add held-out 12-generation 16-file, 8192-byte fixed-length test with a new seed and broader change positions.
- Zero extension/fixture identity used as mechanism admission. This oracle is not a product policy.
- Exact same snapshot bytes for every arm. Zstd-19 one frame per actual ownership unit; process-start/CLI costs distinguished from codec bytes. No empty/duplicate frames gifted.
- Charge fixed metadata for every generation/member SHA-256 (source/reconstruction integrity), file/generation count and each physical compressed frame descriptor (16 bytes). The same shared manifest charge applies to every arm; literal payload, checkpoints, XOR residual bytes, frame count and descriptors all counted. Index layout is simple research accounting, not a valid r24 archive.
- Implement actual encode -> decode/verification for every generation; reject if even one member SHA/length differs. Report complete charged bytes, create wall/CPU, frame count, selected generation decoded logical bytes (no magic cache), maxima/median and representative winning/losing arms. Preserve raw JSON and exact code SHA in CI artifact.
- For full-history solid and unwindowed file histories, selecting a generation must charge every required decoded frame and preceding reconstruction data; never pretend compressed seeks exist. Windowed frames must fully decompress the four adjacent states of their window before selecting one state.
- Control `window_raw` is mandatory to identify whether any win is from temporal XOR rather than window organization alone. Control `solid_history` is mandatory to avoid a weak comparator. Compare Pareto vectors; never optimize one scalar by weakening locality.

## Decision and safety boundaries

A research-only oracle cannot claim actual CMPCT size, cross-platform performance, authenticated archive integrity, changing file sets, filesystem metadata, transactional recovery, true range-read physical I/O or product readiness. Decoder and descriptor complexity, window update cost, process startup, RSS, and recovery semantics remain explicit debt. No version, format, release thresholds, frozen benchmark, product source or other agent branch may change. Strong simple baseline is allowed to win. Record negative/falsified hypotheses without threshold changes.

## Concurrency / provenance

Prospective prediction committed *before* instrument implementation or result observation. Recheck open PRs before late writes. O126 owns only the separate research script/workflow/prereg/result lane. #440 owns discovery STATE. All outputs should be self-contained and zero-history reproducible. O126 is an independent activation, not a fictitious swarm.
