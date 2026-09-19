# v0.30 ML full-extraction verification-fold productization — preregistration

Status: **PREREGISTERED / NO PRODUCT CREDIT**

Authority base: `agent/v030-authoritative-integration` at `9c5227b645e646567b7963a9e90aad784a7ee430`.

## Prior decision-changing evidence

PR #143 measured corrected bounded valid-input headroom on the frozen ML workload: exact tree identity with 26.9521% / 26.0795% wall reduction after restoring physical `usize/csize` bounds (run `35423432030`, artifact `10579015495`). PR #145 then paid the hostile/scope rung (run `35426251534`, source `015a2e8788712a39a0e4d724efc26cf74aa6ee55`, artifact `10579345691`): payload SHA, physical size bounds, record CRC, post-CRC in-memory corruption, transactional rollback and corrupted-payload `strong_verify` all failed closed. The global research monkeypatch was also decisively rejected as product architecture because a logical-SHA-only mutation leaked deferral into `strong_verify` and selective reads.

The preserved release debt is ML extraction `1.421556x` versus the unchanged `1.25x` ceiling. Closing it requires about 12.07% relative whole-product reduction, or about 45.51% transfer of the corrected local oracle saving.

## Product hypothesis

A **strict-by-default, explicit reader policy** can defer only nested semantic SHA proofs that are subsumed by the mandatory authenticated terminal streamed-tree decision during complete transactional G04 extraction, while preserving every existing bound and keeping all non-complete-read surfaces strict.

The implementation must remain one reader, not a copied oracle. No caller-name heuristic, global monkeypatch, workload identity, format-byte change, threshold change or public flag is allowed.

## Minimal ownership seam

1. `_G04Session(..., verify_nested_semantic_sha: bool = True)`; strict default.
2. `record()`: payload SHA, codec admission, physical `usize/csize`, transform bounds, inverse, physical/logical size and record CRC remain unconditional. Only the reconstructed-record SHA comparison may be conditional.
3. `node()`: dependency/recipe/source/output bounds and exact reconstructed length remain unconditional. Only the node SHA comparison may be conditional.
4. `_consume_g04_file(..., verify_file_sha: bool = True)`: path safety, declared size accounting, output writes and terminal `tree.update(raw)` remain unconditional. Only per-file SHA allocation/update/final compare may be conditional.
5. `_stream_g04(..., verify_nested_semantic_sha: bool = True)` passes the policy explicitly to the session/file consumer. Default remains strict.
6. `entropygraph_v030_release_reader_policy.extract_verified_into_staging()` alone opts out for G04 because its caller owns an unpublished staging tree and requires the terminal streamed-tree identity before publication.
7. `strong_verify`, ordinary reader extraction, `read_member` and `read_member_with_stats` remain strict by default. PrefixGraph is untouched.

## Falsifiers / kill conditions

Kill or narrow this productization if any of the following occurs:

- archive/tree identity changes on valid input;
- payload SHA, physical `usize/csize`, CRC, transform/recipe/node bounds, declared file size, output budget, path safety or terminal tree checks are weakened or bypassed;
- injected post-CRC reconstruction corruption can publish or damage the pre-existing destination;
- a logical-SHA-only mutation is accepted by `strong_verify` or selective reads;
- ordinary strict reader extraction accidentally inherits deferral;
- fresh-process whole-product ML extraction fails to retain enough of the measured headroom to materially close the unchanged release gap, after CPU/RSS/temp-I/O accounting;
- another inherited release property regresses.

A performance win cannot rescue a safety/scope failure.

## Required evidence ladder

Before product credit:

1. implement the explicit strict-default policy in the owning reader/promotion facade with no duplicate reader;
2. unit/scope tests proving only verified staging G04 extraction opts out;
3. hostile matrix: payload auth, physical size policy, CRC, post-CRC fault, logical-SHA-only scope mutation, path/size/resource failures and transactional rollback;
4. exact valid tree/archive identity and selective/`strong_verify` strictness;
5. fresh-process product A/B with wall, CPU, whole-process-tree RSS and temporary-I/O accounting on the frozen ML workload;
6. unchanged runtime/extraction authority on all required workloads;
7. after source freeze, regenerate fingerprint-bound shared-build/runtime and other strict-release receipts together rather than paying custody twice for an intermediate fingerprint.

## Concurrency / claim

This branch claims only the narrow scoped productization of the already-earned ML verification-fold mechanism. It must re-read authoritative head before late writes. If another branch lands the same reader-policy mutation first, reconcile/continue it rather than duplicate implementation.

## Claim boundary

This preregistration changes no product source, archive bytes, release threshold, evaluator, format, reader semantics or release status. Production remains v0.29.0 / r24; v0.30 remains merge/tag/version/publish locked until strict current-fingerprint authority says otherwise.
