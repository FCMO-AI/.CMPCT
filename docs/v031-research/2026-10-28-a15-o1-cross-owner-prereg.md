# A15-O1 — Preregistered cross-member physical ownership falsifier

Date: 2026-10-28 UTC
Status: FROZEN QUESTION BEFORE NEW EXPERIMENT CODE; scientific oracle, NOT production or format work.
Parent: A15-O0 PR #677 exact `6b1eab092955d995e1099aefd9d5fadcac57df9f`.
Published control: main `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / r24.

## Why this question instead of more A15 synthetic transforms?

O0's bounded typed grammar succeeded on independent member-local byte transforms but offers no external owner references. Its result already admits that it does not prove a smaller universal Reader. A decisive cheap structural-transfer fork is whether independent typed frames can preserve **cross-member physical deduplication** and member-selective reconstruction as effectively as the simpler established shared-chunk reference table. If not, this *version of the grammar* cannot subsume the existing ownership model without adding at least one more primitive; no further opcode tuning is justified as universal-reader evidence.

## Frozen question, prediction and kill

Compare two exactly reconstructing, fully charged, member-selective archive envelopes using the same synthetic source, libzstd-19 and per-member SHA-256:
- **A15-O0-direct**: byte-exact O0 grammar shape (9-B header, shared direct program entry, 42-B/member descriptors and independent compressed frames); no cross-member ownership or optional transform search. This is a generous direct fallback for the original A15 grammar and avoids charging irrelevant unsuccessful transform-search CPU.
- **CHUNKREF control**: one physical owner per SHA-unique fixed 4 KiB chunk; a fixed bounded index of per-member owner refs, per-owner SHA-256 and compressed frame, per-member SHA-256 and original size. Charge *all* headers, descriptors, frames and references. It is a research control, not a claim to reproduce CMPCT's current r24 exact bytes.

Deterministic random, high-entropy 32-member groups × 16 chunks of 4096 bytes in three prospective regimes, plus an independent held-out seed:
1. identical members (all 16 chunks shared);
2. partial commonality (12 globally shared chunks plus four unique chunks/member);
3. distinct unrelated chunks (no sharing expected).

Prespecified scope of scientific positive/negative: CHUNKREF must be <=70% of A15 direct bytes in both shared regimes and must not win by >=5% in distinct regime; all members must reconstruct byte-identically and verify SHA with independently implemented referee, and all negative/invalid envelopes must fail closed. If a result violates the prediction, report it and refine the model, not the threshold. This is a deliberately direct structural-coverage test; it is **not** a novel compression claim.

Additional observations, not promotion gates: member decode CPU/wall, source/build time, actual unique owner count and selected-member decoded work. Any sample noise or partial failure stays visible. Avoid comparing a single solid Zstd stream against member-selective formats.

## Controls and oracle ladder

Cheapest mathematical fact: each independent O0 member record must carry a compressed payload even when another member has identical bytes; it contains no authenticated owner-ref opcode. The empirical court tests *magnitude*, descriptor overhead and realistic crossover against fully charged chunk references. The control's own explicit SHA, bounds and reference protection must not be omitted. A typed IR with an added REF opcode is a **new question** and does not inherit O0's low-cost result.

Predicted extension needed for product relevance: bounded REF with authenticated physical-owner lifecycle and optional direct fallback. O0's existing code already supplies strong bespoke direct controls, so this test cannot assert source/maintenance simplification. Falsification of *O0 as a universal storage grammar* need not retire A15 as a larger design space.

## Attack / integrity / scope

Referee must not import producer. Mutate one owner ref to an out-of-bounds value, mutate owner payload bytes, mutate a member digest, truncate, append data, and attempt incompatible original-size. Refuse accepted wrong bytes or false source identities. Preserve exact raw results and provenance; negatives are first-class.

No source under `src/`, `native/`, frozen benchmarks, reader/format/release policy, shared Discovery `STATE.json`, threshold, or owner PR may change. The reserved active lanes #653, #662, #676 and discovery #574 remain untouched. Before any late shared write, check exact branch HEAD and new concurrent PRs.

## Decision budget

Stop at the cheapest empirical test that can distinguish whether *this precise independent-frame A15 grammar* can preserve cross-member ownership economically. No automatic promotion, no source complexity claim, no full Reader equivalence, no byte claim about published CMPCT, no merge/release.

disproof: Wrong original SHA/bytes, accepted malformed ref/envelope, uncharged descriptor, invalid comparability or failed held-out criterion invalidates any positive.
quality-ratchet: unchanged published product; research carries no release credit.
