# POSIX Byte-Namespace O1 — Prospective Whole-Tree Reconstruction Court

Status: preregistered research, **not a revision-24/25 format proposal or product implementation**. Mission: test whether a separately versioned, byte-aware metadata namespace can faithfully reconstruct *whole POSIX trees*, beyond O0's isolated segment codec roundtrips, with a bounded and authenticated decoder.

## Authority, control and concurrency
Canonical repository `FCMO-AI/.CMPCT`, shipping v0.30.0/r24 unchanged. Source ancestor: independent [PR #254](https://github.com/FCMO-AI/.CMPCT/pull/254) exact HEAD `2f256fe79785803a58c62e3422b226c4a747b888`, [Issue #252](https://github.com/FCMO-AI/.CMPCT/issues/252). Prior O0 has 4,314 segment roundtrips, casefold and long-path counterexamples, independent hosted court run 39951843878. Work is *new whole-tree manifest/decoder evidence*, with no edits to the #254 owner. Other current independent scopes (#324/#326 native MessagePack ambiguity, #327 native PACK consumer, #328 gate evidence) are non-overlapping. No claim to an imaginary shared agent lock. Reconcile the owner head and avoid rewriting shared `docs/discovery/STATE.json`.

## Primary falsifiable question
Can a *research-only* typed MessagePack byte-path manifest, with independent payload ownership and bounded decoder, encode, authenticate, validate and reconstruct a real POSIX tree including invalid-UTF8 raw paths, hardlinks, relative symlinks and raw xattr keys, with exactly matching **filesystem byte identities**? Can the corresponding O0 canonical escaped-string control do the same under the same semantics and reveal the full-manifest exported byte cost?

### Prediction
1. Both O0 wire grammars produce identical *physical* source tree under a strict Linux byte-path decoder and exact-type canonicality checks, if explicit version dispatch and preflight precede publication.
2. Full manifest size / decoder cost need not match the isolated segment byte result. A control made of valid-UTF8-only names must continue to roundtrip in the same model; original r24 is not expected to support raw byte names.
3. Deliberate alias/traversal/duplicate/hardlink/symlink/xattr-invalid structures are rejected **before writes**. POSIX-only malformed data never silently maps to a different Windows/casefold name.
4. The initially cheaper-looking escaped-name grammar is likely inferior for invalid-UTF8-heavy paths; report entire serialized manifest + compressed bytes and payload identity, not just per-key bytes.

### Simpler control / rival explanation
O0 isolated codec bijection plus conventional pathlib can explain successful *name* roundtrip without any valid filesystem reconstruction. The stronger test is source-to-wire-to-fresh-filesystem and an independent before/after byte-name tree inventory. A single lexically safe copy of source tree that skips wire conversion is an external baseline, not a format alternative. Standard UTF-8-only r24 path handling remains the practical incumbent for accepted trees.

### Kill/narrow and adversarial boundaries
Any altered filename byte, xattr byte, symlink target byte, hardlink identity, regular data SHA, path owner, duplicate index key, or unauthorized destination write kills the full-tree claim. Tests must reject malformed MessagePack (including duplicate keys), path `.`/`..`/`/`/NUL, unknown type/tag, alias under declared target casefold mode, hardlink pointing outside or to nonexistent owner, xattr key collision and oversized control. Preflight must be side-effect-free; do not claim race safety on concurrently mutated directories. Unsupported xattrs may be marked host-unavailable, but not silently certified. Preserve filename component <=255B and total path <=4095B in this detached model; do not silently redefine revision 24/25 ceilings.

### Evidence ladder and measured costs
Rung: structural and actual-POSIX filesystem oracle with exact raw materialized tree and held-out perturbations. Source tree, record count, per-mode packed manifest bytes, compressed manifest bytes, payload bytes, full *detached* artifact budget, serialization/reconstruction wall and memory metrics where available, and hostile rejects. Compare same tree and same payload for typed and escaped variants; emit immutable manifest fingerprint for reruns. Hosted Linux Actions court if available; cite exact commit SHA/run/artifact. No release/product/compatibility credit until real Builder/Reader/Rust, genuine CMPCT bytes, A/B performance, portability, updates/recovery, and release gate.

### Future decision
If complete POSIX tree reconstruction survives, preserve as a versioned-namespace design seed and pursue a Rust/Python independent conformance grammar with explicit target OS admission. If alias/security/materialization losses occur, preserve a negative outcome, retire or narrow unsafe grammar and prefer canonical typed bytes. Never change current revision 24 or O0 oracle to manufacture a favorable result.
