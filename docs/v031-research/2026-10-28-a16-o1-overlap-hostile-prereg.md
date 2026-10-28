# A16-O1 — co-owner overlap hostile falsifier (prospective)
Date: 2026-10-28 UTC
Status: frozen prediction BEFORE implementing or measuring this new structural perturbation. Science-only, no product/format/threshold/release changes.
Parent: A16-O0 PR #683, first prereg b9ead845f328e536113d1b74282295ca59f1d0f6; recorded O0 result b4970a067bce7e9bfa7cb641f60ef9a73e68b06f.

## New causal question
A16-O0 groups consecutive chunks whenever both belong to the binary globally-shared class (each appears in >=2 member files). But two chunks each reused by multiple owners need not be reused **together by the same owners**. Coalescing can destroy sharing rather than merely shift an encoding cost. Does a wholly shared, high-entropy structural hostile cause >5x full-envelope size amplification for SEGREF vs the fully charged compact fixed-chunk CHUNKREF control, despite all individual chunks being shared?

## Fixed input independent of outcome
Produce 32 source members of 16 x 4 KiB blocks. For each logical block position j, generate exactly four high-entropy 4KiB blocks with deterministic seeded random bytes. Assign each candidate to eight of the 32 members through a separate per-position seeded permutation of [0,1,2,3] each repeated exactly eight times. Use independent seeds 20261030 and 20261031. This guarantees every chunk is shared between eight different members, but does not guarantee that entire concatenated 64 KiB members repeat. No fixture identifier participates in runtime segmentation or representation selection; only source bytes and cross-member equality count.

## Frozen prediction and control
With the exact existing A16-O0 run coalescer (no admission threshold change), all 16 blocks in every member are classified shared, hence one 64 KiB segment/member, nearly unique. Fixed CHUNKREF may reuse at most 64 physical 4 KiB owners across all 32 members. Predict on *both* seeds that SEGREF complete bytes >=5.0x CHUNKREF. All 32 members must reconstruct exactly, with independent detached parsing, per-owner and per-member SHA-256 and no hidden free information; complete bytes include all compressed streams, ownership metadata, hashes and refs. Direct fallback must continue to be eligible, but the ungated SEGREF path is the target of this falsifier. If amplification is <5x or semantic identity fails, mark hypothesis falsified, do not change threshold. This is a research adversary, no product or universal inference.

## Decision / kill
>=5x amplification proves binary sharing-class coalescence cannot be an unconditional ownership rule. A further family would need co-owner intersection-aware grouping and prospective cost-bounded admission; this single adversary does not prove those routes worth productizing. Combined with the A16-O0 original joint threshold failure, default to PARK without nearby threshold gardening. No edits to shared Discovery STATE or other PRs; preserve all losses.
