# J24E01 — prospective metadata-only extraction effect bound

**2026-10-28 UTC · preregistration before the first implementation byte**  
**Science only, no Reader/Builder/format/version/benchmark/policy/release change.**

## Authority and concurrency

Released source `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT v0.30.0, r24. Reader `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Main `docs/discovery/CONCURRENCY_PROTOCOL.md` and `tools/discovery_claims.py` are absent; `docs/discovery/STATE.json` is stale against extensive v0.31 work and its reconciliation is owned by #574. We will not alter that state. Owners #609, #615, #569, #573, #690, #699, #704 and separate defect courts #688/#693/#697/#700 remain authoritative for production fixes; this separate nonproduct branch owns only a prospective model/oracle and neither duplicates their Reader writes nor claims release authority.

## Primary question

Can one bounded **write-effect model**, derived only from authenticated-index-compatible logical rows and physical blob lengths, conservatively bound **logical output bytes actually materialized/linked** across direct, micro-PACK, fixed/CDC chunks, sparse extents, symlinks and hardlink chains *without* inflating logical contents, and reject invalid geometry before touching destination paths?

Known falsifiers: (a) #688 signed negative symlink; (b) #693 nonnegative undersized hardlink; (c) #697 undersized nonnegative symlink; (d) #700 sparse writes beyond ftruncate size. The existing Reader's `sum(row[4])` is a deliberately weak but accurate baseline, not silently replaced.

## Mechanism and challenger

For each regular storage mode, account for the maximum of declared length and all physically addressed positions. For a direct file or symlink, compare metadata size against the physical blob's uncompressed length and fail closed if inconsistent. For PACK/chunk/CDC, prove the declared slice or sum equals logical size. For sparse, prove extents are ordered, disjoint, in bounds, and sum of contained physical blob lengths equals each declared extent length. Resolve hardlink aliases as a directed acyclic graph to a regular physical file and require equal effective logical lengths. Count a hardlink's logical namespace size **even when physical storage is shared**. On any inability to prove the bound, reject rather than guess. Pure model only: no destination mutation, unpacking or hashing, and no claim that the wire index itself is trustworthy without a separate authenticated loader/physical-header proof.

Stronger simple controls: (1) historical declared-size sum; (2) a conservative `max(row declared, direct physical blob length)` without graph/extent proof; (3) strict existing `validation.preflight_archive`, which is a structure oracle and not an effects/planned-output admission on published Reader. Do not weaken any of them.

## Frozen prospective predictions / kill criteria

- **H1:** A model of fewer than 200 source lines can return the exact logical output budget on every valid synthetic member family, and reject (not merely overcount) all four known signed-index counterexample shapes before destination mutation, with *no* logical member decompression.
- **H2:** For 2,000 deterministically seeded held-out valid graphs (including 1–16 members, all storage kinds, aliases and empty files) the effect sum equals an independently calculated file/symlink output-size oracle. All independently injected invalid mutants must fail. A 50,000-alias chain must finish without recursive stack overflow and with O(n) traversal count.
- **H3:** The result is limited to a metadata-model rung. It cannot prove file-content SHA, actual BHDR and signed-index consistency, filesystem namespace safety, concurrent mutation/TOCTOU, publication atomicity or current full Reader promotion. These are explicit non-goals.

Any valid graph discrepancy, accepted known hostile geometry, unbounded alias recursion/cycle, or `>200`-line implementation loses H1/H2; preserve the loss instead of changing thresholds. A negative is decision-changing if it shows metadata-only quota requires physical-content read or an unaffordable ownership scan. The independent test must not call the proposed model's internal helper to construct expected answers.

## Costs and decision

Record exact path/source SHA, model lines, number of cases, invalid cases, runtime including 50k chain, and whether any product file changed. If positive, it proves only a potential unified preadmission design boundary and gives existing owners a reusable testable formula. If negative, retire the metadata-only quota unification and continue product-owner correction without threshold gardening.
