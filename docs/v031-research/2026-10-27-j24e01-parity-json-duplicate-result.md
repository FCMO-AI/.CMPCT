# J24E01 — exact-source result: contradictory JSON evidence fails closed

**Date:** 2026-10-27 UTC. **Research/product-candidate scope:** release-benchmark evidence ingestion only. **PR:** [#561](https://github.com/FCMO-AI/.CMPCT/pull/561) (DRAFT). Original owner [#306](https://github.com/FCMO-AI/.CMPCT/pull/306) and full admission composition [#328](https://github.com/FCMO-AI/.CMPCT/pull/328) remain separate. Published v0.30.0/r24 unchanged.

## Immutable ordering and comparator authority

Prospective fork/preregistration commit `923bfaba3f61fcdb38b652201d61f012ff607d30` precedes test `c749040a862d1de2f06ce0563580606714cc226d` and comparator patch `720932f334969d74d3d6d6526b37d14cd392de6c`. Original source-parent `84bcd4144e3cf95bbc66a9cb3df8c7c101b89bb9` (existing owner #306), original comparator Git blob `2cea1b4d0cfe52259e5bc6b870c8207b4c889610`; candidate comparator Git blob `22172ba4465b297bba54b0120f3419abe632cbd1`.

## Decisive evidence

[GitHub Actions source-exact two-host run 40435830138](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435830138): `SUCCESS` on Ubuntu 24.04 and Windows Server 2022 at exact HEAD `854824ce9ed957da0b246233a216cc9277d49065`, with actual `git show` original-source comparison, independent synthetic raw JSON strings, and actual comparator CLI. Each host reported **37 passed** in the focused new and inherited tests.

The original source produced **PASS on five ambiguous duplicate-member reports** (repeated timing, repeated corpus map, duplicate schema, repeated archive bytes and repeated logical input length). The candidate refused each as `duplicate JSON object key`; it preserved a valid unique-key A/A PASS and a genuinely measured +7%/+7ms unique-key FAIL, under existing zero-byte / >5% AND >3ms rules.

Original receipt links: [Ubuntu artifact 12703359981](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435830138/artifacts/12703359981), digest `sha256:64104f19cac2b0e76645e496eba0c6f654034fc30d20ce4441db7eb016278da0`; [Windows artifact 12703409519](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435830138/artifacts/12703409519), digest `sha256:2d9931053df23f58dd9b0709de73ddf49e2c9968bd8c09cb94c569919814c558`. GitHub verified artifact upload; these archived JSON observations were not independently downloaded/rehash-audited in this activation, so **do not** inflate evidence to external artifact-authentication credit.

A first two-host run [40435390447](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435390447) failed because the original-source duplicate-schema control used a real RED report and incorrectly predicted an original PASS. This was a **test expectation contradiction**, not an algorithm failure; the corrected A/A duplicate-schema case is now an authentic original-source false-green. A later two-host run [40435595698](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435595698) proved the independent comparison but failed to run pytest due to an unrelated CMPCT-wide `conftest.py` import requiring `msgpack` in a comparator-only environment. The final workflow uses `pytest --noconftest` solely for the standalone comparator tests; the inherited numerical comparator test still executes. Both reds are preserved in history.

## Interpretation and negative boundaries

**Decision: ACCEPT_SCOPED_JSON_EVIDENCE_GUARD; NO PRODUCT/RELEASE CREDIT.** This protects against an evidence-serialization false green rather than improving compression, archive size, create/extract CPU, RSS, or Reader safety. Unique-key forged/inaccurate numbers, missing corpus fingerprints and full workflow classification remain separate trust boundaries. It adds a simple dictionary membership test per parsed object, with no official full-product timing claim.

RFC 8259 §4 ([source](https://www.rfc-editor.org/rfc/rfc8259.html#section-4)) recommends unique JSON object names and explains why duplicate-name consumer behavior is not interoperable. Python 3.11's [`json.object_pairs_hook` contract](https://docs.python.org/3.11/library/json.html#json.load) permits checking decoded member names before last-wins collapse. Strict evidence admission is intentionally stronger than merely parsing syntactically valid JSON.

## Remaining gates and next action

The original comparator owner #306 and integration owner #328 were notified. The current PR is draft; its current HEAD (after this result-note commit) still requires exact-HEAD CI reconciliation, generic suite, performance admission/custody rules and legitimate integration decision. An administrative workflow SUCCESS that skips a substantive benchmark is **not** performance credit. The original source and frozen corpus/policy were not modified. No merge, version change, Discovery state change, or release promotion.

**Disproof:** any ambiguous duplicate accepted or valid same-input comparison misclassified, any changed normative timing/byte threshold, a changed source identity, or a failure of original-source provenance invalidates this scoped positive. **Quality ratchet:** original/source and candidate controls remain paired, independent CLI/parsing and inherited numeric cases retain their original strength, negatives remain visible.
