# ONE-G0.2 native segment-plan fusion — terminal result

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

## Mission lock

Test whether exact maximal +1 Ref/Surprise segmentation can be emitted in one native observation pass rather than a count pass followed by a second full scan, without changing the generic ONE representation.

Frozen authority: `docs/one/evidence/ONE_G02_NATIVE_SEGMENT_PLAN_FUSION_PREREG_2026-09-05.md`.

## Exact CI receipt

- branch source head: `258664325f154b07e2aec0d06b43280ae91025e9`
- workflow run: `33981130462`
- job: `101346425309` (`native-segment-plan-fusion`)
- conclusion: **success**
- job start/completion: `2026-09-05T17:32:09Z` / `2026-09-05T17:32:28Z`
- result artifact: `9973814004`
- artifact digest: `sha256:aa613741fda3ae7928392adedd1a3f297b68b93cbed5575f1047ea2cd982fdce`
- artifact name records the PR merge SHA `6006a8ffd609604a6d54035e13c1f688b821abbe`; the Actions job itself is bound to branch head `258664325f154b07e2aec0d06b43280ae91025e9`.
- ONE semantic/hostile test step: success.
- frozen native segment-plan gate step: success.

Because the benchmark exits non-zero on any frozen gate failure, the exact CI receipt establishes all preregistered inequalities: exact candidate/baseline/Python-oracle plan equality for all 14 rows, exact coverage, no mutation or overflow, candidate scan traffic <=0.51x baseline on every row, every >=16 KiB row <=0.70x elapsed, no row >1.03x, and no extra persistent state.

The connector available to this run exposes artifact metadata but not binary artifact contents, so exact CI per-row nanosecond samples are not recopied here. They remain in immutable artifact `9973814004`; this note does not manufacture unavailable row timings.

## Independent local corroboration (not CI timing authority)

A same-source native `-O3` rerun of the frozen C kernel reproduced the expected mechanism on the same deterministic cases. Candidate/baseline median elapsed ratios ranged from **0.4948x to 0.6448x** across 4–256 KiB, while modeled target scan traffic was exactly **0.5000x** on every row. These local timings are corroboration only; promotion authority is the green frozen CI gate above.

The causal result is stronger than a generic speed claim: the old path paid two complete target scans solely because it counted boundaries before emission. A preallocated output bound makes that first pass unnecessary. One-pass emission removes exactly one full target scan without weakening semantics.

## Hostile reviewer

This does **not** establish product writer speed. The microbenchmark still materializes a transient native segment array before Program/wire construction. On the deterministic `fragmented_every96` case, the local rerun observed 5,464 segments at 256 KiB, or 65,568 bytes of transient `Segment` storage (`sizeof(Segment)==12`). Relation admission, arbitrary pair discovery, Program allocation, actual ONE wire emission, authentication, and comparator supremacy are outside this claim.

Therefore the result advances only the one-pass segment-plan construction principle. The next causal owner is transient plan materialization/readback, not another segmentation threshold.

## Decision

**ADVANCE `native one-pass segment-plan fusion`.**

Next falsifier: stream the same generic Ref/Surprise control representation directly during the native pass and compare byte-for-byte with one-pass-plan-then-encode. Charge output bytes identically and measure eliminated transient plan bytes/readback. Do not add a relation opcode and do not treat a research control stream as a new reader ontology.
