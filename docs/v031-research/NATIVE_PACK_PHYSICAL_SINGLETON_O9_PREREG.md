# O9 — physical owner census and single-distinct micro-PACK admission falsifier

Date: 2026-10-24 UTC. **PREREGISTERED BEFORE NEW O9 IMPLEMENTATION OR MEASUREMENT.** Source baseline is PR #330 head `779b5158aa40fe842e746848731f16f4f6fce36e`, inherited product/C consumer source from PR #327 `030bd50aff682592f67eba1dc5376b83bfe83fae`. O8, O8b, O8c and their original preregistrations/results are immutable controls, not to be rerun with changed hypotheses.

## Primary scientific question

O8c's exact same-path court found normal micro-PACK 1491 B versus inherited no-PACK 1422 B (+69 B) on 256 identical text files, but 26,308 B *saved* on 256 independent high-entropy text files even though native **Zstd** group admission was zero. Does the actual revision-24 physical owner ledger resolve this paradox (including RAW physical PACK), and is the *single-distinct-content physical group* a generically provable source of unnecessary per-member recipe bytes that can be avoided without deleting a compressibility win?

## Two distinct evidence rungs

**A — source-exact physical census:** Build the four already frozen O8c .txt source families, using unmodified `Builder` with default and documented `CMPCT_MICRO_PACK_MAX_FILE=0` policies and reproducible single-worker settings; parse the actual committed r24 index and physical `BHDR` records. Report file-table storage types, distinct content SHA count, distinct referenced physical blob IDs per kind, physical S_PACK codec distribution (RAW/ZSTD/other), physical sizes, complete bytes, index compressed/uncompressed and blob record counts, including repeated hash equality. Independently read every archived logical member and compare SHA against source. Explicitly assert *nothing* about native C batching based solely on physical PACK membership; native O8c Zstd-only count remains separate.

**B — held-out reversible singleton bypass oracle:** In test code only, subclass the exact inherited Builder and, *after* invoking its unchanged `_build_micro_packs`, revert only S_PACK rows with offset 0, whole-pack length equal to that one physical candidate, and an unambiguous `.cmpct-pack` hint to S_BLOB of the **same SHA**; remove only that singleton pack hint. Do not change the Builder or its fallback/codecs/thresholds. This tests a pure ownership/admission alternative, NOT a new canonical encoder. Compare full archive and create time against unchanged default and no-PACK controls on original four families and independent held-out shapes: 64/256 repeated all-equal high-entropy and compressible files; one-vs-two-distinct blobs with repeated paths; a mixed two-extension tree. Never key a proposed product policy off family names, extensions or fixture hashes. Distinct physical group count comes from content address, not archive path identity.

## Predictions and falsifiers

- O8c independent high-entropy normal will contain physical S_PACK references predominantly to RAW-coded physical blob(s), explaining why zero native Zstd batches can coincide with storage reduction; **falsified** by actual physical records showing no PACK or only Zstd.
- O8c duplicate normal will have one physically distinct original payload, S_PACK references and extra logical recipe/index cost; **falsified** if its physical census differs.
- A one-distinct group should have no inter-item redundancy to earn, but its `.cmpct-pack` hint changes codec levels; the bypass **may lose actual archive bytes** on some source shapes. Any reproducible held-out loss invalidates *unconditional* product admission promotion and earns a narrower/counter-mechanism question, not threshold gardening.
- Stronger control `no-PACK` may beat both alternatives on one shape and lose severely on others; retain all negative rows.
- Any unreadable archive, wrong logical path/set/bytes, nondeterministic same-policy archive SHA, file-header/index disagreement, mutated source, altered product blob SHA, hidden environment contamination, omitted negative, or changed release-frozen gate invalidates the experiment.

## Whole-system charge and scope

For each corpus/policy capture exact whole archive bytes, compressed/uncompressed index, physical blob payload+framing bytes, total decoded logical bytes, unique physical content counts, build wall and CPU, and complete source-tree SHA equality using original Reader. Pair reproducible build runs per policy for hash identity and timing; do not infer SSD physical I/O, universal extraction gains, full RSS, Windows compatibility or release promotion. Separate oracle-level evidence from product results. Do not claim official ABBA or release parity: O9 is a narrow structural and small-product falsifier. Keep original r24 format and unchanged 0-byte promotion rule.

## Concurrency and continuity

O9 is a *new independently preregistered subquestion* on the existing PR #330 research lane, not an overlay onto active native owner PR #327/#326 or BDC #242. No writes to shared `docs/discovery/STATE.json`; it remains a staleable cache. Do not modify product source, original O8/O8b/O8c tests/docs, historical release fingerprints or comparator. Commit a stable receipt with exact O9 source/head/CI/artifact identities and empirical strongest negative after the experiment. Stop or narrow single-distinct admission if a simpler unmodified control wins or held-out regressions undermine global value.

## Cheapest decision unlocked

A rigorous physical census can determine whether **RAW pack** is responsible for the paradox before any algorithmic optimization. A bounded singleton-only A/B can either justify a tiny generalized product patch with explicit regression debt, or falsify unconditional singleton bypass before paying for a costly production refactor.
