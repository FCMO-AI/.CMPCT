# O31 — canonical hardlink owner resolution and inherited full-suite red gates (preregistration)

Date: 2026-10-24. Baseline: PR #381 / O28 at `9c9cecc6c21dc741e57188076ea43dc0ede6425b`, Reader blob `c7850c08c7bb27563955c6e2294b8c17c140d0a2`. Format r24, v0.30.0 released, v0.31 development. This record precedes implementation.

## Primary scientific question
Can ordinary Reader use the **same canonical logical hardlink owner identity** as strict preflight and extraction, without weakening the eager rejection of cycles/invalid owners, without reintroducing quadratic or recursive walks, and while preserving the complete inherited O25/O27 security and destination contracts?

## Baseline / falsifiable prediction
PR #383 / O29 (source `997705a0308f9be7295f4f0f83d7f07a68249188`, Actions `40133660256`) reproduced on Ubuntu/macOS/Windows a genuine SHA-committed r24 archive accepted by `preflight_archive` but rejected at ordinary `CMPCT` open when hardlink target uses `sub\\owner.bin` instead of canonical `sub/owner.bin`. PR #381 source also has two full General Tests reds (Actions `40133108686`): (i) a short intentionally malformed row raises IndexError before the inherited canonical-duplicate error; (ii) the validator-held-out directory-target test still expects an invalid graph to fail at extract rather than earlier Reader open. Official parity aborts at this pytest gate before any measured benchmark (`40133108577`).

Prediction: a per-index canonical-to-raw owner map at open will accept both signed spelling variants, route existing read/SHA surfaces and physical hardlink extraction to the same terminal raw owner, and preserve early failure on unsafe targets, cycles, missing/non-regular owners and collisions. Postponing malformed-row classification until **after** canonical collision detection preserves inherited duplicate error priority; explicit malformed-row rejection closes a short-row omission. The directory-target test must strengthen the rejection stage, not relax the adversary.

## Alternatives / stronger controls
1. Raw-key-only owner resolution: cheaper, but O29 already falsifies compatibility with strict authenticated preflight.
2. Normalize target only for read, leaving extraction independent: rejects real product reconstruction and permits semantic divergence; not accepted.
3. Invoke full preflight on every Reader open: redundant entire-tree work and higher complexity; compare only if bounded map fails.
4. Reject backslashes in strict preflight: breaks an already admitted r24 lexical class and weakens format compatibility; prohibited without normative migration.

## Cheapest decisive evidence
Build on unchanged #381 source, reproduce exact O29 signed physical archive control, add product-fixed positive opening/read/range/SHA/extraction and hostile bad-target/collision checks. Preserve original O25 and O27 tests unchanged and exact-source bound. Run multi-OS focused GitHub Actions, full General Tests, original signed-tree tests, Native/Fuzz and official parity as independent gates. Fail if any inherited safety test breaks, same-archive bytes/contents diverge, unsafe target is accepted, canonical alias collision is allowed, or new cold/RSS/latency debt becomes material. Source/provenance fixture identity remains first-class. Never alter format or promotion rules.

## Costs and limits
Extra canonical-to-raw path lookup O(number of entries) memory at Reader open; anticipated removal of duplicated extraction hardlink graph traversal. No claimed performance win without direct measurement. No race-safe destination or source snapshot claim. Owner PRs #378/#380/#381 and scientific PR #383 remain untouched; this is an independent prospective **product follow-up**, not overwrite or merge. State cache not a lock; reconcile source before every write.
