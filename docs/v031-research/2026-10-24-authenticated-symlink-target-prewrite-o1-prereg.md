# O1 — Authenticated unsafe symlink target prewrite boundary (preregistration)

Date: 2026-10-24 UTC
Status: **FROZEN PREDICTION, before any Reader or test implementation in this lane**
Repository: `FCMO-AI/.CMPCT`; parent PR #345 at exact `33c4ef777542039ab3c1b97797e5ac8ca31af96a`.
Format: released v0.30.0 / r24. No format or release changes authorized.

## Baseline mechanism and question

The composed Python `CMPCT.extractall(..., safe_symlinks=True)` validates names and authenticated non-directory ancestor relations *before* member writes, but evaluates each symlink's decoded target only later, inside the sequential publication loop. With a valid signed r24 archive containing an ordinary file lexically preceding an unsafe symlink (absolute or parent-relative target), the reader can publish the ordinary member and then refuse the symlink target. Does this produce a preventable partial write, and can a prewrite safety rejection retain normal symlink semantics without adding a second unbounded decode or weakening either Reader/source proof?

## Prediction and disproof

1. Source-exact `Builder` archive with `a-first.bin` and `z-escape` symlink target `../outside` causes `extractall(safe_symlinks=True)` to reject **after** `a-first.bin` is written in inherited source. Use real Builder/Reader rather than mocking per-row iteration.
2. The minimal product repair validates symlink target bytes and per-platform path constraints **before any archive member creation**, using the identical strict policy as ordinary publication; valid relative symlinks still roundtrip and `safe_symlinks=False` retains explicit override behavior. The actual published target bytes must be those checked, or later modification must be made impossible/proven harmless.
3. Hostile corpus controls: parent escape, absolute target, Windows root/drive-relative where applicable, and normal relative target. The result must remain source-exact, no size or wire change.
4. Kill/narrow condition: if the Builder cannot emit this authentic signed shape, if Reader already rejects before writes in exact source, if the added pass changes safe legitimate symlink behavior, or if predecode introduces unbounded memory/decode amplification, retire or redesign; do not weaken existing safety/benchmarks to make a test pass.

## Simpler control and alternative explanation

One-pass decoding during the write loop already rejects an unsafe target; it is insufficient to establish an all-input prewrite refusal when earlier members have been materialized. This is *not* a claim of atomic extraction under I/O failure, malicious concurrent destination modification or pre-existing symlink pivots (Issue #265). A proof-only static validator without decoding authenticated symlink bytes cannot decide the target value. Prefer one prewrite decoded-target cache with an explicit accounting bound to speculative replay or a second full member read.

## Evidence and accounting boundary

Frozen corpus identity is `Builder(root, workers=1, reproducible=True)` with true symlink bytes and ordinary file, independently checked through actual `CMPCT` and `os.readlink`. First run adversarial regression against parent HEAD as an intentionally red witness, then implement a narrowly scoped change on isolated child branch and execute targeted + general hosted CI. Report exact-head CI, adverse false positives, payload bytes decoded, temporary memory footprint/limits, and release gate if changed product behavior. No canonical merge/version/release until all inherited gates are earned.
