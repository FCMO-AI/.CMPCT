# J24G87 — factorized temporal member-plane checkpoint O0 (prospective preregistration)

**2026-10-30 UTC. Immutable before results.** Research-only child of J24G86 PR #838 exact 8c8285503e01cdcbb5645373b23cf038ce06f15d. Separate representation question; do not reclassify J24G86 complete-index negative or modify its thresholds. Published main remains v0.30.0/r24.

## One primary scientific question
Can a signed checkpoint store only the **current mutable member/file plane**, referencing by an authenticated 32-byte SHA256 root the already present immutable header-index planes (blobs, recipes, dict_blob, fsmeta, features), rather than redundantly serializing all of them? This requires **new explicit representation semantics** if ever materialized, not a legal r24 kind-0 checkpoint. Do not claim current Reader can read it.

## Frozen prediction and decision criterion
For the exact two source archives already authenticated in J24G86 (8,192 middle deletes and 32,768 tail deletes; 65 original physical footers), model K in {8,16,32}. A checkpoint at K must supply complete current file rows, explicit stable plane-ref digest (32 bytes), an 8-byte identity/offset pointer, a 16-byte format/version/flags allowance, and the ordinary 68-byte signed footer, plus all compressed bytes; deduct only the genuinely replaced delta body/footer. Reuse immutable original index bytes already physically resident (do not assume a gifted uncharged dictionary). Include every actual surviving file row with original storage descriptor. Same original source SHA for both variants.

A K32 mechanism survives O0 if it reduces worst-case logical delta applications >=2x and adds <=5% complete archive bytes on **both** authentic cases. K8/K16 are reported as diverse cost frontier but are not required to survive. Even a positive O0 earns no product credit without a real executable decoder / recovery court. A failure of K32 at this generous low rung retires the simple factorized-checkpoint model for these histories.

## Falsifiable semantic admission
Before pricing, reconstruct generation64 complete index from physical footer as in J24G86. Require every non-file plane to be identical to authenticated initial base, byte/structurally; require no new physical blobs in any tested delta and no changes to storage descriptors. An external mutation/add to mutable blob/recipe/fsmeta owner must deny the reference and force full index fallback. A reference to only source SHA but lacking authenticated source availability/offset is not a valid product design; this O0 counts the extra identity pointer and remains research only.

## Controls, alternatives and debt
Controls: original historical K64 and charged full-index checkpoints from J24G86. Both original signed chains, CMA4 content hashes, final exact file membership and source SHA remain authority. Compare worst-case logical delta applications only, never claim wall time improvement. Test a tampered reference/root digest as a negative. A positive would create new decoder/root-resolution complexity, possible fsmeta path-identity coupling, crash-tail/compaction/append ownership, memory/dependency depth and old-reader incompatibility debt: they are not deferred silently into an unpriced 0-byte story. Do not change current code, format, benchmark, release gate, policy, discovery state or owner branches.

## Concurrent ownership
No narrow open claim identified on factorized immutable-plane authenticated temporal checkpoint. #834 owns path-frontcoding, #795 signed replay, #836 cooperative writer lease, #574 discovery STATE. This is a distinct no-product O0 body+footer accounting oracle.
