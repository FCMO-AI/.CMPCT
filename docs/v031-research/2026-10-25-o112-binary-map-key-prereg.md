# O112 — Authenticated binary-key MessagePack parser-equivalence falsifier (prospective preregistration)

Date: 2026-10-25. **Scientific-only proposal: do not confuse a PASS confirming divergence with product safety.**

Base: actual PR #316 source HEAD `1ed92767e6438d9bb8835ddc7ae27160440c2014`, which installed a Python all-map duplicate key hook but a Rust root-only **string-key** deduplication guard. Product/release floor v0.30.0 / r24 remains untouched. This lane does not own or modify PR #316 Reader or Rust code.

## Primary question and prediction (recorded before hosted execution)

Can a fully authenticated r24 primary MessagePack root index with two identical **binary (bin-encoded) unknown root keys** be accepted by the native reader while rejected by the installed Python Reader and preflight? The key is b'O112-opaque' encoded using `msgpack.Packer(use_bin_type=True)`, not an integer key. Python `strict_map_key=True` allows bytes but rejects integer map keys before its duplicate hook; a binary key is the better controlled discriminator. The PR #316 Rust root loop examines only `key.as_str()`, so `rmpv::Value::Binary` bypasses its uniqueness set. Prediction: on each frozen independent RAW/Zstd/Deflate r24 archive, adding one unique binary unknown key to the index does not change either reader's logical member or content, while adding **two equal** binary keys (same original map fields, same blob) causes Python and preflight to reject at open, but Rust C ABI `cmpct_open` to succeed and expose the original member exactly. Both index copies, SHA-256 index hash, footer and physical blob must be coherent. Three unchanged goldens and three distinct single-bin controls are mandatory.

## Falsifier and decision

`FALSIFY` the predicted accepted/rejected gap if Rust refuses duplicate binary keys or Python accepts them. If either control with one unique bin key is rejected, the claim of *duplicate-specific* asymmetry is inconclusive: separate unknown-field policy from key uniqueness before drawing a conclusion. Same-host independent installed Python+Rust and byte-identical archive for all readers are required. Codec or schema failure is not product evidence. A reproduced gap is a **negative** for the PR #316 candidate's cross-reader parser contract, not an authorization to ship or to modify a threshold/evaluator. Record individual status codes, hashes and contradictory evidence.

## Cheapest decisive court and accounting

Reuse PR #316's true independent three goldens, authentic ABI loader, index recompression/frame reauthentication, unchanged plaintext/physical blob, and exact source SHA. Add a scientifically independent typed-root-key instrument on an isolated branch. One RAW/Zstd/Deflate 3x3 court provides orthogonal codec controls without expensive full-product benchmark. No new codec, format, archived bytes, Builder/Reader/Rust edits, native ABI, release identity, policy rewrite, or separate state database. Costs: one CI Linux x86_64 Rust release build, Python import/install, and nine small same-wire input archives, negligible temp I/O; no meaningful performance credit.

## Alternatives and debts

A plain parser micro-example confirms the bytes-vs-str distinction but is **not** installed-product proof. Ordinary corrupted-index SHA trivially fails and cannot discriminate semantic policy. Integer-key injection fails default Python strict map-key admission before testing duplication, so it is a weaker control. This experiment does **not** establish generalized nested map, extension-bin, integer, arbitrary future generation, non-Linux, native recovery or 1.0 canonical MessagePack behavior. If the gap exists, return the smallest source-exact falsifier to PR #316/Issue #317; leave implementation ownership unchanged. Any repair must reject semantically ambiguous maps rather than choosing first/last, and preserve legitimate r24 golden archive behavior.

## Coordination / promotion

Root-string duplicate research is already owned by #316; this is the explicitly unmeasured **binary-key residual** and is intentionally science-only. No collision with #270 Reader composition or #283 constructor cleanup. No edits to `docs/discovery/STATE.json`, frozen science, independent owners, or release gates. Future full conformance and general/release gates remain separate.

**Quality ratchet:** preserve all 3 golden source SHA-256s, all physical blob bytes, and both authenticated index copies while isolating binary-key multiplicity as the only hostile difference; no fabricated product pass and no scientific rule changes after observation.
