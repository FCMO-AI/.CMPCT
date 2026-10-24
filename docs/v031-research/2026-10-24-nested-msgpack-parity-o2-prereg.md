# CMPCT v0.31 — authenticated nested/non-text MessagePack ambiguity O2 (prospective)

Date: 2026-10-24. **Frozen before executing the product oracle.** Status: research falsifier; no product, release or format claim.

## Authority / concurrency
Base is the integrated duplicate-root rejection and deterministic Reader cleanup owner PR #321, exact `1eb8db5a2f493323e60fdc8aa2d801ce2be26f35`. Owner PR #316 already proves and fixes duplicate **text root** map keys; PR #321 owns Reader resource cleanup. This O2 tests a *different surface*: duplicate keys **nested in a legitimate `fsmeta` map** and duplicate non-text root keys, without altering those owners' code. No other currently open PR claims O2. Any product fix will be separately scoped to Rust parser policy and independently reviewed; base owner files remain unchanged unless that explicit subsequent decision is earned.

## Primary question and prediction
Can a fully SHA-256-authenticated r24 archive with no duplicated text root keys, but duplicated nested `fsmeta.owner` or non-text root integer keys, be rejected by Python Reader/preflight and accepted by native Rust `cmpct_open`?

Prediction from current exact source: Python `object_pairs_hook=unique_map_pairs` recursively detects duplicates and fails closed; Rust's `HashSet<String>` examines only text keys at root and admits both adversaries. For each RAW/Zstd/raw-Deflate independent fixed archive, the same signed wire should yield Python+preflight rejection with native accept in both nested key orders. Valid frozen files must still open on all readers. If Rust rejects either hostile class already, narrow the hypothesis immediately; never claim a result without hosted native execution.

## Stronger controls / alternatives / cheapest decisive route
- Mere random index corruption is not a control: it fails SHA without testing parser semantics. Reconstruct both compressed index copies, SHA header/footer and preserve physical data bytes.
- A Python-only MessagePack microtest predicts the mechanism but does not prove Rust's product behavior.
- Use the existing independent direct-codec fixtures and identical ABI calls from `tests/native_duplicate_root_index_oracle.py` with an additive tests-only script; run installed Python + compiled native ABI together in GitHub Actions.

## Kill / cost / ethics
If native refuses all signed adversaries, hypothesis falsified. If native admits, preserve one durable negative with original bytes/fingerprints, then choose between (a) bounded recursive native map-key validation with independent positive/hostile controls or (b) narrowed policy with explicit unknown-field/read-scope semantics. Do not patch the frozen corpus, weaken signed hashes, change parser limits/gates or conflate acceptance divergence with incorrect reconstructed bytes. Extra test CI compute and small archive bytes are fully charged; product perf and portability remain unmeasured. Historical v0.30/r24, format magic and published releases immutable.
