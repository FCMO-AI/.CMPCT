# J24B03-H3 — unsupported RAW physical flags and reserved bits

Date: 2026-10-27 UTC. **PROSPECTIVE** bounded conformance/hardening question on existing owner PR #609. This prediction precedes H3 instrument and product changes; original J24B03/J24B03-H/H2/A/P/M/M2 evidence, thresholds, original frozen sources, and failures are immutable.

## Baseline and tension
Released r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0` and current guarded Reader source Git blob `33deb74e196f7e40aa8351b6ec426a24255d5eec` unpack physical `BHDR=<4sBBHQQII32s>`. Strict physical `preflight_archive` rejects nonzero `flags` or `reserved`. Both original and guarded direct RAW `read_range` check magic, codec, sizes and metadata but **not** `flags/reserved`. `_blob` and RAW extraction helpers likewise do not consistently enforce these two control fields. Static inspection alone is not a hosted behavioral result.

## One primary falsifiable question
On exact signed-index r24 bytes with otherwise intact logical index, frame payload, CRC, SHA and lengths, does independently altering only RAW physical `flags` or `reserved` make the published and pre-H3 guarded Readers accept selected range bytes that strict preflight rejects? Can a **minimal** fail-closed guard reject all unsupported controls for direct selected reads (regular/symlink) and RAW extraction helper without damaging valid published records? Where possible also reject full ordinary decoded-blob reads on the same unsupported physical fields.

## Prospective predictions, controls, kill conditions
- Independently generate one valid RAW `K_FILE` and one valid RAW `K_SYMLINK` via existing Builder-independent `wire()` court. Both control archives must remain byte-exact on `read_range(name,7,8)`, `read(name)`, `verify()` and strict `preflight_archive`.
- Mutate only one field of the physical header at a time: `flags=1`, `flags=128`, `reserved=1`, `reserved=65535`; 2 kinds × 4 = **8** hostile inputs. All retain the same authenticated indexes and byte-for-byte physical payload, and strictly fail `preflight_archive`. Preserve the actual historical and pre-H3 candidate outcomes without imposing a false prediction of historical behavior.
- Stronger control: full payload SHA and physical header changes must be independently rechecked with stdlib-only parsing and archive hashes. A selected/full accepted malformed archive after the fix is a candidate correctness failure for that operation. A rejected/altered good control is also a failure.
- Distinguish direct-selected, full ordinary reads, verified extraction and preflight. A green targeted test **does not** establish universal hostile header completeness, mutable-inode safety, whole-product CPU/RSS parity, full r24 release gates, or merge authorization.
- No evaluator loosening or retrofit to historical H. Direct fast path must not acquire a per-read whole-file SHA merely for these bits. Preserve release version/format and other owners' Reader branches.
- If source already rejects these controls through an earlier path, retire the conjectured gap and keep the negative. The cheapest decision rung is independent wire-level derivation plus a source-exact hosted A/B; only then consider an O(1) product guard.
- If material per-query/read performance debt appears, preserve it, isolate its owner and do not promote until the inherited performance gate is satisfied.

## Concurrency and scientific scope
This is one bounded *different-field* physical-control extension in existing #609; not a new competing Reader implementation. #569 owns composed chunked Reader and ~27–28× cold-open debt, #615 owns hardlink aliases; #574 owns Discovery STATE reconciliation. No new state cache, changed policy, format, release, benchmark criterion or human data. Evidence must include exact source SHA, original artifacts and platform results; pending CI is never PASS.
