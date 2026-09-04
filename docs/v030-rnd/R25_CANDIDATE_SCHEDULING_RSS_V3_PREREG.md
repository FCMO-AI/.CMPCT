# r25 candidate scheduling RSS A/B v3 — superseding frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge diagnostic / no release credit**.

## Supersedes

V3 supersedes V2 for causal interpretation only. V1 and V2 remain immutable invalid evidence in their preserved result records.

V2 repaired the tree-identity proof but its serialized arm patched `canonical.RC.ThreadPoolExecutor`. Canonical shipping instead binds `_overlapped_release_candidate_build` in the `entropygraph_v030_canonical_final` module namespace, so both V2 arms retained the same candidate overlap and serialized workers reported zero intercepted submissions.

## Frozen question

Unchanged: on deterministic `resemblance_hostile_v1 / 01_shifted_versions`, does serializing **only** the exact shipping G0-G4-versus-PrefixGraph candidate overlap materially reduce total fresh-process peak RSS while preserving the exact selected complete product artifact and all canonical semantics?

## Arms

- **Concurrent:** unmodified canonical shipping build.
- **Serialized:** replace only canonical-final's module-global `ThreadPoolExecutor` with a routing factory. When and only when `thread_name_prefix == "cmpct-v030-prefixgraph"`, return an inline executor; every other executor construction is delegated to the original executor unchanged.

This routing requirement is critical because canonical-final also uses its module-global executor for internal G0-G4 overlay work. V3 may not serialize or otherwise alter those internal executors.

## Frozen identity and semantic proof

Retain V2 exactly:

1. `research_tree_sha256 = canonical.RC.treehash(source)` (`research-content-tree-v1`);
2. `expected_verification_tree_sha256 = canonical.treehash(source)` (`canonical-filesystem-user-tree-v1`);
3. every final shipping product strongly verifies to the second identity;
4. exact semantic owners for PrefixGraph, G0-G4 and reader must match `PROFILE_ISOLATION`;
5. both arms select PrefixGraph;
6. paired arms must have identical complete bytes, physical SHA-256, verified tree and selection.

## Intervention proof

The serialized arm is valid only if:

- exactly one executor construction with prefix `cmpct-v030-prefixgraph` is intercepted;
- exactly one PrefixGraph future submission runs inline;
- every non-PrefixGraph executor request is delegated to the original executor;
- the concurrent arm reports no routing intervention.

The routing factory must preserve original constructor arguments for delegated executors.

## Workload, order and metric

Unchanged from V1/V2:

- deterministic shifted-version corpus built once by parent;
- two fresh-process repetitions per arm;
- order: concurrent -> serialized, then serialized -> concurrent;
- total fresh-process peak RSS is decisive; baseline-subtracted `ru_maxrss` is diagnostic only;
- wall time remains explicit debt.

## Decision thresholds — unchanged

- valid RSS reduction **>=20%**: support candidate concurrency/lifetime ownership;
- valid reduction **<10%**: retire inner candidate concurrency as the primary explanation;
- **10–20%**: ambiguous; no production scheduling change.

An invalid run earns no causal decision. No product source, representation, selector, admission, integrity, locality, recovery, corpus, threshold or release rule may change.

## Next boundary if retired

If V3 validly returns <10%, preserve that scoped negative and move to the already-observed **outer genuine-r24 versus r25/product lifetime overlap** in canonical shipping. Do not tune G0-G4 or PrefixGraph scheduling further without new causal evidence.

## Custody

This preregistration and its V3 worker/oracle/workflow become immutable once substantive execution begins. Any further defect requires a new superseding freeze.
